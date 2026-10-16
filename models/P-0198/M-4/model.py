#!/usr/bin/env python3
"""P-0198/M-4 AODI — 2x2 slot conservation + asymmetric-hole model (stdlib).

See spec.md. No curve fitting. No CBC/CSR/CRRF math.
Absolute makespan only via H-INJ-DOM relative scaling of published T_off.
Dual-busy inject-hole is identically 0 (mechanism-fail if not).
Cycle-level 2x2 / Rejoin timing is out of scope (Dr.Sim).
"""

from __future__ import annotations

import math
import sys

# ---- Envelope pins (SOURCE in comments; same T_off nails as sibling P-0198) ----
# problems/P-0198.yaml + docs/srcfc_ca_model/data.json scheme=off
T_OFF = {
    "uniform_read": 4403.2,   # YAML + data.json
    "uniform_write": 4834.6,  # YAML + data.json
    "broadcast": 492.0,       # data.json; YAML emphasizes goodput not makespan
    "gather": 537.2,
    "reduce": 537.2,
    "allgather": 1668.6,
    "allreduce": 990.6,
    "alltoall": 4098.0,
}

# collapse_settings.json + YAML narrative
COLLAPSED = {
    "uniform_read": True,    # peak-then-collapse narrative in YAML
    "uniform_write": False,  # YAML: platform ~5.5 TB/s, no reported collapse
    "broadcast": False,
    "gather": True,
    "reduce": True,
    "allgather": True,
    "allreduce": True,
    "alltoall": True,
}

# Inject-fail dominated classes for H-INJ-DOM relative makespan.
# alltoall is listed so T_hat prints, but it is DUAL-BUSY SAT — never folded
# into the asymmetric 0.70-0.95 or any 0.50-0.85 aggregation.
INJ_DOM = {"gather", "reduce", "allgather", "allreduce", "alltoall"}
DUAL_BUSY_CLASSES = {"alltoall"}

# YAML pin: 46080 txns for uniform read/write. Collectives: unpublished.
N_TXN = {
    "uniform_read": 46080,
    "uniform_write": 46080,
}

# Uniform-read goodput pins (YAML). Collapse band ~2.8–3.4 TB/s.
# 1 TB/s = 1000 B/ns → band ≈ 2800–3400 B/ns.
G_PEAK_READ = 5761.0
G_COLL_LO = 2800.0
G_COLL_HI = 3400.0

AGE_MAX = 8  # card default; bounds deflection count only
H_HOP = 6.0  # H-HOP: ~half of a 12-node ring; scale, not measured
EPS = 1e-12

# H-RHO-CLASS defaults (assumptions, NOT measured). alltoall: c=+1 dual-sat.
# (rho_pref, rho_opp, corr, regime)
CLASS_RHO = {
    "uniform_read": (0.72, 0.28, 0.00, "asymmetric"),
    "uniform_write": (0.68, 0.38, 0.10, "asymmetric"),
    "broadcast": (0.40, 0.18, 0.00, "asymmetric"),
    "gather": (0.78, 0.25, 0.00, "asymmetric"),
    "reduce": (0.78, 0.25, 0.00, "asymmetric"),
    "allgather": (0.82, 0.48, 0.20, "mixed"),
    "allreduce": (0.80, 0.52, 0.25, "mixed"),
    "alltoall": (0.93, 0.93, 1.00, "dual-busy-sat"),
}

# card-claim columns — NOT measured
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

CLASSES = (
    "uniform_read",
    "uniform_write",
    "broadcast",
    "gather",
    "reduce",
    "allgather",
    "allreduce",
    "alltoall",
)


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def frechet_joint(rho_pref: float, rho_opp: float, corr: float):
    """Joint occupancy with Frechet bounds. H-CORR.

    Returns (p_pref_only, p_opp_only, p_dual, p_empty).
    """
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
    p_pref_only = rho_pref - p_dual
    p_opp_only = rho_opp - p_dual
    p_empty = 1.0 - rho_pref - rho_opp + p_dual
    return p_pref_only, p_opp_only, p_dual, p_empty


