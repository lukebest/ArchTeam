#!/usr/bin/env python3
"""P-0198/M-5r1 CRRF-SB — native residual vs exclusive-epoch algebra (stdlib).

See spec.md. No curve fitting. Numbers are hypotheses, NOT measured.
Does not paste T2 1.5625 or T3 0.551/0.583/17.05 as card-claim.
"""

from __future__ import annotations

import math

# Public T_off nails (YAML + data.json off). Same as M-5 T2. Not silicon.
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

DAT_DOM = {"gather", "reduce", "allgather", "allreduce", "alltoall", "uniform_read"}
SNP_KILL = 1.4
T2_Q1_15_1 = 1.5625  # historical T2 pin; NOT a legal cycle schedule; NOT a pass
T3_NIGHT_SNP_PATH = 17.0533  # signed T3 night observation of M-5; NOT an r1 claim
T3_NIGHT_MIXED = 32.5873
T3_GATHER_0551 = 0.551  # unsigned; do not treat as card-claim


def duty_frac(r: int) -> tuple[float, float]:
    return r / (r + 1.0), 1.0 / (r + 1.0)


def t_drain_cycles(k_circ: float, c_ring: float, n_pipe: float) -> float:
    return (k_circ + 1.0) * c_ring + n_pipe


def fmt(x: float, nd: int = 4) -> str:
    if math.isinf(x):
        return "inf"
    return f"{x:.{nd}f}"


def snp_lat_q1(r: int, q: float, l_snp: float) -> float:
    """T2 H-SNP-LAT (illegal as a cycle schedule)."""
    duty_dat = r / (r + 1.0)
    e_wait = duty_dat * (r * q / 2.0)
    return (l_snp + e_wait) / l_snp


def snp_lat_m5_coarse(duty_dat: float, t_steady: float, t_drain: float, l_snp: float) -> float:
    """Exclusive epoch + one drain per DAT generation (T3 architect note)."""
    t_period = t_steady + t_drain
    e_wait = duty_dat * (t_period / 2.0)
    return (l_snp + e_wait) / l_snp


def snp_lat_sb(rho_wire: float, l_snp: float) -> float:
    rho = min(max(rho_wire, 0.0), 1.0 - 1e-9)
    e_wait = rho / (1.0 - rho)
    return (l_snp + e_wait) / l_snp


def c_dat_eff(duty_dat: float, f_steady: float, tau_sync: float, tau_bind: float, p_steal: float):
    ideal = 1.0 + duty_dat
    ghost = duty_dat * f_steady * (1.0 - p_steal)
    raw = 1.0 + ghost - tau_sync - tau_bind
    eff = min(ideal, max(1.0, raw))
    return eff, ideal, ghost


