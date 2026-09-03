#!/usr/bin/env python3
"""P-0103/M-4 CR-MRDR (G[23]) — T2 first-principles occupancy model.

Self-contained. Python 3. stdlib only. No external files. No H100.
Absolute BW is a μ_d-assumption column (not printed). Clock / μ_d / DRAM /
row-buffer UNKNOWN. Envelope source: TEAM-SPEC / problem YAML. No H100.

Runs three mapper arms on the same AP (not a second old-card file):
  current   LIVE_DIGIT on,  TRIT_INJ on
  trit_off  LIVE_DIGIT on,  TRIT_INJ off
  ablation  d[i]=G[i],      TRIT_INJ on   (must reproduce n_DMC=6 and 3)

Primary floorplan is die=DMC[8]. die_env=DMC/192 is contrast only.
"""

from __future__ import annotations

import statistics
import sys

# ---------------------------------------------------------------------------
# Envelope — problems/P-0103.yaml
# ---------------------------------------------------------------------------
N_DMC = 384  # 2^7 * 3
N_BANK = 18432  # 2^11 * 9
N_DIE = 2
N_DMC_PER_DIE_ENVELOPE = N_DMC // N_DIE  # 192; contrast decode only
N_HA_PER_DIE = 96
N_PIPE_PER_HA = 2
GRAIN_BYTES = 512  # 2^9
GRAIN_SHIFT = 9  # G = A[63:9]
WORKING_SET_BYTES = 8 * (1 << 30)  # 8 GiB
WORKING_SET_4GIB_BYTES = 4 * (1 << 30)  # G[23] frozen (Prof. Sys T1)
N_CORE = 120
OUTSTANDING_PER_CORE = 128
N_INFLIGHT = N_CORE * OUTSTANDING_PER_CORE  # Little: 15360

# Mixed-radix decode — mechanisms/P-0103/M-4.md §2.2
RADIX_TRIT = 3
N_GROUP_BITS = 7  # q[6:0] → 2^7 = 128 groups
N_BANK_Q_BITS = 4  # q[10:7] → 2^4 = 16
N_DIGITS = 11  # i = 0..10
MID_TAP_STRIDE = 11  # G[i+11]; i+11 ∈ {11..21}, never 23
HIGH_TAP = 23  # G[23] = A[32]; NOT G[21]
GROUP_N = 1 << N_GROUP_BITS  # 128
BANK_Q_N = 1 << N_BANK_Q_BITS  # 16
BANKS_PER_DMC = RADIX_TRIT * BANK_Q_N  # 48
N_DIGIT_MSB = N_DIGITS - 1  # 10; q[j] = d[10-j]

# Floorplan bit slices — card §2.2, IMPLEMENT AS WRITTEN
DIE_BIT = 8  # die = DMC[8] cuts 384 into 256+128, NOT envelope 192+192
HA_SHIFT = 1  # HA = DMC[7:1]
HA_WIDTH = 7
PIPE_BIT = 0
DIE0_DMC_UNDER_BIT8 = 1 << DIE_BIT  # 256
DIE1_DMC_UNDER_BIT8 = N_DMC - DIE0_DMC_UNDER_BIT8  # 128
PACK_RATIO_FAIL = 3 / 2  # die issue ratio ≥ 1.5 → n_DMC=384 is not BW success

# Fold (H0_2==3)?0:H0_2 — 2b value 0b11 maps to 0; histogram {2,1,1}
FOLD_WIDTH = 2
FOLD_ILLEGAL = (1 << FOLD_WIDTH) - 1  # 3
H0_HI = (16, 19)  # ⊕ G[19:16]
H0_LO = (12, 15)  # ⊕ G[15:12]
H1_HI = (8, 11)  # ⊕ G[11:8]
H1_LO = (4, 7)  # ⊕ G[7:4]

# Unweighted 7-term mod 3 — NOT G mod 9
T0_TAPS = (0, 3, 6, 10, 13, 16, 19)
T1_TAPS = (1, 4, 7, 11, 14, 17, 20)

# Ablation constraints (T1; later numbers void if these miss)
ABLATION_N_DMC_1_5_MIB = 6
ABLATION_N_DMC_2_MIB = 3

