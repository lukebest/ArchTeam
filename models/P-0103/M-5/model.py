#!/usr/bin/env python3
"""P-0103/M-5 B3CSH — occupancy model (stdlib). See spec.md."""

from __future__ import annotations

import math
import sys

N_DMC = 384
N_BANK = 18432
W = 1 << 33
Q_TOT = 120 * 128
SEED = 20260903

TRIT = (0, 1, 2, 0, 1, 2, 0, 1)  # histogram 3,3,2

S_LIST = (
    ("512B", 512),
    ("1KiB", 1024),
    ("1536B", 1536),
    ("3KiB", 3072),
    ("4608B", 4608),
    ("12KiB", 12 * 1024),
    ("1.5MiB", 1572864),
    ("2MiB", 2 * 1024 * 1024),
)

NAMED = {
    "1536B": ("δ=3", (0,)),
    "4608B": ("δ=9", (0, 1)),
    "12KiB": ("δ=24", (1, 2)),
    "1.5MiB": ("δ=3072", (3,)),
}


def k_of(base, s):
    return (W - 1 - base) // s + 1


def csa(a, b, c):
    t = a + b + c
    return t % 3, t // 3


def chunks(addr):
    g = addr >> 9
    return (
        (addr >> 9) & 7,
        (addr >> 12) & 7,
        (addr >> 15) & 7,
        (addr >> 18) & 7,
        (addr >> 21) & 7,
        (addr >> 24) & 7,
        (addr >> 27) & 7,
        (addr >> 30) & 7,
    ), g


def pmix_bits(g):
    bits = []
    for i in range(11):
        lo = (g >> (10 - i)) & 1
        hi = (g >> (11 + i)) & 1
        bits.append(lo ^ hi)
    return bits


def pmix_val(bits, lo, hi):
    v = 0
    for i in range(lo, hi + 1):
        v |= bits[i] << (i - lo)
    return v


def tree(w):
    s0, c0 = csa(w[0], w[1], w[2])
    s1, c1 = csa(w[3], w[4], w[5])
    p0, p1 = w[6], w[7]
    s2, c2 = csa(s0, s1, p0)
    s3, c3 = csa(s2, p1, 0)  # d0
    s4, c4 = csa(c0, c1, c2)
    s5, c5 = csa(s4, c3, 0)  # d1
    d2, _ = csa(c4, c5, 0)
    d0, d1 = s3, s5
    return d0, d1, d2


def map_b3(addr):
    ch, g = chunks(addr)
    w = [TRIT[c] for c in ch]
    d0, d1, d2 = tree(w)
    sigma = sum(w)
    assert d0 + 3 * d1 + 9 * d2 == sigma
    r_hash = d0 + 3 * d1
    dmc_odd = (d0 + d1 + d2) % 3
    bits = pmix_bits(g)
    dmc = dmc_odd + 3 * pmix_val(bits, 0, 6)
    bank = (r_hash % 3) + 3 * pmix_val(bits, 7, 10)
    return dmc, bank, d0, dmc_odd, bits[0], g % 3, ch


def map_ctrl(addr):
    """G mod 3 as DMC trit; same p_mix[6:0]."""
    _, g = chunks(addr)
    bits = pmix_bits(g)
    dmc = (g % 3) + 3 * pmix_val(bits, 0, 6)
    return dmc, 0, None, g % 3, bits[0], g % 3, None


def xor_fold(g, width):
    acc, mask = 0, (1 << width) - 1
    while g:
        acc ^= g & mask
        g >>= width
    return acc


