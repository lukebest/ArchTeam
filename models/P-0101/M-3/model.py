#!/usr/bin/env python3
"""P-0101/M-3 层次正交放置 — occupancy model (stdlib). See spec.md."""

from __future__ import annotations

import random
import sys

# TEAM-SPEC team-384dmc-18432bank (problem YAML identities)
N_DIE = 2
CORES_PER_DIE = 60
HA_PER_DIE = 96
PIPE_PER_HA = 2
BANK_PER_DMC = 48
N_CORE = N_DIE * CORES_PER_DIE  # 120
N_HA = N_DIE * HA_PER_DIE  # 192
N_DMC = N_DIE * HA_PER_DIE * PIPE_PER_HA  # 384
N_BANK = N_DMC * BANK_PER_DMC  # 18432
GRAIN = 512
W = 1 << 33
Q_CORE = 128
Q_TOT = N_CORE * Q_CORE  # 15360
SEED = 20260903
N_RANDOM_BASES = 8

# 假设 H-ENC9 (M-1 16→9 table not listed on the card)
ENC9 = (0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 1, 2, 3, 4, 5, 6)

S_LIST = (
    ("512B", 512),
    ("512KiB", 512 * 1024),
    ("1MiB", 1024 * 1024),
    ("2MiB", 2 * 1024 * 1024),
)


def enc3(two_bits: int) -> int:
    # card: {00,01,10,11} → {0,1,2,0}
    return (0, 1, 2, 0)[two_bits & 3]


def topo(dmc: int) -> tuple[int, int, int]:
    die = dmc // 192
    ha = die * 96 + ((dmc // 2) % 96)
    pipe = dmc % 2
    return die, ha, pipe


def map_proposed(addr: int) -> tuple[int, int]:
    p = (addr >> 26) & 0x7F
    t = enc3((addr >> 24) & 3)
    dmc0 = t * 128 + p
    s = 0  # SK=0
    dmc = (dmc0 + 3 * s) % 384
    # 假设 H-B4: LSB-align, zero-extend 3b
    b4 = ((addr >> 21) & 7) ^ ((addr >> 11) & 15)
    b3 = enc3((addr >> 19) & 3)
    bank = b3 * 16 + (b4 % 16)
    if bank > 47:
        bank = 47
    return dmc, bank


def map_modn(addr: int) -> tuple[int, int]:
    g = addr >> 9
    flat = g % 18432
    return flat // 48, flat % 48


def map_m1(addr: int) -> tuple[int, int]:
    d = (addr >> 21) & 0xFFF
    v = d  # P = 0
    c = ENC9[(addr >> 13) & 15]
    flat = (c * 4096 + v) % 18432
    return flat // 48, flat % 48


def map_low(addr: int) -> tuple[int, int]:
    dmc = ((addr >> 9) & 0x1FF) % 384
    bank = ((addr >> 9) & 0x3F) % 48
    return dmc, bank


MAPPERS = (
    ("M-3", map_proposed),
    ("B-modN", map_modn),
    ("B-M1", map_m1),
    ("B-low", map_low),
)


def k_of(base: int, s: int) -> int:
    return (W - 1 - base) // s + 1


def accumulate(mapper, base: int, s: int, n: int):
    dmc_h = [0] * N_DMC
    bank_h = [0] * N_BANK
    die_h = [0] * N_DIE
    ha_h = [0] * N_HA
    t_h = [0] * 3
    for k in range(n):
        addr = base + k * s
        dmc, bank = mapper(addr)
        dmc_h[dmc] += 1
        bank_h[dmc * 48 + bank] += 1
        die, ha, _ = topo(dmc)
        die_h[die] += 1
        ha_h[ha] += 1
        t_h[enc3((addr >> 24) & 3)] += 1
    return dmc_h, bank_h, die_h, ha_h, t_h


def summarize(dmc_h, bank_h, die_h, ha_h, n_pts: int, k: int):
    n_dmc = sum(1 for c in dmc_h if c)
    n_bank = sum(1 for c in bank_h if c)
    n_die = sum(1 for c in die_h if c)
    n_ha = sum(1 for c in ha_h if c)
    occ = [c for c in dmc_h if c]
    min_occ = min(occ) if occ else 0
    mean_occ = (sum(occ) / len(occ)) if occ else 0.0
    mm = (min_occ / mean_occ) if mean_occ else 0.0
    x_rel = (min(N_DMC, n_pts) / n_dmc) if n_dmc else float("inf")
    bank_frac = n_bank / N_BANK
    kn = k / N_BANK
    ha_share = [c / n_pts for c in ha_h] if n_pts else [0.0] * N_HA
    hog = 1.5 * (2.0 / 384.0)
    max_ha = max(ha_share) if ha_share else 0.0
    n_hog = sum(1 for x in ha_share if x > hog + 1e-15)
    return {
        "n_DMC": n_dmc,
        "n_bank": n_bank,
        "n_die": n_die,
        "n_HA": n_ha,
        "X_rel": x_rel,
        "min_occ": min_occ,
        "mean_occ": mean_occ,
        "min/mean": mm,
        "bank%": bank_frac,
        "K/N": kn,
        "die0": die_h[0],
        "die1": die_h[1],
        "max_HA_share": max_ha,
        "HA_hog_gt_1.5x": n_hog,
        "hog_line": hog,
    }


def fmt(x):
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


def print_row(cols, widths):
    print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))


