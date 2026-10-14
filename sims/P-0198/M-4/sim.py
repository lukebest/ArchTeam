#!/usr/bin/env python3
"""P-0198/M-4 AODI — cycle-level bufferless-ring SimPy model.

Cycle-accurate (card + Dr.Sim must-verify; do NOT approximate with mean ρ):
  same-cycle 2×2 truth table × node × CHI four rings,
  inject-hole sampled with the busy mask on the same beat,
  hole buckets asymmetric vs dual-busy (dual-busy hole≡0 is a hard fail),
  per-packet φ (remaining preferred hops after rejoin arming) — not Σage,
  AGE_MAX gates further deflect; independent Rejoin (preferred-empty only),
  deflect-off ablation; opposite-ring util + completions,
  warmup ≥ one ring lap; no silent drop / third slot / flit queue.
Black box: hop latency, flit=txn, RBRG, HBM, coherence, D2D, clock.
T2 analytical model is NOT on main (PR #65). Compare uses signed audit
pins + spec §3 formulas; never treat card-claim bands as measured.

No CBC / CSR / CRRF math. Ablation is deflect-off on this card only.
"""

from __future__ import annotations

import argparse
import math
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
from _lib.t2load import load_aodi_t2  # noqa: E402
from _lib.workloads import SEED  # noqa: E402

CHI = ("Req", "Rsp", "Snp", "Dat")
DIRS = ("CW", "CCW")
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
DUAL_BUSY_CLASSES = {"alltoall"}
ASYM_CLASSES = {
    "uniform_read",
    "uniform_write",
    "broadcast",
    "gather",
    "reduce",
}
ARMS = ("deflect-off", "AODI-on", "rejoin-off")
BYTES_PER_TXN = 512
AGE_MAX_DEFAULT = 8
EPS = 1e-12

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

# Signed T2 pins (director / audit, PR #65). Cite; do not invent.
# card-claim bands are NOT signed — never treat as measured.
T2_SIGNED = {
    "hole_dual": 0,
    "phi_age_end": 1,
    "deflect_off_hard": True,
    "alltoall_t_mix": 1.0,
    "gather_t_mix": 0.8448,
    "reduce_t_mix": 0.8448,
    "uniform_read_t_mix": 0.8770,
}

# T2 default assumption set (PR #65 model.py). Analytical replay only.
T2_LAM_AGE = 0.90
T2_ETA_USE = 0.25
T2_KAPPA_MIG = 0.0
T2_H_HOP = 6.0
T2_CLASS_RHO = {
    "uniform_read": (0.72, 0.28, 0.00, "asymmetric"),
    "uniform_write": (0.68, 0.38, 0.10, "asymmetric"),
    "broadcast": (0.40, 0.18, 0.00, "asymmetric"),
    "gather": (0.78, 0.25, 0.00, "asymmetric"),
    "reduce": (0.78, 0.25, 0.00, "asymmetric"),
    "allgather": (0.82, 0.48, 0.20, "mixed"),
    "allreduce": (0.80, 0.52, 0.25, "mixed"),
    "alltoall": (0.93, 0.93, 1.00, "dual-busy-sat"),
}
CARD_CLAIM = {
    "uniform_read": "0.70-0.95x asym",
    "uniform_write": "0.70-0.95x asym",
    "broadcast": "0.70-0.95x asym",
    "gather": "0.70-0.95x asym",
    "reduce": "0.70-0.95x asym",
    "allgather": "0.70-0.95x asym",
    "allreduce": "0.70-0.95x asym",
    "alltoall": "0.95-1.05x (~0 gain)",
}

# ---- T2 analytical replay (spec §3 / PR #65). Not cycle-measured. ----


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def t2_frechet_joint(rho_pref: float, rho_opp: float, corr: float):
    if not (0.0 <= rho_pref <= 1.0 and 0.0 <= rho_opp <= 1.0):
        raise ValueError("occupancy out of [0,1]")
    corr = max(-1.0, min(1.0, corr))
    p_ind = rho_pref * rho_opp
    p_lo = max(0.0, rho_pref + rho_opp - 1.0)
    p_hi = min(rho_pref, rho_opp)
    if corr >= 0.0:
        p_dual = p_ind + corr * (p_hi - p_ind)
    else:
        p_dual = p_ind + corr * (p_ind - p_lo)
    p_dual = max(p_lo, min(p_hi, p_dual))
    return rho_pref - p_dual, rho_opp - p_dual, p_dual, 1.0 - rho_pref - rho_opp + p_dual


def t2_occupancy_rates(rho_pref: float, rho_opp: float, corr: float,
                       lam_age: float, eta_use: float, deflect_on: bool):
    p_pref_only, p_opp_only, p_dual, p_empty = t2_frechet_joint(rho_pref, rho_opp, corr)
    en = 1.0 if deflect_on else 0.0
    p_hole_asym = clip01(eta_use) * p_pref_only * clip01(lam_age) * en
    p_hole_dual = 0.0  # HARD CONTRACT
    p_inj_off = 1.0 - rho_pref
    return {
        "p_pref_only": p_pref_only,
        "p_opp_only": p_opp_only,
        "p_dual": p_dual,
        "p_empty": p_empty,
        "p_hole_asym": p_hole_asym,
        "p_hole_dual": p_hole_dual,
        "p_inj_off": p_inj_off,
        "p_inj_on": p_inj_off + p_hole_asym,
    }


