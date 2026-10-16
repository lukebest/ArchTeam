#!/usr/bin/env python3
"""P-0198/M-5 CRRF — slot conservation + time-mux + drain-tax model (stdlib).

See spec.md. No curve fitting. Not CBC empty-slot math.
Absolute Dat makespan only via H-DAT-DOM relative scaling of published T_off.
Cycle-level Rebind FSM / skew window is out of scope (Dr.Sim).
"""

from __future__ import annotations

import math
import sys

# ---- Envelope pins (SOURCE in comments) ----
# problems/P-0198.yaml + docs/srcfc_ca_model/data.json scheme=off
# Same T_off nails as sibling P-0198 cards.
T_OFF = {
    "uniform_read": 4403.2,   # YAML + data.json
    "uniform_write": 4834.6,  # YAML + data.json
    "broadcast": 492.0,       # data.json; YAML emphasizes goodput not makespan
    "gather": 537.2,
    "reduce": 537.2,
    "allgather": 1668.6,
    "allreduce": 990.6,
    "alltoall": 4098.0,
    # snp_path: no published ns — ratios only
}

COLLAPSED = {
    "uniform_read": True,    # peak-then-collapse narrative in YAML
    "uniform_write": False,  # YAML: platform ~5.5 TB/s
    "broadcast": False,
    "gather": True,
    "reduce": True,
    "allgather": True,
    "allreduce": True,
    "alltoall": True,
    "snp_path": False,
}

# Dat-slot-contention dominated classes for H-DAT-DOM relative makespan
DAT_DOM = {"gather", "reduce", "allgather", "allreduce", "alltoall", "uniform_read"}

# Duty scan Dat:Snp (card §4). rebind-off is the 1:1 ablation, not a ratio arm.
DUTY_SCAN = ((3, 1), (7, 1), (15, 1))
SNP_KILL = 1.4  # card §2.5 / T1: Snp makespan ≤ 1.4× rebind-off
EPOCH_MOD = 4   # 2-bit epoch

# Uniform-read goodput pins (YAML). Collapse band ~2.8–3.4 TB/s → 2800–3400 B/ns.
G_PEAK_READ = 5761.0
G_COLL_LO = 2800.0
G_COLL_HI = 3400.0


def duty_frac(r: int, s: int = 1):
    tot = r + s
    return r / tot, s / tot


def t_drain_cycles(k_circ: float, c_ring: float, n_pipe: float) -> float:
    """ARM_DRAIN→DRAIN (k_circ rings) + epoch_committed (1 ring) + bind pipe."""
    return (k_circ + 1.0) * c_ring + n_pipe


def f_steady_of(t_steady: float, t_drain: float) -> float:
    tot = t_steady + t_drain
    if tot <= 0:
        return 0.0
    return t_steady / tot


def c_dat_eff(duty_dat: float, f_steady: float, tau_sync: float, tau_bind: float):
    """Effective Dat slots. Time-mux ≠ permanent second Dat port."""
    ideal = 1.0 + duty_dat
    ghost = duty_dat * f_steady
    raw = 1.0 + ghost - tau_sync - tau_bind
    # never mint above ideal; never worse than a dedicated Dat ring
    eff = min(ideal, max(1.0, raw))
    return eff, ideal, ghost


def c_snp_eff(duty_snp: float, f_steady: float) -> float:
    return duty_snp * f_steady


def amdahl_T(t_off: float, f_dat: float, c_eff: float):
    if c_eff <= 0:
        return float("inf"), 0.0
    speedup = 1.0 / (1.0 - f_dat + f_dat / c_eff)
    return t_off / speedup, speedup


def write_ratio(c_dat: float, beta_write: float) -> float:
    c_w = 1.0 + beta_write * (c_dat - 1.0)
    if c_w <= 0:
        return float("inf")
    return 1.0 / c_w