# S set — never averaged. δ in grains = S / 512.
# 1.5MiB = 3·2^19 B → δ = 3·2^10. 2MiB = 2^21 B → δ = 2^12.
S_SET = (
    ("512B", 1),
    ("1KiB", 1 << 1),
    ("1536B", RADIX_TRIT),
    ("3KiB", RADIX_TRIT << 1),
    ("4608B", RADIX_TRIT * RADIX_TRIT),  # 9; G mod 9 frozen ≠ XOR digits frozen
    ("12KiB", (RADIX_TRIT << 3)),  # 24 = 3·2^3
    ("1.5MiB", RADIX_TRIT << 10),  # 3072; G[9:0] frozen, U:=G>>10 steps +3
    ("2MiB", 1 << 12),  # 4096; G[11:0] frozen
)
KILLER_NAMES = ("1.5MiB", "2MiB")

# Mapper arms: same circuit, switches. Not a second old-card implementation.
ARM_CURRENT = "current"  # LIVE_DIGIT on, TRIT_INJ on
ARM_TRIT_OFF = "trit_off"  # LIVE_DIGIT on, TRIT_INJ off
ARM_ABLATION = "ablation"  # d[i]=G[i], TRIT_INJ on
ARMS = (ARM_CURRENT, ARM_TRIT_OFF, ARM_ABLATION)


def grain_count(ws_bytes: int) -> int:
    return ws_bytes >> GRAIN_SHIFT


NIBBLE_MASK = (1 << 4) - 1  # 4b window for H0/H1 fold


def xor_nibble(g: int, shift: int) -> int:
    """Parity of g[shift+3:shift]. 4b XOR-reduce (card fold)."""
    x = (g >> shift) & NIBBLE_MASK
    x ^= x >> 2
    x ^= x >> 1
    return x & 1


def fold_pair(g: int, hi_lo: int, lo_lo: int) -> int:
    """2b fold then (v==3)?0:v. Histogram {2,1,1} on a uniform 2b source."""
    two = (xor_nibble(g, hi_lo) << 1) | xor_nibble(g, lo_lo)
    return 0 if two == FOLD_ILLEGAL else two


def trit_sum(g: int, taps: tuple[int, ...]) -> int:
    acc = 0
    for tap in taps:
        acc += (g >> tap) & 1
    return acc % RADIX_TRIT


def _digit(g: int, i: int, live_digit: bool, g23: int) -> int:
    bit = (g >> i) & 1
    if live_digit:
        bit ^= (g >> (i + MID_TAP_STRIDE)) & 1
        bit ^= g23
    return bit


def map_address(g: int, live_digit: bool, trit_inj: bool) -> tuple[int, int, int, int, int, int]:
    """Bit-exact CR-MRDR. Returns (DMC, q_group, t0p, die_bit8, die_env, trit).

    d[i] = G[i] ⊕ G[i+11] ⊕ G[23]   (or G[i] if ablation)
    q[j] = d[10-j]
    q[6:0] integer uses q[0] as LSB (= d[10] under reversal)
    t0 = unweighted 7-term mod 3  (t1 same form; bank not scored here)
    H0 = fold(G[19:12]), H1 = fold(G[11:4])
    t0' = (t0+H0) mod 3 if TRIT_INJ else t0
    DMC = t0' + 3·q[6:0]
    die = DMC[8]          # primary; do not replace with /192
    die_env = DMC / 192   # contrast only
    """
    g23 = (g >> HIGH_TAP) & 1
    # q[j] = d[10-j]; unroll group bits to keep the AP loop branch-light
    q_group = (
        _digit(g, 10, live_digit, g23)
        | (_digit(g, 9, live_digit, g23) << 1)
        | (_digit(g, 8, live_digit, g23) << 2)
        | (_digit(g, 7, live_digit, g23) << 3)
        | (_digit(g, 6, live_digit, g23) << 4)
        | (_digit(g, 5, live_digit, g23) << 5)
        | (_digit(g, 4, live_digit, g23) << 6)
    )
    t0 = trit_sum(g, T0_TAPS)
    if trit_inj:
        t0p = (t0 + fold_pair(g, H0_HI[0], H0_LO[0])) % RADIX_TRIT
    else:
        t0p = t0
    dmc = t0p + RADIX_TRIT * q_group
    die_bit8 = (dmc >> DIE_BIT) & 1
    die_env = dmc // N_DMC_PER_DIE_ENVELOPE
    return dmc, q_group, t0p, die_bit8, die_env, t0p


