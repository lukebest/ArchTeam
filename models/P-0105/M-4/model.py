#!/usr/bin/env python3
"""P-0105/M-4 SNS — occupancy model (stdlib). See spec.md."""

from __future__ import annotations

import random
import sys

N_DMC = 384
N_BANK = 18432
W = 1 << 33
Q_TOT = 120 * 128
SEED = 20260903
GRAIN = 512

S_CHECK = (0, 3, 42, 17, 68, 183, 62, 5, 8, 139, 146, 89, 204, 255, 166, 141)

S_LIST = (
    ("2MiB", 2 * 1024 * 1024),
    ("1MiB", 1024 * 1024),
    ("512KiB", 512 * 1024),
    ("4608B", 4608),
    ("512B", 512),
)


def sbox(u: int) -> int:
    return (pow(u, 5, 256) + pow(u, 3, 256) + u) % 256


def fold384(raw: int) -> int:
    q = min(raw // 384, 10)
    r = raw - 384 * q
    if r >= 384:
        r -= 384
    return r


def shear(x: int, y: int) -> int:
    seven_y = ((y << 3) - y) & 0xFFF
    return (x + seven_y) & 0xFFF


def map_sns(phys: int):
    x = (phys >> 9) & 0xFFF
    y = (phys >> 21) & 0xFFF
    xp = shear(x, y)
    z = sbox((xp >> 4) & 0xFF) ^ (y & 0xFF)
    raw = (z << 4) | (xp & 0xF)
    dmc = fold384(raw)
    w = (xp >> 4) & 0x3F
    bank = w if w < 48 else w - 48
    return dmc, bank, raw, xp


def map_shear_only(phys: int):
    x = (phys >> 9) & 0xFFF
    y = (phys >> 21) & 0xFFF
    xp = shear(x, y)
    dmc = fold384(xp)
    w = (xp >> 4) & 0x3F
    bank = w if w < 48 else w - 48
    return dmc, bank, xp, xp


def map_sbox_only(phys: int):
    x = (phys >> 9) & 0xFFF
    z = sbox((x >> 4) & 0xFF)  # no XOR y
    raw = (z << 4) | (x & 0xF)
    dmc = fold384(raw)
    w = (x >> 4) & 0x3F
    bank = w if w < 48 else w - 48
    return dmc, bank, raw, x


def map_mod384(phys: int):
    g = phys >> 9
    return g % 384, g % 48, None, None


def map_low(phys: int):
    g = phys >> 9
    x = g & 0x1FF
    dmc = x if x < 384 else x - 384
    return dmc, (g & 0x3F) % 48, None, None


def map_high(phys: int):
    y = (phys >> 21) & 0xFFF
    return y % 384, y % 48, None, None


def k_of(base, s):
    return (W - 1 - base) // s + 1


def run_mapper(fn, base, s, n):
    dmc_h = [0] * N_DMC
    bank_h = [0] * N_BANK
    per_dmc_banks = [set() for _ in range(N_DMC)]
    kind8 = [set() for _ in range(N_DMC)]
    for i in range(n):
        phys = base + i * s
        dmc, bank, *_ = fn(phys)
        dmc_h[dmc] += 1
        bank_h[dmc * 48 + bank] += 1
        per_dmc_banks[dmc].add(bank)
        kind8[dmc].add(bank % 8)
    n_dmc = sum(1 for c in dmc_h if c)
    n_bank = sum(1 for c in bank_h if c)
    occ = [c for c in dmc_h if c]
    mm = (min(occ) / (sum(occ) / len(occ))) if occ else 0.0
    x_rel = (min(N_DMC, n) / n_dmc) if n_dmc else float("inf")
    banks_per = [len(per_dmc_banks[d]) for d in range(N_DMC) if dmc_h[d]]
    k8 = [len(kind8[d]) for d in range(N_DMC) if dmc_h[d]]
    return {
        "n_DMC": n_dmc,
        "n_bank": n_bank,
        "X_rel": x_rel,
        "min/mean": mm,
        "bank_per_dmc_min": min(banks_per) if banks_per else 0,
        "bank_per_dmc_max": max(banks_per) if banks_per else 0,
        "bank%8_kinds_min": min(k8) if k8 else 0,
        "dmc_h": dmc_h,
    }


def covering_bound():
    # 4096 = 10*384 + 256  — UNIFORM raw, independent of S-box
    hits = [10] * 384
    for i in range(256):
        hits[i] += 1
    mean = 4096 / 384
    var = sum((h - mean) ** 2 for h in hits) / 384
    cv = (var ** 0.5) / mean
    return max(hits), min(hits), cv


def fmt(x):
    return f"{x:.4f}" if isinstance(x, float) else str(x)


def prow(cols, w):
    print("  ".join(str(c).ljust(x) for c, x in zip(cols, w)))


def main() -> int:
    got = [sbox(u) for u in range(16)]
    if tuple(got) != S_CHECK:
        print("S-box checksum FAIL", got)
        return 1
    mx, mn, cv = covering_bound()
    print("P-0105/M-4 SNS  occupancy model")
    print("envelope TEAM-SPEC team-384dmc-18432bank   bench team-interleave-microbench")
    print(f"S(u)=u^5+u^3+u mod 256 INTEGER  S(0..15) checksum OK")
    print(f"COVERING_BOUND (uniform raw, NOT a mechanism golden): max={mx} min={mn} CV={cv:.4f}")
    print("do not calibrate SNS against that bound")
    print(f"SEED={SEED}  μ_d UNKNOWN  GB/s not printed  no H100")
    print()

    rng = random.Random(SEED)
    grain_bases = [0, GRAIN, 2 * GRAIN, 3 * GRAIN, 7 * GRAIN, 15 * GRAIN, 31 * GRAIN, 63 * GRAIN]
    aligned = [0, 2 * 1024 * 1024, 4 * 1024 * 1024, 6 * 1024 * 1024]
    extra = []
    while len(extra) < 4:
        extra.append(rng.randrange(0, 4096, GRAIN))

    print("=== TABLE S x mapper  (base=0, 512B-grain family uses base=0 here) ===")
    w = (8, 12, 8, 7, 8, 8, 8, 10, 10)
    prow(("S", "mapper", "|I|", "n_DMC", "n_bank", "X_rel", "min/mean", "bks/DMC", "bank%8"), w)
    for s_name, s in S_LIST:
        k = k_of(0, s)
        n = min(k, Q_TOT)
        for mname, fn in (
            ("SNS", map_sns),
            ("B-mod384", map_mod384),
            ("B-low", map_low),
            ("B-high", map_high),
            ("ABL-shear", map_shear_only),
            ("ABL-sbox", map_sbox_only),
        ):
            st = run_mapper(fn, 0, s, n)
            prow(
                (
                    s_name, mname, n, st["n_DMC"], st["n_bank"], fmt(st["X_rel"]),
                    fmt(st["min/mean"]),
                    f"{st['bank_per_dmc_min']}-{st['bank_per_dmc_max']}",
                    st["bank%8_kinds_min"],
                ),
                w,
            )
        if s_name == "4608B":
            print("  ^^ 4608B is 3-adic×phase; reported alone (not averaged)")

    print()
    print("=== T1 base sweeps S=2MiB  (512B-grain vs 2MiB-aligned, SEPARATE) ===")
    s = 2 * 1024 * 1024
    k = k_of(0, s)
    n = min(k, Q_TOT)

    def sweep(label, bases):
        print(f"-- {label} --")
        prow(("base", "SNS", "shear", "sbox", "mod384", "low", "high"), (14, 6, 6, 6, 8, 6, 6))
        sns_n = []
        sbox_n = []
        sbox_ids = []
        for b in bases:
            vals = []
            ids = None
            for fn in (map_sns, map_shear_only, map_sbox_only, map_mod384, map_low, map_high):
                st = run_mapper(fn, b, s, min(k_of(b, s), Q_TOT))
                vals.append(st["n_DMC"])
                if fn is map_sbox_only:
                    ids = tuple(i for i, c in enumerate(st["dmc_h"]) if c)
            sns_n.append(vals[0])
            sbox_n.append(vals[2])
            sbox_ids.append(ids)
            prow((hex(b), *vals), (14, 6, 6, 6, 8, 6, 6))
        mean = sum(sns_n) / len(sns_n)
        rel = ((max(sns_n) - min(sns_n)) / mean) if mean else 0.0
        print(f"SNS n_DMC across bases: {sns_n}  rel_diff=(max-min)/mean={rel:.4f}")
        print(f"ABL-sbox n_DMC={sbox_n}  occupied DMC ids={sbox_ids}")
        print("CONSTRAINT: SNS n_DMC=384 and rel_diff<0.05; ABL-sbox must change with phase (count or id)")
        return rel, sbox_n

    sweep("512B-grain phases (incl. page-inner 0..4K-512)", grain_bases + extra)
    print()
    sweep("2MiB-aligned only", aligned)

    print()
    print("=== S=2MiB SNS bank histogram (base=0) ===")
    st = run_mapper(map_sns, 0, s, n)
    print(f"banks per occupied DMC: min={st['bank_per_dmc_min']} max={st['bank_per_dmc_max']}")
    print(f"bank%8 kinds min={st['bank%8_kinds_min']}  (6b window can collapse toward 6 banks/DMC)")
    print("winning only min/mean while losing absolute BW = fail (BW not computed; μ_d UNKNOWN)")
    print("no H100; covering bound is not a golden SNS number")
    return 0


if __name__ == "__main__":
    sys.exit(main())