def t2_wait_rejoin(rho_pref: float) -> float:
    gap = 1.0 - rho_pref
    if gap <= EPS:
        return float("inf")
    return 1.0 / gap


def t2_makespan_ratios(p_inj_off: float, p_inj_on: float, p_hole_asym: float,
                       rho_pref: float, h_hop: float):
    if p_inj_off <= 0 and p_inj_on <= 0:
        t_inj = 1.0
    elif p_inj_on <= 0:
        t_inj = float("inf")
    else:
        t_inj = p_inj_off / p_inj_on
    w = t2_wait_rejoin(rho_pref)
    extra = float("inf") if math.isinf(w) else (1.0 + w)
    f_vic = min(1.0, p_hole_asym / max(rho_pref, EPS))
    if math.isinf(extra):
        t_vic = float("inf")
        t_mix = float("inf") if f_vic > 0 else t_inj
    else:
        t_vic = 1.0 + extra / max(h_hop, EPS)
        t_mix = (1.0 - f_vic) * t_inj + f_vic * t_vic
    return t_inj, t_mix, f_vic, extra


def t2_class_row(cls: str, deflect_on: bool = True,
                 lam_age: float = T2_LAM_AGE, eta_use: float = T2_ETA_USE,
                 h_hop: float = T2_H_HOP):
    rho_pref, rho_opp, corr, regime = T2_CLASS_RHO[cls]
    occ = t2_occupancy_rates(rho_pref, rho_opp, corr, lam_age, eta_use, deflect_on)
    if occ["p_hole_dual"] != 0.0:
        raise AssertionError("MECHANISM FAIL: T2 dual-busy hole>0")
    t_inj, t_mix, f_vic, extra = t2_makespan_ratios(
        occ["p_inj_off"], occ["p_inj_on"], occ["p_hole_asym"], rho_pref, h_hop
    )
    return {
        "cls": cls,
        "regime": regime,
        "occ": occ,
        "t_inj": t_inj,
        "t_mix": t_mix,
        "t_off": T_OFF[cls],
        "t_hat": T_OFF[cls] * t_mix if not math.isinf(t_mix) else float("inf"),
        "f_vic": f_vic,
        "extra": extra,
        "rho_pref": rho_pref,
        "rho_opp": rho_opp,
    }


def t2_phi_walk(h_init: int, n_deflect: int, age_max: int, rejoin_fires: bool):
    """Per-packet φ, not Σage. Signed probe: φ→0 and age_end=1."""
    phi = float(h_init)
    age = 0
    trace = [("start-pref", phi, age)]
    freeze = False
    for _ in range(n_deflect):
        if age >= age_max:
            trace.append(("deflect-blocked-AGE_MAX", phi, age))
            break
        age += 1
        trace.append(("deflect-unarmed", phi, age))
    if n_deflect > 0:
        if not rejoin_fires:
            freeze = True
            trace.append(("phi-freeze-pref-full", phi, age))
            return trace, age, freeze, age <= age_max
        phi = 1.0 + float(h_init)
        trace.append(("rejoin-armed", phi, age))
        phi -= 1.0
        trace.append(("rejoin-done", phi, age))
    while phi > 0:
        prev = phi
        phi -= 1.0
        if phi >= prev:
            return trace, age, freeze, False
        trace.append(("pref-hop", phi, age))
    return trace, age, freeze, True


def try_load_t2_module():
    try:
        return load_aodi_t2()
    except FileNotFoundError:
        return None


# ---- Geometry / 2×2 silicon contract ----


def hops_cw(src: int, dst: int, n: int) -> int:
    return (dst - src) % n


def hops_ccw(src: int, dst: int, n: int) -> int:
    return (src - dst) % n


def dir_of(src: int, dst: int, n: int) -> str:
    cw = hops_cw(src, dst, n)
    ccw = hops_ccw(src, dst, n)
    return "CW" if cw <= ccw else "CCW"


def hops_along(src: int, dst: int, direction: str, n: int) -> int:
    return hops_cw(src, dst, n) if direction == "CW" else hops_ccw(src, dst, n)


def next_node(node: int, direction: str, n: int) -> int:
    return (node + 1) % n if direction == "CW" else (node - 1) % n


def opp_dir(direction: str) -> str:
    return "CCW" if direction == "CW" else "CW"


def slots_after(cw_busy: bool, ccw_busy: bool, inject_ok: bool) -> int:
    """Physical highway slots occupied after the action (max legal = 2)."""
    n = int(cw_busy) + int(ccw_busy)
    if inject_ok:
        if cw_busy and ccw_busy:
            return n + 1  # illegal third occupant
        return 2 if (cw_busy or ccw_busy) else 1
    return n