def slots_after(cw_busy: bool, ccw_busy: bool, inject_ok: bool) -> int:
    """Physical highway slots occupied after the action (max legal = 2)."""
    n = int(cw_busy) + int(ccw_busy)
    if inject_ok:
        # Legal inject occupies a slot that deflection emptied, or was empty.
        # Count the post-state occupancy, not "busy bits + inject".
        if cw_busy and ccw_busy:
            return n + 1  # illegal third occupant
        if cw_busy and not ccw_busy:
            return 2  # T moved to CCW, inject on CW
        if (not cw_busy) and ccw_busy:
            return 2  # inject on empty preferred; opp still busy
        return 1  # inject into dual-empty
    return n


def truth_row(cw_busy: bool, ccw_busy: bool, inject_pending: bool,
              preferred: str, deflect_on: bool, age_ok: bool):
    """Evaluate one 2x2 atom. preferred in {'CW','CCW'}."""
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
        # HARD: no inject, hole≡0. H-SWAP: thru-only (swap would need age++).
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
        # preferred empty: inject, no hole from AODI
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
    }


def occupancy_rates(rho_pref: float, rho_opp: float, corr: float,
                    lam_age: float, eta_use: float, deflect_on: bool):
    """Steady hole / inject rates. p_hole_dual is identically 0."""
    p_pref_only, p_opp_only, p_dual, p_empty = frechet_joint(
        rho_pref, rho_opp, corr
    )
    s = p_pref_only + p_opp_only + p_dual + p_empty
    if abs(s - 1.0) > 1e-9:
        raise AssertionError("occupancy atoms do not sum to 1")
    lam_age = clip01(lam_age)
    eta_use = clip01(eta_use)
    en = 1.0 if deflect_on else 0.0
    p_hole_asym = eta_use * p_pref_only * lam_age * en
    p_hole_dual = 0.0  # HARD CONTRACT — do not derive from occupancy
    p_inj_off = 1.0 - rho_pref
    p_inj_on = p_inj_off + p_hole_asym
    return {
        "p_pref_only": p_pref_only,
        "p_opp_only": p_opp_only,
        "p_dual": p_dual,
        "p_empty": p_empty,
        "p_hole_asym": p_hole_asym,
        "p_hole_dual": p_hole_dual,
        "p_inj_off": p_inj_off,
        "p_inj_on": p_inj_on,
    }


def wait_rejoin(rho_pref: float) -> float:
    gap = 1.0 - rho_pref
    if gap <= EPS:
        return float("inf")
    return 1.0 / gap


def opposite_util(rho_opp: float, p_hole_asym: float, rho_pref: float,
                  kappa_mig: float) -> float:
    """H-OPEN (kappa=0) or H-MIGRATE closed-loop first-order fill."""
    w = wait_rejoin(rho_pref)
    if math.isinf(w):
        extra = 1.0 if p_hole_asym > 0 else 0.0
    else:
        extra = clip01(kappa_mig) * p_hole_asym * w
    return clip01(rho_opp + extra)


def makespan_ratios(p_inj_off: float, p_inj_on: float, p_hole_asym: float,
                    rho_pref: float, h_hop: float):
    """H-INJ-DOM inject ratio + H-VICTIM mix. Dual-busy → both ≈1."""
    if p_inj_off <= 0 and p_inj_on <= 0:
        t_inj = 1.0
    elif p_inj_on <= 0:
        t_inj = float("inf")
    else:
        t_inj = p_inj_off / p_inj_on
    w = wait_rejoin(rho_pref)
    extra = float("inf") if math.isinf(w) else (1.0 + w)
    f_vic = min(1.0, p_hole_asym / max(rho_pref, EPS))
    if math.isinf(extra):
        t_vic = float("inf")
        t_mix = float("inf") if f_vic > 0 else t_inj
    else:
        t_vic = 1.0 + extra / max(h_hop, EPS)
        t_mix = (1.0 - f_vic) * t_inj + f_vic * t_vic
    return t_inj, t_mix, f_vic, extra