def map_mod(mod):
    def fn(addr):
        g = addr >> 9
        return g % mod, (g // mod) % 48, None, None, None, None, None

    return fn


def map_xor2(addr):
    g = addr >> 9
    x = xor_fold(g, 9)
    dmc = x if x < 384 else x - 384
    return dmc, xor_fold(g >> 1, 6) % 48, None, None, None, None, None


def gf2_rank_pmix():
    """11×22 matrix: outputs p_mix[i] = G[10-i] XOR G[11+i]."""
    rows = []
    for i in range(11):
        row = [0] * 22
        row[10 - i] = 1
        row[11 + i] = 1
        rows.append(row)
    rank = 0
    cols = 22
    used = [False] * 11
    for c in range(cols):
        piv = None
        for r in range(11):
            if not used[r] and rows[r][c]:
                piv = r
                break
        if piv is None:
            continue
        used[piv] = True
        rank += 1
        for r in range(11):
            if r != piv and rows[r][c]:
                rows[r] = [a ^ b for a, b in zip(rows[r], rows[piv])]
    return rank


def cramer_v(table):
    # table 3x3
    n = sum(sum(r) for r in table)
    if n == 0:
        return 0.0
    row_s = [sum(r) for r in table]
    col_s = [sum(table[r][c] for r in range(3)) for c in range(3)]
    chi = 0.0
    for r in range(3):
        for c in range(3):
            e = row_s[r] * col_s[c] / n
            if e == 0:
                continue
            chi += (table[r][c] - e) ** 2 / e
    return math.sqrt(chi / (n * 2.0))  # min(3-1,3-1)=2


def stats(dmc_h, bank_h, n):
    n_dmc = sum(1 for c in dmc_h if c)
    n_bank = sum(1 for c in bank_h if c)
    occ = [c for c in dmc_h if c]
    min_occ = min(occ) if occ else 0
    mean_occ = (sum(occ) / len(occ)) if occ else 0.0
    mm = (min_occ / mean_occ) if mean_occ else 0.0
    x_rel = (min(N_DMC, n) / n_dmc) if n_dmc else float("inf")
    return n_dmc, n_bank, x_rel, mm


def fmt(x):
    return f"{x:.4f}" if isinstance(x, float) else str(x)


def prow(cols, w):
    print("  ".join(str(c).ljust(x) for c, x in zip(cols, w)))


def select_k(mask, k):
    n_good = bin(mask).count("1")
    if n_good == 0:
        return 0, n_good
    slot = k % n_good  # NO further mod 3
    seen = 0
    for i in range(48):
        if (mask >> i) & 1:
            if seen == slot:
                return i, n_good
            seen += 1
    return 0, n_good


def main() -> int:
    rank = gf2_rank_pmix()
    print("P-0103/M-5 B3CSH  occupancy model")
    print("envelope TEAM-SPEC team-384dmc-18432bank   bench team-interleave-microbench")
    print(f"Q_tot={Q_TOT}  GF2_11 rank (11x22 map) = {rank}  (do not claim 11)")
    print("dmc_odd=(d0+d1+d2) mod 3   FORBIDDEN to use d0 as DMC trit")
    print("μ_d UNKNOWN; GB/s not printed; no H100")
    print()

    print("=== TABLE sequential issued (S never averaged) ===")
    w = (8, 10, 8, 8, 7, 8, 8, 8, 10, 8)
    prow(
        ("S", "mapper", "K", "|I|", "n_DMC", "n_bank", "X_rel", "min/mean", "d0!=odd", "pmix0"),
        w,
    )
    named_flip = {}
    v4608 = None
    ctrl4608 = None
    pmix0_2m = None
    for s_name, s in S_LIST:
        k = k_of(0, s)
        n = min(k, Q_TOT)
        for mname, fn in (
            ("B3CSH", map_b3),
            ("CTRL-g%3", map_ctrl),
            ("B-%31", map_mod(31)),
            ("B-%192", map_mod(192)),
            ("B-%248", map_mod(248)),
            ("B-XOR2", map_xor2),
        ):
            dmc_h = [0] * N_DMC
            bank_h = [0] * N_BANK
            flips = [0] * 8
            prev = None
            neq = 0
            p0s = set()
            table = [[0] * 3 for _ in range(3)]
            for i in range(n):
                addr = i * s
                out = fn(addr)
                dmc, bank = out[0], out[1]
                dmc_h[dmc] += 1
                bank_h[(dmc % 384) * 48 + (bank % 48)] += 1
                if mname == "B3CSH":
                    d0, dmc_odd, p0, g3, ch = out[2], out[3], out[4], out[5], out[6]
                    if d0 != dmc_odd:
                        neq += 1
                    p0s.add(p0)
                    table[dmc_odd][g3] += 1
                    if prev is not None:
                        for j in range(8):
                            if ch[j] != prev[j]:
                                flips[j] += 1
                    prev = ch
                elif mname == "CTRL-g%3" and s_name == "4608B":
                    pass
            nd, nb, xr, mm = stats(dmc_h, bank_h, n)
            if mname == "B3CSH":
                named_flip[s_name] = flips
                if s_name == "4608B":
                    v4608 = cramer_v(table)
                if s_name == "2MiB":
                    pmix0_2m = p0s
            if mname == "CTRL-g%3" and s_name == "4608B":
                ctrl4608 = nd
            prow(
                (
                    s_name, mname, k, n, nd, nb, fmt(xr), fmt(mm),
                    neq if mname == "B3CSH" else "-",
                    f"|{len(p0s)}|" if mname == "B3CSH" else "-",
                ),
                w,
            )

    print()
    print("=== C0..C7 flip counts (sequential consecutive issued) ===")
    print("named: δ=3→C0; δ=9→C0+C1; δ=24→C1+C2; δ=3072→C3")
    prow(("S", "name", "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "match?"),
         (8, 10, 6, 6, 6, 6, 6, 6, 6, 6, 8))
    for s_name, _ in S_LIST:
        fl = named_flip[s_name]
        tag, expect = NAMED.get(s_name, ("", ()))
        live = tuple(i for i, c in enumerate(fl) if c > 0)
        ok = all(i in live for i in expect) if expect else "-"
        prow((s_name, tag or "-", *fl, ok), (8, 10, 6, 6, 6, 6, 6, 6, 6, 6, 8))

    print()
    print("=== T1 δ=9 Cramér-V(dmc_odd, G mod 3) ===")
    print(f"V={v4608:.4f}  CONSTRAINT V<0.3; fail if corr>=0.8")
    print("note: δ=9 freezes G mod 9 ⇒ G mod 3 is constant on the AP; V then reflects a one-column table")
    print(f"CTRL G-mod-3-as-trit n_DMC={ctrl4608}  (expect ≈128 when 3|δ)")
    print(f"d0 != dmc_odd count printed above — formulas differ (Σ mod 3 = d0)")

    print()
    print("=== T1 S=2MiB p_mix[0] freeze ===")
    print(f"|{{p_mix[0]}}|={len(pmix0_2m) if pmix0_2m else '?'}  (G[10]⊕G[11] both dead if G[11:0] frozen)")
    print("declare rank drop; do not hide as n_DMC=384 if image shrinks")

    print()
    print("=== N_good=32 vs 36 select-k (no extra mod 3) ===")
    # 1/3 pattern n=32; uniform 25% n=36
    m32 = 0
    for i in range(48):
        if i % 3 != 0:
            m32 |= 1 << i
    m36 = 0
    dead36 = {0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44}
    for i in range(48):
        if i not in dead36:
            m36 |= 1 << i
    print(f"N_good_32={bin(m32).count('1')}  N_good_36={bin(m36).count('1')}  separate tables")
    s, n = 4608, min(k_of(0, 4608), Q_TOT)
    for label, mask in (("N_good=32", m32), ("N_good=36", m36)):
        dmc_h = [0] * N_DMC
        bank_h = [0] * N_BANK
        for i in range(n):
            dmc, bank, d0, odd, p0, g3, ch = map_b3(i * s)
            r_hash = d0 + 3 * (0)  # bank already from map; recompute k from card
            # k = (r_hash mod 3)+3*p_mix[10:7] == bank before select
            phys, ng = select_k(mask, bank)
            dmc_h[dmc] += 1
            bank_h[dmc * 48 + phys] += 1
        nd, nb, xr, mm = stats(dmc_h, bank_h, n)
        print(f"  {label}: n_DMC={nd} n_bank={nb} min/mean={mm:.4f}  (k mod N_good only)")
    print("no H100; no CLAIM-as-input")
    return 0


if __name__ == "__main__":
    sys.exit(main())
