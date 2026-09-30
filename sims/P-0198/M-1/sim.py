#!/usr/bin/env python3
"""P-0198/M-1 CBC — cycle-level bufferless-ring SimPy model.

Cycle-accurate (card + Dr.Sim must-verify):
  Bubble FSM IDLE/WATCH/EMIT/HOLD × node × direction × CHI four rings,
  64×8 calendar (1R shared across ≤8 FSMs) + phase alignment,
  1b tag + 4b age hop-by-hop, bubble cluster-length histogram,
  same-cycle steal / raw-inject / fail counts (separate),
  warmup ≥ one ring lap, software-epoch only (no arrival oracle).
Black box: hop latency, flit=txn, RBRG, HBM, coherence, D2D, clock.
T2 analytical model is NOT on main (PR #54). Compare uses signed audit
numbers + spec §3 formulas; never treat card-claim 0.55–0.85× as measured.
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

from _lib.stats import rel_err  # noqa: E402
from _lib.t2load import load_cbc_t2  # noqa: E402
from _lib.workloads import SEED  # noqa: E402

CHI = ("Req", "Rsp", "Snp", "Dat")
DIRS = ("CW", "CCW")
STATES = ("IDLE", "WATCH", "EMIT", "HOLD")
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
INJ_DOM = {"gather", "reduce", "allgather", "allreduce", "alltoall"}
DUTY_P2P = (1 / 16, 1 / 8)
DUTY_COLL = (1 / 4, 1 / 2)
AGE_MAX = 15
W_EMIT = 8
CAL_ROWS = 64
BYTES_PER_TXN = 512

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

# Signed T2 audit (PR #56) — director / 评估审计. card-claim is NOT signed.
T2_SIGNED = {
    "sum_ok": True,
    "h_inj_dom_d25": 0.7368,
    "h_inj_dom_d50": 0.5833,
    "hard1_t_off": 537.2,
    "hard1_t_cbc": 313.4,
    "dual_d25": 1.3333,
    "dual_d50": 2.0000,
}
T2_H_RHO = 0.20
T2_H_ETA0 = 0.35
T2_H_ETA = 0.85
T2_H_LAM_AGE = 1.0
CARD_CLAIM_COLL = "0.55-0.85x"  # print as card-claim only; never measured

ARMS = (
    "calendar-off",
    "duty=0",
    "CBC-P2P-1/16",
    "CBC-P2P-1/8",
    "CBC-coll-1/4",
    "CBC-coll-1/2",
    "fixed-high-1/2",
)


def duty_of_arm(arm: str) -> float:
    return {
        "calendar-off": 0.0,
        "duty=0": 0.0,
        "CBC-P2P-1/16": 1 / 16,
        "CBC-P2P-1/8": 1 / 8,
        "CBC-coll-1/4": 1 / 4,
        "CBC-coll-1/2": 1 / 2,
        "fixed-high-1/2": 1 / 2,
    }[arm]


def calendar_on_of_arm(arm: str) -> bool:
    return arm != "calendar-off"


def density_of(duty: float) -> int:
    return max(0, min(15, int(round(duty * 16.0))))


def encode_cal(density: int, phase: int) -> int:
    return ((density & 0xF) << 4) | (phase & 0xF)


def decode_cal(entry: int) -> tuple[int, int]:
    return (entry >> 4) & 0xF, entry & 0xF


def program_calendar(duty: float, phase: int = 0) -> tuple[int, ...]:
    """64×8: every row holds the same programmed duty/phase (static class)."""
    entry = encode_cal(density_of(duty), phase & 0xF)
    return tuple(entry for _ in range(CAL_ROWS))


def program_phased_calendar(p2p_duty: float, coll_duty: float, phase: int = 0) -> tuple[int, ...]:
    """Row 0 = P2P epoch, row 1 = fan-in epoch. No arrival-time fill."""
    table = [encode_cal(density_of(p2p_duty), phase & 0xF) for _ in range(CAL_ROWS)]
    table[1] = encode_cal(density_of(coll_duty), phase & 0xF)
    return tuple(table)


# ---- T2 analytical replay (spec §3 / PR #54 model.py). Not cycle-measured. ----

def t2_partition(rho_empty: float, d: float, lam_age: float = T2_H_LAM_AGE) -> tuple[float, float]:
    if rho_empty < 0 or rho_empty > 1:
        raise ValueError("rho_empty out of [0,1]")
    d = max(0.0, min(1.0, d))
    lam_age = max(0.0, min(1.0, lam_age))
    rho_bubble = min(d, 1.0) * rho_empty
    rho_bubble_eff = lam_age * rho_bubble
    rho_raw_eff = rho_empty - rho_bubble_eff
    return rho_raw_eff, rho_bubble_eff


def t2_p_inj(rho_empty: float, d: float, eta: float = T2_H_ETA, eta0: float = T2_H_ETA0,
             lam_age: float = T2_H_LAM_AGE) -> tuple[float, float]:
    p_off = min(rho_empty * eta0, rho_empty)
    p_on = min(rho_empty * ((1.0 - d) * eta0 + d * eta * lam_age), rho_empty)
    return p_off, p_on


def t2_h_inj_dom_ratio(d: float) -> float:
    p_off, p_on = t2_p_inj(T2_H_RHO, d)
    if p_off <= 0 or p_on <= 0:
        return float("inf")
    return p_off / p_on


def t2_dual_ratio(d_a: float) -> float:
    raw, _ = t2_partition(T2_H_RHO, d_a)
    if raw <= 0:
        return float("inf")
    return T2_H_RHO / raw


def try_load_t2_module():
    try:
        return load_cbc_t2()
    except FileNotFoundError:
        return None


@dataclass
class Txn:
    tid: int
    src: int
    dst: int
    chi: str
    cls: str
    kind: str
    tenant: str
    phase: int
    nbytes: int = BYTES_PER_TXN


@dataclass
class Slot:
    kind: str = "empty"  # empty | bubble | payload
    age: int = 0
    src: int = -1
    dst: int = -1
    tid: int = -1
    tenant: str = ""
    cls: str = ""
    kind_inj: str = ""

    @staticmethod
    def empty() -> "Slot":
        return Slot(kind="empty")

    @staticmethod
    def bubble(age: int = 0) -> "Slot":
        return Slot(kind="bubble", age=age)

    @staticmethod
    def payload(txn: Txn, kind_inj: str) -> "Slot":
        return Slot(
            kind="payload",
            src=txn.src,
            dst=txn.dst,
            tid=txn.tid,
            tenant=txn.tenant,
            cls=txn.cls,
            kind_inj=kind_inj,
        )


@dataclass
class BubbleFSM:
    state: str = "IDLE"
    watch: int = 0


def fsm_tick(fsm: BubbleFSM, mandatory: bool, saw_bubble: bool, emitted: bool) -> None:
    """One ring-tick of IDLE/WATCH/EMIT/HOLD. Aligned with the highway cycle.

    W counts cycles since a bubble was seen (card: 过去 W 周期未见气泡), not
    consecutive duty-on ticks. Duty only gates EMIT; a 1-cycle SRAM lookup
    must not wipe the window.
    """
    if saw_bubble:
        fsm.watch = 0
        if mandatory:
            fsm.state = "WATCH"
        else:
            fsm.state = "IDLE"
        return
    fsm.watch += 1
    if not mandatory:
        if fsm.state == "EMIT" and not emitted:
            fsm.state = "IDLE"
        elif fsm.state != "HOLD":
            fsm.state = "IDLE"
        return
    if fsm.state == "IDLE":
        fsm.state = "WATCH"
    if fsm.state == "WATCH" and fsm.watch >= W_EMIT:
        fsm.state = "EMIT"
    elif fsm.state == "EMIT":
        if emitted:
            fsm.state = "HOLD"
            fsm.watch = 0
    elif fsm.state == "HOLD" and fsm.watch >= W_EMIT:
        fsm.state = "WATCH"


def dir_of(src: int, dst: int, n: int) -> str:
    cw = (dst - src) % n
    ccw = (src - dst) % n
    return "CW" if cw <= ccw else "CCW"


def next_node(node: int, direction: str, n: int) -> int:
    return (node + 1) % n if direction == "CW" else (node - 1) % n


def gen_txns(cls: str, n_nodes: int, n_txn: int, seed: int, tenant: str = "solo") -> list[Txn]:
    """Synthetic DV200-class traffic. Same seed → same list (fair compare)."""
    if cls not in CLASSES:
        raise ValueError(f"unknown class {cls}")
    rng = random.Random(seed)
    kind = "p2p" if cls in P2P_CLASSES else "collective"
    chi = "Dat"
    txns: list[Txn] = []

    def add(src: int, dst: int, phase: int = 0) -> None:
        if src == dst:
            raise ValueError("self-dest")
        txns.append(Txn(len(txns), src, dst, chi, cls, kind, tenant, phase))

    if cls in ("uniform_read", "uniform_write"):
        for _ in range(n_txn):
            src = rng.randrange(n_nodes)
            dst = rng.randrange(n_nodes - 1)
            if dst >= src:
                dst += 1
            add(src, dst)
    elif cls in ("gather", "reduce"):
        sink = 0  # static software root — not an arrival oracle
        for i in range(n_txn):
            add(1 + (i % (n_nodes - 1)), sink)
    elif cls == "broadcast":
        root = 0
        i = 0
        while i < n_txn:
            for dst in range(n_nodes):
                if dst == root:
                    continue
                add(root, dst)
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
                    add(src, dst)
                    i += 1
                    if i >= n_txn:
                        break
                if i >= n_txn:
                    break
    elif cls == "allreduce":
        # software epochs: phase 0 fan-in, phase 1 fan-out. Posted by the
        # issue schedule, not by flit arrival times.
        half = max(1, n_txn // 2)
        sink = 0
        for i in range(half):
            add(1 + (i % (n_nodes - 1)), sink, phase=0)
        i = 0
        while len(txns) < n_txn:
            dst = 1 + (i % (n_nodes - 1))
            add(sink, dst, phase=1)
            i += 1
    else:  # alltoall
        for i in range(n_txn):
            src = i % n_nodes
            dst = (src + 1 + rng.randrange(n_nodes - 1)) % n_nodes
            add(src, dst)
    return txns[:n_txn]


@dataclass
class SimConfig:
    n_nodes: int = 12
    n_bottom: int = 0  # bbox: extra nodes on the same ring (12+2 → 14)
    chi: tuple[str, ...] = CHI
    dirs: tuple[str, ...] = DIRS
    duty: float = 0.0
    calendar_on: bool = True
    lookup_lat: int = 1
    cal_phase: int = 0
    table: tuple[int, ...] | None = None
    warmup_laps: int = 1
    outstanding: int = 16
    hop_lat: int = 1  # black-box; 1 = one cycle per hop
    n_txn: int = 96
    traffic_class: str = "gather"
    seed: int = SEED
    tenant_b_class: str | None = None
    tenant_b_n_txn: int = 96
    max_cycles: int | None = None
    epoch_mode: str = "fixed"  # fixed | software


@dataclass
class Occupancy:
    rho_payload: float
    rho_empty: float
    rho_raw: float
    rho_bubble: float
    sum_ok: bool
    n_samples: int
    cluster_hist: dict[int, int]
    mean_cluster: float


@dataclass
class CycleResult:
    cycles: int
    completed: int
    issued: int
    warmup_cycles: int
    makespan: int
    first_issue: int
    last_complete: int
    steal: int
    raw_inject: int
    fail: int
    emit: int
    age_degrade: int
    p_inj: float
    rho_payload: float
    rho_empty: float
    rho_raw: float
    rho_bubble: float
    sum_ok: bool
    delta_rho_empty: float
    cluster_hist: dict[int, int]
    mean_cluster: float
    fsm_counts: dict[str, int]
    cal_lookups: int
    collapsed: bool
    goodput_b_per_cyc: float
    n_nodes: int
    n_fsm: int
    software_epochs_seen: list[int]
    oracle_used: bool
    tenant_completed: dict[str, int]
    tenant_makespan: dict[str, int]
    tenant_p_inj: dict[str, float]
    hypothesis: str = "H-RING-BB"


class Fabric:
    def __init__(self, cfg: SimConfig, txns: list[Txn]):
        if cfg.hop_lat != 1:
            raise NotImplementedError("hop_lat>1 is parameterized bbox; smoke uses 1")
        self.cfg = cfg
        self.n = cfg.n_nodes + cfg.n_bottom
        if self.n < 3:
            raise ValueError("need ≥3 nodes")
        self.chis = tuple(cfg.chi)
        self.dirs = tuple(cfg.dirs)
        self.warmup = max(cfg.warmup_laps, 1) * self.n
        self.slots = {c: {d: [Slot.empty() for _ in range(self.n)] for d in self.dirs} for c in self.chis}
        self.fsm = {c: {d: [BubbleFSM() for _ in range(self.n)] for d in self.dirs} for c in self.chis}
        self.table = cfg.table if cfg.table is not None else program_calendar(cfg.duty, cfg.cal_phase)
        if len(self.table) != CAL_ROWS:
            raise ValueError("calendar must be 64×8")
        self.cal_out = (0, 0)
        self.cal_pending = decode_cal(self.table[0])
        self.cal_lookups = 0
        self.software_epoch = 0
        self.epochs_seen: list[int] = []
        self.queues: list[dict[str, deque[Txn]]] = [
            {"collective": deque(), "p2p": deque()} for _ in range(self.n)
        ]
        self.inflight = [0] * self.n
        self.done_at: dict[int, int] = {}
        self.issue_at: dict[int, int] = {}
        self.stats = Counter()
        self.cluster_hist: dict[int, int] = defaultdict(int)
        self.occ = Counter()
        self.cycle = 0
        self.oracle_used = False
        self.active_chi = {t.chi for t in txns} or {"Dat"}
        for t in txns:
            self.queues[t.src][t.kind].append(t)
        extra = 8 * max(1, len(txns)) * self.n
        self.limit = cfg.max_cycles if cfg.max_cycles is not None else self.warmup + extra + 256

    def n_fsm(self) -> int:
        return len(self.chis) * len(self.dirs) * self.n

    def _update_software_epoch(self) -> None:
        # Posted issue-schedule phase only. Do not inspect in-flight arrivals.
        if self.cfg.epoch_mode != "software":
            return
        for n in range(self.n):
            for kind in ("collective", "p2p"):
                q = self.queues[n][kind]
                if q:
                    self.software_epoch = q[0].phase & 63
                    return

    def _calendar_tick(self, cycle: int) -> None:
        self._update_software_epoch()
        if not self.epochs_seen or self.epochs_seen[-1] != self.software_epoch:
            self.epochs_seen.append(self.software_epoch)
        entry = self.table[self.software_epoch & 63]
        decoded = decode_cal(entry)
        self.cal_lookups += 1
        if self.cfg.lookup_lat <= 0:
            self.cal_out = decoded
        else:
            if cycle == 0:
                self.cal_out = (0, 0)
            else:
                self.cal_out = self.cal_pending
            self.cal_pending = decoded

    def _mandatory(self, node: int, cycle: int) -> bool:
        if not self.cfg.calendar_on:
            return False
        dens, phase = self.cal_out
        if dens <= 0:
            return False
        return ((cycle + phase + node) % 16) < dens

    def _apply_age(self, slot: Slot) -> Slot:
        if slot.kind != "bubble":
            return slot
        aged = Slot.bubble(slot.age + 1)
        if aged.age >= AGE_MAX:
            self.stats["age_degrade"] += 1
            return Slot.empty()
        return aged

    def _record_occupancy(self, slots: list[Slot], chi: str) -> None:
        if chi not in self.active_chi:
            return
        for s in slots:
            if s.kind == "payload":
                self.occ["payload"] += 1
            elif s.kind == "bubble":
                self.occ["bubble"] += 1
            else:
                self.occ["raw"] += 1
            self.occ["slots"] += 1

    def _record_clusters(self, slots: list[Slot]) -> None:
        n = len(slots)
        if n == 0:
            return
        kinds = [s.kind == "bubble" for s in slots]
        if not any(kinds):
            return
        # circular runs
        start = 0
        while start < n and kinds[start]:
            start += 1
        if start == n:
            self.cluster_hist[n] += 1
            return
        i = start
        for _ in range(n):
            if kinds[i]:
                run = 0
                while kinds[i]:
                    run += 1
                    i = (i + 1) % n
                self.cluster_hist[run] += 1
            else:
                i = (i + 1) % n

    def _ready_idx(self, node: int, chi: str, direction: str, kind: str) -> int | None:
        if self.cycle < self.warmup:
            return None
        if self.inflight[node] >= self.cfg.outstanding:
            return None
        q = self.queues[node][kind]
        for i, t in enumerate(q):
            if t.chi == chi and dir_of(t.src, t.dst, self.n) == direction:
                return i
        return None

    def _pop_ready(self, node: int, chi: str, direction: str, kind: str) -> Txn | None:
        i = self._ready_idx(node, chi, direction, kind)
        if i is None:
            return None
        q = self.queues[node][kind]
        txn = q[i]
        del q[i]
        return txn

    def _inject(self, node: int, txn: Txn, slot: Slot, sampling: bool) -> Slot:
        if slot.kind == "bubble":
            if sampling:
                self.stats["steal"] += 1
                self.stats["steal", txn.tenant] += 1
            inj = "steal"
        else:
            if sampling:
                self.stats["raw_inject"] += 1
                self.stats["raw_inject", txn.tenant] += 1
            inj = "raw"
        if sampling:
            self.stats["attempts"] += 1
            self.stats["attempts", txn.tenant] += 1
        self.inflight[node] += 1
        self.issue_at[txn.tid] = self.cycle
        return Slot.payload(txn, inj)

    def _arbitrate(self, node: int, chi: str, direction: str, slot: Slot,
                   mandatory: bool, fsm: BubbleFSM, sampling: bool) -> tuple[Slot, bool]:
        want_c = self._ready_idx(node, chi, direction, "collective") is not None
        want_p = self._ready_idx(node, chi, direction, "p2p") is not None
        emptyish = slot.kind in ("empty", "bubble")
        if not emptyish:
            if (want_c or want_p) and sampling:
                kind = "collective" if want_c else "p2p"
                idx = self._ready_idx(node, chi, direction, kind)
                ten = self.queues[node][kind][idx].tenant if idx is not None else "solo"
                self.stats["fail"] += 1
                self.stats["attempts"] += 1
                self.stats["fail", ten] += 1
                self.stats["attempts", ten] += 1
            return slot, False
        if want_c:
            txn = self._pop_ready(node, chi, direction, "collective")
            assert txn is not None
            return self._inject(node, txn, slot, sampling), False
        if want_p:
            txn = self._pop_ready(node, chi, direction, "p2p")
            assert txn is not None
            return self._inject(node, txn, slot, sampling), False
        # Same-cycle emit: W cycles since last bubble (watch is pre-tick).
        emit_ready = fsm.state == "EMIT" or (fsm.watch + 1 >= W_EMIT)
        if (self.cfg.calendar_on and mandatory and emit_ready
                and slot.kind == "empty"):
            if sampling:
                self.stats["emit"] += 1
            return Slot.bubble(0), True
        return slot, False

    def _complete(self, slot: Slot, cycle: int) -> None:
        self.done_at[slot.tid] = cycle
        if 0 <= slot.src < self.n:
            self.inflight[slot.src] = max(0, self.inflight[slot.src] - 1)
        self.stats["complete"] += 1
        self.stats["complete", slot.tenant] += 1
        if slot.tenant:
            prev = self.stats["last_complete", slot.tenant]
            if cycle >= prev:
                self.stats["last_complete", slot.tenant] = cycle
            first = self.stats["first_issue_saved", slot.tenant]
            issued = self.issue_at.get(slot.tid, cycle)
            if first == 0 or issued < first:
                self.stats["first_issue_saved", slot.tenant] = issued

    def pending(self) -> int:
        return sum(len(q["collective"]) + len(q["p2p"]) for q in self.queues)

    def step(self, cycle: int) -> None:
        self.cycle = cycle
        sampling = cycle >= self.warmup
        self._calendar_tick(cycle)
        new = {c: {d: [Slot.empty() for _ in range(self.n)] for d in self.dirs} for c in self.chis}
        for chi in self.chis:
            for d in self.dirs:
                aged = [self._apply_age(self.slots[chi][d][n]) for n in range(self.n)]
                if sampling:
                    self._record_occupancy(aged, chi)
                    self._record_clusters(aged)
                for n in range(self.n):
                    slot = aged[n]
                    if slot.kind == "payload" and slot.dst == n:
                        self._complete(slot, cycle)
                        slot = Slot.empty()
                    mandatory = self._mandatory(n, cycle)
                    fsm = self.fsm[chi][d][n]
                    saw = slot.kind == "bubble"
                    slot, emitted = self._arbitrate(n, chi, d, slot, mandatory, fsm, sampling)
                    fsm_tick(fsm, mandatory, saw, emitted)
                    if sampling:
                        self.stats["fsm", fsm.state] += 1
                    new[chi][d][next_node(n, d, self.n)] = slot
        self.slots = new

    def done(self) -> bool:
        if self.cycle < self.warmup:
            return False
        if self.pending() == 0 and sum(self.inflight) == 0:
            # Idle / empty-ring probes must keep ticking so age and clusters exist.
            if not self.issue_at:
                return self.cycle + 1 >= self.limit
            return True
        return False

    def occupancy(self) -> Occupancy:
        tot = self.occ["slots"]
        if tot <= 0:
            return Occupancy(0, 0, 0, 0, True, 0, {}, 0.0)
        pay = self.occ["payload"] / tot
        raw = self.occ["raw"] / tot
        bub = self.occ["bubble"] / tot
        empty = raw + bub
        ok = abs((pay + empty) - 1.0) < 1e-12 and abs((raw + bub) - empty) < 1e-12
        hist = dict(self.cluster_hist)
        if hist:
            num = sum(k * v for k, v in hist.items())
            den = sum(hist.values())
            mean_c = num / den if den else 0.0
        else:
            mean_c = 0.0
        return Occupancy(pay, empty, raw, bub, ok, tot, hist, mean_c)

    def result(self) -> CycleResult:
        occ = self.occupancy()
        steal = int(self.stats["steal"])
        raw = int(self.stats["raw_inject"])
        fail = int(self.stats["fail"])
        attempts = steal + raw + fail
        p_inj = (steal + raw) / attempts if attempts else 0.0
        issued = len(self.issue_at)
        completed = len(self.done_at)
        if self.issue_at and self.done_at:
            first = min(self.issue_at.values())
            last = max(self.done_at.values())
            span = max(1, last - first)
        else:
            first = last = 0
            span = 1
        fail_rate = fail / attempts if attempts else 0.0
        tenants = {t for t in ("solo", "A", "B") if self.stats["complete", t] or self.stats["attempts", t]}
        t_comp = {t: int(self.stats["complete", t]) for t in tenants}
        t_ms: dict[str, int] = {}
        t_p: dict[str, float] = {}
        for t in tenants:
            fi = int(self.stats["first_issue_saved", t])
            la = int(self.stats["last_complete", t])
            t_ms[t] = max(0, la - fi) if la else 0
            st = int(self.stats["steal", t])
            rw = int(self.stats["raw_inject", t])
            fa = int(self.stats["fail", t])
            att = st + rw + fa
            t_p[t] = (st + rw) / att if att else 0.0
        fsm_counts = {s: int(self.stats["fsm", s]) for s in STATES}
        return CycleResult(
            cycles=self.cycle,
            completed=completed,
            issued=issued,
            warmup_cycles=self.warmup,
            makespan=span,
            first_issue=first,
            last_complete=last,
            steal=steal,
            raw_inject=raw,
            fail=fail,
            emit=int(self.stats["emit"]),
            age_degrade=int(self.stats["age_degrade"]),
            p_inj=p_inj,
            rho_payload=occ.rho_payload,
            rho_empty=occ.rho_empty,
            rho_raw=occ.rho_raw,
            rho_bubble=occ.rho_bubble,
            sum_ok=occ.sum_ok,
            delta_rho_empty=0.0,
            cluster_hist=occ.cluster_hist,
            mean_cluster=occ.mean_cluster,
            fsm_counts=fsm_counts,
            cal_lookups=self.cal_lookups,
            collapsed=fail_rate >= 0.50,
            goodput_b_per_cyc=(completed * BYTES_PER_TXN) / span,
            n_nodes=self.n,
            n_fsm=self.n_fsm(),
            software_epochs_seen=list(self.epochs_seen),
            oracle_used=self.oracle_used,
            tenant_completed=t_comp,
            tenant_makespan=t_ms,
            tenant_p_inj=t_p,
        )


def run_cycles(cfg: SimConfig, txns: list[Txn] | None = None) -> CycleResult:
    """Same SimPy clock + fabric for every arm. Workload list is an input."""
    if txns is None:
        txns = gen_txns(cfg.traffic_class, cfg.n_nodes + cfg.n_bottom, cfg.n_txn, cfg.seed)
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


def run_arm(arm: str, cls: str, seed: int, **kwargs) -> CycleResult:
    duty = duty_of_arm(arm)
    cfg = SimConfig(
        duty=duty,
        calendar_on=calendar_on_of_arm(arm),
        traffic_class=cls,
        seed=seed,
        **kwargs,
    )
    n = cfg.n_nodes + cfg.n_bottom
    txns = gen_txns(cls, n, cfg.n_txn, seed)
    return run_cycles(cfg, txns)


def run_dual(d_a: float, seed: int, **kwargs) -> tuple[CycleResult, CycleResult]:
    """Tenant A = gather (collective), B = uniform_read. Same driver/seed."""
    base = dict(kwargs)
    n_nodes = base.get("n_nodes", 12)
    n_bottom = base.get("n_bottom", 0)
    n = n_nodes + n_bottom
    n_txn = base.get("n_txn", 96)
    n_b = base.get("tenant_b_n_txn", n_txn)
    a = gen_txns("gather", n, n_txn, seed, tenant="A")
    b = gen_txns("uniform_read", n, n_b, seed + 1, tenant="B")
    # shift B tids so they don't collide
    off = 10_000
    b = [Txn(t.tid + off, t.src, t.dst, t.chi, t.cls, t.kind, t.tenant, t.phase, t.nbytes) for t in b]
    cfg_dual = SimConfig(duty=d_a, calendar_on=True, traffic_class="gather", seed=seed, **base)
    dual = run_cycles(cfg_dual, a + b)
    cfg_solo = SimConfig(duty=0.0, calendar_on=False, traffic_class="uniform_read", seed=seed + 1, **base)
    solo = run_cycles(cfg_solo, gen_txns("uniform_read", n, n_b, seed + 1, tenant="B"))
    return dual, solo


def occupancy_delta(on: CycleResult, off: CycleResult) -> float:
    return on.rho_empty - off.rho_empty


def compare_to_t2(cls: str, arm: str, t3: CycleResult, t3_off: CycleResult | None = None) -> dict:
    """Like-to-like vs signed T2. Does not substitute T2 into T3 columns."""
    d = duty_of_arm(arm)
    t2_ratio = t2_h_inj_dom_ratio(d) if cls in INJ_DOM and d > 0 else float("nan")
    if t3_off is not None and t3_off.p_inj > 0 and t3.p_inj > 0 and cls in INJ_DOM:
        t3_ratio = t3_off.p_inj / t3.p_inj
    else:
        t3_ratio = float("nan")
    raw_t2, bub_t2 = t2_partition(t3.rho_empty, d)
    err_ratio = rel_err(t3_ratio, t2_ratio) if t3_ratio == t3_ratio and t2_ratio == t2_ratio else 0.0
    err_bub = rel_err(t3.rho_bubble, bub_t2) if t3.rho_empty > 0 else 0.0
    flag = False
    if t3_ratio == t3_ratio and t2_ratio == t2_ratio:
        flag = flag or err_ratio > 0.30
    if t3.rho_empty > 1e-12 and d > 0:
        flag = flag or err_bub > 0.30
    return {
        "class": cls,
        "arm": arm,
        "d": d,
        "t3_p_inj": t3.p_inj,
        "t3_T_hat_over_T_off": t3_ratio,
        "t2_T_hat_over_T_off": t2_ratio,
        "rel_err_ratio": err_ratio,
        "t3_rho_empty": t3.rho_empty,
        "t3_rho_raw": t3.rho_raw,
        "t3_rho_bubble": t3.rho_bubble,
        "t2_rho_bubble": bub_t2,
        "t2_rho_raw": raw_t2,
        "rel_err_rho_bubble": err_bub,
        "t3_sum_ok": t3.sum_ok,
        "t2_sum_ok": True,
        "flag_gt_30pct": flag,
        "card_claim": CARD_CLAIM_COLL if cls in INJ_DOM else "n/a",
        "card_claim_is_measured": False,
        "t3_makespan": t3.makespan,
        "t3_steal": t3.steal,
        "t3_raw_inject": t3.raw_inject,
        "t3_fail": t3.fail,
    }


def signed_t2_rows() -> list[dict]:
    """Director/audit pins as their own rows (T2 column only)."""
    return [
        {
            "metric": "sum_ok",
            "arm": "all-d",
            "t3": "",
            "t2": True,
            "rel_err": 0.0,
            "flag_gt_30pct": False,
            "note": "conservation exact in T2 by construction",
        },
        {
            "metric": "H-INJ-DOM T_hat/T_off",
            "arm": "d=1/4",
            "t3": "",
            "t2": T2_SIGNED["h_inj_dom_d25"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed audit; cycle row filled by sweep",
        },
        {
            "metric": "H-INJ-DOM T_hat/T_off",
            "arm": "d=1/2",
            "t3": "",
            "t2": T2_SIGNED["h_inj_dom_d50"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed audit; cycle row filled by sweep",
        },
        {
            "metric": "HARD-1 T_off vs T_cbc (ns, H-INJ-DOM)",
            "arm": "gather",
            "t3": "",
            "t2": f"{T2_SIGNED['hard1_t_off']}>{T2_SIGNED['hard1_t_cbc']}",
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "T2 ns; T3 compares cycle makespan inequality, not ns",
        },
        {
            "metric": "dual-tenant T_B_dual/T_B_solo",
            "arm": "d_A=1/4",
            "t3": "",
            "t2": T2_SIGNED["dual_d25"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed fail_T",
        },
        {
            "metric": "dual-tenant T_B_dual/T_B_solo",
            "arm": "d_A=1/2",
            "t3": "",
            "t2": T2_SIGNED["dual_d50"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "signed fail_T",
        },
        {
            "metric": "card-claim",
            "arm": "collapsed-collectives",
            "t3": "NOT measured",
            "t2": CARD_CLAIM_COLL,
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "card-claim only; director did not sign",
        },
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CBC cycle sim (single run)")
    p.add_argument("--class", dest="cls", choices=CLASSES, default="gather")
    p.add_argument("--arm", choices=ARMS, default="CBC-coll-1/4")
    p.add_argument("--n-nodes", type=int, default=12)
    p.add_argument("--n-bottom", type=int, default=0)
    p.add_argument("--n-txn", type=int, default=96)
    p.add_argument("--outstanding", type=int, default=16)
    p.add_argument("--lookup-lat", type=int, default=1)
    p.add_argument("--warmup-laps", type=int, default=1)
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)
    r = run_arm(
        args.arm,
        args.cls,
        args.seed,
        n_nodes=args.n_nodes,
        n_bottom=args.n_bottom,
        n_txn=args.n_txn,
        outstanding=args.outstanding,
        lookup_lat=args.lookup_lat,
        warmup_laps=args.warmup_laps,
    )
    print(
        f"CBC T3 class={args.cls} arm={args.arm} n={args.n_nodes}+{args.n_bottom} "
        f"|I|={args.n_txn} seed={args.seed}"
    )
    print(
        f"fsm×{r.n_fsm} warmup={r.warmup_cycles} makespan={r.makespan} "
        f"completed={r.completed} collapsed={r.collapsed}"
    )
    print(
        f"arb steal={r.steal} raw-inject={r.raw_inject} fail={r.fail} "
        f"p_inj={r.p_inj:.4f} emit={r.emit} age_degrade={r.age_degrade}"
    )
    print(
        f"occ ρ_pay={r.rho_payload:.4f} ρ_empty={r.rho_empty:.4f} "
        f"ρ_raw={r.rho_raw:.4f} ρ_bub={r.rho_bubble:.4f} sum_ok={r.sum_ok} "
        f"mean_cluster={r.mean_cluster:.3f}"
    )
    print(
        f"calendar lookups={r.cal_lookups} epochs={r.software_epochs_seen} "
        f"oracle={r.oracle_used} goodput={r.goodput_b_per_cyc:.2f} B/cyc "
        f"(clock UNKNOWN; not TB/s)"
    )
    print(f"card-claim {CARD_CLAIM_COLL} is NOT measured")
    print("0.85 is a pass bar, not a measured mean; no team-384dmc")
    t2mod = try_load_t2_module()
    print("T2 model.py on this tree:" + (" yes" if t2mod else " no (PR #54 only; using signed constants)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