def arm_flags(arm: str) -> tuple[bool, bool]:
    if arm == ARM_CURRENT:
        return True, True
    if arm == ARM_TRIT_OFF:
        return True, False
    if arm == ARM_ABLATION:
        return False, True
    raise ValueError(arm)


def walk(delta_grain: int, ws_bytes: int, arm: str, with_corr: bool = False) -> dict:
    """Count |q|, n_DMC, die issue, trit traffic on a sequential AP.

    Uniqueness uses bitsets of size 128 / 384 (envelope), not hash sets.
    Correlation sums are optional — only killer APs need them.
    """
    live_digit, trit_inj = arm_flags(arm)
    g_hi = grain_count(ws_bytes)
    q_hit = bytearray(GROUP_N)
    dmc_hit = bytearray(N_DMC)
    dmc_die8_0 = bytearray(N_DMC)
    dmc_die8_1 = bytearray(N_DMC)
    dmc_env_0 = bytearray(N_DMC)
    dmc_env_1 = bytearray(N_DMC)
    issue_die8 = [0, 0]
    issue_die_env = [0, 0]
    trit_issue = [0, 0, 0]
    ha_ge_n = 0
    n_pts = 0
    q_sum = [0] * N_GROUP_BITS
    q_pair = [[0] * N_GROUP_BITS for _ in range(N_GROUP_BITS)]
    q_g23 = [0] * N_GROUP_BITS
    g23_sum = 0
    ha_mask = (1 << HA_WIDTH) - 1

    g = 0
    while g < g_hi:
        dmc, q_group, t0p, die8, die_env, _ = map_address(g, live_digit, trit_inj)
        q_hit[q_group] = 1
        dmc_hit[dmc] = 1
        if die8:
            dmc_die8_1[dmc] = 1
        else:
            dmc_die8_0[dmc] = 1
        issue_die8[die8] += 1
        if die_env == 0:
            dmc_env_0[dmc] = 1
            issue_die_env[0] += 1
        elif die_env == 1:
            dmc_env_1[dmc] = 1
            issue_die_env[1] += 1
        trit_issue[t0p] += 1
        if ((dmc >> HA_SHIFT) & ha_mask) >= N_HA_PER_DIE:
            ha_ge_n += 1
        if with_corr:
            g23 = (g >> HIGH_TAP) & 1
            g23_sum += g23
            b = 0
            while b < N_GROUP_BITS:
                qi = (q_group >> b) & 1
                q_sum[b] += qi
                q_g23[b] += qi * g23
                c = 0
                while c < N_GROUP_BITS:
                    q_pair[b][c] += qi * ((q_group >> c) & 1)
                    c += 1
                b += 1
        n_pts += 1
        g += delta_grain

    n_q = sum(q_hit)
    n_dmc = sum(dmc_hit)
    i0, i1 = issue_die8[0], issue_die8[1]
    ratio = (i0 / i1) if i1 else float("inf")
    unique_die8 = (sum(dmc_die8_0), sum(dmc_die8_1))
    unique_env = (sum(dmc_env_0), sum(dmc_env_1))
    pack_fail = (
        ha_ge_n > 0
        or unique_die8[0] != N_DMC_PER_DIE_ENVELOPE
        or unique_die8[1] != N_DMC_PER_DIE_ENVELOPE
    )
    return {
        "n_pts": n_pts,
        "n_q": n_q,
        "n_dmc": n_dmc,
        "issue_die8": (i0, i1),
        "ratio_die8": ratio,
        "unique_die8": unique_die8,
        "issue_die_env": tuple(issue_die_env),
        "unique_die_env": unique_env,
        "trit_issue": tuple(trit_issue),
        "ha_ge96": ha_ge_n,
        "pack_fail": pack_fail,
        "q_sum": q_sum,
        "q_pair": q_pair,
        "q_g23": q_g23,
        "g23_sum": g23_sum,
    }