def phi_walk(h_init: int, n_deflect: int, age_max: int, rejoin_fires: bool):
    """Per-packet φ, not Σage. Returns (phi_trace, ages, freeze, ok)."""
    phi = float(h_init)
    age = 0
    trace = [("start-pref", phi, age)]
    freeze = False
    # Deflect moves to wrong ring; φ is unarmed (not progress). age++ on commit.
    for _ in range(n_deflect):
        if age >= age_max:
            trace.append(("deflect-blocked-AGE_MAX", phi, age))
            break
        age += 1
        # unarmed: do not treat φ as advanced; record None-progress via same φ
        trace.append(("deflect-unarmed", phi, age))
    if n_deflect > 0:
        if not rejoin_fires:
            freeze = True
            trace.append(("phi-freeze-pref-full", phi, age))
            return trace, age, freeze, age <= age_max
        # rejoin armed: φ := 1 + remaining preferred hops (here remaining=h_init)
        phi = 1.0 + float(h_init)
        trace.append(("rejoin-armed", phi, age))
        phi -= 1.0  # the rejoin hop itself
        trace.append(("rejoin-done", phi, age))
    # preferred-direction hops
    while phi > 0:
        prev = phi
        phi -= 1.0
        if phi >= prev:
            return trace, age, freeze, False
        trace.append(("pref-hop", phi, age))
    return trace, age, freeze, True


def fmt(x: float, nd: int = 4) -> str:
    if isinstance(x, str):
        return x
    if math.isinf(x):
        return "inf"
    return f"{x:.{nd}f}"


def prow(cols, widths):
    print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))


def class_row(cls: str, lam_age: float, eta_use: float, kappa_mig: float,
              deflect_on: bool, h_hop: float):
    rho_pref, rho_opp, corr, regime = CLASS_RHO[cls]
    occ = occupancy_rates(rho_pref, rho_opp, corr, lam_age, eta_use, deflect_on)
    if occ["p_hole_dual"] != 0.0:
        raise AssertionError("MECHANISM FAIL: dual-busy hole>0")
    rho_opp_hat = opposite_util(rho_opp, occ["p_hole_asym"], rho_pref, kappa_mig)
    t_inj, t_mix, f_vic, extra = makespan_ratios(
        occ["p_inj_off"], occ["p_inj_on"], occ["p_hole_asym"], rho_pref, h_hop
    )
    t_off = T_OFF[cls]
    t_hat = t_off * t_mix if not math.isinf(t_mix) else float("inf")
    freeze = (1.0 - rho_pref) <= EPS
    c_opp_rel = (rho_opp / rho_opp_hat) if rho_opp_hat > EPS else 1.0
    return {
        "cls": cls,
        "regime": regime,
        "rho_pref": rho_pref,
        "rho_opp": rho_opp,
        "rho_opp_hat": rho_opp_hat,
        "corr": corr,
        "occ": occ,
        "t_inj": t_inj,
        "t_mix": t_mix,
        "t_off": t_off,
        "t_hat": t_hat,
        "f_vic": f_vic,
        "extra": extra,
        "freeze": freeze,
        "c_opp_rel": c_opp_rel,
    }


