#!/usr/bin/env python3
"""P-0198/M-1 CBC — empty-slot conservation + inject-opportunity model (stdlib).

See spec.md. No curve fitting. Absolute makespan only via H-INJ-DOM relative
scaling of published T_off. Cycle-level FSM is out of scope (Dr.Sim).
"""

from __future__ import annotations

import math
import sys

# ---- Envelope pins (SOURCE in comments) ----
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
    "uniform_read": True,   # peak-then-collapse narrative in YAML
    "uniform_write": False, # YAML: platform ~5.5 TB/s, no reported collapse
    "broadcast": False,
    "gather": True,
    "reduce": True,
    "allgather": True,
    "allreduce": True,
    "alltoall": True,
}

# Inject-fail dominated classes for H-INJ-DOM relative makespan
INJ_DOM = {"gather", "reduce", "allgather", "allreduce", "alltoall"}

# Uniform-read goodput pins (YAML). Collapse band given as ~2.8–3.4 TB/s.
# 1 TB/s = 1000 B/ns → band ≈ 2800–3400 B/ns.
G_PEAK_READ = 5761.0  # B/ns at offered ~5767
G_COLL_LO = 2800.0
G_COLL_HI = 3400.0

DUTY_P2P = (1 / 16, 1 / 8)
DUTY_COLL = (1 / 4, 1 / 2)
AGE_MAX = 15
W_EMIT = 8


def partition_empty(rho_empty: float, d: float, lam_age: float = 1.0):
    """Tag fraction d of empties as bubbles. Does not mint empty."""
    if rho_empty < 0 or rho_empty > 1:
        raise ValueError("rho_empty out of [0,1]")
    d = max(0.0, min(1.0, d))
    lam_age = max(0.0, min(1.0, lam_age))
    rho_bubble = min(d, 1.0) * rho_empty
    rho_bubble_eff = lam_age * rho_bubble
    rho_raw_eff = rho_empty - rho_bubble_eff
    return rho_raw_eff, rho_bubble_eff


def p_inj_coll(rho_empty: float, d: float, eta: float, eta0: float, lam_age: float = 1.0):
    """Collective inject opportunity with placement efficiency η (spec §3.3)."""
    # off: visible empty at fan-in neighborhood
    p_off = rho_empty * eta0
    # on: untouched raw share + bubbled share delivered with η
    p_on = rho_empty * ((1.0 - d) * eta0 + d * eta * lam_age)
    # cannot exceed total empty
    p_on = min(p_on, rho_empty)
    p_off = min(p_off, rho_empty)
    return p_off, p_on


def relative_makespan(t_off: float, p_off: float, p_on: float):
    """H-INJ-DOM: T ∝ 1/p_inj."""
    if p_off <= 0 or p_on <= 0:
        return float("inf"), float("inf")
    ratio = p_off / p_on
    return t_off * ratio, ratio


def amdahl_T(t_off: float, f_coll: float, s_inj: float):
    if s_inj <= 0:
        return float("inf")
    speedup = 1.0 / (1.0 - f_coll + f_coll / s_inj)
    return t_off / speedup, speedup


def goodput_with_keep(g_peak: float, rho_empty: float, d: float, kappa_keep: float, lam_age: float = 1.0):
    """P2P side-effect probe: unstolen bubbles reduce effective payload capacity."""
    _, rho_b = partition_empty(rho_empty, d, lam_age)
    c_frac = 1.0 - rho_b * kappa_keep
    c_frac = max(0.0, min(1.0, c_frac))
    g = g_peak * c_frac
    return g, c_frac, (g <= G_COLL_HI)


def dual_tenant_B(rho_empty: float, d_a: float, lam_age: float = 1.0):
    """B (uniform read) only gets raw after A steals all bubbles."""
    rho_raw, _ = partition_empty(rho_empty, d_a, lam_age)
    p_solo = rho_empty  # solo B can use all empties (η=1 local)
    p_dual = rho_raw
    if p_dual <= 0:
        return float("inf"), p_solo, p_dual
    return p_solo / p_dual, p_solo, p_dual


def fmt(x: float, nd: int = 4) -> str:
    if math.isinf(x):
        return "inf"
    return f"{x:.{nd}f}"


def prow(cols, widths):
    print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))