def pearson(n: int, sum_x: int, sum_y: int, sum_xy: int) -> float:
    """Sample correlation from bit sums. Sourced: Pearson product-moment."""
    if n <= 1:
        return float("nan")
    num = n * sum_xy - sum_x * sum_y
    den_x = n * sum_x - sum_x * sum_x
    den_y = n * sum_y - sum_y * sum_y
    # den_* = n * Σx^2 - (Σx)^2 with x∈{0,1} so Σx^2=Σx
    if den_x <= 0 or den_y <= 0:
        return float("nan")
    return num / (den_x ** 0.5 * den_y ** 0.5)


def fmt_pair(a: int, b: int) -> str:
    return f"{a}:{b}"


def classify(arm: str, n_q: int, n_dmc: int) -> str:
    if arm == ARM_ABLATION:
        return "ablation (expect 6 / 3)"
    if arm == ARM_TRIT_OFF:
        if n_dmc >= N_DMC:
            return "VOID: trit-off reached 384 (trit stealing 6→384)"
        if n_q < GROUP_N:
            return "group-index failure (|q|<128)"
        if n_dmc > GROUP_N:
            return f"trit-off: |q|=128 but n_DMC={n_dmc} not ≈128 (t0 walks; H0 not the only ×3)"
        return "trit-off (expect |q|=128, n_DMC≈128)"
    # current
    if n_dmc < GROUP_N:
        return "group-index failure (n_DMC<128)"
    if n_dmc < N_DMC:
        return "trit failure (128≤n_DMC<384)"
    return "current target (|q|=128 and n_DMC=384)"


def print_row(s_name: str, arm: str, r: dict) -> None:
    i0, i1 = r["issue_die8"]
    e0, e1 = r["issue_die_env"]
    t0, t1, t2 = r["trit_issue"]
    bw_note = ""
    if r["n_dmc"] == N_DMC and r["ratio_die8"] >= PACK_RATIO_FAIL:
        bw_note = "  n_DMC=384 NOT BW success (die ratio≥1.5)"
    pack = "PACK_FAIL" if r["pack_fail"] else "pack_ok"
    print(
        f"{s_name:<8} {arm:<9} "
        f"|q|={r['n_q']:<4} n_DMC={r['n_dmc']:<4} "
        f"die8 {fmt_pair(i0, i1):<12} ratio={r['ratio_die8']:.3f} "
        f"uniq8={fmt_pair(*r['unique_die8']):<8} "
        f"die_env {fmt_pair(e0, e1):<12} uniq_env={fmt_pair(*r['unique_die_env']):<8} "
        f"trit={t0}/{t1}/{t2} "
        f"HA≥{N_HA_PER_DIE}:{r['ha_ge96']} {pack} "
        f"{classify(arm, r['n_q'], r['n_dmc'])}"
        f"{bw_note}"
    )


def print_corr(title: str, r: dict) -> None:
    n = r["n_pts"]
    print(f"  {title}  n={n}  corr(q[i], G[{HIGH_TAP}]) and pairwise q-bit (Pearson)")
    bits = " ".join(f"q{i}" for i in range(N_GROUP_BITS))
    print(f"    i      corr(q[i],G[{HIGH_TAP}])")
    i = 0
    while i < N_GROUP_BITS:
        c = pearson(n, r["q_sum"][i], r["g23_sum"], r["q_g23"][i])
        print(f"    q[{i}]  {c:+.4f}")
        i += 1
    print(f"    pairwise  {bits}")
    i = 0
    while i < N_GROUP_BITS:
        cells = []
        j = 0
        while j < N_GROUP_BITS:
            c = pearson(n, r["q_sum"][i], r["q_sum"][j], r["q_pair"][i][j])
            cells.append(f"{c:+.2f}" if c == c else "  nan")
            j += 1
        print(f"    q[{i}]     " + " ".join(cells))
        i += 1


