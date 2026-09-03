#!/usr/bin/env python3
"""P-0103/M-1 MRFI — occupancy model (stdlib). See spec.md."""

from __future__ import annotations

import random
import sys

N_DIE = 2
N_CORE = 120
N_DMC = 384
N_BANK = 18432
GRAIN = 512
W = 1 << 33
Q_TOT = 120 * 128
SEED = 20260903

ROM16 = (0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 1, 2, 3, 4, 5, 6)

S_LIST = (
    ("512B", 512),
    ("1KiB", 1024),
    ("1536B", 1536),
    ("3KiB", 3072),
    ("4608B", 4608),
    ("12KiB", 12 * 1024),
    ("1.5MiB", 1572864),  # 3 * 2^19; S_g = 3072
    ("2MiB", 2 * 1024 * 1024),
)


def k_of(base: int, s: int) -> int:
    return (W - 1 - base) // s + 1


def xor_fold(g: int, width: int) -> int:
    acc = 0
    mask = (1 << width) - 1
    while g:
        acc ^= g & mask
        g >>= width
    return acc


def map_mrfi(addr: int):
    g = addr >> 9
    p = g & 0x7FF
    r = g % 9
    p_wide = (addr >> 9) & 0xFFFF
    idx4 = (
        (p_wide & 0xF)
        ^ ((p_wide >> 4) & 0xF)
        ^ ((p_wide >> 8) & 0xF)
        ^ ((p_wide >> 12) & 0xF)
    )
    f = ROM16[idx4]
    rp = (r + f) % 9
    idx = p + 2048 * ((2 * ((rp - (p % 9)) % 9)) % 9)
    dmc_div = idx // 48
    bank = idx % 48
    dmc_asm = (rp % 3) + 3 * (dmc_div // 3)
    return dmc_div, bank, dmc_asm, rp


def map_mod(mod: int):
    def fn(addr: int):
        g = addr >> 9
        return g % mod, (g // mod) % 48, None, None

    return fn


def map_xor2(addr: int):
    g = addr >> 9
    x = xor_fold(g, 9)
    dmc = x if x < 384 else x - 384
    y = xor_fold(g >> 1, 6)
    return dmc, y % 48, None, None


MAPPERS = (
    ("MRFI", map_mrfi),
    ("B-%31", map_mod(31)),
    ("B-%192", map_mod(192)),
    ("B-%248", map_mod(248)),
    ("B-XOR2", map_xor2),
)


def retry_xor(bank: int, mask: int, live5: int) -> int:
    def live(b):
        return (mask >> b) & 1

    if live(bank):
        return bank
    b1 = (bank ^ live5) % 48
    if live(b1):
        return b1
    b2 = (b1 ^ ((live5 << 1) | 1)) % 48
    if live(b2):
        return b2
    return b2  # stay; may be dead


def mask_random(frac_dead: float, rng: random.Random) -> int:
    bits = 0
    for i in range(48):
        if rng.random() >= frac_dead:
            bits |= 1 << i
    return bits if bits else 1


def mask_third() -> int:
    bits = 0
    for i in range(48):
        if i % 3 != 0:
            bits |= 1 << i
    return bits  # 32 live


def accumulate(mapper, base, s, n, mask=None, rng=None):
    dmc_h = [0] * N_DMC
    bank_h = [0] * N_BANK
    mismatch = 0
    dead = 0
    trit_h = [0] * 3
    for k in range(n):
        addr = base + k * s
        dmc, bank, dmc_asm, rp = mapper(addr)
        if dmc_asm is not None and dmc != dmc_asm:
            mismatch += 1
        if mask is not None:
            live5 = ((addr >> 9) & 0x1F)
            bank = retry_xor(bank, mask, live5)
            if ((mask >> bank) & 1) == 0:
                dead += 1
        dmc_h[dmc] += 1
        bank_h[dmc * 48 + bank] += 1
        if rp is not None:
            trit_h[rp % 3] += 1
    return dmc_h, bank_h, mismatch, dead, trit_h


def stats(dmc_h, bank_h, n):
    n_dmc = sum(1 for c in dmc_h if c)
    n_bank = sum(1 for c in bank_h if c)
    occ = [c for c in dmc_h if c]
    min_occ = min(occ) if occ else 0
    mean_occ = (sum(occ) / len(occ)) if occ else 0.0
    mm = (min_occ / mean_occ) if mean_occ else 0.0
    x_rel = (min(N_DMC, n) / n_dmc) if n_dmc else float("inf")
    return n_dmc, n_bank, x_rel, min_occ, mean_occ, mm


def fmt(x):
    return f"{x:.4f}" if isinstance(x, float) else str(x)


def prow(cols, widths):
    print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))