def main() -> int:
    print("P-0198/M-4 AODI  2x2 slot-conservation + asymmetric-hole model")
    print("envelope DV200 tests/soc_sim  repo lukebest/bufferless-ring-noc")
    print("SOURCE T_off: problems/P-0198.yaml + docs/srcfc_ca_model/data.json off")
    print("no silicon ±15%; no team-384dmc; no decode-*; 0.85 is pass bar not mean")
    print("dual-busy inject-hole ≡ 0; gain window = asymmetric occupancy only")
    print("alltoall dual-busy-sat expected gain ≈0 — separate row, never averaged")
    print("phi = per-packet remaining preferred hops after rejoin arming; NOT Σage")
    print("no mixed conclusions with M-1/M-2/M-5")
    print()

    # ---- Default assumption set (named; scanned below) ----
    lam_age = 0.90     # H-AGE: fraction of transit flits with age < AGE_MAX
    eta_use = 0.25     # H-USE: pending inject actually consumes a legal hole
    kappa_mig = 0.0    # H-OPEN: no opposite backfill on the main table
    h_hop = H_HOP      # H-HOP

    print("=== ASSUMPTIONS (labeled; not silicon) ===")
    print(f"H-PEND I=1 in inject-starve epochs")
    print(f"H-RHO-CLASS per-class (rho_pref, rho_opp, corr) — see table")
    print(f"H-CORR Frechet; alltoall c=+1 dual-sat")
    print(f"H-AGE lam_age={lam_age} AGE_MAX={AGE_MAX} (bounds deflect count only)")
    print(f"H-USE eta_use={eta_use}")
    print(f"H-REJOIN geometric wait 1/(1-rho_pref); no preemption")
    print(f"H-SWAP dual-busy thru-only (swap must age++ / AGE_MAX if ever allowed)")
    print(f"H-OPEN kappa_mig={kappa_mig} (H-MIGRATE scanned later)")
    print(f"H-INJ-DOM T∝1/p_inj for collapsed / occupancy-limited classes")
    print(f"H-VICTIM mix uses extra=1+E[wait_rejoin], H={h_hop}")
    print(f"H-HOP H={h_hop}")
    print()

    # ---- 2x2 truth table ----
    print("=== 2x2 TRUTH TABLE (preferred=CW; inject pending=yes) ===")
    tw = (10, 10, 28, 6, 8, 8, 10)
    prow(("CW", "CCW", "action", "hole", "inject", "slots", "legal"), tw)
    atoms = (
        (True, False, "asymmetric pref-busy"),
        (False, True, "pref-empty opp-busy"),
        (False, False, "dual-empty"),
        (True, True, "dual-busy"),
    )
    for cw, ccw, _label in atoms:
        row = truth_row(cw, ccw, True, "CW", True, True)
        prow(
            (
                "busy" if cw else "empty",
                "busy" if ccw else "empty",
                row["action"],
                str(row["hole"]),
                str(row["inject_ok"]),
                str(row["slots"]),
                "FAIL" if row["illegal"] else "ok",
            ),
            tw,
        )
        if row["dual"] and row["hole"] != 0:
            print("MECHANISM FAIL: dual-busy hole!=0")
            return 1
        if row["illegal"]:
            print("MECHANISM FAIL: third slot")
            return 1
    # Illegal claim: dual-busy + inject would need 3 slots
    occ_illegal = slots_after(True, True, True)
    print(
        f"illegal dual-busy+inject occupants={occ_illegal} (>2 ⇒ third-slot; "
        f"silicon must not implement)"
    )
    if occ_illegal <= 2:
        print("internal error: illegal row should exceed 2 slots")
        return 1
    print("CONSTRAINT: dual-busy ⇒ inject-hole≡0; no silent drop/buffer")
    print()

    # ---- Conservation of occupancy atoms ----
    print("=== OCCUPANCY ATOMS (sum=1; no mint) ===")
    for cls in CLASSES:
        rho_p, rho_o, c, regime = CLASS_RHO[cls]
        a, b, d, e = frechet_joint(rho_p, rho_o, c)
        ok = abs((a + b + d + e) - 1.0) < 1e-12
        print(
            f"  {cls:14} regime={regime:14} pref_only={a:.4f} opp_only={b:.4f} "
            f"dual={d:.4f} empty={e:.4f} sum_ok={ok}"
        )
        if not ok:
            return 1
    print()

    # ---- Per-packet φ (not Σage) ----
    print("=== PHI WALK (per-packet; NOT Σage) ===")
    trace, age_end, frz, ok = phi_walk(6, 1, AGE_MAX, rejoin_fires=True)
    for ev, ph, ag in trace:
        print(f"  event={ev:24} phi={fmt(ph)}  age={ag}  (age is NOT progress)")
    print(
        f"phi reached 0? {trace[-1][1] == 0.0}  age_end={age_end} "
        f"(Σage would be {age_end}, which does not measure arrival)"
    )
    if not ok or trace[-1][1] != 0.0:
        print("phi walk failed")
        return 1
    _, _, frz2, _ok_frz = phi_walk(6, 1, AGE_MAX, rejoin_fires=False)
    print(f"probe: preferred forever full ⇒ phi freeze={frz2} (Archi condition)")
    if not frz2:
        print("expected freeze when rejoin cannot fire")
        return 1
    print(f"AGE_MAX={AGE_MAX} bounds n_deflect; rejoin only if preferred outlet empty")
    print()

    # ---- Per-class (no averaging) ----
    print("=== PER-CLASS (no averaging; card-claim is NOT measured) ===")
    widths = (14, 14, 8, 10, 10, 10, 10, 8, 10, 12, 22)
    prow(
        (
            "class",
            "regime",
            "collaps",
            "hole_as",
            "hole_du",
            "T_off",
            "T_hat",
            "T_inj",
            "T_mix",
            "opp_util",
            "card-claim",
        ),
        widths,
    )
    for cls in CLASSES:
        r = class_row(cls, lam_age, eta_use, kappa_mig, True, h_hop)
        occ = r["occ"]
        if occ["p_hole_dual"] != 0.0:
            print("MECHANISM FAIL: dual-busy hole>0")
            return 1
        # T_hat is model-relative for every class; card-claim is a separate column.
        prow(
            (
                cls,
                r["regime"],
                str(COLLAPSED[cls]),
                fmt(occ["p_hole_asym"]),
                fmt(occ["p_hole_dual"]),
                fmt(r["t_off"], 1),
                fmt(r["t_hat"], 1),
                fmt(r["t_inj"]),
                fmt(r["t_mix"]),
                fmt(r["rho_opp_hat"]),
                CARD_CLAIM[cls],
            ),
            widths,
        )
        n_pin = N_TXN.get(cls)
        n_s = str(n_pin) if n_pin is not None else "n/a (unpublished)"
        c_time = (1.0 / r["t_mix"]) if r["t_mix"] not in (0.0, float("inf")) else float("inf")
        print(
            f"           p_inj_off={fmt(occ['p_inj_off'])} p_inj_on={fmt(occ['p_inj_on'])} "
            f"P(dual)={fmt(occ['p_dual'])} P(pref_only)={fmt(occ['p_pref_only'])} "
            f"N_txn={n_s} C_eq_work={n_s} C_eq_time_rel={fmt(c_time)} "
            f"C_opp_rel={fmt(r['c_opp_rel'])} phi_freeze={r['freeze']} "
            f"(card-claim column is NOT measured; inject-success is NOT the endpoint)"
        )
        if cls in DUAL_BUSY_CLASSES:
            gain0 = abs(r["t_mix"] - 1.0) < 0.05
            print(
                f"           DUAL-BUSY SAT separate row: T_mix={fmt(r['t_mix'])} "
                f"expected gain≈0 ? {gain0}  "
                f"DO NOT fold into 0.50-0.85x or 0.70-0.95x aggregation"
            )
            if occ["p_hole_asym"] > 1e-9:
                print(
                    "           note: residual hole_asym from |rho| gap only; "
                    "corr=+1 forces pref_only≈0"
                )
    print()

    # ---- Hole buckets (asymmetric vs dual-busy) ----
    print("=== HOLE BUCKETS (asymmetric vs dual-busy) ===")
    hole_as_sum = 0.0
    hole_du_sum = 0.0
    for cls in CLASSES:
        r = class_row(cls, lam_age, eta_use, kappa_mig, True, h_hop)
        hole_as_sum += r["occ"]["p_hole_asym"]
        hole_du_sum += r["occ"]["p_hole_dual"]
        print(
            f"  {cls:14} bucket={'dual-busy' if cls in DUAL_BUSY_CLASSES else 'asymmetric/mixed'} "
            f"hole_asym={fmt(r['occ']['p_hole_asym'])} hole_dual={fmt(r['occ']['p_hole_dual'])}"
        )
    print(f"SUM hole_dual across classes = {fmt(hole_du_sum)} (must be 0)")
    if hole_du_sum != 0.0:
        print("MECHANISM FAIL: dual-busy hole bucket non-zero")
        return 1
    print("assert dual-busy hole≡0: PASS")
    print()

    # ---- Ablation: deflect-off ----
    print("=== ABLATION deflect-off (report opp util + completions; ban inject-success-only) ===")
    aw = (14, 12, 10, 10, 10, 10, 10, 10)
    prow(
        ("class", "arm", "hole_as", "hole_du", "T_hat", "T/T_off", "opp_util", "C_time"),
        aw,
    )
    attrib_ok = True
    for cls in CLASSES:
        on = class_row(cls, lam_age, eta_use, kappa_mig, True, h_hop)
        off = class_row(cls, lam_age, eta_use, kappa_mig, False, h_hop)
        for name, r in (("AODI-on", on), ("deflect-off", off)):
            c_time = (1.0 / r["t_mix"]) if r["t_mix"] not in (0.0, float("inf")) else float("inf")
            prow(
                (
                    cls,
                    name,
                    fmt(r["occ"]["p_hole_asym"]),
                    fmt(r["occ"]["p_hole_dual"]),
                    fmt(r["t_hat"], 1),
                    fmt(r["t_mix"]),
                    fmt(r["rho_opp_hat"]),
                    fmt(c_time),
                ),
                aw,
            )
        if on["occ"]["p_hole_dual"] != 0.0 or off["occ"]["p_hole_dual"] != 0.0:
            print("MECHANISM FAIL: hole_dual>0 on ablation")
            return 1
        if cls not in DUAL_BUSY_CLASSES and CLASS_RHO[cls][3] == "asymmetric":
            if not (off["t_mix"] + 1e-9 >= on["t_mix"]):
                attrib_ok = False
                print(f"           ATTRIB FAIL {cls}: deflect-off not worse than AODI-on")
        if cls in DUAL_BUSY_CLASSES:
            print(
                f"           alltoall deflect-off T_mix={fmt(off['t_mix'])} "
                f"AODI-on T_mix={fmt(on['t_mix'])} (expect both ≈1; gain≈0)"
            )
    print(
        f"HARD probe: deflect-off T >= AODI-on T on asymmetric classes? {attrib_ok} "
        f"(required to attribute)"
    )
    print()

    # ---- Goodput side note (uniform_read peak-after) ----
    print("=== UNIFORM_READ GOODPUT (collapse band; not inject-success) ===")
    print(f"G_peak={G_PEAK_READ} B/ns  collapse_band=[{G_COLL_LO},{G_COLL_HI}] B/ns (YAML TB/s)")
    print(
        "1-cycle opposite holes do not mint ring capacity (still 2 slots/node/channel). "
        "This linear model does NOT reproduce 5761 → 2.8-3.4e3 B/ns; "
        "report the curve from tests/soc_sim, do not claim collapse relief from p_inj."
    )
    print()

    # ---- Sensitivity ----
    print("=== SENSITIVITY (gather unless noted): occupancy pair / corr, and eta_use × kappa_mig ===")
    print("-- vary (rho_pref, rho_opp, corr) on gather template --")
    for rho_p, rho_o, c, tag in (
        (0.60, 0.20, 0.0, "wide-asym"),
        (0.78, 0.25, 0.0, "default-gather"),
        (0.85, 0.40, 0.3, "narrow-asym"),
        (0.90, 0.90, 0.0, "high-indep"),
        (0.93, 0.93, 1.0, "dual-sat"),
    ):
        occ = occupancy_rates(rho_p, rho_o, c, lam_age, eta_use, True)
        t_inj, t_mix, _, _ = makespan_ratios(
            occ["p_inj_off"], occ["p_inj_on"], occ["p_hole_asym"], rho_p, h_hop
        )
        print(
            f"  {tag:16} rho=({rho_p:.2f},{rho_o:.2f}) c={c:.1f} "
            f"hole_as={fmt(occ['p_hole_asym'])} hole_du={fmt(occ['p_hole_dual'])} "
            f"T_inj={fmt(t_inj)} T_mix={fmt(t_mix)}"
        )
        if occ["p_hole_dual"] != 0.0:
            return 1
    print("-- vary eta_use (gather occupancies, kappa_mig=0) --")
    rho_p, rho_o, c, _ = CLASS_RHO["gather"]
    for eu in (0.05, 0.15, 0.25, 0.40, 0.70):
        occ = occupancy_rates(rho_p, rho_o, c, lam_age, eu, True)
        _, t_mix, _, _ = makespan_ratios(
            occ["p_inj_off"], occ["p_inj_on"], occ["p_hole_asym"], rho_p, h_hop
        )
        print(f"  eta_use={eu:.2f}  T_mix={fmt(t_mix)}  hole_as={fmt(occ['p_hole_asym'])}")
    print("-- vary kappa_mig (gather; opposite fill) --")
    for km in (0.0, 0.25, 0.50, 0.75, 1.00):
        occ = occupancy_rates(rho_p, rho_o, c, lam_age, eta_use, True)
        rho_hat = opposite_util(rho_o, occ["p_hole_asym"], rho_p, km)
        # re-evaluate holes at filled opposite (one-shot closed loop)
        occ2 = occupancy_rates(rho_p, rho_hat, c, lam_age, eta_use, True)
        _, t_mix, _, _ = makespan_ratios(
            occ2["p_inj_off"], occ2["p_inj_on"], occ2["p_hole_asym"], rho_p, h_hop
        )
        print(
            f"  kappa_mig={km:.2f}  rho_opp_hat={fmt(rho_hat)}  "
            f"hole_as'={fmt(occ2['p_hole_asym'])}  T_mix'={fmt(t_mix)}"
        )
    print()
    print("most sensitive: (rho_pref, rho_opp, corr) opens/closes the hole window;")
    print("eta_use sets how much of pref_only is actually an inject hole;")
    print("kappa_mig can mirror-fill opposite and collapse the window to dual-busy≈0")
    print()

    # ---- Magic gaps ----
    print("=== MAGIC-GAP FLAG ===")
    g = class_row("gather", lam_age, eta_use, kappa_mig, True, h_hop)
    in_asym_band = 0.70 <= g["t_mix"] <= 0.95
    print(
        f"gather default T_mix={fmt(g['t_mix'])} in card-claim[0.70,0.95]? {in_asym_band} "
        f"(card-claim is NOT measured)"
    )
    if not in_asym_band:
        print(
            "GAP: asymmetric card 0.70-0.95x not hit under default H-USE/H-VICTIM; "
            "do not treat card interval as model output"
        )
    print(
        f"gather pure H-INJ-DOM T_inj={fmt(g['t_inj'])} — often below 0.70 "
        f"(over-credits inject; victim/rejoin tax is the honest mix)"
    )
    a2a = class_row("alltoall", lam_age, eta_use, kappa_mig, True, h_hop)
    print(
        f"alltoall T_mix={fmt(a2a['t_mix'])} hole_dual={fmt(a2a['occ']['p_hole_dual'])} "
        f"gain≈0 separate row; NEVER fold into 0.50-0.85x"
    )
    if abs(a2a["t_mix"] - 1.0) > 0.05:
        print(
            "GAP: alltoall T_mix not ≈1 under H-CORR=+1; check residual |rho| gap "
            "— still do not advertise dual-busy speedup"
        )
    print(
        "GAP: uniform_read peak-after collapse (5761→2.8-3.4e3 B/ns) is congestion "
        "dynamics; 1-cycle holes do not explain it"
    )
    print(
        "GAP: phi freeze when preferred never empties — age+rejoin is conditional "
        "progress, not a livelock proof"
    )
    print(
        "GAP: claiming 0.50-0.85x on dual-busy/alltoall is a card-narrative error; "
        "this model refuses that fold"
    )
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