def little_line(n_dmc: int) -> str:
    # Little (1961): L = λW. Closed system of N_INFLIGHT tokens.
    # per-DMC occupancy = N_INFLIGHT / n_DMC. Not measured BW.
    if n_dmc == 0:
        return "undef"
    return f"{N_INFLIGHT}/{n_dmc} = {N_INFLIGHT / n_dmc:.4f} outstanding/DMC"


def main() -> int:
    print("P-0103/M-4 CR-MRDR T2 occupancy model", flush=True)
    print("void: frozen-window MRDR and G[21] draft. Independent of batch A.")
    print(
        f"envelope: N_DMC={N_DMC} N_bank={N_BANK} "
        f"{N_DIE}×{N_DMC_PER_DIE_ENVELOPE} DMC/die × {N_HA_PER_DIE} HA × {N_PIPE_PER_HA} pipe  "
        f"grain={GRAIN_BYTES}B W={WORKING_SET_BYTES}B  "
        f"{N_CORE} cores × {OUTSTANDING_PER_CORE} outstanding = {N_INFLIGHT}"
    )
    print(
        "source: TEAM-SPEC / problem YAML. "
        "clock / μ_d / DRAM / row-buffer: UNKNOWN. "
        "absolute BW = μ_d assumption (not printed). "
        "0.85 is a pass line, not a mean. no H100. no ±15% vs silicon."
    )
    print(
        f"mapper: d[i]=G[i]⊕G[i+{MID_TAP_STRIDE}]⊕G[{HIGH_TAP}]  "
        f"q[j]=d[{N_DIGIT_MSB}-j]  DMC=t0'+{RADIX_TRIT}·q[6:0]  "
        f"die=DMC[{DIE_BIT}] (primary)  die_env=DMC/{N_DMC_PER_DIE_ENVELOPE} (contrast)"
    )
    print(
        f"Little: {N_INFLIGHT}/{N_DMC} ≈ {N_INFLIGHT / N_DMC:.4f} vs "
        f"{N_INFLIGHT}/{ABLATION_N_DMC_1_5_MIB} = "
        f"{N_INFLIGHT / ABLATION_N_DMC_1_5_MIB:.4f} at n_DMC=6"
    )
    print(
        f"X_rel occupancy (not BW): vs mod-N {GROUP_N} is ×{N_DMC // GROUP_N}; "
        f"vs old circuit {ABLATION_N_DMC_1_5_MIB} is ×{N_DMC // ABLATION_N_DMC_1_5_MIB}"
    )
    hist_w = (2, 1, 1)
    hist_min_mean = min(hist_w) / statistics.mean(hist_w)
    print(
        f"{{2,1,1}} trit-class: min/mean = {min(hist_w)}/{statistics.mean(hist_w):.4f} "
        f"= {hist_min_mean:.4f} even if n_DMC={N_DMC} "
        f"(occupancy; BW 0.85 is a pass line, not a mean)"
    )
    print()

    delta = {name: dg for name, dg in S_SET}
    killers: dict[tuple[str, str], dict] = {}

    print("--- KILLER STRIDES (separate columns; never averaged) ---", flush=True)
    print(
        f"{'S':<8} {'arm':<9} metrics  "
        f"die=DMC[{DIE_BIT}] issue + unique   contrast die_env=DMC/{N_DMC_PER_DIE_ENVELOPE}"
    )
    for s_name in KILLER_NAMES:
        for arm in ARMS:
            r = walk(delta[s_name], WORKING_SET_BYTES, arm, with_corr=(arm == ARM_CURRENT))
            killers[(s_name, arm)] = r
            print_row(s_name, arm, r)
    print()

    # Ablation constraints — later numbers void if these miss Archi's circuit
    a15 = killers[("1.5MiB", ARM_ABLATION)]["n_dmc"]
    a2 = killers[("2MiB", ARM_ABLATION)]["n_dmc"]
    assert a15 == ABLATION_N_DMC_1_5_MIB, (
        f"ablation 1.5MiB n_DMC={a15}, expected {ABLATION_N_DMC_1_5_MIB}; "
        "later numbers void (did not hit Archi's circuit)"
    )
    assert a2 == ABLATION_N_DMC_2_MIB, (
        f"ablation 2MiB n_DMC={a2}, expected {ABLATION_N_DMC_2_MIB}; "
        "later numbers void (did not hit Archi's circuit)"
    )
    print(
        f"ASSERT OK: ablation d[i]=G[i] → n_DMC={a15} at 1.5MiB, "
        f"n_DMC={a2} at 2MiB"
    )
    print()

    print("--- S SET (current arm only; rows never averaged) ---", flush=True)
    for s_name, dg in S_SET:
        if s_name in KILLER_NAMES:
            r = killers[(s_name, ARM_CURRENT)]
        else:
            r = walk(dg, WORKING_SET_BYTES, ARM_CURRENT)
        print_row(s_name, ARM_CURRENT, r)
        if s_name == "4608B":
            print(
                "         note: δ=9 so G mod 9 frozen; XOR digits are not "
                "required to freeze (do not substitute G mod 9 for |q|)"
            )
    print()

    print("--- SENSITIVITY: G[23] frozen (W=4GiB) vs live (W=8GiB), current ---")
    for s_name in KILLER_NAMES:
        r4 = walk(delta[s_name], WORKING_SET_4GIB_BYTES, ARM_CURRENT, with_corr=False)
        r8 = killers[(s_name, ARM_CURRENT)]
        print(
            f"{s_name:<8} W=4GiB |q|={r4['n_q']} n_DMC={r4['n_dmc']}  "
            f"W=8GiB |q|={r8['n_q']} n_DMC={r8['n_dmc']}  "
            f"(≤4GiB / 120 cores same phase: does |q| stay {GROUP_N}?)"
        )
        if r4["n_q"] < GROUP_N:
            print(f"         4GiB: |q| dropped below {GROUP_N} with G[{HIGH_TAP}] frozen")
    print()

    print("--- SENSITIVITY: TRIT_INJ on/off at 8GiB (already in killer matrix) ---")
    for s_name in KILLER_NAMES:
        on = killers[(s_name, ARM_CURRENT)]
        off = killers[(s_name, ARM_TRIT_OFF)]
        print(
            f"{s_name:<8} trit_on  |q|={on['n_q']} n_DMC={on['n_dmc']}  "
            f"trit_off |q|={off['n_q']} n_DMC={off['n_dmc']}"
        )
        if off["n_dmc"] >= N_DMC:
            print("         VOID: trit-off still 384; trit is stealing 6→384")
        if on["n_dmc"] < GROUP_N:
            print("         group-index failure")
        elif on["n_dmc"] < N_DMC:
            print("         trit failure (not 'not a failure')")
    print()

    print("--- CORRELATIONS (current, 8GiB; do not substitute GF(2) rank for |q|) ---")
    for s_name in KILLER_NAMES:
        print_corr(s_name, killers[(s_name, ARM_CURRENT)])
    print()

    print("--- LITTLE / X_rel (occupancy ratios, not measured BW) ---")
    for s_name in KILLER_NAMES:
        n = killers[(s_name, ARM_CURRENT)]["n_dmc"]
        n_off = killers[(s_name, ARM_TRIT_OFF)]["n_dmc"]
        n_ab = killers[(s_name, ARM_ABLATION)]["n_dmc"]
        print(f"{s_name:<8} current {little_line(n)}  trit_off {little_line(n_off)}  ablation {little_line(n_ab)}")
    print(
        f"CLAIM occupancy (not BW): 1.5MiB {ABLATION_N_DMC_1_5_MIB}→{N_DMC} "
        f"(×{N_DMC // ABLATION_N_DMC_1_5_MIB}); "
        f"2MiB {ABLATION_N_DMC_2_MIB}→{N_DMC} "
        f"(×{N_DMC // ABLATION_N_DMC_2_MIB})"
    )
    print(
        f"X_rel vs integer-mod image {GROUP_N}: ×{N_DMC // GROUP_N} occupancy. "
        "min/mean occupancy and BW 0.85 are separate columns; this script does not emit BW."
    )
    print()
    print("done. no absolute GB/s. no H100. die=DMC[8] was not replaced by /192.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
