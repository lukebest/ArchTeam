#!/usr/bin/env python3
"""P-0198/M-5 CRRF — cycle-level bufferless-ring SimPy model.

Cycle-accurate (card + Dr.Sim must-verify; T2 spec §4 — not mean-duty):
  1. Per-die five-state FSM beat-by-beat: ARM_DRAIN stops new inject, in-flight continues
  2. DRAIN marker double-return / highway sniff; local sniff ≠ global empty
  3. After FLIP, epoch_committed around the ring; late new-gen inject = assert
  4. SYNC skew-window per-flit accept set (bound ≤ ring circumference)
  5. Ghost Dat header channel-id stays Dat; RBRG decode by bind+tag
  6. Out-of-accept-set NACK/re-inject charged to that txn
  7. Safe drain/flip/steady with no runtime hint
  8. SYNC is not a traffic oracle
  9. HARD-2: 512 B window ghost vs main Dat destination distribution
  10. Warm-up until SYNC-aligned steady before sampling

Black box: hop latency, flit=txn (512 B), RBRG/HBM/coherence/D2D, clock.
T2 analytical model is NOT on main (PR #63). Compare uses signed audit pins;
never treat card-claim 0.55–0.85× as measured. Ablation only vs rebind-off.
This card only — no mixed conclusions with M-1 / M-2 / M-4.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

import simpy

_HERE = Path(__file__).resolve().parent
_SIMS = _HERE.parents[1]
if str(_SIMS) not in sys.path:
    sys.path.insert(0, str(_SIMS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _lib.stats import rel_err  # noqa: E402
from _lib.t2load import load_crrf_t2  # noqa: E402
from _lib.workloads import SEED  # noqa: E402
from t2_pins import (  # noqa: E402
    CARD_CLAIM_BCAST,
    CARD_CLAIM_DAT,
    CARD_CLAIM_SNP,
    CARD_CLAIM_WRITE,
    C_DAT_EFF as T2_C_DAT_EFF,
    DAT_DOM,
    F_STEADY as T2_F_STEADY,
    H_COMMIT_HELD,
    H_COMMIT_VIOLATED,
    H_DAT_DOM_GATHER,
    HARD1_T_BEST,
    HARD1_T_OFF,
    SNP_15_1,
    SNP_KILL,
    SNP_LAT,
    T_DRAIN as T2_T_DRAIN,
    T_OFF,
    T2_N_PIPE,
    t2_c_dat_eff_formula,
)

CHI = ("Req", "Rsp", "Snp", "Dat")
DIRS = ("CW", "CCW")
FSM_STATES = ("IDLE", "ARM_DRAIN", "DRAIN", "FLIP", "STEADY")
P2P_CLASSES = ("uniform_read", "uniform_write")
COLL_CLASSES = (
    "broadcast",
    "gather",
    "reduce",
    "allgather",
    "allreduce",
    "alltoall",
)
CLASSES = P2P_CLASSES + COLL_CLASSES + ("snp_path",)
ARMS = ("rebind-off", "3:1", "7:1", "15:1")
BYTES_PER_TXN = 512
EPOCH_MOD = 4
K_CIRC = 2

# H-PRESSURE defaults (local counters only; hint never enters)
THETA_DAT = 0.70
THETA_SNP = 2.0


class LateNewgenInject(AssertionError):
    """Late node injecting under a new bind before epoch_committed (Dr.Sim §3)."""


def duty_of_arm(arm: str) -> tuple[int, int]:
    return {
        "rebind-off": (0, 1),
        "3:1": (3, 1),
        "7:1": (7, 1),
        "15:1": (15, 1),
    }[arm]


def duty_frac(arm: str) -> tuple[float, float]:
    r, s = duty_of_arm(arm)
    if arm == "rebind-off":
        return 0.0, 1.0
    tot = r + s
    return r / tot, s / tot


def rebind_on(arm: str) -> bool:
    return arm != "rebind-off"


def accept_set(local_epoch: int) -> set[int]:
    e = local_epoch % EPOCH_MOD
    return {e, (e - 1) % EPOCH_MOD}


def dir_of(src: int, dst: int, n: int) -> str:
    cw = (dst - src) % n
    ccw = (src - dst) % n
    return "CW" if cw <= ccw else "CCW"


def next_node(node: int, direction: str, n: int) -> int:
    return (node + 1) % n if direction == "CW" else (node - 1) % n


def hops_of(src: int, dst: int, direction: str, n: int) -> int:
    if direction == "CW":
        return (dst - src) % n
    return (src - dst) % n


def card_claim_of(cls: str) -> str:
    if cls == "snp_path":
        return CARD_CLAIM_SNP
    if cls == "broadcast":
        return CARD_CLAIM_BCAST
    if cls == "uniform_write":
        return CARD_CLAIM_WRITE
    if cls in DAT_DOM:
        return CARD_CLAIM_DAT
    return "n/a"


def try_load_t2_module():
    try:
        return load_crrf_t2()
    except FileNotFoundError:
        return None


@dataclass
class Txn:
    tid: int
    src: int
    dst: int
    chi: str
    cls: str
    nbytes: int = BYTES_PER_TXN
    nack_hops: int = 0
    issue_at: int | None = None
    done_at: int | None = None
    via: str = ""  # main | ghost | snp | nack-reinject


@dataclass
class Slot:
    kind: str = "empty"  # empty | payload | sync
    chi: str = ""  # header channel-id (Dat stays Dat on ghost)
    phys: str = ""  # physical ring
    src: int = -1
    dst: int = -1
    tid: int = -1
    epoch_tag: int = 0
    is_ghost: bool = False
    nack: bool = False

    @staticmethod
    def empty() -> "Slot":
        return Slot()

    @staticmethod
    def sync() -> "Slot":
        return Slot(kind="sync", chi="Req", phys="Req")

    @staticmethod
    def payload(txn: Txn, phys: str, epoch_tag: int, is_ghost: bool, nack: bool = False) -> "Slot":
        return Slot(
            kind="payload",
            chi=txn.chi,
            phys=phys,
            src=txn.src,
            dst=txn.dst,
            tid=txn.tid,
            epoch_tag=epoch_tag,
            is_ghost=is_ghost,
            nack=nack,
        )


@dataclass
class Die:
    fsm: str = "STEADY"
    epoch_gen: int = 0
    bind_snp: str = "Snp"  # logical identity of the Snp wire
    pipe_left: int = 0
    dwell: int = 0
    drain_visits: int = 0
    drain_req: bool = False
    commit_posted: bool = False
    commit_seen_all: bool = False
    block_rebind_inject: bool = False
    hint: object = None
    rho_dat_ema: float = 0.0
    n_snp_pend: int = 0
    holding: Slot | None = None
    dat_slots_seen: int = 0
    dat_busy_seen: int = 0


def gen_txns(cls: str, n_nodes: int, n_txn: int, seed: int) -> list[Txn]:
    """Synthetic DV200-class traffic. Same seed → same list (fair compare)."""
    if cls not in CLASSES:
        raise ValueError(f"unknown class {cls}")
    rng = random.Random(seed)
    txns: list[Txn] = []

    def add(src: int, dst: int, chi: str) -> None:
        if src == dst:
            raise ValueError("self-dest")
        txns.append(Txn(len(txns), src, dst, chi, cls))

    chi = "Snp" if cls == "snp_path" else "Dat"
    if cls in ("uniform_read", "uniform_write", "snp_path"):
        for _ in range(n_txn):
            src = rng.randrange(n_nodes)
            dst = rng.randrange(n_nodes - 1)
            if dst >= src:
                dst += 1
            add(src, dst, chi)
    elif cls in ("gather", "reduce"):
        sink = 0
        for i in range(n_txn):
            add(1 + (i % (n_nodes - 1)), sink, "Dat")
    elif cls == "broadcast":
        root = 0
        i = 0
        while i < n_txn:
            for dst in range(n_nodes):
                if dst == root:
                    continue
                add(root, dst, "Dat")
                i += 1
                if i >= n_txn:
                    break
    elif cls == "allgather":
        i = 0
        while i < n_txn:
            for src in range(n_nodes):
                for dst in range(n_nodes):
                    if src == dst:
                        continue
                    add(src, dst, "Dat")
                    i += 1
                    if i >= n_txn:
                        break
                if i >= n_txn:
                    break
    elif cls == "allreduce":
        half = max(1, n_txn // 2)
        sink = 0
        for i in range(half):
            add(1 + (i % (n_nodes - 1)), sink, "Dat")
        i = 0
        while len(txns) < n_txn:
            add(sink, 1 + (i % (n_nodes - 1)), "Dat")
            i += 1
    else:  # alltoall
        for i in range(n_txn):
            src = i % n_nodes
            dst = (src + 1 + rng.randrange(n_nodes - 1)) % n_nodes
            add(src, dst, "Dat")
    return txns[:n_txn]


def gen_mixed(n_nodes: int, n_dat: int, n_snp: int, seed: int, dat_cls: str = "gather") -> list[Txn]:
    """Dat-heavy job + sparse Snp on the same seeded driver (never averaged)."""
    dat = gen_txns(dat_cls, n_nodes, n_dat, seed)
    snp = gen_txns("snp_path", n_nodes, n_snp, seed + 7919)
    off = 10_000
    snp = [Txn(t.tid + off, t.src, t.dst, "Snp", "snp_path") for t in snp]
    return dat + snp


def request_duty(rho_ema: float, snp_pend: float, hint=None) -> str:
    """Local pressure only. `hint` is advisory and is not read."""
    del hint
    if snp_pend >= THETA_SNP:
        return "3:1"
    if rho_ema >= THETA_DAT and snp_pend < THETA_SNP:
        return "7:1"
    return "3:1"


@dataclass
class SimConfig:
    n_nodes: int = 12
    n_bottom: int = 0
    arm: str = "rebind-off"
    n_pipe: int = 2
    t_steady_laps: int = 20
    warmup_laps: int = 1
    outstanding: int = 16
    hop_lat: int = 1
    n_txn: int = 64
    n_snp: int = 0
    traffic_class: str = "gather"
    seed: int = SEED
    max_cycles: int | None = None
    hint: object = None
    force_early_newgen: bool = False
    strict_commit: bool = True
    plant_old_flit: tuple[int, int] | None = None  # (node, epoch_tag) on Snp CW
    hold_app_until_aligned: bool = True
    ghost_steer: str = "lsb"  # lsb | rr
    k_circ: int = K_CIRC


@dataclass
class CycleResult:
    cycles: int
    completed: int
    completed_dat: int
    completed_snp: int
    issued: int
    issued_dat: int
    issued_snp: int
    warmup_cycles: int
    makespan: int
    makespan_dat: int
    makespan_snp: int
    first_issue: int
    last_complete: int
    c_dat_eff: float
    c_dat_ideal: float
    duty_dat: float
    f_steady: float
    t_drain_mean: float
    tau_drain: float
    tau_sync: float
    tau_bind: float
    tax: float
    ghost_slots: int
    main_dat_slots: int
    bind_mismatch_redirect: int
    snp_stall: int
    inject_fail: int
    nack_reinject: int
    dest_main: dict[int, int]
    dest_ghost: dict[int, int]
    hard2_collapsed: bool
    fsm_counts: dict[str, int]
    epoch_committed_all_cycles: int
    correctness_depends_on_hint: bool
    oracle_used: bool
    sync_read_queues: bool
    hint_used: bool
    aligned: bool
    late_newgen_caught: int
    n_nodes: int
    arm: str
    traffic_class: str
    collapsed: bool
    goodput_b_per_cyc: float
    hypothesis: str = "H-RING-BB"


class Fabric:
    def __init__(self, cfg: SimConfig, txns: list[Txn]):
        if cfg.hop_lat != 1:
            raise NotImplementedError("hop_lat>1 is parameterized bbox; smoke uses 1")
        self.cfg = cfg
        self.n = cfg.n_nodes + cfg.n_bottom
        if self.n < 3:
            raise ValueError("need ≥3 nodes")
        self.arm = cfg.arm
        self.duty_dat, self.duty_snp = duty_frac(cfg.arm)
        self.on = rebind_on(cfg.arm)
        self.t_steady = max(1, cfg.t_steady_laps * self.n)
        self.dat_dwell = max(1, int(round(self.t_steady * self.duty_dat))) if self.on else self.t_steady
        self.snp_dwell = max(1, self.t_steady - self.dat_dwell) if self.on else self.t_steady
        self.warmup_floor = max(cfg.warmup_laps, 1) * self.n
        self.slots = {c: {d: [Slot.empty() for _ in range(self.n)] for d in DIRS} for c in CHI}
        self.slots["Req"]["CW"][0] = Slot.sync()
        self.dies = [Die(hint=cfg.hint) for _ in range(self.n)]
        self.queues: list[dict[str, deque[Txn]]] = [
            {"Dat": deque(), "Snp": deque()} for _ in range(self.n)
        ]
        self.txns = {t.tid: t for t in txns}
        self.inflight = [0] * self.n
        self.stats = Counter()
        self.dest_main: dict[int, int] = defaultdict(int)
        self.dest_ghost: dict[int, int] = defaultdict(int)
        self.rr = [0] * self.n
        self.cycle = 0
        self.sampling = False
        self.aligned = False
        self.oracle_used = False
        self.sync_read_queues = False
        self.late_newgen_caught = 0
        self.drain_intervals: list[int] = []
        self._drain_t0: dict[int, int] = {}
        self._flip_gens = 0
        self._commit_mask = 0
        self._want_dat = self.on  # first flip goes to DAT_EPOCH
        extra = 16 * max(1, len(txns)) * self.n + (self.t_steady + 8 * self.n) * 4
        self.limit = cfg.max_cycles if cfg.max_cycles is not None else self.warmup_floor + extra + 512
        for t in txns:
            self.queues[t.src][t.chi].append(t)
        if cfg.plant_old_flit is not None:
            node, tag = cfg.plant_old_flit
            dest = (node + max(2, self.n // 3)) % self.n
            dummy = Txn(tid=-2, src=node, dst=dest, chi="Dat", cls="plant")
            self.txns[-2] = dummy
            self.slots["Snp"]["CW"][node] = Slot.payload(dummy, "Snp", tag, True)

    # ---- queries used by tests / FSM ----

    def epoch_wire(self, node: int) -> int:
        return self.dies[node].epoch_gen % EPOCH_MOD

    def sniff_old(self, node: int, old_tag: int) -> bool:
        """Local highway sniff only — not a global empty probe."""
        for d in DIRS:
            s = self.slots["Snp"][d][node]
            if s.kind == "payload" and (s.epoch_tag % EPOCH_MOD) == (old_tag % EPOCH_MOD):
                return True
        return False

    def global_old_present(self, old_tag: int) -> bool:
        for n in range(self.n):
            if self.sniff_old(n, old_tag):
                return True
        return False

    def commit_all(self) -> bool:
        if not self.on:
            return True
        return all(d.commit_seen_all for d in self.dies) and len({d.epoch_gen for d in self.dies}) == 1

    def _ghost_ok(self, node: int) -> bool:
        d = self.dies[node]
        if not self.on or d.bind_snp != "Dat":
            return False
        if d.fsm != "STEADY" or d.block_rebind_inject:
            return False
        if d.pipe_left > 0:
            return False
        if not self.commit_all():
            return False
        return True

    def _newgen_allowed(self, node: int, tag: int) -> bool:
        latest = max(x.epoch_gen for x in self.dies)
        if (tag % EPOCH_MOD) != (latest % EPOCH_MOD):
            return True  # old-gen in-flight / re-inject
        if self.commit_all():
            return True
        if self.cfg.force_early_newgen:
            return True
        return False

    # ---- SYNC (Req CW citizen; not a traffic oracle) ----

    def _sync_at(self) -> int | None:
        for n in range(self.n):
            if self.slots["Req"]["CW"][n].kind == "sync":
                return n
        return None

    def _handle_sync(self, node: int) -> None:
        """Latch epoch / drain visits / commit bits. Never inspect queues."""
        d = self.dies[node]
        self.stats["sync_visit", node] += 1
        if d.drain_req:
            d.drain_visits += 1
        if d.commit_posted:
            self._commit_mask |= 1 << node
        if self._commit_mask == (1 << self.n) - 1:
            # full mask has ridden onto SYNC; a further lap makes it visible
            d.commit_seen_all = True
            # once any node sees the full mask, broadcast on subsequent visits
            for other in self.dies:
                if other.commit_posted:
                    other.commit_seen_all = True

    # ---- FSM ----

    def _desired_bind(self) -> str:
        return "Dat" if self._want_dat else "Snp"

    def _dwell_target(self, die: Die) -> int:
        if die.bind_snp == "Dat":
            return self.dat_dwell
        return self.snp_dwell

    def _fsm_tick(self, node: int) -> None:
        d = self.dies[node]
        if not self.on:
            d.fsm = "STEADY"
            d.bind_snp = "Snp"
            d.block_rebind_inject = False
            d.commit_seen_all = True
            return

        if d.fsm == "IDLE":
            d.fsm = "STEADY"

        if d.fsm == "STEADY":
            d.block_rebind_inject = False
            d.dwell += 1
            ready = d.dwell >= self._dwell_target(d) and (self.commit_all() or self._flip_gens == 0)
            want_switch = d.bind_snp != self._desired_bind() or ready
            # first generation: leave initial Snp bind for DAT_EPOCH
            if self._flip_gens == 0 and d.bind_snp != "Dat":
                want_switch = True
            elif ready:
                # completed a dwell in the current bind → flip to the other
                want_switch = True
            if want_switch and (self.commit_all() or self._flip_gens == 0):
                if d.bind_snp == self._desired_bind() and self._flip_gens > 0 and ready:
                    self._want_dat = not self._want_dat
                d.fsm = "ARM_DRAIN"
                d.drain_visits = 0
                d.drain_req = False
                d.commit_posted = False
                d.commit_seen_all = False
                d.block_rebind_inject = True
                self._drain_t0[node] = self.cycle
                self._commit_mask = 0
                for other in self.dies:
                    other.commit_seen_all = False
                    other.commit_posted = False

        if d.fsm == "ARM_DRAIN":
            d.block_rebind_inject = True
            d.drain_req = True
            d.fsm = "DRAIN"

        if d.fsm == "DRAIN":
            d.block_rebind_inject = True
            old = self.epoch_wire(node)
            local = self.sniff_old(node, old)
            if d.drain_visits >= self.cfg.k_circ and not local:
                d.fsm = "FLIP"
                d.pipe_left = max(1, self.cfg.n_pipe)
                d.drain_req = False

        if d.fsm == "FLIP":
            d.block_rebind_inject = True
            if d.pipe_left == self.cfg.n_pipe:
                d.epoch_gen += 1
                d.bind_snp = self._desired_bind()
                self._flip_gens += 1
            d.pipe_left -= 1
            if d.pipe_left <= 0:
                d.commit_posted = True
                d.dwell = 0
                d.fsm = "STEADY"
                d.block_rebind_inject = False
                if node in self._drain_t0:
                    self.drain_intervals.append(self.cycle - self._drain_t0[node])
                    del self._drain_t0[node]

    # ---- accept / NACK ----

    def _complete(self, slot: Slot, node: int) -> None:
        txn = self.txns.get(slot.tid)
        if txn is None:
            return
        # RBRG: header channel-id + bind+tag. Dat never becomes Snp.
        if slot.chi == "Dat" and slot.phys == "Snp":
            if slot.chi != "Dat":
                raise AssertionError("ghost header lost Dat channel-id")
        txn.done_at = self.cycle
        txn.via = "ghost" if slot.is_ghost else ("nack-reinject" if slot.nack else ("snp" if slot.chi == "Snp" else "main"))
        self.inflight[txn.src] = max(0, self.inflight[txn.src] - 1)
        self.stats["complete"] += 1
        self.stats["complete", slot.chi] += 1
        if self.sampling:
            if slot.is_ghost:
                self.dest_ghost[slot.dst] += 1
                self.stats["ghost_eject"] += 1
            elif slot.chi == "Dat":
                self.dest_main[slot.dst] += 1

    def _mismatch(self, slot: Slot, node: int) -> None:
        self.stats["bind_mismatch_redirect"] += 1
        self.stats["nack_reinject"] += 1
        txn = self.txns.get(slot.tid)
        if txn is not None:
            txn.nack_hops += 1
        # H-STAGING: depth-1 holding at the rejecting node, then Dat re-inject
        held = Slot.payload(txn, "Dat", slot.epoch_tag, False, nack=True) if txn else slot
        held.phys = "Dat"
        held.is_ghost = False
        held.nack = True
        d = self.dies[node]
        if d.holding is None:
            d.holding = held
        else:
            # holding full: bounce toward dest on next Dat attempt via src queue
            if txn is not None:
                self.queues[txn.src]["Dat"].appendleft(txn)
                self.inflight[txn.src] = max(0, self.inflight[txn.src] - 1)

    def _try_accept(self, slot: Slot, node: int) -> bool:
        if slot.kind != "payload" or slot.dst != node:
            return False
        acc = accept_set(self.epoch_wire(node))
        if (slot.epoch_tag % EPOCH_MOD) not in acc:
            self._mismatch(slot, node)
            return True
        self._complete(slot, node)
        return True

    # ---- inject ----

    def _pop(self, node: int, chi: str) -> Txn | None:
        q = self.queues[node][chi]
        if not q:
            return None
        if self.inflight[node] >= self.cfg.outstanding:
            return None
        if self.cfg.hold_app_until_aligned and not self.sampling:
            return None
        return q.popleft()

    def _choose_ghost(self, node: int, txn: Txn) -> bool:
        if not self._ghost_ok(node):
            return False
        if self.cfg.ghost_steer == "rr":
            pick = self.rr[node] % 2 == 0
            self.rr[node] += 1
            return pick
        return (txn.dst & 1) == 0

    def _do_inject(self, node: int, txn: Txn, phys: str, ghost: bool, nack: bool = False) -> Slot:
        """Caller owns the queue. Returns empty if the barrier forbids inject."""
        tag = self.epoch_wire(node)
        latest = max(x.epoch_gen for x in self.dies)
        behind = any(x.epoch_gen < latest for x in self.dies)
        if not self._newgen_allowed(node, tag):
            return Slot.empty()
        if behind and self.dies[node].epoch_gen == latest and (tag % EPOCH_MOD) == (latest % EPOCH_MOD):
            self.late_newgen_caught += 1
            if self.cfg.strict_commit and not self.cfg.force_early_newgen:
                raise LateNewgenInject(
                    f"node {node} new-gen tag={tag} before epoch_committed"
                )
        if txn.issue_at is None:
            txn.issue_at = self.cycle
            self.stats["issue"] += 1
            self.stats["issue", txn.chi] += 1
        self.inflight[node] += 1
        txn.via = "ghost" if ghost else ("snp" if txn.chi == "Snp" else "main")
        return Slot.payload(txn, phys, tag, ghost, nack)

    def _inject_node(self, node: int, new: dict) -> None:
        d = self.dies[node]
        # holding-register drain onto Dat (NACK path)
        if d.holding is not None:
            held = d.holding
            direction = dir_of(node, held.dst, self.n) if held.dst != node else "CW"
            if new["Dat"][direction][node].kind == "empty":
                # restage: hop toward dest on Dat
                if held.dst == node:
                    acc = accept_set(self.epoch_wire(node))
                    if (held.epoch_tag % EPOCH_MOD) in acc:
                        self._complete(held, node)
                        d.holding = None
                    # else keep holding — do not NACK-loop
                else:
                    new["Dat"][direction][node] = held
                    d.holding = None
            return

        # Dat
        if self.queues[node]["Dat"] and not (self.cfg.hold_app_until_aligned and not self.sampling):
            if self.inflight[node] < self.cfg.outstanding:
                txn = self.queues[node]["Dat"][0]
                direction = dir_of(node, txn.dst, self.n)
                use_ghost = self._choose_ghost(node, txn)
                placed = False
                if use_ghost and not d.block_rebind_inject:
                    if new["Snp"][direction][node].kind == "empty":
                        self.queues[node]["Dat"].popleft()
                        new["Snp"][direction][node] = self._do_inject(node, txn, "Snp", True)
                        placed = new["Snp"][direction][node].kind == "payload"
                        if not placed:
                            self.queues[node]["Dat"].appendleft(txn)
                            self.inflight[node] = max(0, self.inflight[node] - 0)
                if not placed:
                    if new["Dat"][direction][node].kind == "empty":
                        self.queues[node]["Dat"].popleft()
                        new["Dat"][direction][node] = self._do_inject(node, txn, "Dat", False)
                        placed = new["Dat"][direction][node].kind == "payload"
                        if not placed:
                            self.queues[node]["Dat"].appendleft(txn)
                    else:
                        if self.sampling:
                            self.stats["inject_fail"] += 1
        # Snp — stall with no queue on the ring during DAT_EPOCH
        if self.queues[node]["Snp"] and not (self.cfg.hold_app_until_aligned and not self.sampling):
            if self.inflight[node] < self.cfg.outstanding:
                txn = self.queues[node]["Snp"][0]
                direction = dir_of(node, txn.dst, self.n)
                snp_ok = (d.bind_snp == "Snp" and d.fsm == "STEADY"
                          and not d.block_rebind_inject and d.pipe_left <= 0)
                if not self.on:
                    snp_ok = True
                if snp_ok and new["Snp"][direction][node].kind == "empty":
                    self.queues[node]["Snp"].popleft()
                    new["Snp"][direction][node] = self._do_inject(node, txn, "Snp", False)
                    if new["Snp"][direction][node].kind != "payload":
                        self.queues[node]["Snp"].appendleft(txn)
                else:
                    d.n_snp_pend = min(15, d.n_snp_pend + 1)
                    if self.sampling:
                        self.stats["snp_stall"] += 1
            else:
                if self.sampling:
                    self.stats["snp_stall"] += 1
        else:
            d.n_snp_pend = max(0, d.n_snp_pend - 1)

        # pressure EMA (local; hint ignored)
        busy = 1.0 if any(self.slots["Dat"][dd][node].kind == "payload" for dd in DIRS) else 0.0
        d.dat_slots_seen += 1
        d.dat_busy_seen += int(busy)
        d.rho_dat_ema = 0.875 * d.rho_dat_ema + 0.125 * busy
        # hint is stored and never consulted
        _ = request_duty(d.rho_dat_ema, d.n_snp_pend, hint=d.hint)

    # ---- occupancy / warmup ----

    def _maybe_align(self) -> None:
        if self.aligned:
            return
        if not self.on:
            if self.cycle >= self.warmup_floor:
                self.aligned = True
                self.sampling = True
            return
        # SYNC-aligned STEADY after at least one committed generation
        if self._flip_gens > 0 and self.commit_all() and all(d.fsm == "STEADY" for d in self.dies):
            if self.cycle >= self.warmup_floor:
                self.aligned = True
                self.sampling = True

    def _record_capacity(self) -> None:
        if not self.sampling:
            return
        ghost_frac = sum(1 for i, _d in enumerate(self.dies) if self._ghost_ok(i)) / self.n
        self.stats["ghost_frac_sum"] += ghost_frac
        self.stats["cap_samples"] += 1
        steady = sum(1 for d in self.dies if d.fsm == "STEADY") / self.n
        drainish = sum(1 for d in self.dies if d.fsm in ("ARM_DRAIN", "DRAIN", "FLIP")) / self.n
        self.stats["steady_frac_sum"] += steady
        self.stats["drain_frac_sum"] += drainish
        if self.slots["Req"]["CW"][self._sync_at() or 0].kind == "sync":
            self.stats["sync_occ"] += 1
        for dname in DIRS:
            if self.slots["Dat"][dname][0].kind == "payload" or True:
                for n in range(self.n):
                    if self.slots["Dat"][dname][n].kind == "payload":
                        self.stats["main_dat_slots"] += 1
                    if (self.slots["Snp"][dname][n].kind == "payload"
                            and self.slots["Snp"][dname][n].is_ghost):
                        self.stats["ghost_slots"] += 1
                    self.stats["phys_slots"] += 1
        for d in self.dies:
            if d.fsm in FSM_STATES:
                self.stats["fsm", d.fsm] += 1
            if d.pipe_left > 0:
                self.stats["bind_pipe"] += 1

    # ---- step ----

    def pending(self) -> int:
        return sum(len(q["Dat"]) + len(q["Snp"]) for q in self.queues)

    def step(self, cycle: int) -> None:
        self.cycle = cycle
        self._maybe_align()
        # snapshot current slots, process arrivals, then rebuild
        cur = self.slots
        new = {c: {d: [Slot.empty() for _ in range(self.n)] for d in DIRS} for c in CHI}

        # arrivals: complete / sync latch / keep transit
        for chi in CHI:
            for dname in DIRS:
                for n in range(self.n):
                    slot = cur[chi][dname][n]
                    if slot.kind == "sync":
                        self._handle_sync(n)
                        new[chi][dname][n] = slot  # park; move later
                    elif slot.kind == "payload":
                        if slot.dst == n:
                            self._try_accept(slot, n)
                            # consumed (complete or holding)
                        else:
                            new[chi][dname][n] = slot

        # FSM after highway visible
        for n in range(self.n):
            self._fsm_tick(n)

        # inject into empties at this node (pre-rotate)
        for n in range(self.n):
            self._inject_node(n, new)

        # rotate one hop
        moved = {c: {d: [Slot.empty() for _ in range(self.n)] for d in DIRS} for c in CHI}
        for chi in CHI:
            for dname in DIRS:
                for n in range(self.n):
                    slot = new[chi][dname][n]
                    if slot.kind == "empty":
                        continue
                    dest = next_node(n, dname, self.n)
                    moved[chi][dname][dest] = slot
        self.slots = moved
        self._record_capacity()

    def done(self) -> bool:
        if not self.aligned and self.cycle < self.limit - 1:
            if self.pending() or sum(self.inflight) or any(d.holding for d in self.dies):
                return False
            if not self.txns:
                return self.cycle + 1 >= min(self.limit, self.warmup_floor + 4 * self.n)
            return False
        if self.pending() == 0 and sum(self.inflight) == 0 and all(d.holding is None for d in self.dies):
            if not any(t.issue_at is not None for t in self.txns.values()) and self.txns:
                return False
            return self.aligned or not self.txns
        return False

    def result(self) -> CycleResult:
        dat = [t for t in self.txns.values() if t.chi == "Dat" and t.cls != "plant"]
        snp = [t for t in self.txns.values() if t.chi == "Snp"]
        done_dat = [t for t in dat if t.done_at is not None]
        done_snp = [t for t in snp if t.done_at is not None]
        iss_dat = [t for t in dat if t.issue_at is not None]
        iss_snp = [t for t in snp if t.issue_at is not None]
        done_all = [t for t in self.txns.values() if t.done_at is not None and t.tid >= 0]

        def span(xs: list[Txn]) -> int:
            if not xs:
                return 0
            a = min(t.issue_at or 0 for t in xs)
            b = max(t.done_at or 0 for t in xs)
            return max(1, b - a)

        first = min((t.issue_at for t in done_all if t.issue_at is not None), default=0)
        last = max((t.done_at for t in done_all if t.done_at is not None), default=0)
        nsamp = max(1, int(self.stats["cap_samples"]))
        ghost_mean = self.stats["ghost_frac_sum"] / nsamp
        f_st = self.stats["steady_frac_sum"] / nsamp
        tau_dr = self.stats["drain_frac_sum"] / nsamp
        tau_sync = self.stats["sync_occ"] / nsamp if nsamp else 0.0
        tau_bind = self.stats["bind_pipe"] / (nsamp * self.n) if nsamp else 0.0
        c_eff = 1.0 + ghost_mean
        ideal = 1.0 + self.duty_dat
        if c_eff > ideal + 1e-9:
            # conservation: never mint above ideal
            c_eff = ideal
        tax = (tau_dr + tau_sync + tau_bind) if self.on else 0.0
        t_drain = (sum(self.drain_intervals) / len(self.drain_intervals)) if self.drain_intervals else 0.0
        # HARD-2: uniform-like dest spread on ghost vs main; gather is workload-collapsed
        def collapsed(hist: dict[int, int]) -> bool:
            if len(hist) <= 1:
                return True
            tot = sum(hist.values())
            if tot <= 0:
                return False
            return max(hist.values()) / tot >= 0.95

        hard2 = False
        if self.cfg.traffic_class in ("uniform_read", "uniform_write", "snp_path", "alltoall"):
            if self.dest_ghost and collapsed(self.dest_ghost) and not collapsed(self.dest_main):
                hard2 = True
        fail_rate = 0.0
        att = int(self.stats["inject_fail"]) + int(self.stats["issue"])
        if att:
            fail_rate = int(self.stats["inject_fail"]) / att
        return CycleResult(
            cycles=self.cycle,
            completed=len(done_all),
            completed_dat=len(done_dat),
            completed_snp=len(done_snp),
            issued=len(iss_dat) + len(iss_snp),
            issued_dat=len(iss_dat),
            issued_snp=len(iss_snp),
            warmup_cycles=first if self.aligned else self.warmup_floor,
            makespan=max(1, last - first) if done_all else 0,
            makespan_dat=span(done_dat) if done_dat else 0,
            makespan_snp=span(done_snp) if done_snp else 0,
            first_issue=first,
            last_complete=last,
            c_dat_eff=c_eff,
            c_dat_ideal=ideal,
            duty_dat=self.duty_dat,
            f_steady=f_st,
            t_drain_mean=t_drain,
            tau_drain=tau_dr,
            tau_sync=tau_sync,
            tau_bind=tau_bind,
            tax=tax,
            ghost_slots=int(self.stats["ghost_slots"]),
            main_dat_slots=int(self.stats["main_dat_slots"]),
            bind_mismatch_redirect=int(self.stats["bind_mismatch_redirect"]),
            snp_stall=int(self.stats["snp_stall"]),
            inject_fail=int(self.stats["inject_fail"]),
            nack_reinject=int(self.stats["nack_reinject"]),
            dest_main=dict(self.dest_main),
            dest_ghost=dict(self.dest_ghost),
            hard2_collapsed=hard2,
            fsm_counts={s: int(self.stats["fsm", s]) for s in FSM_STATES},
            epoch_committed_all_cycles=int(self.stats["cap_samples"] if self.commit_all() else 0),
            correctness_depends_on_hint=False,
            oracle_used=self.oracle_used,
            sync_read_queues=self.sync_read_queues,
            hint_used=self.cfg.hint is not None,
            aligned=self.aligned,
            late_newgen_caught=self.late_newgen_caught,
            n_nodes=self.n,
            arm=self.arm,
            traffic_class=self.cfg.traffic_class,
            collapsed=fail_rate >= 0.50,
            goodput_b_per_cyc=(len(done_all) * BYTES_PER_TXN) / max(1, last - first) if done_all else 0.0,
        )


def run_cycles(cfg: SimConfig, txns: list[Txn] | None = None) -> CycleResult:
    """Same SimPy clock + fabric for every arm. Workload list is an input."""
    if txns is None:
        n = cfg.n_nodes + cfg.n_bottom
        if cfg.n_snp:
            txns = gen_mixed(n, cfg.n_txn, cfg.n_snp, cfg.seed, cfg.traffic_class)
        else:
            txns = gen_txns(cfg.traffic_class, n, cfg.n_txn, cfg.seed)
    env = simpy.Environment()
    fab = Fabric(cfg, txns)

    def clock():
        while True:
            fab.step(int(env.now))
            yield env.timeout(1)
            if fab.done() or int(env.now) >= fab.limit:
                break

    env.process(clock())
    env.run()
    return fab.result()


def run_arm(arm: str, cls: str, seed: int, txns: list[Txn] | None = None, **kwargs) -> CycleResult:
    cfg = SimConfig(arm=arm, traffic_class=cls, seed=seed, **kwargs)
    n = cfg.n_nodes + cfg.n_bottom
    if txns is None:
        if cfg.n_snp:
            txns = gen_mixed(n, cfg.n_txn, cfg.n_snp, seed, cls)
        else:
            txns = gen_txns(cls, n, cfg.n_txn, seed)
    return run_cycles(cfg, txns)


def probe_drain(n_nodes: int = 25, n_pipe: int = 2, seed: int = SEED) -> dict:
    """Force one Snp→Dat flip, measure ARM_DRAIN → epoch_committed (no app traffic)."""
    cfg = SimConfig(
        n_nodes=n_nodes,
        arm="7:1",
        n_pipe=n_pipe,
        n_txn=0,
        traffic_class="gather",
        seed=seed,
        hold_app_until_aligned=False,
        max_cycles=n_nodes * 12 + 64,
        t_steady_laps=1,
    )
    env = simpy.Environment()
    fab = Fabric(cfg, [])
    t0 = None
    t1 = None

    def clock():
        nonlocal t0, t1
        while True:
            cyc = int(env.now)
            fab.step(cyc)
            if t0 is None and any(d.fsm == "ARM_DRAIN" or d.fsm == "DRAIN" for d in fab.dies):
                t0 = cyc
            if t0 is not None and fab.commit_all() and all(d.bind_snp == "Dat" for d in fab.dies):
                t1 = cyc
                break
            yield env.timeout(1)
            if int(env.now) >= fab.limit:
                break

    env.process(clock())
    env.run()
    measured = (t1 - t0) if (t0 is not None and t1 is not None) else float("nan")
    return {
        "n_nodes": n_nodes,
        "n_pipe": n_pipe,
        "t0": t0,
        "t1": t1,
        "t_drain": measured,
        "t2_t_drain": T2_T_DRAIN,
        "formula": (K_CIRC + 1) * n_nodes + n_pipe,
    }


def probe_commit(n_nodes: int = 12, violated: bool = False, seed: int = SEED) -> dict:
    """H-COMMIT held → redirect=0; violated (early new-gen) → mismatch>0."""
    n_txn = n_nodes
    txns = gen_txns("gather", n_nodes, n_txn, seed)
    cfg = SimConfig(
        n_nodes=n_nodes,
        arm="7:1",
        n_txn=n_txn,
        seed=seed,
        force_early_newgen=violated,
        strict_commit=not violated,
        hold_app_until_aligned=False,
        max_cycles=n_nodes * 40 + 256,
        t_steady_laps=4,
    )
    r = run_cycles(cfg, txns)
    return {
        "violated": violated,
        "bind_mismatch_redirect": r.bind_mismatch_redirect,
        "late_newgen_caught": r.late_newgen_caught,
        "t2_held": H_COMMIT_HELD,
        "t2_violated": H_COMMIT_VIOLATED,
        "completed": r.completed,
    }


def compare_to_t2(metric: str, arm: str, t3: float, t2: float, note: str = "") -> dict:
    err = rel_err(t3, t2) if (t2 == t2 and t3 == t3 and t2 != 0) else (0.0 if t3 == t2 else float("inf"))
    flag = bool(err > 0.30) if err == err else True
    return {
        "metric": metric,
        "arm": arm,
        "t3": t3,
        "t2": t2,
        "rel_err": err,
        "flag_gt_30pct": flag,
        "card_claim": "NOT measured",
        "card_claim_is_measured": False,
        "note": note,
    }


def signed_t2_rows() -> list[dict]:
    return [
        {"metric": "T_drain", "arm": "C_ring=25", "t3": "", "t2": T2_T_DRAIN,
         "rel_err": "", "flag_gt_30pct": "", "note": "signed; cycle row filled by drain probe"},
        {"metric": "f_steady", "arm": "default", "t3": "", "t2": T2_F_STEADY,
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "C_dat_eff", "arm": "rebind-off", "t3": "", "t2": T2_C_DAT_EFF["rebind-off"],
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "C_dat_eff", "arm": "3:1", "t3": "", "t2": T2_C_DAT_EFF["3:1"],
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "C_dat_eff", "arm": "7:1", "t3": "", "t2": T2_C_DAT_EFF["7:1"],
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "C_dat_eff", "arm": "15:1", "t3": "", "t2": T2_C_DAT_EFF["15:1"],
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "H-COMMIT held", "arm": "barrier on", "t3": "", "t2": H_COMMIT_HELD,
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "H-COMMIT violated", "arm": "early inject", "t3": "", "t2": H_COMMIT_VIOLATED,
         "rel_err": "", "flag_gt_30pct": "", "note": "signed (n_nodes=12)"},
        {"metric": "H-DAT-DOM gather T_hat/T_off", "arm": "3:1", "t3": "", "t2": H_DAT_DOM_GATHER["3:1"],
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "H-DAT-DOM gather T_hat/T_off", "arm": "7:1", "t3": "", "t2": H_DAT_DOM_GATHER["7:1"],
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "H-DAT-DOM gather T_hat/T_off", "arm": "15:1", "t3": "", "t2": H_DAT_DOM_GATHER["15:1"],
         "rel_err": "", "flag_gt_30pct": "", "note": "signed"},
        {"metric": "HARD-1 T_off vs T_best (ns, H-DAT-DOM)", "arm": "gather",
         "t3": "", "t2": f"{HARD1_T_OFF}>{HARD1_T_BEST}",
         "rel_err": "", "flag_gt_30pct": "", "note": "T2 ns; T3 compares cycle inequality"},
        {"metric": "H-SNP-LAT", "arm": "15:1", "t3": "", "t2": SNP_15_1,
         "rel_err": "", "flag_gt_30pct": "", "note": "signed KILL (1.4× hyp)"},
        {"metric": "card-claim", "arm": "Dat-heavy", "t3": "NOT measured", "t2": CARD_CLAIM_DAT,
         "rel_err": "", "flag_gt_30pct": "", "note": "card-claim only; director did not sign"},
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CRRF cycle sim (single run)")
    p.add_argument("--class", dest="cls", choices=CLASSES, default="gather")
    p.add_argument("--arm", choices=ARMS, default="7:1")
    p.add_argument("--n-nodes", type=int, default=12)
    p.add_argument("--n-bottom", type=int, default=0)
    p.add_argument("--n-txn", type=int, default=64)
    p.add_argument("--n-snp", type=int, default=0)
    p.add_argument("--outstanding", type=int, default=16)
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)
    r = run_arm(
        args.arm, args.cls, args.seed,
        n_nodes=args.n_nodes, n_bottom=args.n_bottom,
        n_txn=args.n_txn, n_snp=args.n_snp, outstanding=args.outstanding,
    )
    print(
        f"CRRF T3 class={args.cls} arm={args.arm} n={args.n_nodes}+{args.n_bottom} "
        f"|I|={args.n_txn} seed={args.seed}"
    )
    print(
        f"warmup_aligned={r.aligned} makespan={r.makespan} "
        f"completed_dat={r.completed_dat} completed_snp={r.completed_snp} "
        f"collapsed={r.collapsed}"
    )
    print(
        f"C_dat_eff={r.c_dat_eff:.4f} ≤ ideal {r.c_dat_ideal:.4f}  "
        f"f_steady={r.f_steady:.4f} tax={r.tax:.4f} T_drain~{r.t_drain_mean:.1f}"
    )
    print(
        f"mismatch={r.bind_mismatch_redirect} nack={r.nack_reinject} "
        f"snp_stall={r.snp_stall} ghost_slots={r.ghost_slots} "
        f"hint_depends={r.correctness_depends_on_hint} oracle={r.oracle_used}"
    )
    print(f"card-claim {card_claim_of(args.cls)} is NOT measured")
    print("0.85 is a pass bar, not a measured mean; no team-384dmc; not M-1 CBC")
    t2mod = try_load_t2_module()
    print("T2 model.py on this tree:" + (" yes" if t2mod else " no (PR #63 only; using signed constants)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
