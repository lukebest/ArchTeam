#!/usr/bin/env python3
"""P-0106/M-5 AffineRebind — occupancy model (stdlib). See spec.md."""

from __future__ import annotations

import math
import sys

N_DMC = 384
N_BANK = 18432
W = 1 << 33
Q_TOT = 120 * 128
SEED = 20260903

DOC = (
    ("512B", 512),
    ("3x512B", 3 * 512),
    ("9x512B", 9 * 512),
    ("512KiB", 512 * 1024),
    ("1MiB", 1024 * 1024),
    ("2MiB", 2 * 1024 * 1024),
)
CAND = (1, 5, 7, 11, 13, 17, 19, 23, 25, 31, 35, 37, 41, 43, 47)


def xor_fold6(g: int) -> int:
    # 假设 H-FOLD6 PIN: g[i] = XOR_k G[i+6k] for i+6k <= 55
    out = 0
    for i in range(6):
        bit = 0
        kk = 0
        while i + 6 * kk <= 55:
            bit ^= (g >> (i + 6 * kk)) & 1
            kk += 1
        out |= bit << i
    return out


def xor_fold9(g: int) -> int:
    acc = 0
    while g:
        acc ^= g & 0x1FF
        g >>= 9
    return acc


def upstream_dmc(g: int) -> int:
    # 假设 H-UP-DMC
    x = xor_fold9(g)
    return x if x < 384 else x - 384


def kth_one(mask: int, slot: int) -> int:
    seen = 0
    for i in range(48):
        if (mask >> i) & 1:
            if seen == slot:
                return i
            seen += 1
    return -1


def popcount(mask: int) -> int:
    return bin(mask).count("1")