def truth_row(cw_busy: bool, ccw_busy: bool, inject_pending: bool,
              preferred: str, deflect_on: bool, age_ok: bool):
    """Same-cycle 2×2 atom. preferred in {'CW','CCW'}. T2 / card silicon contract."""
    pref_busy = cw_busy if preferred == "CW" else ccw_busy
    opp_busy = ccw_busy if preferred == "CW" else cw_busy
    dual = cw_busy and ccw_busy
    illegal = False
    hole = 0
    inject_ok = False
    action = "idle"
    if not inject_pending:
        action = "thru" if (cw_busy or ccw_busy) else "idle"
    elif dual:
        action = "thru-or-gated-swap"
        inject_ok = False
        hole = 0
    elif pref_busy and (not opp_busy):
        if deflect_on and age_ok:
            action = "deflect-opp+inject-pref"
            inject_ok = True
            hole = 1
        else:
            action = "fail-wait"
            inject_ok = False
            hole = 0
    else:
        action = "inject-pref"
        inject_ok = True
        hole = 0
    occ = slots_after(cw_busy, ccw_busy, inject_ok)
    if occ > 2:
        illegal = True
        action = "ILLEGAL-third-slot"
    return {
        "action": action,
        "hole": hole,
        "inject_ok": inject_ok,
        "slots": occ,
        "illegal": illegal,
        "dual": dual,
        "pref_busy": pref_busy,
        "opp_busy": opp_busy,
    }


# ---- Traffic / flits ----


@dataclass
class Txn:
    tid: int
    src: int
    dst: int
    chi: str
    cls: str
    nbytes: int = BYTES_PER_TXN


@dataclass
class Flit:
    tid: int
    src: int
    dst: int
    chi: str
    cls: str
    pref_dir: str
    cur_dir: str
    age: int = 0
    armed: bool = True
    phi: float = 0.0
    sticky: bool = False
    just_injected: bool = False

    def clone_progress(self) -> "Flit":
        return Flit(
            tid=self.tid, src=self.src, dst=self.dst, chi=self.chi, cls=self.cls,
            pref_dir=self.pref_dir, cur_dir=self.cur_dir, age=self.age,
            armed=self.armed, phi=self.phi, sticky=self.sticky,
        )