def main() -> int:
    print("P-0198/M-5r1 CRRF-SB  native-residual vs exclusive-epoch model")
    print("envelope DV200 tests/soc_sim  inference makespan/tail is the primary metric")
    print("ALL ratios below are hypotheses / NOT measured / not card-claim")
    print("do not paste T2 1.5625 or T3 0.551/0.583/17.05/32.59 as r1 results")
    print("0.85 is pass bar, not a measured mean; no silicon ±15%")
    print("this card only — no ranking vs eliminated M-1 / M-2 / M-4")
    print()

    c_ring = 25.0
    k_circ = 2.0
    n_pipe = 2.0
    t_steady = 20.0 * c_ring
    tau_sync = 0.02
    tau_bind = 0.02
    l_snp = c_ring / 2.0
    lam_snp = 0.05
    alpha_occ = 0.55  # H-WIRE: in-flight fraction of eligible ghost slots
    f_dat = 0.70

    t_drain = t_drain_cycles(k_circ, c_ring, n_pipe)
    f_st = t_steady / (t_steady + t_drain)
    tau_drain = 1.0 - f_st

    print("=== ASSUMPTIONS (labeled; not silicon) ===")
    print(f"H-SLOT S_phys=1")
    print(f"H-DRAIN T_drain={fmt(t_drain,1)}  H-FLIP T_steady={fmt(t_steady,1)} f_steady={fmt(f_st)}")
    print(f"H-SNP-LAT L_snp={fmt(l_snp,1)}  H-SNP-SPARSE lambda_snp={lam_snp}  H-WIRE alpha_occ={alpha_occ}")
    print(f"H-EPOCH-COARSE uses T_steady+T_drain, not q=1")
    print(f"H-GEO empty-slot wait = rho/(1-rho)")
    print(f"H-SRC-FC-NO-SLOT source FC does not mint a second Dat ring")
    print()

    print("=== HISTORICAL PINS (do not treat as r1 measured) ===")
    print(f"  T2 q=1 15:1 H-SNP-LAT = {T2_Q1_15_1}  (illegal cycle schedule)")
    print(f"  T3 night M-5 snp_path 15:1 = {T3_NIGHT_SNP_PATH}  mixed = {T3_NIGHT_MIXED}")
    print(f"  T3 night gather T/off = {T3_GATHER_0551}  (unsigned; not card-claim)")
    print()

    print("=== CONSERVATION + CAPACITY (SB taxes steal-back) ===")
    print("  arm         duty_dat  p_steal  C_ideal  C_ghost  C_dat_sb  <=ideal  <2  untaxed")
    caps = {}
    for name, r in (("rebind-off", 0), ("3:1", 3), ("7:1", 7), ("15:1", 15)):
        if name == "rebind-off":
            d_dat, d_snp = 0.0, 1.0
            p_steal = 0.0
            c_eff, ideal, ghost = 1.0, 1.0, 0.0
        else:
            d_dat, d_snp = duty_frac(r)
            p_steal = min(1.0, lam_snp / max(d_snp, 1e-9))
            # sparse: pending events are rare; cap steal share at lambda
            p_steal = min(p_steal, lam_snp)
            c_eff, ideal, ghost = c_dat_eff(d_dat, f_st, tau_sync, tau_bind, p_steal)
        caps[name] = {
            "r": r,
            "duty_dat": d_dat,
            "duty_snp": d_snp,
            "p_steal": p_steal,
            "c_dat": c_eff,
            "ideal": ideal,
            "ghost": ghost,
        }
        taxes = 0.0 if name == "rebind-off" else tau_drain + tau_sync + tau_bind
        untaxed = (c_eff + 1e-12 >= ideal) and taxes <= 1e-12 and name != "rebind-off"
        print(
            f"  {name:11} {d_dat:8.4f}  {p_steal:7.4f}  {ideal:7.4f}  {ghost:7.4f}  "
            f"{c_eff:8.4f}  {c_eff <= ideal + 1e-12}     {c_eff < 2.0} {untaxed}"
        )
    print("CONSTRAINT: time-mux ≠ second Dat port; untaxed_double must be False")
    print()

    print("=== SNP LATENCY (per arm; never fold into Dat mean) ===")
    print(
        "  arm         T2_q1  M5_coarse  SB_empty  SB<=1.4  SB<1.5625  "
        "M5_coarse>1.4  vs_T3night"
    )
    for name in ("rebind-off", "3:1", "7:1", "15:1"):
        cap = caps[name]
        if name == "rebind-off":
            t2 = 1.0
            m5 = 1.0
            sb = 1.0
            rho = 0.0
        else:
            r = cap["r"]
            t2 = snp_lat_q1(r, 1.0, l_snp)
            m5 = snp_lat_m5_coarse(cap["duty_dat"], t_steady, t_drain, l_snp)
            rho = min(0.95, cap["ghost"] * alpha_occ)
            sb = snp_lat_sb(rho, l_snp)
        mark = "HISTORICAL" if name == "15:1" else ""
        print(
            f"  {name:11} {fmt(t2)}  {fmt(m5,2):>9}  {fmt(sb)}  "
            f"{sb <= SNP_KILL}     {sb < T2_Q1_15_1}       "
            f"{m5 > SNP_KILL}           {mark}"
        )
        if name != "rebind-off":
            print(
                f"           hypothesis H-SNP-LAT-SB rho_wire={fmt(rho)} "
                f"E[wait_empty]={fmt(rho / max(1.0 - rho, 1e-9), 2)}  NOT measured"
            )
    print()
    print("  M-5 exclusive (coarse) is the diagnosed 15:1 killer: wait tracks T_steady+T_drain")
    print("  T2 q=1 column exists only to show why 1.5625 must not be pasted onto T3")
    print(f"  T3 night exclusive 15:1 was {T3_NIGHT_SNP_PATH}/{T3_NIGHT_MIXED} (M-5, not r1)")
    print()

    print("=== H-SNP-CAP CONTRAST (Snp storm; not default inference mix) ===")
    print("  arm         M5_1/C_snp  SB_native(~1)  note")
    for name in ("3:1", "7:1", "15:1"):
        cap = caps[name]
        c_snp_m5 = cap["duty_snp"] * f_st
        m5_cap = 1.0 / max(c_snp_m5, 1e-9)
        print(f"  {name:11} {fmt(m5_cap,2):>10}  {fmt(1.0):>13}  exclusive duty starves Snp")
    print()

    print("=== INFERENCE DAT (H-DAT-DOM; card-claim NOT measured) ===")
    print("  class          arm         C_dat_sb  T_hat/T_off  card-claim")
    for cls in ("uniform_read", "gather", "allreduce", "allgather"):
        t_off = T_OFF[cls]
        for arm in ("rebind-off", "3:1", "7:1", "15:1"):
            cap = caps[arm]
            ratio = 1.0 if arm == "rebind-off" else 1.0 / cap["c_dat"]
            print(
                f"  {cls:14} {arm:11} {fmt(cap['c_dat'])}  {fmt(ratio)}     "
                f"{'1.0 baseline' if arm == 'rebind-off' else '0.55-0.85x NOT measured'}"
            )
            if arm != "rebind-off" and cls in DAT_DOM:
                amdahl = 1.0 / (1.0 - f_dat + f_dat / cap["c_dat"])
                print(
                    f"                 amdahl f_dat={f_dat} T_amdahl/T_off="
                    f"{fmt(1.0 / amdahl)}  (hypothesis; T_off={t_off})"
                )
    print("  broadcast: H-DAT-DOM off (baseline not collapsed)")
    print("  training collectives: secondary, not a pass column")
    print()

    print("=== FOUR-ARM ATTRIBUTION (hypotheses) ===")
    print("  arm              Dat_slots   Snp_lat_rule           beats_noCC_Dat  beats_M5_Snp")
    print("  no CC            1           1.0 (1:1 bind)         —               —")
    print("  source FC        1           1.0                    no (H-SRC-FC)   n/a (Snp already 1:1)")
    print("  M-5 exclusive    1+ghost     coarse epoch wait      yes (T3 HARD-1) no (T3 15:1 KILL)")
    print("  M-5r1 SB         1+ghost-sb  empty-slot wait        hypothesis      hypothesis")
    print("  sb-off ablation must restore M-5-like Snp KILL or attribution fails")
    print("  ghost-off ablation must restore no-CC Dat makespan or attribution fails")
    print("  higher p_inj without shorter inference makespan/tail = no credit")
    print()

    print("=== HYPOTHESIS vs 1.5625 (not a claim) ===")
    sb15 = snp_lat_sb(min(0.95, caps["15:1"]["ghost"] * alpha_occ), l_snp)
    print(f"  H-SNP-LAT-SB 15:1 sparse = {fmt(sb15)}  kill_1.4={sb15 > SNP_KILL}  "
          f"below_T2_1.5625={sb15 < T2_Q1_15_1}")
    print("  H-SNP-MIX-SB: same rule; Dat steal-back tax goes to C_dat_eff_sb, not Snp lockout")
    print("  If cycle 15:1 mixed Snp >1.4× rebind-off, the arm fails — do not retune narrative")
    print()
    print("exit 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