def alpha_search(n: int) -> int:
    best_a, best_s = None, None
    sgs = [s // 512 for _, s in DOC]
    for a in CAND:
        if math.gcd(a, n) != 1:
            continue
        score = max(math.gcd(a * sg, n) for sg in sgs)
        if best_s is None or score < best_s or (score == best_s and a < best_a):
            best_a, best_s = a, score
    return best_a if best_a is not None else 1


def mask_full():
    return (1 << 48) - 1


def mask_n40():
    # 负载基线 n=40 (L=32+spare): 8 retired, spread
    dead = (0, 6, 12, 18, 24, 30, 36, 42)
    m = (1 << 48) - 1
    for d in dead:
        m &= ~(1 << d)
    return m


def mask_uniform(n_live: int) -> int:
    # first n_live bits — TEAM-SPEC scan, not yield
    return (1 << n_live) - 1


def mask_third_bias():
    # retire bank≡0 (mod 3) ⇒ n=32, factor 3 removed
    m = 0
    for i in range(48):
        if i % 3 != 0:
            m |= 1 << i
    return m


def skip_dead(g6: int, mask: int) -> int:
    slot = g6 % 48
    for _ in range(48):
        if (mask >> slot) & 1:
            return slot
        slot = (slot + 1) % 48
    return -1


def k_of(base, s):
    return (W - 1 - base) // s + 1


def run(kind, mask, alpha, s, n_pts):
    n = popcount(mask)
    dmc_h = [0] * N_DMC
    bank_h = [0] * N_BANK
    classes = [set() for _ in range(N_DMC)]
    dead = 0
    for i in range(n_pts):
        addr = i * s
        g = addr >> 9
        g6 = xor_fold6(g)
        dmc = upstream_dmc(g)
        if kind == "skip-dead":
            bank = skip_dead(g6, mask)
        else:
            slot = (alpha * g6) % n if n else 0
            bank = kth_one(mask, slot)
        if bank < 0 or ((mask >> bank) & 1) == 0:
            dead += 1
            continue
        dmc_h[dmc] += 1
        bank_h[dmc * 48 + bank] += 1
        classes[dmc].add(bank)
    n_dmc = sum(1 for c in dmc_h if c)
    n_bank = sum(1 for c in bank_h if c)
    occ = [c for c in dmc_h if c]
    mm = (min(occ) / (sum(occ) / len(occ))) if occ else 0.0
    x_rel = (min(N_DMC, n_pts) / n_dmc) if n_dmc else float("inf")
    cls = [len(classes[d]) for d in range(N_DMC) if dmc_h[d]]
    return {
        "n_DMC": n_dmc,
        "n_bank": n_bank,
        "X_rel": x_rel,
        "min/mean": mm,
        "dead": dead,
        "cls_min": min(cls) if cls else 0,
        "cls_max": max(cls) if cls else 0,
        "cls_mean": (sum(cls) / len(cls)) if cls else 0.0,
        "n": n,
        "alpha": alpha,
    }


def fmt(x):
    return f"{x:.4f}" if isinstance(x, float) else str(x)


def prow(cols, w):
    print("  ".join(str(c).ljust(x) for c, x in zip(cols, w)))


def main() -> int:
    print("P-0106/M-5 AffineRebind  occupancy model")
    print("envelope TEAM-SPEC team-384dmc-18432bank   bench team-interleave-microbench")
    print("g=XOR_fold6 PIN  g[i]=XOR G[i+6k] (i+6k<=55)  taps frozen")
    print("μ_d UNKNOWN; GB/s not printed; no H100; no CLAIM-as-input")
    print()

    g_demo = xor_fold6(0x123456789ABCDEF)
    print(f"XOR_fold6 smoke g(0x123456789ABCDEF)={g_demo} (netlist, not AP gcd)")
    print()

    masks = (
        ("full-good", mask_full()),
        ("n=40", mask_n40()),
        ("unif-25%(n=36)", mask_uniform(36)),
        ("unif-12.5%(n=42)", mask_uniform(42)),
        ("unif-6.25%(n=45)", mask_uniform(45)),
        ("3-biased(n=32)", mask_third_bias()),
    )

    print("=== α search (card) vs α=1  [gcd identity: search does not change gcd] ===")
    prow(("mask", "n", "α_minimax", "gcd(α S_g,n) vs gcd(S_g,n) all Doc"), (18, 4, 10, 40))
    alphas = {}
    for label, mask in masks:
        n = popcount(mask)
        a = alpha_search(n)
        alphas[label] = a
        sgs = [s // 512 for _, s in DOC]
        same = all(math.gcd(a * sg, n) == math.gcd(sg, n) for sg in sgs)
        prow((label, n, a, f"identical={same}"), (18, 4, 10, 40))
    print("α search is a CONSTANT on gcd when gcd(α,n)=1")
    print("uniform 25% n=36 STILL has factor 3 — not a 3-adic test")
    print("3-adic ONLY from 3-residue-biased column")
    print()

    print("=== occupancy  (issued I=min(K,Q_tot); XOR_fold6 netlist) ===")
    w = (10, 18, 12, 4, 7, 8, 6, 8, 8, 8)
    prow(
        ("S", "mask", "mapper", "α", "n_DMC", "n_bank", "dead", "cls_min", "cls_mean", "min/mean"),
        w,
    )
    store = {}
    for s_name, s in DOC:
        k = k_of(0, s)
        n_pts = min(k, Q_TOT)
        sg = s // 512
        for label, mask in masks:
            n = popcount(mask)
            a1 = 1 if math.gcd(1, n) == 1 else alpha_search(n)
            am = alphas[label]
            variants = (
                ("skip-dead", "skip-dead", 1),
                ("modn-α=1", "modn", a1),
                ("modn-minimax", "modn", am),
            )
            for vname, kind, a in variants:
                st = run(kind, mask, a, s, n_pts)
                store[(s_name, label, vname)] = st
                prow(
                    (
                        s_name, label, vname, st["alpha"], st["n_DMC"], st["n_bank"],
                        st["dead"], st["cls_min"], fmt(st["cls_mean"]), fmt(st["min/mean"]),
                    ),
                    w,
                )
            # sanity gcd table for this n, S
            print(
                f"    gcd_table {label} S_g={sg}: n/gcd(S_g,n)={n // math.gcd(sg, n) if n else 0} "
                f"(AP sanity; not a substitute for XOR_fold6)"
            )

    print()
    print("=== T1 primary contrast: skip-dead vs modn-α=1  (n=40, 2MiB) ===")
    a = store[("2MiB", "n=40", "skip-dead")]
    b = store[("2MiB", "n=40", "modn-α=1")]
    c = store[("2MiB", "n=40", "modn-minimax")]
    print(f"skip-dead  cls_mean={a['cls_mean']:.4f} n_bank={a['n_bank']} dead={a['dead']}")
    print(f"modn-α=1   cls_mean={b['cls_mean']:.4f} n_bank={b['n_bank']} dead={b['dead']}")
    print(f"minimax    cls_mean={c['cls_mean']:.4f} n_bank={c['n_bank']} dead={c['dead']} α={c['alpha']}")
    if b["cls_mean"]:
        diff = abs(c["cls_mean"] - b["cls_mean"]) / b["cls_mean"]
        print(f"(mod n, α=1) vs minimax cls_mean rel-diff={diff:.4f}  CONSTRAINT <0.05 on large 2-power")

    print()
    print("=== full-good gain vs no-rebind ≈ 0 ===")
    fg_s = store[("2MiB", "full-good", "skip-dead")]
    fg_m = store[("2MiB", "full-good", "modn-minimax")]
    print(f"full-good skip-dead n_bank={fg_s['n_bank']}  minimax n_bank={fg_m['n_bank']} dead={fg_m['dead']}")

    print()
    print("=== three-mask same-table snapshot (2MiB) as T1 bench ===")
    prow(("mask", "skip_cls", "a1_cls", "mm_cls", "dead_a1"), (18, 10, 8, 8, 8))
    for label in ("full-good", "n=40", "3-biased(n=32)"):
        s0 = store[("2MiB", label, "skip-dead")]
        s1 = store[("2MiB", label, "modn-α=1")]
        s2 = store[("2MiB", label, "modn-minimax")]
        prow((label, fmt(s0["cls_mean"]), fmt(s1["cls_mean"]), fmt(s2["cls_mean"]), s1["dead"]),
             (18, 10, 8, 8, 8))
    print("dead hits must be 0 on kth-one / skip-dead live paths")
    print("6.25/12.5/25% are TEAM-SPEC problem-scan, not measured yield")
    return 0


if __name__ == "__main__":
    sys.exit(main())