def snp_wait(r: int, q: float) -> float:
    """H-SNP-LAT: expected wait for SNP_EPOCH under uniform arrival."""
    duty_dat = r / (r + 1.0)
    t_dat = r * q
    return duty_dat * (t_dat / 2.0)


def snp_lat_ratio(r: int, q: float, l_snp: float) -> float:
    if l_snp <= 0:
        return float("inf")
    return (l_snp + snp_wait(r, q)) / l_snp


def accept_set(local_epoch: int):
    e = local_epoch % EPOCH_MOD
    return {e, (e - 1) % EPOCH_MOD}


def mismatch_count(tag: int, local_epoch: int, n_receivers: int) -> int:
    if (tag % EPOCH_MOD) in accept_set(local_epoch):
        return 0
    return n_receivers


def fmt(x: float, nd: int = 4) -> str:
    if math.isinf(x):
        return "inf"
    return f"{x:.{nd}f}"


def prow(cols, widths):
    print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))


def main() -> int:
    print("P-0198/M-5 CRRF  physical-slot + time-mux + drain-tax model")
    print("envelope DV200 tests/soc_sim  repo lukebest/bufferless-ring-noc")
    print("SOURCE T_off: problems/P-0198.yaml + docs/srcfc_ca_model/data.json off")
    print("no silicon ±15%; no team-384dmc; no decode-*; 0.85 is pass bar not mean")
    print("time-mux ≠ permanent second Dat slot; C_dat_eff ≤ 1+duty_dat − taxes")
    print("COLL_EP / runtime hint is advisory only; correctness ignores it")
    print("this card only — no mixed conclusions with M-1 / M-2 / M-4")
    print()

    # ---- Default assumption set (named; scanned below) ----
    c_ring = 25.0            # docs/topology.md example; not an absolute-makespan pin
    k_circ = 2.0             # H-DRAIN: marker returns twice
    n_pipe = 2.0             # bind pipe 1–2
    t_steady = 20.0 * c_ring # H-FLIP: min STEADY dwell / hysteresis
    tau_sync = 0.02          # amortized SYNC/DRAIN on Req (not a predictor)
    tau_bind = 0.02          # amortized bind pipe
    f_dat = 0.70             # H-AMDAHL
    beta_write = 0.15        # H-WRITE-SYM
    q = 1.0                  # H-EPOCH-Q: fine slot TDM
    l_snp = c_ring / 2.0     # H-SNP-LAT
    lam_snp = 0.05           # H-SNP-SPARSE offered Snp slot-demand / T_off
    theta_dat = 0.70
    theta_snp = 2.0
    n_nodes = 12             # DV200 top; probe scale only

    t_drain = t_drain_cycles(k_circ, c_ring, n_pipe)
    f_st = f_steady_of(t_steady, t_drain)
    tau_drain = 1.0 - f_st

    print("=== ASSUMPTIONS (labeled; not silicon) ===")
    print(f"H-SLOT S_phys=1 per direction×physical ring")
    print(f"H-DRAIN k_circ={k_circ} C_ring={c_ring} n_pipe={n_pipe} T_drain={fmt(t_drain,1)}")
    print(f"H-FLIP T_steady={fmt(t_steady,1)} f_steady={fmt(f_st)} tau_drain={fmt(tau_drain)}")
    print(f"H-TMUX tau_sync={tau_sync} tau_bind={tau_bind}")
    print(f"H-AMDAHL f_dat={f_dat}")
    print(f"H-WRITE-SYM beta_write={beta_write}")
    print(f"H-EPOCH-Q q={q}")
    print(f"H-SNP-LAT L_snp={fmt(l_snp,1)}  H-SNP-SPARSE lambda_snp={lam_snp}")
    print(f"H-PRESSURE theta_dat={theta_dat} theta_snp={theta_snp}")
    print(f"H-COMMIT epoch_committed is all-node AND barrier before new-gen inject")
    print(f"H-STAGING mismatch path = depth-1 holding (not a highway queue)")
    print()

    # ---- Conservation / capacity ----
    print("=== CONSERVATION + CAPACITY (exact slot; taxed time-mux) ===")
    print("  arm         duty_dat  C_ideal  C_ghost  C_dat_eff  C_snp_eff  <=ideal  <2  untaxed_double")
    capacity = {}
    for name, r, s in (("rebind-off", 0, 1), ("3:1", 3, 1), ("7:1", 7, 1), ("15:1", 15, 1)):
        if name == "rebind-off":
            d_dat, d_snp = 0.0, 1.0
            c_eff, ideal, ghost = 1.0, 1.0, 0.0
            c_s = 1.0
        else:
            d_dat, d_snp = duty_frac(r, s)
            c_eff, ideal, ghost = c_dat_eff(d_dat, f_st, tau_sync, tau_bind)
            c_s = c_snp_eff(d_snp, f_st)
        capacity[name] = {
            "r": r,
            "duty_dat": d_dat,
            "duty_snp": d_snp,
            "c_dat": c_eff,
            "c_snp": c_s,
            "ideal": ideal,
        }
        leq = c_eff <= ideal + 1e-12
        lt2 = c_eff < 2.0 - 1e-12
        taxes = (0.0 if name == "rebind-off" else tau_drain + tau_sync + tau_bind)
        untaxed = (c_eff + 1e-12 >= ideal) and taxes <= 1e-12 and name != "rebind-off"
        print(
            f"  {name:11} {d_dat:8.4f}  {ideal:7.4f}  {ghost:7.4f}  {c_eff:9.4f}  "
            f"{c_s:9.4f}  {leq}     {lt2} {untaxed}"
        )
    print("CONSTRAINT: time-mux ≠ second Dat port; C_dat_eff ≤ 1+duty_dat after drain+SYNC+pipe")
    print("CONSTRAINT: flag_untaxed_double must be False on every on-arm")
    print()

    # ---- Epoch barrier / accept set / mismatch ----
    print("=== EPOCH BARRIER + ACCEPT SET + MISMATCH (H-COMMIT / H-MISMATCH0) ===")
    late_e, early_e = 5, 6
    print(f"  accept(late E={late_e % EPOCH_MOD})={sorted(accept_set(late_e))}")
    print(f"  accept(early E+1={early_e % EPOCH_MOD})={sorted(accept_set(early_e))}")
    inter = accept_set(late_e) & accept_set(early_e)
    print(f"  intersection (old gen still OK both sides)={sorted(inter)}")
    new_tag = early_e
    mm_late_new = mismatch_count(new_tag, late_e, n_nodes)
    mm_late_old = mismatch_count(late_e, late_e, n_nodes)
    print(f"  new-gen tag={new_tag % EPOCH_MOD} at late node: mismatch_receivers={mm_late_new} (must be >0)")
    print(f"  old-gen tag={late_e % EPOCH_MOD} at late node: mismatch_receivers={mm_late_old} (must be 0)")

    # H-COMMIT held: no late nodes when new inject starts
    mm_held = mismatch_count(new_tag, early_e, 0)  # 0 late receivers
    # violated: all still late
    mm_viol = mismatch_count(new_tag, late_e, n_nodes)
    print(f"  H-COMMIT held (0 late at new inject): bind_mismatch_redirect={mm_held}  target≈0? {mm_held == 0}")
    print(f"  H-COMMIT violated (late still on E):   bind_mismatch_redirect={mm_viol}  must be >0? {mm_viol > 0}")
    print("  out-of-accept-set path = NACK / re-inject on home Dat ring; no silent drop; no permanent stall")
    print("  steady-state target bind_mismatch_redirect==0; nonzero must be explained")
    print()

    # ---- Phase arm / hint advisory ----
    print("=== PHASE ARM (local pressure only; hint advisory) ===")

    def request_duty(rho_ema: float, snp_pend: float):
        if snp_pend >= theta_snp:
            return "3:1"
        if rho_ema >= theta_dat and snp_pend < theta_snp:
            return "7:1"
        return "3:1"

    cases = (
        ("dat_high_snp_low", 0.90, 0.0),
        ("dat_high_snp_high", 0.90, 4.0),
        ("dat_low_snp_low", 0.40, 0.0),
    )
    for label, rho, pend in cases:
        d0 = request_duty(rho, pend)
        d_hint = request_duty(rho, pend)  # hint does not enter correctness / duty request
        print(
            f"  {label:20} rho_ema={rho:.2f} snp_pend={pend:.1f} "
            f"duty={d0}  duty_with_COLL_EP_hint={d_hint}  same={d0 == d_hint}"
        )
    print("  correctness_depends_on_hint=False  (drain/flip/barrier/accept/redirect unchanged)")
    print("  SYNC aligns epoch / carries DRAIN and epoch_committed; SYNC ≠ traffic prediction")
    print()

    # ---- Per-class Dat / write / broadcast ----
    print("=== PER-CLASS (no averaging; no Dat-mean hiding Snp) ===")
    widths = (14, 8, 8, 10, 10, 12, 10, 14)
    prow(
        ("class", "collaps", "arm", "C_dat", "T_off", "T_hat", "T_hat/T_off", "card-claim"),
        widths,
    )
    card_claim = {
        "gather": "0.55-0.85x",
        "reduce": "0.55-0.85x",
        "allgather": "0.55-0.85x",
        "allreduce": "0.55-0.85x",
        "alltoall": "0.55-0.85x",
        "uniform_read": "0.55-0.85x",
        "broadcast": "n/a-neutral",
        "uniform_write": "0.85-1.05x",
        "snp_path": "<=1.4x kill",
    }
    dat_ratios = {arm: {} for arm in capacity}

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
        for arm in ("rebind-off", "3:1", "7:1", "15:1"):
            cap = capacity[arm]
            if cls in DAT_DOM:
                if arm == "rebind-off":
                    ratio = 1.0
                    t_hat = t_off
                else:
                    ratio = 1.0 / cap["c_dat"]
                    t_hat = t_off * ratio
                prow(
                    (
                        cls,
                        str(COLLAPSED[cls]),
                        arm,
                        fmt(cap["c_dat"]),
                        fmt(t_off, 1),
                        fmt(t_hat, 1),
                        fmt(ratio),
                        card_claim[cls],
                    ),
                    widths,
                )
                dat_ratios[arm][cls] = ratio
                if arm != "rebind-off":
                    t_a, sp = amdahl_T(t_off, f_dat, cap["c_dat"])
                    print(
                        f"           amdahl f_dat={f_dat} C_dat={fmt(cap['c_dat'])} "
                        f"T_amdahl={fmt(t_a,1)} T_amdahl/T_off={fmt(t_a / t_off)} "
                        f"speedup={fmt(sp)}  (card-claim column is NOT measured)"
                    )
            elif cls == "uniform_write":
                if arm == "rebind-off":
                    ratio = 1.0
                    t_hat = t_off
                else:
                    ratio = write_ratio(cap["c_dat"], beta_write)
                    t_hat = t_off * ratio
                prow(
                    (
                        cls,
                        str(COLLAPSED[cls]),
                        arm,
                        fmt(cap["c_dat"]),
                        fmt(t_off, 1),
                        fmt(t_hat, 1),
                        fmt(ratio),
                        card_claim[cls],
                    ),
                    widths,
                )
                dat_ratios[arm][cls] = ratio
            else:
                # broadcast: not collapsed; H-DAT-DOM off
                prow(
                    (
                        cls,
                        str(COLLAPSED[cls]),
                        arm,
                        fmt(cap["c_dat"]),
                        fmt(t_off, 1),
                        "n/a",
                        "n/a",
                        card_claim[cls],
                    ),
                    widths,
                )
    print()

    # ---- Snp makespan + completions (mandatory; never fold into Dat mean) ----
    print("=== SNP PATH (mandatory endpoints; 1.4× is a kill hypothesis) ===")
    print("  H-SNP-LAT = mixed/sparse per-message wait; H-SNP-CAP = saturated storm (expose-only)")
    print(
        f"  arm         duty_snp  C_snp  E[wait]  T_lat/T_off  kill_1.4  "
        f"T_cap/T_off  N_comp_on/off  comp_drop"
    )
    # Use gather as the Dat-heavy window that Snp rides on (same T_off scale).
    t_off_ref = T_OFF["gather"]
    snp_rows = []
    for arm in ("rebind-off", "3:1", "7:1", "15:1"):
        cap = capacity[arm]
        if arm == "rebind-off":
            ewait = 0.0
            r_lat = 1.0
            r_cap = 1.0
            t_hat_dat = t_off_ref
            n_off = min(lam_snp * t_off_ref, 1.0 * t_off_ref)
            n_on = n_off
        else:
            ewait = snp_wait(cap["r"], q)
            r_lat = snp_lat_ratio(cap["r"], q, l_snp)
            r_cap = (1.0 / cap["c_snp"]) if cap["c_snp"] > 0 else float("inf")
            t_hat_dat = t_off_ref * (1.0 / cap["c_dat"])
            n_off = min(lam_snp * t_off_ref, 1.0 * t_off_ref)
            n_on = min(lam_snp * t_off_ref, cap["c_snp"] * t_hat_dat)
        kill = r_lat > SNP_KILL
        drop = n_on + 1e-12 < n_off
        snp_rows.append((arm, r_lat, kill, drop, n_on, n_off, r_cap))
        print(
            f"  {arm:11} {cap['duty_snp']:8.4f}  {fmt(cap['c_snp'])}  {fmt(ewait,2)}  "
            f"{fmt(r_lat)}     {kill}      {fmt(r_cap)}     "
            f"{fmt(n_on,1)}/{fmt(n_off,1)}   {drop}"
        )
    print("  kill hypothesis: H-SNP-LAT T_snp/T_off > 1.4 → that duty FAILS (do not hide behind Dat mean)")
    print("  H-SNP-CAP is not the mixed-load main column; it shows saturated Snp would blow 1.4×")
    print("  completions: Dat-heavy fixed work keeps Dat completions=issued; Snp listed separately")
    print()

    # ---- Ablation HARD-1 ----
    print("=== ABLATION rebind-off vs duty scan (gather exemplar; HARD-1) ===")
    t_off = T_OFF["gather"]
    t_off_arm = t_off  # C=1
    print(f"  {'arm':11} C_dat    T_hat    T_hat/T_off  Dat_better_than_off?")
    t_on_min = None
    for arm in ("rebind-off", "3:1", "7:1", "15:1"):
        c = capacity[arm]["c_dat"]
        ratio = 1.0 / c
        t_hat = t_off * ratio
        worse = t_hat > t_off_arm + 1e-12 if arm != "rebind-off" else False
        if arm != "rebind-off":
            t_on_min = t_hat if t_on_min is None else min(t_on_min, t_hat)
        print(
            f"  {arm:11} {fmt(c)}  {fmt(t_hat,1)}  {fmt(ratio)}     "
            f"{'n/a' if arm == 'rebind-off' else (not worse)}"
        )
    print(
        f"HARD-1 probe: rebind-off T_hat ({fmt(t_off_arm,1)}) > best on-arm T_hat "
        f"({fmt(t_on_min,1)})? {t_off_arm > t_on_min}  (must be true to attribute Dat win)"
    )
    print("Snp column is the control baseline on the same arms — see SNP PATH table")
    print()

    # ---- Sensitivity ----
    print("=== SENSITIVITY (two most sensitive pairs) ===")
    print("-- (T_steady, k_circ) → f_steady / C_dat_eff / Dat H-DAT-DOM at 7:1 --")
    d7, _ = duty_frac(7, 1)
    for ts_mult in (2.0, 5.0, 10.0, 20.0, 50.0):
        for kc in (2.0, 4.0):
            td = t_drain_cycles(kc, c_ring, n_pipe)
            ts = ts_mult * c_ring
            fs = f_steady_of(ts, td)
            ce, _, _ = c_dat_eff(d7, fs, tau_sync, tau_bind)
            print(
                f"  T_steady={ts_mult:.0f}*C_ring k_circ={kc:.0f}  f_steady={fmt(fs)}  "
                f"C_dat_eff={fmt(ce)}  T_hat/T_off={fmt(1.0 / ce)}"
            )
    print("-- (q, L_snp) → H-SNP-LAT ratio vs 1.4× kill at each duty --")
    for qi in (1.0, 2.0, 4.0, c_ring):
        for ls in (c_ring / 4.0, c_ring / 2.0, c_ring):
            bits = []
            for r in (3, 7, 15):
                rr = snp_lat_ratio(r, qi, ls)
                bits.append(f"{r}:1={fmt(rr)}{'KILL' if rr > SNP_KILL else 'ok':>4}")
            print(f"  q={qi:5.1f} L_snp={ls:5.1f}  " + "  ".join(bits))
    print()
    print("most sensitive: (T_steady/k_circ) sets drain tax and whether Dat stays in 0.55-0.85")
    print("most sensitive: (q, L_snp) sets whether 7:1/15:1 survive the Snp 1.4× kill")
    print()

    # ---- Magic-gap flags ----
    print("=== MAGIC-GAP FLAG ===")
    ce7 = capacity["7:1"]["c_dat"]
    ratio7 = 1.0 / ce7
    t_a7, _ = amdahl_T(1.0, f_dat, ce7)
    in_band_dom = 0.55 <= ratio7 <= 0.85
    in_band_am = 0.55 <= t_a7 <= 0.85
    print(
        f"7:1 default H-DAT-DOM T_hat/T_off={fmt(ratio7)} "
        f"in card-claim[0.55,0.85]? {in_band_dom}"
    )
    print(
        f"7:1 default Amdahl T_hat/T_off={fmt(t_a7)} "
        f"in card-claim[0.55,0.85]? {in_band_am}"
    )
    if not in_band_dom:
        print(
            "GAP: card 0.55-0.85x Dat-heavy not reached under H-DAT-DOM without "
            "raising f_steady or cutting taxes; do not treat card interval as model output"
        )
    wr = write_ratio(ce7, beta_write)
    print(f"7:1 uniform_write T_hat/T_off={fmt(wr)} card-claim[0.85,1.05]? {0.85 <= wr <= 1.05}")

    r15 = [row for row in snp_rows if row[0] == "15:1"][0]
    r7 = [row for row in snp_rows if row[0] == "7:1"][0]
    print(
        f"7:1  H-SNP-LAT={fmt(r7[1])} kill={r7[2]}  15:1 H-SNP-LAT={fmt(r15[1])} kill={r15[2]}"
    )
    if not r15[2]:
        print(
            "GAP: 15:1 did not trip Snp 1.4× under default (q,L_snp); "
            "coarse q or short L_snp must still be scanned — do not publish only 7:1"
        )
    if r7[2]:
        print(
            "GAP: 7:1 already fails Snp 1.4× under default H-SNP-LAT; "
            "sweet-spot narrative is assumption-bound"
        )
    print(
        "GAP: H-SNP-CAP ratios ≫ 1.4 at 7:1/15:1 — if Snp is not sparse the kill hyp fires; "
        "do not claim Dat win on a Snp-saturated fabric"
    )
    print(
        "GAP: near-double Dat without tax is forbidden by construction "
        f"(7:1 C_dat_eff={fmt(ce7)} vs ideal {fmt(capacity['7:1']['ideal'])})"
    )
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