def main() -> int:
    rng = random.Random(SEED)
    print("P-0101/M-3 层次正交放置  occupancy model")
    print("envelope TEAM-SPEC team-384dmc-18432bank   bench team-interleave-microbench")
    print(f"N_DMC={N_DMC} N_bank={N_BANK} Q_tot={Q_TOT} W=2^33 SK=0 SEED={SEED}")
    print("primary outputs: occupancy; μ_d UNKNOWN; GB/s not printed")
    print("issued set I = first min(K, Q_tot) AP points (Little window)")
    print()

    headers = (
        "S", "mapper", "K", "|I|", "n_DMC", "n_bank", "n_die", "n_HA",
        "X_rel", "min/mean", "bank%", "K/N", "die0", "die1",
    )
    widths = (8, 8, 8, 8, 7, 8, 6, 6, 8, 8, 8, 8, 6, 6)

    print("=== TABLE issued occupancy (base=0 sequential) ===")
    print_row(headers, widths)
    seq_stats = {}
    for s_name, s in S_LIST:
        base = 0
        k = k_of(base, s)
        n = min(k, Q_TOT)
        for mname, fn in MAPPERS:
            dmc_h, bank_h, die_h, ha_h, _ = accumulate(fn, base, s, n)
            st = summarize(dmc_h, bank_h, die_h, ha_h, n, k)
            seq_stats[(s_name, mname)] = st
            print_row(
                (
                    s_name, mname, k, n, st["n_DMC"], st["n_bank"], st["n_die"],
                    st["n_HA"], fmt(st["X_rel"]), fmt(st["min/mean"]),
                    fmt(st["bank%"]), fmt(st["K/N"]), st["die0"], st["die1"],
                ),
                widths,
            )

    print()
    print("=== T1 KILL-LINE S=512B sequential unique DMC (issued) ===")
    st = seq_stats[("512B", "M-3")]
    print(f"M-3 n_DMC_issued={st['n_DMC']}   Archi_fail_if==1   Sys_wants_occupancy>=0.95")
    print(f"CONSTRAINT: must not collapse to <<128; fail value 1 is Archi")
    print(f"same table includes 512KiB/1MiB/2MiB (not 2MiB-only)")

    print()
    print("=== T1 KILL-LINE SK=0 S=2MiB >=8 random bases HA hog ===")
    hog = 1.5 * (2.0 / 384.0)
    print(f"hog line = 1.5*(2/384) = {hog:.6f}")
    s = 2 * 1024 * 1024
    # grain-aligned phases in [0, S) so K stays 4096 (not truncated near W)
    bases = [0]
    while len(bases) < N_RANDOM_BASES:
        b = rng.randrange(0, s, GRAIN)
        if b not in bases:
            bases.append(b)
    print(f"bases (grain-aligned, SEED={SEED}): {bases}")
    print_row(
        ("base", "n_DMC", "die0", "die1", "die_ratio", "max_HA", "n_HA_hog", "bank%", "K/N"),
        (14, 7, 6, 6, 10, 10, 8, 8, 8),
    )
    hog_any = 0
    for b in bases:
        k = k_of(b, s)
        n = min(k, Q_TOT)
        dmc_h, bank_h, die_h, ha_h, _ = accumulate(map_proposed, b, s, n)
        st = summarize(dmc_h, bank_h, die_h, ha_h, n, k)
        ratio = (st["die0"] / st["die1"]) if st["die1"] else float("inf")
        hog_any += st["HA_hog_gt_1.5x"]
        print_row(
            (
                hex(b), st["n_DMC"], st["die0"], st["die1"], fmt(ratio),
                fmt(st["max_HA_share"]), st["HA_hog_gt_1.5x"],
                fmt(st["bank%"]), fmt(st["K/N"]),
            ),
            (14, 7, 6, 6, 10, 10, 8, 8, 8),
        )
    print("ENC3 2:1:1 ⇒ die visits ~5:3 (2560:1536 on K=4096) is wiring, not a fit")
    print(f"HA hog DMC-count over bases (sum of HA exceeding line): {hog_any}")
    print("CONSTRAINT: no HA issued share > 1.5*(2/384)")

    print()
    print("=== sanity bank occupancy <= K/N (S=2MiB M-3) ===")
    st = seq_stats[("2MiB", "M-3")]
    print(f"bank%={st['bank%']:.6f}  K/N={st['K/N']:.6f}  exceed={st['bank%']>st['K/N']+1e-12}")
    print("exceed ⇒ model bug, not card success (problem YAML)")

    print()
    print("=== Little / roofline (occupancy ratios, not speedup) ===")
    a = seq_stats[("2MiB", "M-3")]["n_DMC"]
    b = seq_stats[("2MiB", "B-modN")]["n_DMC"]
    print(f"S=2MiB issued n_DMC  M-3={a}  B-modN={b}  ratio={a/b if b else 'inf'}")
    print("9 vs 384 Little ratio is NOT a measured speedup; μ_d ASSUMPTION unnamed numeric")
    print("no H100 numbers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