def main() -> int:
    print("P-0198/M-1 CBC  empty-slot conservation model")
    print("envelope DV200 tests/soc_sim  repo lukebest/bufferless-ring-noc")
    print("SOURCE T_off: problems/P-0198.yaml + docs/srcfc_ca_model/data.json off")
    print("no silicon ±15%; no team-384dmc; no decode-*; 0.85 is pass bar not mean")
    print("H-INJ-DOM relative makespan only for collapsed collectives")
    print()

    # ---- Default assumption set (named; scanned below) ----
    rho_empty = 0.20          # H-RHO: fan-in still has some eject empties
    eta0 = 0.35               # visible empty at sink neighborhood without CBC
    eta = 0.85                # with CBC bubbles steered to neighborhood
    f_coll = 0.70             # Amdahl fan-in time fraction
    lam_age = 1.0
    kappa_keep = 0.50         # fraction of bubbles not stolen under dense P2P duty

    print("=== ASSUMPTIONS (labeled; not silicon) ===")
    print(f"H-RHO rho_empty={rho_empty}")
    print(f"H-PLACE eta0={eta0} eta={eta}")
    print(f"H-AMDAHL f_coll={f_coll}")
    print(f"H-AGE lam_age={lam_age} AGE_MAX={AGE_MAX} W={W_EMIT}")
    print(f"H-KEEP kappa_keep={kappa_keep}")
    print()

    # ---- Conservation ----
    print("=== CONSERVATION (exact) ===")
    for d in (0.0, 1 / 16, 1 / 8, 1 / 4, 1 / 2):
        raw, bub = partition_empty(rho_empty, d, lam_age)
        ok = abs((raw + bub) - rho_empty) < 1e-12
        print(
            f"  d={d:.4f}  rho_empty={rho_empty:.4f}  raw={raw:.4f}  bub={bub:.4f}  "
            f"sum_ok={ok}  delta_vs_off={0.0:.4f}"
        )
    print("CONSTRAINT: CBC does not mint empty; delta_rho_empty=0 by construction")
    print()

    # ---- Per-class relative makespan ----
    print("=== PER-CLASS (no averaging) H-INJ-DOM where collapsed collective ===")
    widths = (14, 8, 8, 10, 10, 10, 10, 12, 10)
    prow(
        ("class", "collaps", "d", "p_off", "p_on", "T_off", "T_hat", "T_hat/T_off", "card-claim"),
        widths,
    )
    card_claim = {
        "gather": "0.55-0.85x",
        "reduce": "0.55-0.85x",
        "allgather": "0.55-0.85x",
        "allreduce": "0.55-0.85x",
        "alltoall": "0.55-0.85x",
        "broadcast": "0.90-1.05x",
        "uniform_read": "0.95-1.10x",
        "uniform_write": "0.95-1.10x",
    }
    for cls in (
        "uniform_read",
        "uniform_write",
        "broadcast",
        "gather",
        "reduce",
        "allgather",
        "allreduce",
        "alltoall",
    ):
        t_off = T_OFF[cls]
        if cls in INJ_DOM:
            for d in DUTY_COLL:
                p_off, p_on = p_inj_coll(rho_empty, d, eta, eta0, lam_age)
                t_hat, ratio = relative_makespan(t_off, p_off, p_on)
                prow(
                    (
                        cls,
                        str(COLLAPSED[cls]),
                        f"{d:.4f}",
                        fmt(p_off),
                        fmt(p_on),
                        fmt(t_off, 1),
                        fmt(t_hat, 1),
                        fmt(ratio),
                        card_claim[cls],
                    ),
                    widths,
                )
                # Amdahl companion
                s_inj = (p_on / p_off) if p_off > 0 else float("inf")
                t_a, sp = amdahl_T(t_off, f_coll, s_inj)
                print(
                    f"           amdahl f_coll={f_coll} S_inj={fmt(s_inj)} "
                    f"T_amdahl={fmt(t_a,1)} speedup={fmt(sp)} "
                    f"(card-claim column is NOT measured)"
                )
        else:
            # near-neutral: report p_inj under P2P duties; T_hat n/a under H-INJ-DOM
            for d in DUTY_P2P:
                p_off, p_on = p_inj_coll(rho_empty, d, eta0, eta0, lam_age)  # η=η0: no place gain
                prow(
                    (
                        cls,
                        str(COLLAPSED[cls]),
                        f"{d:.4f}",
                        fmt(p_off),
                        fmt(p_on),
                        fmt(t_off, 1),
                        "n/a",
                        "n/a",
                        card_claim[cls],
                    ),
                    widths,
                )
    print()

    # ---- Ablation ----
    print("=== ABLATION (gather exemplar; HARD-1) ===")
    t_off = T_OFF["gather"]
    rows = []
    for name, d in (
        ("calendar-off", 0.0),
        ("duty=0", 0.0),
        ("CBC-coll-1/4", 0.25),
        ("CBC-coll-1/2", 0.50),
        ("fixed-high-1/2", 0.50),
    ):
        p_off, p_on = p_inj_coll(rho_empty, d, eta, eta0, lam_age)
        if name.startswith("calendar") or name.startswith("duty"):
            # off arm uses η0 only
            p_on = rho_empty * eta0
        t_hat, ratio = relative_makespan(t_off, rho_empty * eta0, p_on)
        rows.append((name, d, p_on, t_hat, ratio))
        print(
            f"  {name:16} d={d:.4f} p_inj={fmt(p_on)} T_hat={fmt(t_hat,1)} "
            f"T_hat/T_off={fmt(ratio)}"
        )
    t_cbc = min(r[3] for r in rows if r[0].startswith("CBC"))
    t_off_arm = rows[0][3]
    print(
        f"HARD-1 probe: calendar-off T_hat ({fmt(t_off_arm,1)}) > CBC T_hat ({fmt(t_cbc,1)})? "
        f"{t_off_arm > t_cbc}  (must be true to attribute)"
    )
    print()

    # ---- P2P goodput side effect ----
    print("=== P2P GOODPUT SIDE-EFFECT (uniform_read peak-after) ===")
    print(f"G_peak={G_PEAK_READ} B/ns  collapse_band=[{G_COLL_LO},{G_COLL_HI}] B/ns (YAML TB/s)")
    for d in (0.0, 1 / 16, 1 / 8, 1 / 4, 1 / 2):
        g, cfrac, flag = goodput_with_keep(G_PEAK_READ, rho_empty, d, kappa_keep, lam_age)
        print(
            f"  d={d:.4f}  C_eff/C={fmt(cfrac)}  G_hat={fmt(g,1)} B/ns  "
            f"flag_collapse_band={flag}"
        )
    print("Bench condition: P2P duty<=1/8 must NOT drop another order into collapse band")
    print()

    # ---- Dual tenant ----
    print("=== DUAL-TENANT (Sys): A collective high duty, B uniform read ===")
    for d_a in DUTY_COLL:
        worst, p_solo, p_dual = dual_tenant_B(rho_empty, d_a, lam_age)
        g_b, _, flag_g = goodput_with_keep(G_PEAK_READ, rho_empty, d_a, 1.0, lam_age)
        # B cannot steal: kappa_keep=1 on A's bubbles
        flag_t = worst >= 1.10
        print(
            f"  d_A={d_a:.4f}  T_B_dual/T_B_solo={fmt(worst)}  "
            f"p_solo={fmt(p_solo)} p_dual={fmt(p_dual)}  "
            f"G_B_hat={fmt(g_b,1)}  fail_T={flag_t} fail_G={flag_g}"
        )
    print("Sys pass if worsen <10% and G not in collapse band")
    print()

    # ---- Sensitivity: two most sensitive pairs ----
    print("=== SENSITIVITY (gather, d=1/4): eta/eta0 and rho_empty × f_coll ===")
    print("-- vary eta (eta0 fixed) --")
    for eta_i in (0.40, 0.55, 0.70, 0.85, 1.00):
        p_off, p_on = p_inj_coll(rho_empty, 0.25, eta_i, eta0, lam_age)
        _, ratio = relative_makespan(T_OFF["gather"], p_off, p_on)
        print(f"  eta={eta_i:.2f}  T_hat/T_off={fmt(ratio)}  S_inj={fmt(p_on/p_off)}")
    print("-- vary rho_empty (eta,eta0 fixed) --")
    for re in (0.05, 0.10, 0.20, 0.35, 0.50):
        p_off, p_on = p_inj_coll(re, 0.25, eta, eta0, lam_age)
        _, ratio = relative_makespan(T_OFF["gather"], p_off, p_on)
        # ratio independent of rho_empty under this linear form — show explicitly
        print(
            f"  rho_empty={re:.2f}  T_hat/T_off={fmt(ratio)}  "
            f"(linear model: ratio independent of rho_empty; level p_on={fmt(p_on)})"
        )
    print("-- vary f_coll via Amdahl at d=1/4 --")
    p_off, p_on = p_inj_coll(rho_empty, 0.25, eta, eta0, lam_age)
    s_inj = p_on / p_off
    for fc in (0.40, 0.55, 0.70, 0.85, 0.95):
        t_a, sp = amdahl_T(T_OFF["gather"], fc, s_inj)
        print(
            f"  f_coll={fc:.2f}  T_amdahl/T_off={fmt(t_a/T_OFF['gather'])}  speedup={fmt(sp)}"
        )
    print()
    print("most sensitive: (eta/eta0) sets S_inj; f_coll sets Amdahl translation to makespan")
    print("rho_empty sets absolute inject level but not ratio under H-PLACE linear form")
    print()
    print("=== MAGIC-GAP FLAG ===")
    # card claim 0.55–0.85 needs ratio in that band
    p_off, p_on = p_inj_coll(rho_empty, 0.50, eta, eta0, lam_age)
    _, ratio = relative_makespan(1.0, p_off, p_on)
    in_band = 0.55 <= ratio <= 0.85
    print(
        f"at d=1/2 default assumptions: T_hat/T_off={fmt(ratio)} "
        f"in card-claim[0.55,0.85]? {in_band}"
    )
    if not in_band:
        print(
            "GAP: card 0.55-0.85x not reached without raising eta/eta0 or f_coll; "
            "do not treat card interval as model output"
        )
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
