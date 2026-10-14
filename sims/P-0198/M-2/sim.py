#!/usr/bin/env python3
"""P-0198/M-2 CSR — cycle-level Rendezvous–Grant SimPy model.

Cycle-accurate (card + T2 spec §5 / Dr.Sim must-verify):
  per-cycle per-active-CAM Dat_beats_held (must stay 0),
  same-cycle RENDZ reclassify vs any payload reject-and-orbit,
  4 dedicated FSM items × independent timeout; concurrent_live_cam ≤ 4,
  Classifier + FORCE_FALLBACK notify bounded cycles,
  GRANT emit + static order-table window (no arrival oracle),
  endpoint fold RF/cache port contention (no zero-latency reduce),
  alltoall segmented GRANT residual buckets/percentiles,
  warmup + 12+2 / four-ring / 512 B / ost 256|512 envelope.
Black box (假设 H-RING-BB): hop=1, clock UNKNOWN, HBM/coherence/D2D omitted.
T2 analytical model is NOT on main (PR #66). Compare uses signed audit
pins (PR #68) + spec §3 formulas; never treat card-claim bands as measured.

Orthogonal to M-1 CBC (T3 淘汰, PR #62/#64) and M-5 CRRF. Do not mix.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import simpy

_HERE = Path(__file__).resolve().parent
_SIMS = _HERE.parents[1]
if str(_SIMS) not in sys.path:
    sys.path.insert(0, str(_SIMS))

from _lib.stats import rel_err  # noqa: E402
from _lib.t2load import load_csr_t2  # noqa: E402
from _lib.workloads import SEED  # noqa: E402

CHI = ("Req", "Rsp", "Snp", "Dat")
DIRS = ("CW", "CCW")
CAM_STATES = ("IDLE", "COLLECT", "GRANT_PENDING", "GRANT_SENT", "FORCE_FALLBACK")
P2P_CLASSES = ("uniform_read", "uniform_write")
COLL_CLASSES = (
    "broadcast",
    "gather",
    "reduce",
    "allgather",
    "allreduce",
    "alltoall",
)
CLASSES = P2P_CLASSES + COLL_CLASSES
FANIN_DOM = {"gather", "reduce", "allgather", "allreduce"}
SPINE_ELIGIBLE = FANIN_DOM | {"alltoall", "broadcast"}

N_CAM = 4
N_TOP = 12
N_BEATS = 8  # 512 B / 64 B flit
TIMEOUT_DEFAULT = 255
BITS_PER_CAM = 16 + 12 + 3 + 8
CAM_BITS = N_CAM * BITS_PER_CAM
BYTES_PER_TXN = 512
TREE_ARITY = 4
CLASSIFIER_LAT = 1
CAM_MATCH_LAT = 1
FF_NOTIFY_LAT = 1
GRANT_EMIT_LAT = 1

# Published T_off (ns) — YAML + data.json off. Absolute ns are T2-only.
T_OFF = {
    "uniform_read": 4403.2,
    "uniform_write": 4834.6,
    "broadcast": 492.0,
    "gather": 537.2,
    "reduce": 537.2,
    "allgather": 1668.6,
    "allreduce": 990.6,
    "alltoall": 4098.0,
}

# Signed T2 audit (PR #68, tip e6d8ca8 / PR #66). card-claim is NOT signed.
T2_SIGNED = {
    "cam_dat_occ": 0,
    "retention": 0,
    "n_cam": 4,
    "invariant_ok": True,
    "a2_f_ov": 0.0952,
    "a2_f_to": 0.0000,
    "a2_f_grant": 0.9048,
    "a5_f_ov": 0.3983,
    "a8_f_ov": 0.5746,
    "a8_card_claim": "INVALID",
    "gather_r": 0.5386,
    "gather_t_hat": 289.3,
    "allgather_t_hat": 898.7,
    "allreduce_t_hat": 533.5,
    "a2a_tree": 0.6932,
    "a2a_res": 1.0,
    "a2a_mix": 0.8159,
    "gate_off_r": 1.0362,
    "gate_off_tax": 0.5500,
    "spine_off_hard": True,
    "spine_off_t_off": 537.2,
    "spine_off_t_on": 289.3,
}

CARD_CLAIM = {
    "gather": "0.45-0.80x",
    "reduce": "0.45-0.80x",
    "allgather": "0.45-0.80x",
    "allreduce": "0.45-0.80x",
    "alltoall": "0.60-0.95x+res",
    "broadcast": "0.75-0.98x",
    "uniform_read": "0.95-1.05x",
    "uniform_write": "0.95-1.05x",
}

ARMS = ("spine-off", "CSR", "CSR-gate-off")


# ---- T2 analytical replay (spec §3 / PR #66 model.py). Not cycle-measured. ----

def erlang_b(n: int, a: float) -> float:
    if n < 0 or a < 0:
        raise ValueError("erlang_b domain")
    if a == 0.0:
        return 0.0
    b = 1.0
    for k in range(1, n + 1):
        b = (a * b) / (k + a * b)
    return b


def t2_completion_split(a: float, t_collect: float = 180.0, n_cam: int = N_CAM):
    f_ov = erlang_b(n_cam, a)
    p_to = 0.0 if t_collect <= TIMEOUT_DEFAULT else 1.0 - TIMEOUT_DEFAULT / t_collect
    f_to = (1.0 - f_ov) * p_to
    f_ok = (1.0 - f_ov) * (1.0 - p_to)
    return f_ov, f_to, f_ok


def t2_r_schedule(f_fanin: float = 0.60, w_grant: float = 1.0, n_src: int = N_TOP,
                  k_grant: float = 0.04, inject_gate: bool = True):
    w = min(max(w_grant, 0.0), float(n_src))
    f = min(max(f_fanin, 0.0), 1.0)
    r_sched = (1.0 - f) + f * (w / n_src)
    tax_orbit = 0.0 if inject_gate else f * (1.0 - w / n_src)
    r_ok = r_sched + max(0.0, k_grant) + tax_orbit
    return r_sched, tax_orbit, r_ok


def t2_mix_ratio(f_grant: float, f_ov: float, f_to: float, r_ok: float, r_fb: float = 1.0):
    return f_grant * r_ok + (f_ov + f_to) * r_fb


def t2_fallback_dominates(f_ov: float, f_to: float) -> bool:
    return (f_ov > 0.5) or (f_to > 0.5)


def try_load_t2_module():
    try:
        return load_csr_t2()
    except FileNotFoundError:
        return None


def classify(opcode: str, spine_off: bool = False, force_p2p: bool = False) -> str:
    """1-cycle classifier ROM: opcode → {RING_P2P, SPINE_RENDZ}."""
    if spine_off or force_p2p:
        return "RING_P2P"
    if opcode in SPINE_ELIGIBLE:
        return "SPINE_RENDZ"
    return "RING_P2P"


def dir_of(src: int, dst: int, n: int) -> str:
    cw = (dst - src) % n
    ccw = (src - dst) % n
    return "CW" if cw <= ccw else "CCW"


def next_node(node: int, direction: str, n: int) -> int:
    return (node + 1) % n if direction == "CW" else (node - 1) % n


def hops_of(src: int, dst: int, n: int) -> int:
    cw = (dst - src) % n
    ccw = (src - dst) % n
    return cw if cw <= ccw else ccw


def group_of(node: int, arity: int = TREE_ARITY) -> int:
    return node // arity


# ---- workload (same seed ⇒ same op list for every arm) ----

@dataclass
class Transfer:
    """One src→dst 512 B message (N_BEATS flits) belonging to a collective op."""
    tid: int
    oid: int
    src: int
    dst: int
    cls: str
    path: str  # TREE | RESIDUAL | P2P
    n_beats: int = N_BEATS
    phase: int = 0


@dataclass
class Op:
    oid: int
    cls: str
    members: tuple[int, ...]
    root: int
    member_mask: int
    transfers: tuple[Transfer, ...]
    spine_class: str  # SPINE_RENDZ or RING_P2P (pre-overflow)


def _mask_of(members: tuple[int, ...]) -> int:
    m = 0
    for n in members:
        if n < 12:
            m |= 1 << n
    return m


def gen_ops(cls: str, n_top: int, n_bottom: int, n_ops: int, seed: int,
            root: int | None = None) -> list[Op]:
    """Synthetic DV200-class collectives. Same seed → same list (fair compare)."""
    if cls not in CLASSES:
        raise ValueError(f"unknown class {cls}")
    rng = random.Random(seed)
    n = n_top + n_bottom
    if root is None:
        root = n_top if n_bottom > 0 else 0
    tops = tuple(range(n_top))
    ops: list[Op] = []
    tid = 0

    def mk_op(members, transfers, spine=None) -> Op:
        sc = classify(cls) if spine is None else spine
        # allreduce: first GRANT is phase-0 fan-in only. Other classes: all TREE senders.
        if cls == "allreduce":
            senders = tuple(sorted({t.src for t in transfers if t.path == "TREE" and t.phase == 0}))
        else:
            senders = tuple(sorted({t.src for t in transfers if t.path == "TREE"}))
        rendz_members = senders if senders else tuple(members)
        return Op(
            oid=len(ops),
            cls=cls,
            members=tuple(rendz_members),
            root=root,
            member_mask=_mask_of(rendz_members),
            transfers=tuple(transfers),
            spine_class=sc,
        )

    for oi in range(n_ops):
        xfers: list[Transfer] = []
        if cls in ("uniform_read", "uniform_write"):
            for _ in range(n_top):
                src = rng.randrange(n)
                dst = rng.randrange(n - 1)
                if dst >= src:
                    dst += 1
                xfers.append(Transfer(tid, oi, src, dst, cls, "P2P"))
                tid += 1
            ops.append(mk_op(tops, xfers))
        elif cls in ("gather", "reduce"):
            for src in tops:
                if src == root:
                    continue
                xfers.append(Transfer(tid, oi, src, root, cls, "TREE"))
                tid += 1
            ops.append(mk_op(tops, xfers))
        elif cls == "broadcast":
            for dst in tops:
                if dst == root:
                    continue
                xfers.append(Transfer(tid, oi, root, dst, cls, "TREE"))
                tid += 1
            ops.append(mk_op(tops, xfers))
        elif cls == "allgather":
            # software-posted fan-out from each top; not an arrival oracle
            for src in tops:
                for dst in tops:
                    if src == dst:
                        continue
                    xfers.append(Transfer(tid, oi, src, dst, cls, "TREE", phase=src))
                    tid += 1
            ops.append(mk_op(tops, xfers))
        elif cls == "allreduce":
            for src in tops:
                if src == root:
                    continue
                xfers.append(Transfer(tid, oi, src, root, cls, "TREE", phase=0))
                tid += 1
            for dst in tops:
                if dst == root:
                    continue
                xfers.append(Transfer(tid, oi, root, dst, cls, "TREE", phase=1))
                tid += 1
            ops.append(mk_op(tops, xfers))
        else:  # alltoall — segmented GRANT vs residual RING_P2P
            # smoke-bounded: each top sends to 3 dests (1 in-group TREE, 2 residual)
            for src in tops:
                in_g = [d for d in tops if d != src and group_of(d) == group_of(src)]
                out_g = [d for d in tops if d != src and group_of(d) != group_of(src)]
                rng.shuffle(in_g)
                rng.shuffle(out_g)
                tree_d = in_g[:1]
                res_d = out_g[:2]
                for d in tree_d:
                    xfers.append(Transfer(tid, oi, src, d, cls, "TREE"))
                    tid += 1
                for d in res_d:
                    xfers.append(Transfer(tid, oi, src, d, cls, "RESIDUAL"))
                    tid += 1
            ops.append(mk_op(tops, xfers))
    return ops


# ---- fabric ----

@dataclass
class Slot:
    kind: str = "empty"  # empty | header | grant | ff | payload
    tid: int = -1
    oid: int = -1
    src: int = -1
    dst: int = -1
    beat: int = 0
    cls: str = ""
    path: str = ""
    born: int = 0

    @staticmethod
    def empty() -> "Slot":
        return Slot()


@dataclass
class CamItem:
    idx: int
    state: str = "IDLE"
    oid: int = -1
    child_bitmap: int = 0
    timeout: int = 0
    member_mask: int = 0
    cls: str = ""
    dat_beats_held: int = 0  # invariant: always 0
    grant_pending_since: int = -1

    def live(self) -> bool:
        return self.state not in ("IDLE",)

    def release(self) -> None:
        self.state = "IDLE"
        self.oid = -1
        self.child_bitmap = 0
        self.timeout = 0
        self.member_mask = 0
        self.cls = ""
        self.dat_beats_held = 0
        self.grant_pending_since = -1


@dataclass
class XferState:
    xfer: Transfer
    header_sent: bool = False
    beats_sent: int = 0
    beats_folded: int = 0
    classified: str = ""
    classified_at: int = -1
    grant_obs: int = -1
    ff_obs: int = -1
    overflow: bool = False
    timeout_fb: bool = False
    done_at: int = -1
    first_payload: int = -1


@dataclass
class SimConfig:
    n_top: int = N_TOP
    n_bottom: int = 2
    chi: tuple[str, ...] = CHI
    dirs: tuple[str, ...] = DIRS
    arm: str = "CSR"
    warmup_laps: int = 1
    outstanding: int = 256
    hop_lat: int = 1
    n_ops: int = 4
    traffic_class: str = "gather"
    seed: int = SEED
    timeout: int = TIMEOUT_DEFAULT
    w_grant: int = 1
    fold_ports: int = 1
    inject_gate: bool = True
    ff_notify: bool = True
    ff_notify_lat: int = FF_NOTIFY_LAT
    classifier_lat: int = CLASSIFIER_LAT
    rbrg_node: int | None = None
    root: int | None = None
    max_cycles: int | None = None
    tree_arity: int = TREE_ARITY


@dataclass
class CycleResult:
    cycles: int
    completed: int
    issued_payload: int
    warmup_cycles: int
    makespan: int
    first_issue: int
    last_complete: int
    cam_overflow_fallback: int
    collect_timeout_fallback: int
    spine_grant: int
    f_overflow: float
    f_timeout: float
    f_grant: float
    fallback_dominates: bool
    card_claim_valid: bool
    dat_beats_held_max: int
    retention_depth_max: int
    concurrent_live_cam_max: int
    invariant_ok: bool
    inject_before_grant: int
    payload_rbrg_reject: int
    same_cycle_reclassify: int
    grant_emits: int
    ff_notifies: int
    classifier_cycles_max: int
    ff_notify_cycles_max: int
    fold_accepts: int
    fold_orbits: int
    inject_ok: int
    inject_fail: int
    collapsed: bool
    residual_makespan: int
    residual_p50: float
    residual_p90: float
    residual_p99: float
    tree_makespan: int
    tree_completed: int
    residual_completed: int
    n_nodes: int
    n_cam: int
    oracle_used: bool
    goodput_b_per_cyc: float
    completions_by_class: dict[str, int]
    hypothesis: str = "H-RING-BB"


class Fabric:
    def __init__(self, cfg: SimConfig, ops: list[Op]):
        if cfg.hop_lat != 1:
            raise NotImplementedError("hop_lat>1 is parameterized bbox; smoke uses 1")
        self.cfg = cfg
        self.n = cfg.n_top + cfg.n_bottom
        if self.n < 3:
            raise ValueError("need ≥3 nodes")
        self.chis = tuple(cfg.chi)
        self.dirs = tuple(cfg.dirs)
        self.warmup = max(cfg.warmup_laps, 1) * self.n
        self.rbrg = cfg.rbrg_node if cfg.rbrg_node is not None else (
            cfg.n_top if cfg.n_bottom > 0 else 0
        )
        self.spine_off = cfg.arm == "spine-off"
        self.inject_gate = bool(cfg.inject_gate) and cfg.arm != "CSR-gate-off" and not self.spine_off
        self.slots = {
            c: {d: [Slot.empty() for _ in range(self.n)] for d in self.dirs}
            for c in self.chis
        }
        self.cam = [CamItem(i) for i in range(N_CAM)]
        self.ops = ops
        self.xstate: dict[int, XferState] = {}
        self.by_src: dict[int, list[XferState]] = {i: [] for i in range(self.n)}
        for op in ops:
            for xf in op.transfers:
                xs = XferState(xfer=xf)
                self.xstate[xf.tid] = xs
                if 0 <= xf.src < self.n:
                    self.by_src[xf.src].append(xs)
        self.op_by_id = {op.oid: op for op in ops}
        self.grant_emit_at: dict[int, int] = {}
        self.ff_visible_at: dict[int, int] = {}
        self.inflight = [0] * self.n
        self.stats = Counter()
        self.live_cam_max = 0
        self.dat_held_max = 0
        self.retention_max = 0
        self.cls_lat_max = 0
        self.ff_lat_max = 0
        self.residual_done: list[int] = []
        self.tree_done: list[int] = []
        self.done_at: dict[int, int] = {}
        self.issue_at: dict[int, int] = {}
        self.cycle = 0
        self.oracle_used = False
        extra = 16 * max(1, sum(len(o.transfers) for o in ops)) * N_BEATS + 4 * self.n
        self.limit = cfg.max_cycles if cfg.max_cycles is not None else self.warmup + extra + 512

    def live_cam(self) -> int:
        return sum(1 for c in self.cam if c.live())

    def _probe_invariants(self) -> None:
        live = self.live_cam()
        if live > self.live_cam_max:
            self.live_cam_max = live
        if live > N_CAM:
            raise RuntimeError(f"concurrent_live_cam={live} > N_cam={N_CAM}")
        held = 0
        for c in self.cam:
            if c.dat_beats_held != 0:
                held = max(held, c.dat_beats_held)
        if held > self.dat_held_max:
            self.dat_held_max = held
        if self.stats["payload_rbrg_reject"] > self.retention_max:
            self.retention_max = int(self.stats["payload_rbrg_reject"])

    def _cam_find(self, oid: int) -> CamItem | None:
        for c in self.cam:
            if c.live() and c.oid == oid:
                return c
        return None

    def _cam_alloc(self, op: Op, timeout: int) -> CamItem | None:
        for c in self.cam:
            if c.state == "IDLE":
                c.state = "COLLECT"
                c.oid = op.oid
                c.child_bitmap = 0
                c.timeout = timeout
                c.member_mask = op.member_mask
                c.cls = op.cls
                c.dat_beats_held = 0
                return c
        return None

    def _force_fallback(self, cam: CamItem, cycle: int) -> None:
        oid = cam.oid
        cam.state = "FORCE_FALLBACK"
        self.stats["collect_timeout_fallback"] += 1
        vis = cycle + (self.cfg.ff_notify_lat if self.cfg.ff_notify else 10**9)
        self.ff_visible_at[oid] = vis
        self.ff_lat_max = max(self.ff_lat_max, vis - cycle)
        for xs in self.xstate.values():
            if xs.xfer.oid == oid:
                xs.timeout_fb = True
        cam.release()

    def _tick_timeouts(self, cycle: int) -> None:
        for c in self.cam:
            if not c.live():
                continue
            if c.state in ("COLLECT", "GRANT_PENDING"):
                if c.timeout > 0:
                    c.timeout -= 1
                if c.timeout <= 0:
                    self._force_fallback(c, cycle)

    def _order_allows(self, xs: XferState, cycle: int) -> bool:
        """Static order table after one GRANT lap. No arrival-time fill.

        Member i may inject only after members before its W_grant group have
        *posted* (beats_sent) their TREE beats. That is an issue schedule,
        not an eject/arrival oracle.
        """
        oid = xs.xfer.oid
        t0 = self.grant_emit_at.get(oid)
        if t0 is None:
            return False
        if cycle < t0 + self.n:
            return False
        op = self.op_by_id[oid]
        if xs.xfer.cls == "allreduce" and xs.xfer.phase == 1:
            if not self._phase0_posted(oid):
                return False
        members = list(op.members) or [xs.xfer.src]
        try:
            idx = members.index(xs.xfer.src)
        except ValueError:
            idx = xs.xfer.src % max(1, len(members))
        w = max(1, int(self.cfg.w_grant))
        group0 = (idx // w) * w
        return self._members_posted(oid, members[:group0], xs.xfer.phase)

    def _members_posted(self, oid: int, members: list[int], phase: int) -> bool:
        need = set(members)
        if not need:
            return True
        for xs in self.xstate.values():
            if xs.xfer.oid != oid or xs.xfer.phase != phase:
                continue
            if xs.xfer.src in need and xs.xfer.path != "RESIDUAL":
                if xs.beats_sent < xs.xfer.n_beats:
                    return False
        return True

    def _phase0_posted(self, oid: int) -> bool:
        """Posted issue-schedule only — do not inspect in-flight arrivals."""
        for xs in self.xstate.values():
            if xs.xfer.oid == oid and xs.xfer.phase == 0:
                if xs.beats_sent < xs.xfer.n_beats:
                    return False
        return True

    def _payload_allowed(self, xs: XferState, cycle: int) -> bool:
        if xs.classified != "SPINE_RENDZ":
            return True
        if xs.overflow or xs.timeout_fb:
            if xs.timeout_fb:
                vis = self.ff_visible_at.get(xs.xfer.oid, cycle)
                return cycle >= vis
            return True
        if not self.inject_gate:
            return True
        if xs.grant_obs < 0:
            return False
        return self._order_allows(xs, cycle)

    def _classify_xfer(self, xs: XferState, cycle: int) -> None:
        if xs.classified:
            return
        op = self.op_by_id[xs.xfer.oid]
        path = "RING_P2P" if self.spine_off else op.spine_class
        if xs.xfer.path == "RESIDUAL":
            path = "RING_P2P"
        if xs.xfer.path == "P2P":
            path = "RING_P2P"
        xs.classified = path
        xs.classified_at = cycle
        self.cls_lat_max = max(self.cls_lat_max, self.cfg.classifier_lat)

    def _ready_header(self, node: int, direction: str) -> XferState | None:
        if self.cycle < self.warmup:
            return None
        if self.spine_off:
            return None
        if dir_of(node, self.rbrg, self.n) != direction:
            return None
        if self.inflight[node] >= self.cfg.outstanding:
            return None
        seen_oid = set()
        for xs in self.by_src[node]:
            if xs.xfer.oid in seen_oid:
                continue
            if xs.header_sent or xs.classified != "SPINE_RENDZ":
                continue
            if xs.classified_at < 0:
                continue
            if self.cycle < xs.classified_at + self.cfg.classifier_lat:
                continue
            seen_oid.add(xs.xfer.oid)
            return xs
        return None

    def _ready_payload(self, node: int, direction: str, cycle: int) -> XferState | None:
        if cycle < self.warmup:
            return None
        if self.inflight[node] >= self.cfg.outstanding:
            return None
        for xs in self.by_src[node]:
            if xs.beats_sent >= xs.xfer.n_beats:
                continue
            if not xs.classified:
                continue
            if cycle < xs.classified_at + self.cfg.classifier_lat:
                continue
            if dir_of(xs.xfer.src, xs.xfer.dst, self.n) != direction:
                continue
            if not self._payload_allowed(xs, cycle):
                continue
            return xs
        return None

    def _rbrg_accept_header(self, slot: Slot, cycle: int) -> Slot:
        """1-cycle CAM match/alloc. Header never becomes Dat occupancy."""
        op = self.op_by_id.get(slot.oid)
        if op is None:
            return Slot.empty()
        cam = self._cam_find(op.oid)
        if cam is None:
            cam = self._cam_alloc(op, self.cfg.timeout)
            if cam is None:
                already = any(
                    xs.overflow for xs in self.xstate.values() if xs.xfer.oid == op.oid
                )
                if not already:
                    self.stats["cam_overflow_fallback"] += 1
                    self.stats["same_cycle_reclassify"] += 1
                    for xs in self.xstate.values():
                        if xs.xfer.oid == op.oid:
                            xs.overflow = True
                            xs.classified = "RING_P2P"
                # header stays on the ring (no RBRG retention)
                return slot
        if 0 <= slot.src < 12:
            cam.child_bitmap |= 1 << slot.src
        cam.timeout = self.cfg.timeout
        cam.dat_beats_held = 0
        complete = (
            cam.member_mask == 0
            or (cam.child_bitmap & cam.member_mask) == cam.member_mask
        )
        if complete and cam.state == "COLLECT":
            cam.state = "GRANT_PENDING"
            cam.grant_pending_since = cycle
        # consume header at divert (not stored as Dat)
        return Slot.empty()

    def _try_grant_or_ff(self, node: int, slot: Slot, cycle: int, sampling: bool) -> Slot:
        if slot.kind != "empty" or node != self.rbrg:
            return slot
        # GRANT has priority over a new FF citizen
        for c in self.cam:
            if c.state == "GRANT_PENDING":
                g = Slot(
                    kind="grant", tid=-1, oid=c.oid, src=node, dst=node,
                    cls=c.cls, born=cycle,
                )
                self.grant_emit_at[c.oid] = cycle
                c.state = "GRANT_SENT"
                self.stats["grant_emits"] += 1
                self.stats["spine_grant"] += 1
                for xs in self.xstate.values():
                    if xs.xfer.oid == c.oid and xs.xfer.src == node:
                        if xs.grant_obs < 0:
                            xs.grant_obs = cycle
                # H-CAM-RELEASE: free after GRANT_SENT
                c.release()
                return g
        return slot

    def _observe_control(self, node: int, slot: Slot, cycle: int) -> None:
        if slot.kind == "grant":
            for xs in self.xstate.values():
                if xs.xfer.oid == slot.oid and xs.xfer.src == node:
                    if xs.grant_obs < 0:
                        xs.grant_obs = cycle
        elif slot.kind == "ff":
            vis = cycle + (self.cfg.ff_notify_lat if self.cfg.ff_notify else 0)
            self.ff_visible_at[slot.oid] = min(self.ff_visible_at.get(slot.oid, vis), vis)

    def _fold(self, node: int, slot: Slot, cycle: int, ports_left: list[int],
              sampling: bool) -> Slot:
        if slot.kind != "payload" or slot.dst != node:
            return slot
        if ports_left[node] <= 0:
            if sampling:
                self.stats["fold_orbits"] += 1
            # destination orbit — flit stays a ring citizen (not an RBRG FIFO)
            return slot
        ports_left[node] -= 1
        xs = self.xstate.get(slot.tid)
        if xs is not None:
            xs.beats_folded += 1
            if xs.beats_folded >= xs.xfer.n_beats and xs.done_at < 0:
                xs.done_at = cycle
                self.done_at[slot.tid] = cycle
                self.stats["complete"] += 1
                self.stats["complete", xs.xfer.cls] += 1
                self.stats["complete", xs.xfer.path] += 1
                if 0 <= xs.xfer.src < self.n:
                    self.inflight[xs.xfer.src] = max(0, self.inflight[xs.xfer.src] - 1)
                fin = self.issue_at.get(slot.tid, cycle)
                if xs.xfer.path == "RESIDUAL":
                    self.residual_done.append(cycle - fin)
                elif xs.xfer.path == "TREE":
                    self.tree_done.append(cycle - fin)
        if sampling:
            self.stats["fold_accepts"] += 1
        return Slot.empty()

    def _inject(self, node: int, chi: str, direction: str, slot: Slot,
                cycle: int, sampling: bool) -> Slot:
        if chi != "Dat":
            return slot
        if slot.kind != "empty":
            if sampling and (
                self._ready_payload(node, direction, cycle) is not None
                or self._ready_header(node, direction) is not None
            ):
                self.stats["inject_fail"] += 1
            return slot
        # RBRG GRANT into an empty Dat slot (citizen, no extra highway)
        if node == self.rbrg:
            g = self._try_grant_or_ff(node, slot, cycle, sampling)
            if g.kind != "empty":
                return g
        # headers before payload (rendezvous first)
        hs = self._ready_header(node, direction)
        if hs is not None:
            for xs in self.by_src[node]:
                if xs.xfer.oid == hs.xfer.oid:
                    xs.header_sent = True
            if sampling:
                self.stats["header_inject"] += 1
            return Slot(
                kind="header", tid=hs.xfer.tid, oid=hs.xfer.oid,
                src=hs.xfer.src, dst=self.rbrg, cls=hs.xfer.cls, born=cycle,
            )
        ps = self._ready_payload(node, direction, cycle)
        if ps is not None:
            if (ps.classified == "SPINE_RENDZ" and ps.grant_obs < 0
                    and not ps.overflow and not ps.timeout_fb and self.inject_gate):
                # should be unreachable; count as mechanism fail
                self.stats["inject_before_grant"] += 1
            if (not self.inject_gate and ps.classified == "SPINE_RENDZ"
                    and ps.grant_obs < 0 and not ps.overflow):
                self.stats["inject_before_grant"] += 1
            ps.beats_sent += 1
            if ps.first_payload < 0:
                ps.first_payload = cycle
                self.issue_at[ps.xfer.tid] = cycle
                self.inflight[node] += 1
            if sampling:
                self.stats["inject_ok"] += 1
                self.stats["issued_payload"] += 1
            return Slot(
                kind="payload", tid=ps.xfer.tid, oid=ps.xfer.oid,
                src=ps.xfer.src, dst=ps.xfer.dst, beat=ps.beats_sent - 1,
                cls=ps.xfer.cls, path=ps.xfer.path, born=cycle,
            )
        return slot

    def _eject_stale_control(self, node: int, slot: Slot, cycle: int) -> Slot:
        if slot.kind in ("header", "grant", "ff") and slot.src == node and cycle > slot.born + self.n:
            return Slot.empty()
        if slot.kind == "header" and node == self.rbrg:
            return slot  # processed in rbrg path
        if slot.kind == "grant" and cycle > slot.born + self.n:
            return Slot.empty()
        return slot

    def pending(self) -> int:
        n = 0
        for xs in self.xstate.values():
            if xs.done_at < 0:
                n += 1
        return n

    def step(self, cycle: int) -> None:
        self.cycle = cycle
        sampling = cycle >= self.warmup
        # post classification on warmup (software schedule, not arrivals)
        if cycle >= self.warmup:
            for xs in self.xstate.values():
                self._classify_xfer(xs, cycle)
        self._tick_timeouts(cycle)
        ports_left = [self.cfg.fold_ports] * self.n
        new = {
            c: {d: [Slot.empty() for _ in range(self.n)] for d in self.dirs}
            for c in self.chis
        }
        for chi in self.chis:
            for d in self.dirs:
                for n in range(self.n):
                    slot = self.slots[chi][d][n]
                    slot = self._eject_stale_control(n, slot, cycle)
                    self._observe_control(n, slot, cycle)
                    if slot.kind == "header" and n == self.rbrg and chi == "Dat":
                        slot = self._rbrg_accept_header(slot, cycle)
                    if slot.kind == "payload" and n == self.rbrg and slot.dst != n:
                        # payload must not enter CAM; never reject-and-park
                        if False:  # structural guard: no RBRG payload path
                            self.stats["payload_rbrg_reject"] += 1
                    slot = self._fold(n, slot, cycle, ports_left, sampling)
                    slot = self._inject(n, chi, d, slot, cycle, sampling)
                    new[chi][d][next_node(n, d, self.n)] = slot
        self.slots = new
        self._probe_invariants()

    def done(self) -> bool:
        if self.cycle < self.warmup:
            return False
        if self.pending() == 0:
            return True
        return False

    def result(self) -> CycleResult:
        ov = int(self.stats["cam_overflow_fallback"])
        to = int(self.stats["collect_timeout_fallback"])
        # completions attributed per op path
        n_ops = len(self.ops)
        # count ops that overflowed / timed out / granted
        ov_ops = {xs.xfer.oid for xs in self.xstate.values() if xs.overflow}
        to_ops = {xs.xfer.oid for xs in self.xstate.values() if xs.timeout_fb}
        gr_ops = set(self.grant_emit_at) - ov_ops - to_ops
        den = max(1, n_ops)
        # first-class endpoints: fallback counts are op-level (CAM events)
        f_ov = ov / den if n_ops else 0.0
        f_to = to / den if n_ops else 0.0
        # grant fraction among ops that used the spine path
        spine_ops = [o for o in self.ops if o.spine_class == "SPINE_RENDZ" and not self.spine_off]
        if spine_ops:
            f_gr = len(gr_ops) / max(1, len(spine_ops))
            # conservation over CAM outcomes
            cam_den = max(1, ov + to + len(gr_ops))
            f_ov = ov / cam_den
            f_to = to / cam_den
            f_gr = len(gr_ops) / cam_den
        else:
            f_gr = 0.0
            f_ov = 0.0
            f_to = 0.0
        issued = len(self.issue_at)
        completed = len(self.done_at)
        if self.issue_at and self.done_at:
            first = min(self.issue_at.values())
            last = max(self.done_at.values())
            span = max(1, last - first)
        else:
            first = last = 0
            span = 1
        def _pct(xs: list[int], p: float) -> float:
            if not xs:
                return 0.0
            s = sorted(xs)
            k = min(len(s) - 1, max(0, int(math.ceil(p / 100.0 * len(s)) - 1)))
            return float(s[k])

        res_ms = max(self.residual_done) if self.residual_done else 0
        tree_ms = max(self.tree_done) if self.tree_done else 0
        fail = int(self.stats["inject_fail"])
        ok = int(self.stats["inject_ok"])
        attempts = fail + ok
        fail_rate = fail / attempts if attempts else 0.0
        inv = (
            self.dat_held_max == 0
            and self.retention_max == 0
            and self.live_cam_max <= N_CAM
            and int(self.stats["payload_rbrg_reject"]) == 0
        )
        dominates = (f_ov > 0.5) or (f_to > 0.5)
        by_cls: dict[str, int] = defaultdict(int)
        for xs in self.xstate.values():
            if xs.done_at >= 0:
                by_cls[xs.xfer.cls] += 1
        return CycleResult(
            cycles=self.cycle,
            completed=completed,
            issued_payload=int(self.stats["issued_payload"]),
            warmup_cycles=self.warmup,
            makespan=span,
            first_issue=first,
            last_complete=last,
            cam_overflow_fallback=ov,
            collect_timeout_fallback=to,
            spine_grant=int(self.stats["spine_grant"]),
            f_overflow=f_ov,
            f_timeout=f_to,
            f_grant=f_gr,
            fallback_dominates=dominates,
            card_claim_valid=not dominates,
            dat_beats_held_max=self.dat_held_max,
            retention_depth_max=self.retention_max,
            concurrent_live_cam_max=self.live_cam_max,
            invariant_ok=inv,
            inject_before_grant=int(self.stats["inject_before_grant"]),
            payload_rbrg_reject=int(self.stats["payload_rbrg_reject"]),
            same_cycle_reclassify=int(self.stats["same_cycle_reclassify"]),
            grant_emits=int(self.stats["grant_emits"]),
            ff_notifies=int(self.stats["collect_timeout_fallback"]),
            classifier_cycles_max=max(self.cls_lat_max, self.cfg.classifier_lat),
            ff_notify_cycles_max=self.ff_lat_max if to else self.cfg.ff_notify_lat,
            fold_accepts=int(self.stats["fold_accepts"]),
            fold_orbits=int(self.stats["fold_orbits"]),
            inject_ok=ok,
            inject_fail=fail,
            collapsed=fail_rate >= 0.50 or (self.stats["fold_orbits"] > self.stats["fold_accepts"] and completed > 0),
            residual_makespan=res_ms,
            residual_p50=_pct(self.residual_done, 50),
            residual_p90=_pct(self.residual_done, 90),
            residual_p99=_pct(self.residual_done, 99),
            tree_makespan=tree_ms,
            tree_completed=int(self.stats["complete", "TREE"]),
            residual_completed=int(self.stats["complete", "RESIDUAL"]),
            n_nodes=self.n,
            n_cam=N_CAM,
            oracle_used=self.oracle_used,
            goodput_b_per_cyc=(completed * BYTES_PER_TXN) / span,
            completions_by_class=dict(by_cls),
        )


def run_cycles(cfg: SimConfig, ops: list[Op] | None = None) -> CycleResult:
    """Same SimPy clock + fabric for every arm. Workload list is an input."""
    if ops is None:
        ops = gen_ops(cfg.traffic_class, cfg.n_top, cfg.n_bottom, cfg.n_ops, cfg.seed, cfg.root)
    env = simpy.Environment()
    fab = Fabric(cfg, ops)

    def clock():
        while True:
            fab.step(int(env.now))
            yield env.timeout(1)
            if fab.done() or int(env.now) >= fab.limit:
                break

    env.process(clock())
    env.run()
    return fab.result()


def run_arm(arm: str, cls: str, seed: int, **kwargs) -> CycleResult:
    gate = arm != "CSR-gate-off"
    cfg = SimConfig(
        arm=arm,
        inject_gate=gate,
        traffic_class=cls,
        seed=seed,
        **kwargs,
    )
    ops = gen_ops(cls, cfg.n_top, cfg.n_bottom, cfg.n_ops, seed, cfg.root)
    return run_cycles(cfg, ops)


def compare_to_t2(cls: str, arm: str, t3: CycleResult, t3_off: CycleResult | None = None) -> dict:
    """Like-to-like vs signed T2. Does not substitute T2 into T3 columns."""
    if t3_off is not None and t3_off.makespan > 0:
        t3_ratio = t3.makespan / t3_off.makespan
    else:
        t3_ratio = float("nan")
    t2_ratio = float("nan")
    if cls in FANIN_DOM and arm == "CSR":
        t2_ratio = T2_SIGNED["gather_r"]
    elif cls in FANIN_DOM and arm == "CSR-gate-off":
        t2_ratio = T2_SIGNED["gate_off_r"]
    elif cls in FANIN_DOM and arm == "spine-off":
        t2_ratio = 1.0
    elif cls == "alltoall" and arm == "CSR":
        t2_ratio = T2_SIGNED["a2a_tree"]
    elif cls == "alltoall" and arm == "spine-off":
        t2_ratio = 1.0
    err = rel_err(t3_ratio, t2_ratio) if t3_ratio == t3_ratio and t2_ratio == t2_ratio else 0.0
    flag = bool(t3_ratio == t3_ratio and t2_ratio == t2_ratio and err > 0.30)
    claim = CARD_CLAIM.get(cls, "n/a")
    return {
        "class": cls,
        "arm": arm,
        "t3_makespan": t3.makespan,
        "t3_T_hat_over_T_off": t3_ratio,
        "t2_T_hat_over_T_off": t2_ratio,
        "rel_err_ratio": err,
        "t3_f_ov": t3.f_overflow,
        "t3_f_to": t3.f_timeout,
        "t3_f_grant": t3.f_grant,
        "t2_a2_f_ov": T2_SIGNED["a2_f_ov"],
        "t2_a8_f_ov": T2_SIGNED["a8_f_ov"],
        "flag_gt_30pct": flag,
        "card_claim": claim,
        "card_claim_is_measured": False,
        "t3_card_claim_valid": t3.card_claim_valid,
        "t3_fallback_dominates": t3.fallback_dominates,
        "t3_invariant_ok": t3.invariant_ok,
        "t3_dat_held_max": t3.dat_beats_held_max,
        "t3_retention_max": t3.retention_depth_max,
        "t3_live_cam_max": t3.concurrent_live_cam_max,
        "t3_cam_overflow_fallback": t3.cam_overflow_fallback,
        "t3_collect_timeout_fallback": t3.collect_timeout_fallback,
        "t3_collapsed": t3.collapsed,
        "t3_residual_p50": t3.residual_p50,
        "t3_residual_p90": t3.residual_p90,
        "t3_tree_makespan": t3.tree_makespan,
        "t3_residual_makespan": t3.residual_makespan,
    }


def signed_t2_rows() -> list[dict]:
    """Director/audit pins as their own rows (T2 column only). Cite, do not invent."""
    return [
        {
            "metric": "CAM Dat occupancy",
            "arm": "invariant",
            "t3": "",
            "t2": T2_SIGNED["cam_dat_occ"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed PR #68; T3 cycle probe must stay 0",
        },
        {
            "metric": "RBRG_reject_retention_depth",
            "arm": "invariant",
            "t3": "",
            "t2": T2_SIGNED["retention"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed PR #68",
        },
        {
            "metric": "N_cam",
            "arm": "silicon",
            "t3": N_CAM,
            "t2": T2_SIGNED["n_cam"],
            "rel_err": 0.0,
            "flag_gt_30pct": False,
            "note": "true concurrent; not TDM-8",
        },
        {
            "metric": "high-ost f_ov (a=8)",
            "arm": "Erlang-B",
            "t3": "",
            "t2": T2_SIGNED["a8_f_ov"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed → card_claim INVALID; cycle row filled by sweep",
        },
        {
            "metric": "spine-off HARD",
            "arm": "gather",
            "t3": "",
            "t2": True,
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "T2 T_hat_off=537.2 > T_hat_on=289.3; T3 compares cycle inequality",
        },
        {
            "metric": "gate-off r",
            "arm": "gather-family",
            "t3": "",
            "t2": T2_SIGNED["gate_off_r"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed ≈1.0362; premature orbit cancels fan-in",
        },
        {
            "metric": "alltoall TREE / RESIDUAL / mix",
            "arm": "split",
            "t3": "",
            "t2": f"{T2_SIGNED['a2a_tree']}/{T2_SIGNED['a2a_res']}/{T2_SIGNED['a2a_mix']}",
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "residual must stay a separate column; mix is NOT a pass number",
        },
        {
            "metric": "card-claim",
            "arm": "all-classes",
            "t3": "NOT measured",
            "t2": "NOT signed",
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "0.45-0.80x etc. are card-claim only; director did not sign as measured",
        },
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CSR cycle sim (single run)")
    p.add_argument("--class", dest="cls", choices=CLASSES, default="gather")
    p.add_argument("--arm", choices=ARMS, default="CSR")
    p.add_argument("--n-top", type=int, default=N_TOP)
    p.add_argument("--n-bottom", type=int, default=2)
    p.add_argument("--n-ops", type=int, default=4)
    p.add_argument("--outstanding", type=int, default=256)
    p.add_argument("--timeout", type=int, default=TIMEOUT_DEFAULT)
    p.add_argument("--w-grant", type=int, default=1)
    p.add_argument("--warmup-laps", type=int, default=1)
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)
    r = run_arm(
        args.arm,
        args.cls,
        args.seed,
        n_top=args.n_top,
        n_bottom=args.n_bottom,
        n_ops=args.n_ops,
        outstanding=args.outstanding,
        timeout=args.timeout,
        w_grant=args.w_grant,
        warmup_laps=args.warmup_laps,
    )
    print(
        f"CSR T3 class={args.cls} arm={args.arm} n={args.n_top}+{args.n_bottom} "
        f"ops={args.n_ops} ost={args.outstanding} seed={args.seed}"
    )
    print(
        f"warmup={r.warmup_cycles} makespan={r.makespan} completed={r.completed} "
        f"collapsed={r.collapsed} invariant_ok={r.invariant_ok}"
    )
    print(
        f"CAM live_max={r.concurrent_live_cam_max} Dat_held_max={r.dat_beats_held_max} "
        f"retention_max={r.retention_depth_max} N_cam={r.n_cam}"
    )
    print(
        f"endpoints ov={r.cam_overflow_fallback} to={r.collect_timeout_fallback} "
        f"grant={r.spine_grant} f_ov={r.f_overflow:.4f} f_to={r.f_timeout:.4f} "
        f"f_grant={r.f_grant:.4f} dominates={r.fallback_dominates} "
        f"card_claim_valid={r.card_claim_valid}"
    )
    print(
        f"inject ok={r.inject_ok} fail={r.inject_fail} before_grant={r.inject_before_grant} "
        f"fold_acc={r.fold_accepts} fold_orb={r.fold_orbits} "
        f"reclass={r.same_cycle_reclassify} oracle={r.oracle_used}"
    )
    if args.cls == "alltoall":
        print(
            f"alltoall TREE ms={r.tree_makespan} n={r.tree_completed}  "
            f"RESIDUAL ms={r.residual_makespan} p50={r.residual_p50:.1f} "
            f"p90={r.residual_p90:.1f} p99={r.residual_p99:.1f} n={r.residual_completed}"
        )
    print(f"card-claim {CARD_CLAIM.get(args.cls, 'n/a')} is NOT measured")
    print("0.85 is a pass bar, not a measured mean; no team-384dmc")
    t2mod = try_load_t2_module()
    print("T2 model.py on this tree:" + (" yes" if t2mod else " no (PR #66 only; using signed constants)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