def main() -> int:
    print("P-0103/M-1 MRFI  occupancy model")
    print("envelope TEAM-SPEC team-384dmc-18432bank   bench team-interleave-microbench")
    print(f"Q_tot={Q_TOT} SEED={SEED}  μ_d UNKNOWN  GB/s not printed  no H100")
    print("issued I = min(K, Q_tot) sequential AP")
    print()

    widths = (8, 8, 8, 8, 7, 8, 8, 8, 10, 8)
    print("=== TABLE 100% good sequential (S never averaged) ===")
    prow(
        ("S", "mapper", "K", "|I|", "n_DMC", "n_bank", "X_rel", "min/mean", "DMC_mismatch", "trit"),
        widths,
    )
    rows = {}
    for s_name, s in S_LIST:
        k = k_of(0, s)
        n = min(k, Q_TOT)
        for mname, fn in MAPPERS:
            dmc_h, bank_h, mis, dead, trit = accumulate(fn, 0, s, n)
            n_dmc, n_bank, x_rel, _, _, mm = stats(dmc_h, bank_h, n)
            rows[(s_name, mname)] = (n_dmc, n_bank, x_rel, mm, mis, n, k, trit)
            trit_s = ",".join(str(t) for t in trit) if mname == "MRFI" else "-"
            mis_s = str(mis) if mname == "MRFI" else "-"
            prow(
                (s_name, mname, k, n, n_dmc, n_bank, fmt(x_rel), fmt(mm), mis_s, trit_s),
                widths,
            )

    print()
    print("=== T1 POINTWISE DMC definitions (MRFI) ===")
    print("DMC_div=idx/48   DMC_asm=(r' mod 3)+3*floor((idx/48)/3)")
    for s_name, _ in S_LIST:
        n_dmc, _, _, _, mis, n, _, _ = rows[(s_name, "MRFI")]
        print(f"  {s_name:8}  |I|={n:5}  mismatch={mis}  n_DMC(div)={n_dmc}")
    print("CONSTRAINT: mismatch must be reported; do not substitute G%384 or r'%3")

    print()
    print("=== T1 1.5MiB OWN COLUMN (not averaged with 1536B) ===")
    a = rows[("1.5MiB", "MRFI")]
    b = rows[("1536B", "MRFI")]
    print(f"1.5MiB  n_DMC={a[0]}  min/mean={a[3]:.4f}  mismatch={a[4]}")
    print(f"1536B   n_DMC={b[0]}  min/mean={b[3]:.4f}  mismatch={b[4]}")
    print("these two rows stay separate")

    print()
    print("=== T1 KILL-LINE S=4608B 100% good sequential ===")
    r = rows[("4608B", "MRFI")]
    k, n = r[6], r[5]
    line = min(384, k) / 3
    print(f"n_DMC={r[0]}  min/mean={r[3]:.4f}  kill if n_DMC<=min(384,K)/3={line:.4f} OR min/mean<0.85")
    print(f"kill_n_DMC={r[0] <= line}  kill_mm={r[3] < 0.85}")

    print()
    print("=== 3/9-factor vs power-of-two on SAME table (MRFI n_DMC) ===")
    prow(("S", "3-adic?", "MRFI", "%31", "%192", "%248", "XOR2"), (8, 8, 6, 6, 6, 6, 6))
    adic = {
        "512B": "2-power", "1KiB": "2-power", "1536B": "3", "3KiB": "3",
        "4608B": "9", "12KiB": "3", "1.5MiB": "3", "2MiB": "2-power",
    }
    for s_name, _ in S_LIST:
        vals = [rows[(s_name, m)][0] for m, _ in MAPPERS]
        prow((s_name, adic[s_name], *vals), (8, 8, 6, 6, 6, 6, 6))

    print()
    print("=== partial-good SEPARATE tables (S=4608B, MRFI, issued) ===")
    s = 4608
    k = k_of(0, s)
    n = min(k, Q_TOT)
    rng = random.Random(SEED)
    print("-- random dead fractions (not averaged with 1/3-pattern) --")
    prow(("kind", "n_DMC", "n_bank", "dead_hits", "min/mean"), (16, 7, 8, 10, 8))
    for frac in (0.0, 0.06, 0.12):
        rng_i = random.Random(SEED + int(frac * 1000))
        mask = mask_random(frac, rng_i)
        dmc_h, bank_h, mis, dead, _ = accumulate(map_mrfi, 0, s, n, mask=mask)
        n_dmc, n_bank, _, _, _, mm = stats(dmc_h, bank_h, n)
        prow((f"random {frac:.2f}", n_dmc, n_bank, dead, fmt(mm)), (16, 7, 8, 10, 8))
    print("-- 1/3-pattern (bank%3==0 dead, N_good=32) --")
    mask = mask_third()
    dmc_h, bank_h, mis, dead, _ = accumulate(map_mrfi, 0, s, n, mask=mask)
    n_dmc, n_bank, _, _, _, mm = stats(dmc_h, bank_h, n)
    prow(("1/3-pattern", n_dmc, n_bank, dead, fmt(mm)), (16, 7, 8, 10, 8))
    print("XOR retry <=2; +1 scan not implemented (forbidden)")
    print("GOOD_MAP is 1R shared: 120-core contention named, not timed here")
    print("no H100 / no CLAIM-as-input")
    return 0


if __name__ == "__main__":
    sys.exit(main())