def gen_txns(cls: str, n_nodes: int, n_txn: int, seed: int, chi: str = "Dat") -> list[Txn]:
    """Synthetic DV200-class traffic. Same seed → same list (fair compare)."""
    if cls not in CLASSES:
        raise ValueError(f"unknown class {cls}")
    rng = random.Random(seed)
    txns: list[Txn] = []

    def add(src: int, dst: int) -> None:
        if src == dst:
            raise ValueError("self-dest")
        txns.append(Txn(len(txns), src, dst, chi, cls))

    if cls in ("uniform_read", "uniform_write"):
        for _ in range(n_txn):
            src = rng.randrange(n_nodes)
            dst = rng.randrange(n_nodes - 1)
            if dst >= src:
                dst += 1
            add(src, dst)
    elif cls in ("gather", "reduce"):
        sink = 0
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
        half = max(1, n_txn // 2)
        sink = 0
        for i in range(half):
            add(1 + (i % (n_nodes - 1)), sink)
        i = 0
        while len(txns) < n_txn:
            add(sink, 1 + (i % (n_nodes - 1)))
            i += 1
    else:  # alltoall — both directions, dual-busy-sat separate from asym fold
        for i in range(n_txn):
            src = i % n_nodes
            half = max(1, n_nodes // 2)
            if i % 2 == 0:
                dst = (src + 1 + rng.randrange(half)) % n_nodes
            else:
                dst = (src - 1 - rng.randrange(half)) % n_nodes
            if dst == src:
                dst = (src + 1) % n_nodes
            add(src, dst)
    return txns[:n_txn]


@dataclass
class SimConfig:
    n_nodes: int = 12
    n_bottom: int = 0  # bbox: extra nodes on the same ring (12+2 → 14)
    chi: tuple[str, ...] = CHI
    dirs: tuple[str, ...] = DIRS
    deflect_on: bool = True
    rejoin_on: bool = True
    age_max: int = AGE_MAX_DEFAULT
    warmup_laps: int = 1
    outstanding: int = 16
    hop_lat: int = 1
    n_txn: int = 64
    traffic_class: str = "gather"
    seed: int = SEED
    max_cycles: int | None = None
    force_dual_busy: bool = False
    force_dual_busy_chi: str = "Dat"


@dataclass
class CycleResult:
    cycles: int
    completed: int
    issued: int
    warmup_cycles: int
    makespan: int
    first_issue: int
    last_complete: int
    inject_ok: int
    inject_fail: int
    deflect: int
    rejoin: int
    hole_asym: int
    hole_dual: int
    dual_busy_cycles: int
    p_inj: float
    rho_pref: float
    rho_opp: float
    rho_cw: float
    rho_ccw: float
    completions_cw: int
    completions_ccw: int
    age_hist: dict[int, int]
    age_at_complete_sum: int
    phi_at_complete_sum: float
    phi_freeze_events: int
    phi_nonincrease_violations: int
    cross_chi: int
    illegal_third: int
    dropped: int
    collapsed: bool
    goodput_b_per_cyc: float
    n_nodes: int
    n_xbar: int
    hole_dual_fail: bool
    hypothesis: str = "H-RING-BB"


def _new_flit(txn: Txn, n: int) -> Flit:
    pref = dir_of(txn.src, txn.dst, n)
    hops = hops_along(txn.src, txn.dst, pref, n)
    return Flit(
        tid=txn.tid, src=txn.src, dst=txn.dst, chi=txn.chi, cls=txn.cls,
        pref_dir=pref, cur_dir=pref, age=0, armed=True, phi=float(hops),
    )


def _deflect_flit(flit: Flit) -> Flit:
    flit.age += 1
    flit.cur_dir = opp_dir(flit.cur_dir)
    flit.armed = False
    # φ is not progress while unarmed on the wrong ring
    return flit


def _rejoin_flit(flit: Flit, node: int, n: int) -> Flit:
    flit.cur_dir = flit.pref_dir
    flit.armed = True
    remain = hops_along(node, flit.dst, flit.pref_dir, n)
    flit.phi = 1.0 + float(remain)  # armed
    flit.phi = float(remain)        # rejoin hop is the U-turn at this node
    return flit


def _recompute_phi_on_pref(flit: Flit, node: int, n: int) -> None:
    if flit.sticky:
        return
    if flit.dst == node:
        flit.phi = 0.0
        return
    if flit.cur_dir == flit.pref_dir and flit.armed:
        nxt = hops_along(node, flit.dst, flit.pref_dir, n)
        # remaining hops from this node (about to leave)
        flit.phi = float(nxt)


@dataclass
class XbarPlan:
    cw_out: Flit | None
    ccw_out: Flit | None
    hole_asym: int = 0
    hole_dual: int = 0
    inject_cw: bool = False
    inject_ccw: bool = False
    inject_fail: int = 0
    deflect: int = 0
    rejoin: int = 0
    illegal: bool = False
    action: str = ""
    dual: bool = False


def plan_xbar(
    cw_in: Flit | None,
    ccw_in: Flit | None,
    want_cw: bool,
    want_ccw: bool,
    deflect_on: bool,
    rejoin_on: bool,
    age_max: int,
    node: int,
    n: int,
) -> XbarPlan:
    """Same-cycle 2×2 + independent Rejoin. Never drops a transit flit."""
    cw = cw_in
    ccw = ccw_in
    cw_out: Flit | None = None
    ccw_out: Flit | None = None
    rejoin = 0

    # Rejoin is decoupled from deflect: wrong-ring flit, preferred outlet empty.
    if rejoin_on and cw is not None and (not cw.sticky) and cw.cur_dir != cw.pref_dir:
        if cw.pref_dir == "CCW" and ccw is None:
            ccw_out = _rejoin_flit(cw, node, n)
            cw = None
            rejoin += 1
    if rejoin_on and ccw is not None and (not ccw.sticky) and ccw.cur_dir != ccw.pref_dir:
        if ccw.pref_dir == "CW" and cw is None and cw_out is None:
            cw_out = _rejoin_flit(ccw, node, n)
            ccw = None
            rejoin += 1

    cw_busy = cw is not None
    ccw_busy = ccw is not None
    dual = cw_busy and ccw_busy
    age_ok_cw = cw is not None and cw.age < age_max and (not cw.sticky)
    age_ok_ccw = ccw is not None and ccw.age < age_max and (not ccw.sticky)

    hole_asym = 0
    hole_dual = 0
    inject_cw = False
    inject_ccw = False
    inject_fail = 0
    deflect = 0
    action = "idle"

    if dual:
        # HARD: thru-only. inject-hole ≡ 0. H-SWAP: no swap (would need age++).
        cw_out = cw
        ccw_out = ccw
        hole_dual = 0
        if want_cw:
            inject_fail += 1
        if want_ccw:
            inject_fail += 1
        action = "thru-or-gated-swap"
        # Pending + dual-busy must not produce a hole. Asserted by caller.
    else:
        # Prefer AODI when the pending's preferred side is the busy one.
        did_aodi = False
        if cw_busy and (not ccw_busy) and ccw_out is None:
            row = truth_row(True, False, want_cw, "CW", deflect_on, age_ok_cw)
            if row["action"] == "deflect-opp+inject-pref" and cw is not None and cw.cur_dir == cw.pref_dir:
                ccw_out = _deflect_flit(cw)
                cw = None
                inject_cw = True
                hole_asym = 1
                deflect += 1
                did_aodi = True
                action = "deflect-opp+inject-pref"
            else:
                cw_out = cw
                if want_cw:
                    inject_fail += 1
                    action = "fail-wait"
                if want_ccw and ccw_out is None:
                    inject_ccw = True
                    action = "inject-pref"
        elif ccw_busy and (not cw_busy) and cw_out is None:
            row = truth_row(False, True, want_ccw, "CCW", deflect_on, age_ok_ccw)
            if row["action"] == "deflect-opp+inject-pref" and ccw is not None and ccw.cur_dir == ccw.pref_dir:
                cw_out = _deflect_flit(ccw)
                ccw = None
                inject_ccw = True
                hole_asym = 1
                deflect += 1
                did_aodi = True
                action = "deflect-opp+inject-pref"
            else:
                ccw_out = ccw
                if want_ccw:
                    inject_fail += 1
                    action = "fail-wait"
                if want_cw and cw_out is None:
                    inject_cw = True
                    action = "inject-pref"
        else:
            # both remaining ins empty (rejoin may have filled one out)
            if want_cw and cw_out is None:
                inject_cw = True
                action = "inject-pref"
            elif want_cw:
                inject_fail += 1
            if want_ccw and ccw_out is None:
                inject_ccw = True
                if action == "idle":
                    action = "inject-pref"
            elif want_ccw:
                inject_fail += 1
        _ = did_aodi

    # Place leftover transit that was not moved
    if cw is not None and cw_out is None and not inject_cw:
        cw_out = cw
    if ccw is not None and ccw_out is None and not inject_ccw:
        ccw_out = ccw

    if inject_cw and cw_out is not None:
        # cannot mint a third slot — cancel inject
        inject_cw = False
        inject_fail += 1
        hole_asym = 0
    if inject_ccw and ccw_out is not None:
        inject_ccw = False
        inject_fail += 1
        hole_asym = 0

    occ = int(cw_out is not None) + int(ccw_out is not None) + int(inject_cw) + int(inject_ccw)
    illegal = occ > 2
    if dual and hole_dual != 0:
        illegal = True

    return XbarPlan(
        cw_out=cw_out, ccw_out=ccw_out, hole_asym=hole_asym, hole_dual=hole_dual,
        inject_cw=inject_cw, inject_ccw=inject_ccw, inject_fail=inject_fail,
        deflect=deflect, rejoin=rejoin, illegal=illegal, action=action, dual=dual,
    )


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
        self.slots: dict[str, dict[str, list[Flit | None]]] = {
            c: {d: [None for _ in range(self.n)] for d in self.dirs} for c in self.chis
        }
        self.queues: list[deque[Txn]] = [deque() for _ in range(self.n)]
        self.inflight = [0] * self.n
        self.done_at: dict[int, int] = {}
        self.issue_at: dict[int, int] = {}
        self.phi_at_done: dict[int, float] = {}
        self.age_at_done: dict[int, int] = {}
        self.phi_last: dict[int, float] = {}
        self.stats = Counter()
        self.occ = Counter()
        self.age_hist: dict[int, int] = defaultdict(int)
        self.cycle = 0
        self.hole_dual_fail = False
        self.active_chi = {t.chi for t in txns} or {"Dat"}
        for t in txns:
            self.queues[t.src].append(t)
        extra = 16 * max(1, len(txns) + self.n) * self.n
        self.limit = cfg.max_cycles if cfg.max_cycles is not None else self.warmup + extra + 512
        if cfg.force_dual_busy:
            self._seed_sticky()

    def n_xbar(self) -> int:
        return len(self.chis) * self.n

    def _seed_sticky(self) -> None:
        chi = self.cfg.force_dual_busy_chi
        tid = -1
        for d in self.dirs:
            for node in range(self.n):
                self.slots[chi][d][node] = Flit(
                    tid=tid, src=node, dst=-1, chi=chi, cls="dual-busy-sat",
                    pref_dir=d, cur_dir=d, sticky=True, armed=True, phi=0.0,
                )
                tid -= 1

    def _ready_idx(self, node: int, chi: str, direction: str) -> int | None:
        if self.cycle < self.warmup and not self.cfg.force_dual_busy:
            return None
        if self.cfg.force_dual_busy and self.cycle < self.warmup:
            return None
        if self.inflight[node] >= self.cfg.outstanding:
            return None
        q = self.queues[node]
        for i, t in enumerate(q):
            if t.chi == chi and dir_of(t.src, t.dst, self.n) == direction:
                return i
        return None

    def _pop_ready(self, node: int, chi: str, direction: str) -> Txn | None:
        i = self._ready_idx(node, chi, direction)
        if i is None:
            return None
        q = self.queues[node]
        txn = q[i]
        del q[i]
        return txn

    def _eject(self, flit: Flit | None, node: int) -> Flit | None:
        if flit is None or flit.sticky:
            return flit
        if flit.dst != node:
            return flit
        if flit.chi not in self.active_chi and flit.cls != "dual-busy-sat":
            pass
        self.done_at[flit.tid] = self.cycle
        self.phi_at_done[flit.tid] = 0.0
        self.age_at_done[flit.tid] = flit.age
        if 0 <= flit.src < self.n:
            self.inflight[flit.src] = max(0, self.inflight[flit.src] - 1)
        self.stats["complete"] += 1
        self.stats["complete", flit.cur_dir] += 1
        return None

    def _record_occ(self, chi: str, sampling: bool) -> None:
        if not sampling or chi not in self.active_chi:
            return
        for d in self.dirs:
            for flit in self.slots[chi][d]:
                self.occ["slots"] += 1
                if flit is not None:
                    self.occ[d] += 1
                    if flit.cur_dir == flit.pref_dir:
                        self.occ["pref"] += 1
                    else:
                        self.occ["opp"] += 1
                    self.age_hist[flit.age] += 1
                else:
                    self.occ["empty"] += 1

    def _track_phi(self, flit: Flit, node: int) -> None:
        if flit.sticky:
            return
        prev = self.phi_last.get(flit.tid)
        if flit.cur_dir == flit.pref_dir and flit.armed:
            _recompute_phi_on_pref(flit, node, self.n)
        if prev is not None and flit.armed and flit.phi > prev + 1e-9:
            # rejoin-arm may legally raise φ by +1 then drop; allow a one-shot rise
            if flit.phi > prev + 1.0 + 1e-9:
                self.stats["phi_nonincrease"] += 1
        if (not flit.armed) and flit.cur_dir != flit.pref_dir:
            self.stats["wrong_wait"] += 1
            if prev is not None and abs(flit.phi - prev) < 1e-12:
                self.stats["phi_freeze"] += 1
        self.phi_last[flit.tid] = flit.phi

    def pending(self) -> int:
        return sum(len(q) for q in self.queues)

    def step(self, cycle: int) -> None:
        self.cycle = cycle
        sampling = cycle >= self.warmup
        new: dict[str, dict[str, list[Flit | None]]] = {
            c: {d: [None for _ in range(self.n)] for d in self.dirs} for c in self.chis
        }
        for chi in self.chis:
            if sampling:
                self._record_occ(chi, True)
            for node in range(self.n):
                cw_in = self._eject(self.slots[chi]["CW"][node], node)
                ccw_in = self._eject(self.slots[chi]["CCW"][node], node)
                if cw_in is not None:
                    self._track_phi(cw_in, node)
                if ccw_in is not None:
                    self._track_phi(ccw_in, node)

                want_cw = self._ready_idx(node, chi, "CW") is not None
                want_ccw = self._ready_idx(node, chi, "CCW") is not None
                plan = plan_xbar(
                    cw_in, ccw_in, want_cw, want_ccw,
                    self.cfg.deflect_on, self.cfg.rejoin_on, self.cfg.age_max,
                    node, self.n,
                )
                if plan.illegal:
                    self.stats["illegal_third"] += 1
                if plan.dual:
                    self.stats["dual_busy"] += 1
                    if plan.hole_dual != 0:
                        self.hole_dual_fail = True
                        raise AssertionError(
                            "MECHANISM FAIL: dual-busy inject-hole>0 "
                            "(third slot or silent drop/buffer)"
                        )
                    if sampling:
                        self.stats["hole_dual"] += plan.hole_dual
                if sampling:
                    self.stats["hole_asym"] += plan.hole_asym
                    self.stats["deflect"] += plan.deflect
                    self.stats["rejoin"] += plan.rejoin
                    self.stats["inject_fail"] += plan.inject_fail

                cw_out, ccw_out = plan.cw_out, plan.ccw_out
                if plan.inject_cw:
                    txn = self._pop_ready(node, chi, "CW")
                    if txn is None:
                        raise AssertionError("inject-cw planned but no txn")
                    if txn.chi != chi:
                        self.stats["cross_chi"] += 1
                        raise AssertionError("cross-CHI inject")
                    flit = _new_flit(txn, self.n)
                    flit.just_injected = True
                    cw_out = flit
                    self.inflight[node] += 1
                    self.issue_at[txn.tid] = self.cycle
                    self.phi_last[txn.tid] = flit.phi
                    if sampling:
                        self.stats["inject_ok"] += 1
                if plan.inject_ccw:
                    txn = self._pop_ready(node, chi, "CCW")
                    if txn is None:
                        raise AssertionError("inject-ccw planned but no txn")
                    if txn.chi != chi:
                        self.stats["cross_chi"] += 1
                        raise AssertionError("cross-CHI inject")
                    flit = _new_flit(txn, self.n)
                    flit.just_injected = True
                    ccw_out = flit
                    self.inflight[node] += 1
                    self.issue_at[txn.tid] = self.cycle
                    self.phi_last[txn.tid] = flit.phi
                    if sampling:
                        self.stats["inject_ok"] += 1

                # Slot conservation: leftover transit must not vanish.
                placed = {id(x) for x in (cw_out, ccw_out) if x is not None}
                for incoming in (cw_in, ccw_in):
                    if incoming is not None and id(incoming) not in placed:
                        self.stats["dropped"] += 1
                        raise AssertionError("silent drop of transit flit")

                occ = int(cw_out is not None) + int(ccw_out is not None)
                if occ > 2:
                    self.stats["illegal_third"] += 1
                    raise AssertionError("third highway slot")

                if cw_out is not None:
                    if cw_out.chi != chi:
                        self.stats["cross_chi"] += 1
                        raise AssertionError("cross-CHI deflect")
                    cw_out.just_injected = False
                    new[chi]["CW"][next_node(node, "CW", self.n)] = cw_out
                if ccw_out is not None:
                    if ccw_out.chi != chi:
                        self.stats["cross_chi"] += 1
                        raise AssertionError("cross-CHI deflect")
                    ccw_out.just_injected = False
                    new[chi]["CCW"][next_node(node, "CCW", self.n)] = ccw_out
        self.slots = new

    def done(self) -> bool:
        if self.cfg.force_dual_busy:
            return self.cycle + 1 >= (self.warmup + max(8, self.n))
        if self.cycle < self.warmup:
            return False
        if self.pending() == 0 and sum(self.inflight) == 0:
            if not self.issue_at:
                return self.cycle + 1 >= self.limit
            return True
        return False

    def result(self) -> CycleResult:
        tot = self.occ["slots"]
        if tot <= 0:
            rho_cw = rho_ccw = rho_pref = rho_opp = 0.0
        else:
            rho_cw = self.occ["CW"] / tot
            rho_ccw = self.occ["CCW"] / tot
            # pref/opp are counted per occupied slot; normalize by slot-samples
            rho_pref = self.occ["pref"] / tot
            rho_opp = self.occ["opp"] / tot
        inj_ok = int(self.stats["inject_ok"])
        inj_fail = int(self.stats["inject_fail"])
        attempts = inj_ok + inj_fail
        p_inj = inj_ok / attempts if attempts else 0.0
        issued = len(self.issue_at)
        completed = len(self.done_at)
        if self.issue_at and self.done_at:
            first = min(self.issue_at.values())
            last = max(self.done_at.values())
            span = max(1, last - first)
        else:
            first = last = 0
            span = 1
        fail_rate = inj_fail / attempts if attempts else 0.0
        return CycleResult(
            cycles=self.cycle,
            completed=completed,
            issued=issued,
            warmup_cycles=self.warmup,
            makespan=span,
            first_issue=first,
            last_complete=last,
            inject_ok=inj_ok,
            inject_fail=inj_fail,
            deflect=int(self.stats["deflect"]),
            rejoin=int(self.stats["rejoin"]),
            hole_asym=int(self.stats["hole_asym"]),
            hole_dual=int(self.stats["hole_dual"]),
            dual_busy_cycles=int(self.stats["dual_busy"]),
            p_inj=p_inj,
            rho_pref=rho_pref,
            rho_opp=rho_opp,
            rho_cw=rho_cw,
            rho_ccw=rho_ccw,
            completions_cw=int(self.stats["complete", "CW"]),
            completions_ccw=int(self.stats["complete", "CCW"]),
            age_hist=dict(self.age_hist),
            age_at_complete_sum=sum(self.age_at_done.values()),
            phi_at_complete_sum=sum(self.phi_at_done.values()),
            phi_freeze_events=int(self.stats["phi_freeze"]),
            phi_nonincrease_violations=int(self.stats["phi_nonincrease"]),
            cross_chi=int(self.stats["cross_chi"]),
            illegal_third=int(self.stats["illegal_third"]),
            dropped=int(self.stats["dropped"]),
            collapsed=fail_rate >= 0.50,
            goodput_b_per_cyc=(completed * BYTES_PER_TXN) / span,
            n_nodes=self.n,
            n_xbar=self.n_xbar(),
            hole_dual_fail=self.hole_dual_fail,
        )


def run_cycles(cfg: SimConfig, txns: list[Txn] | None = None) -> CycleResult:
    """Same SimPy clock + fabric for every arm. Workload list is an input."""
    if txns is None:
        if cfg.force_dual_busy:
            # Pending injects that must fail under dual-busy occupancy.
            txns = gen_txns("alltoall", cfg.n_nodes + cfg.n_bottom, cfg.n_txn, cfg.seed)
        else:
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


def arm_flags(arm: str) -> tuple[bool, bool]:
    if arm == "deflect-off":
        return False, True
    if arm == "AODI-on":
        return True, True
    if arm == "rejoin-off":
        return True, False
    raise ValueError(arm)


def run_arm(arm: str, cls: str, seed: int, **kwargs) -> CycleResult:
    deflect_on, rejoin_on = arm_flags(arm)
    extra = dict(kwargs)
    extra.pop("deflect_on", None)
    extra.pop("rejoin_on", None)
    cfg = SimConfig(
        deflect_on=deflect_on,
        rejoin_on=rejoin_on,
        traffic_class=cls,
        seed=seed,
        **extra,
    )
    n = cfg.n_nodes + cfg.n_bottom
    if cfg.force_dual_busy:
        txns = gen_txns("alltoall", n, cfg.n_txn, seed)
    else:
        txns = gen_txns(cls, n, cfg.n_txn, seed)
    return run_cycles(cfg, txns)


def compare_to_t2(cls: str, t3_on: CycleResult, t3_off: CycleResult) -> dict:
    """Like-to-like vs signed T2. Does not substitute T2 into T3 columns."""
    t2 = t2_class_row(cls, deflect_on=True)
    t2_off = t2_class_row(cls, deflect_on=False)
    if t3_off.makespan > 0:
        t3_mix = t3_on.makespan / t3_off.makespan
    else:
        t3_mix = float("nan")
    t2_mix = t2["t_mix"]
    err = rel_err(t3_mix, t2_mix) if t3_mix == t3_mix and t2_mix == t2_mix else 0.0
    flag = bool(t3_mix == t3_mix and t2_mix == t2_mix and err > 0.30)
    hole_err = rel_err(float(t3_on.hole_dual), float(T2_SIGNED["hole_dual"]))
    if t3_on.hole_dual != T2_SIGNED["hole_dual"]:
        flag = True
    hard = t3_off.makespan + 1e-9 >= t3_on.makespan
    return {
        "class": cls,
        "regime": t2["regime"],
        "t3_T_mix": t3_mix,
        "t2_T_mix": t2_mix,
        "rel_err_T_mix": err,
        "t3_T_hat_off": t3_off.makespan,
        "t3_T_hat_on": t3_on.makespan,
        "t2_T_mix_off": t2_off["t_mix"],
        "t3_hole_asym": t3_on.hole_asym,
        "t3_hole_dual": t3_on.hole_dual,
        "t2_hole_dual": T2_SIGNED["hole_dual"],
        "rel_err_hole_dual": hole_err,
        "t3_rho_opp": t3_on.rho_opp,
        "t3_rho_opp_off": t3_off.rho_opp,
        "t3_completed_on": t3_on.completed,
        "t3_completed_off": t3_off.completed,
        "t3_completions_cw": t3_on.completions_cw,
        "t3_completions_ccw": t3_on.completions_ccw,
        "t3_deflect": t3_on.deflect,
        "t3_rejoin": t3_on.rejoin,
        "t3_inject_ok": t3_on.inject_ok,
        "t3_inject_fail": t3_on.inject_fail,
        "t3_p_inj": t3_on.p_inj,
        "deflect_off_hard_t3": hard,
        "deflect_off_hard_t2": T2_SIGNED["deflect_off_hard"],
        "flag_gt_30pct": flag,
        "card_claim": CARD_CLAIM[cls],
        "card_claim_is_measured": False,
        "alltoall_separate": cls in DUAL_BUSY_CLASSES,
        "note": (
            "alltoall dual-busy-sat separate; expected gain≈0; do not fold"
            if cls in DUAL_BUSY_CLASSES
            else "inject-success is NOT the endpoint"
        ),
    }


def signed_t2_rows() -> list[dict]:
    """Director/audit pins as their own rows (T2 column only)."""
    return [
        {
            "metric": "hole_dual",
            "arm": "all-classes",
            "t3": "",
            "t2": T2_SIGNED["hole_dual"],
            "rel_err": 0.0,
            "flag_gt_30pct": False,
            "note": "HARD; hole>0 = mechanism fail",
        },
        {
            "metric": "phi_age_end",
            "arm": "phi_walk(6,1,AGE_MAX,rejoin)",
            "t3": "",
            "t2": T2_SIGNED["phi_age_end"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "φ→0; age_end=1 is NOT Σage progress",
        },
        {
            "metric": "deflect-off HARD",
            "arm": "asymmetric classes",
            "t3": "",
            "t2": T2_SIGNED["deflect_off_hard"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "deflect-off T >= AODI-on T required to attribute",
        },
        {
            "metric": "alltoall T_mix",
            "arm": "dual-busy-sat",
            "t3": "",
            "t2": T2_SIGNED["alltoall_t_mix"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "expected gain≈0; separate row; never fold into 0.50-0.85x",
        },
        {
            "metric": "gather T_mix",
            "arm": "default H-*",
            "t3": "",
            "t2": T2_SIGNED["gather_t_mix"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "T2 analytical; cycle T_mix is measured separately",
        },
        {
            "metric": "reduce T_mix",
            "arm": "default H-*",
            "t3": "",
            "t2": T2_SIGNED["reduce_t_mix"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "T2 analytical; same occupancy as gather",
        },
        {
            "metric": "uniform_read T_mix",
            "arm": "default H-*",
            "t3": "",
            "t2": T2_SIGNED["uniform_read_t_mix"],
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "T2 analytical; cycle T_mix is measured separately",
        },
        {
            "metric": "card-claim",
            "arm": "asym / dual-busy",
            "t3": "NOT measured",
            "t2": "0.70-0.95x / 0.95-1.05x",
            "rel_err": "",
            "flag_gt_30pct": "",
            "note": "card-claim only; director did not sign",
        },
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="AODI cycle sim (single run)")
    p.add_argument("--class", dest="cls", choices=CLASSES, default="gather")
    p.add_argument("--arm", choices=ARMS, default="AODI-on")
    p.add_argument("--n-nodes", type=int, default=12)
    p.add_argument("--n-bottom", type=int, default=0)
    p.add_argument("--n-txn", type=int, default=64)
    p.add_argument("--outstanding", type=int, default=16)
    p.add_argument("--warmup-laps", type=int, default=1)
    p.add_argument("--age-max", type=int, default=AGE_MAX_DEFAULT)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--force-dual-busy", action="store_true")
    args = p.parse_args(argv)
    r = run_arm(
        args.arm,
        args.cls,
        args.seed,
        n_nodes=args.n_nodes,
        n_bottom=args.n_bottom,
        n_txn=args.n_txn,
        outstanding=args.outstanding,
        warmup_laps=args.warmup_laps,
        age_max=args.age_max,
        force_dual_busy=args.force_dual_busy,
    )
    print(
        f"AODI T3 class={args.cls} arm={args.arm} n={args.n_nodes}+{args.n_bottom} "
        f"|I|={args.n_txn} seed={args.seed}"
    )
    print(
        f"xbar×{r.n_xbar} warmup={r.warmup_cycles} makespan={r.makespan} "
        f"completed={r.completed} collapsed={r.collapsed}"
    )
    print(
        f"hole_asym={r.hole_asym} hole_dual={r.hole_dual} dual_busy={r.dual_busy_cycles} "
        f"deflect={r.deflect} rejoin={r.rejoin} inject_ok={r.inject_ok} fail={r.inject_fail} "
        f"p_inj={r.p_inj:.4f}"
    )
    print(
        f"ρ_pref={r.rho_pref:.4f} ρ_opp={r.rho_opp:.4f} "
        f"complete_cw={r.completions_cw} complete_ccw={r.completions_ccw} "
        f"phi_freeze={r.phi_freeze_events} illegal={r.illegal_third} dropped={r.dropped}"
    )
    print(
        f"goodput={r.goodput_b_per_cyc:.2f} B/cyc (clock UNKNOWN; not TB/s) "
        f"hole_dual_fail={r.hole_dual_fail}"
    )
    print(f"card-claim {CARD_CLAIM[args.cls]} is NOT measured")
    print("0.85 is a pass bar, not a measured mean; no team-384dmc; no M-1/M-2/M-5 mix")
    t2mod = try_load_t2_module()
    print("T2 model.py on this tree:" + (" yes" if t2mod else " no (PR #65 only; using signed constants)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
