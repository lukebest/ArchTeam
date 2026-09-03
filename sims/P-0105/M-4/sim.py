#!/usr/bin/env python3
"""P-0105/M-4 SNS — cycle-level SimPy model.

Cycle-accurate (card + Dr.Sim must-verify):
  12b shear (y<<3 − y), 256×8 integer ROM, XOR, fold384 coarse-q+corr,
  bank_in = x'[9:4] mod 48, 2.25 KB bitmap + 48:6 PE 1-cycle retry.
Black box: DRAM timings (假设 H-DRAM-BB), cores, HA/pipe, refresh.
T2 model is imported read-only from models/P-0105/M-4/model.py.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import simpy

_HERE = Path(__file__).resolve().parent
_SIMS = _HERE.parents[1]
if str(_SIMS) not in sys.path:
    sys.path.insert(0, str(_SIMS))

from _lib.dram import BlackBoxDRAM, DramTiming  # noqa: E402
from _lib.stats import rel_err  # noqa: E402
from _lib.t2load import load_sns_t2  # noqa: E402
from _lib.workloads import (  # noqa: E402
    GRAIN,
    Q_TOT,
    SEED,
    ap_addrs,
    issued_count,
)

N_DMC = 384
N_BANK_PER = 48
S_CHECK = (0, 3, 42, 17, 68, 183, 62, 5, 8, 139, 146, 89, 204, 255, 166, 141)

STRATEGIES = ("sns", "mod384", "low", "high", "shear", "sbox")


def sbox_rom() -> tuple[int, ...]:
    rom = tuple((pow(u, 5, 256) + pow(u, 3, 256) + u) % 256 for u in range(256))
    if rom[:16] != S_CHECK:
        raise RuntimeError(f"S-box checksum FAIL {rom[:16]}")
    return rom


ROM = sbox_rom()


def shear(x: int, y: int) -> int:
    seven_y = ((y << 3) - y) & 0xFFF
    return (x + seven_y) & 0xFFF


def fold384(raw: int) -> int:
    q = min(raw // 384, 10)
    r = raw - 384 * q
    if r >= 384:
        r -= 384
    return r


def bank_from_xp(xp: int) -> int:
    w = (xp >> 4) & 0x3F
    return w if w < 48 else w - 48


def map_sns(phys: int) -> tuple[int, int, int, int]:
    x = (phys >> 9) & 0xFFF
    y = (phys >> 21) & 0xFFF
    xp = shear(x, y)
    z = ROM[(xp >> 4) & 0xFF] ^ (y & 0xFF)
    raw = (z << 4) | (xp & 0xF)
    return fold384(raw), bank_from_xp(xp), raw, xp


def map_shear(phys: int) -> tuple[int, int, int, int]:
    x = (phys >> 9) & 0xFFF
    y = (phys >> 21) & 0xFFF
    xp = shear(x, y)
    return fold384(xp), bank_from_xp(xp), xp, xp


def map_sbox(phys: int) -> tuple[int, int, int, int]:
    x = (phys >> 9) & 0xFFF
    z = ROM[(x >> 4) & 0xFF]
    raw = (z << 4) | (x & 0xF)
    return fold384(raw), bank_from_xp(x), raw, x


def map_mod384(phys: int) -> tuple[int, int, None, None]:
    g = phys >> 9
    return g % 384, g % 48, None, None


def map_low(phys: int) -> tuple[int, int, None, None]:
    g = phys >> 9
    x = g & 0x1FF
    dmc = x if x < 384 else x - 384
    return dmc, (g & 0x3F) % 48, None, None


def map_high(phys: int) -> tuple[int, int, None, None]:
    y = (phys >> 21) & 0xFFF
    return y % 384, y % 48, None, None


MAPPERS = {
    "sns": map_sns,
    "mod384": map_mod384,
    "low": map_low,
    "high": map_high,
    "shear": map_shear,
    "sbox": map_sbox,
}

T2_FN = {
    "sns": "map_sns",
    "mod384": "map_mod384",
    "low": "map_low",
    "high": "map_high",
    "shear": "map_shear_only",
    "sbox": "map_sbox_only",
}


def covering_bound() -> tuple[int, int, float]:
    hits = [10] * 384
    for i in range(256):
        hits[i] += 1
    mean = 4096 / 384
    var = sum((h - mean) ** 2 for h in hits) / 384
    return max(hits), min(hits), (var ** 0.5) / mean


def mask_full() -> int:
    return (1 << 48) - 1


def mask_random_frac(seed: int, n_dead: int = 3) -> int:
    import random

    rng = random.Random(seed)
    m = mask_full()
    for b in rng.sample(range(48), n_dead):
        m &= ~(1 << b)
    return m


def mask_third() -> int:
    m = 0
    for i in range(48):
        if i % 3 != 0:
            m |= 1 << i
    return m


def pe_retry(mask: int, bank: int, policy: str) -> tuple[int, int, bool]:
    """Return (bank, extra_cycles, poisoned). S-box does not participate."""
    if bank >= 0 and (mask >> bank) & 1:
        return bank, 0, False
    if policy == "first":
        order = range(48)
    else:
        order = ((bank + off) % 48 for off in range(1, 49))
    for i in order:
        if (mask >> i) & 1:
            return i, 1, False
    return -1, 1, True


@dataclass
class Occupancy:
    n_dmc: int
    n_bank: int
    x_rel: float
    min_mean: float
    bank_per_min: int
    bank_per_max: int
    kind8_min: int
    dmc_h: list[int]
    maxload: int
    minload: int
    pe_retries: int
    poisoned: int
    dead_pre_pe: int


def occupancy(
    strategy: str,
    base: int,
    stride: int,
    n: int | None = None,
    mask: int = mask_full(),
    pe_policy: str = "next",
) -> Occupancy:
    fn = MAPPERS[strategy]
    n = issued_count(base, stride, n)
    dmc_h = [0] * N_DMC
    bank_h = [0] * (N_DMC * N_BANK_PER)
    per_dmc_banks = [set() for _ in range(N_DMC)]
    kind8 = [set() for _ in range(N_DMC)]
    pe_retries = poisoned = dead_pre = 0
    for i in range(n):
        phys = base + i * stride
        dmc, bank, *_ = fn(phys)
        if ((mask >> bank) & 1) == 0:
            dead_pre += 1
        bank, extra, pois = pe_retry(mask, bank, pe_policy)
        pe_retries += extra
        if pois or bank < 0:
            poisoned += 1
            continue
        dmc_h[dmc] += 1
        bank_h[dmc * 48 + bank] += 1
        per_dmc_banks[dmc].add(bank)
        kind8[dmc].add(bank % 8)
    occ = [c for c in dmc_h if c]
    n_dmc = len(occ)
    n_bank = sum(1 for c in bank_h if c)
    mm = (min(occ) / (sum(occ) / len(occ))) if occ else 0.0
    x_rel = (min(N_DMC, n) / n_dmc) if n_dmc else float("inf")
    banks_per = [len(per_dmc_banks[d]) for d in range(N_DMC) if dmc_h[d]]
    k8 = [len(kind8[d]) for d in range(N_DMC) if dmc_h[d]]
    return Occupancy(
        n_dmc=n_dmc,
        n_bank=n_bank,
        x_rel=x_rel,
        min_mean=mm,
        bank_per_min=min(banks_per) if banks_per else 0,
        bank_per_max=max(banks_per) if banks_per else 0,
        kind8_min=min(k8) if k8 else 0,
        dmc_h=dmc_h,
        maxload=max(occ) if occ else 0,
        minload=min(occ) if occ else 0,
        pe_retries=pe_retries,
        poisoned=poisoned,
        dead_pre_pe=dead_pre,
    )


def rel_diff_n_dmc(vals: list[int]) -> float:
    if not vals:
        return 0.0
    m = sum(vals) / len(vals)
    return ((max(vals) - min(vals)) / m) if m else 0.0


@dataclass
class CycleResult:
    cycles: int
    completed: int
    warmup_discarded: int
    txns_per_cycle: float
    map_cycles: int
    pe_retries: int
    poisoned: int
    row_hit: int
    row_miss: int
    row_empty: int
    n_dmc: int
    n_bank: int
    min_mean_occ: float


@dataclass
class SimConfig:
    strategy: str = "sns"
    map_lat: int = 1
    map_ports: int = 1
    pe_policy: str = "next"
    mask: int = field(default_factory=mask_full)
    n_cores: int = 8
    outstanding: int = 16
    warmup_frac: float = 0.10
    dram: DramTiming = field(default_factory=DramTiming)


def run_cycles(addrs: list[int], cfg: SimConfig) -> CycleResult:
    """Same driver for every strategy: cores + mapper Resource + DRAM bbox."""
    env = simpy.Environment()
    mapper = simpy.Resource(env, capacity=max(1, cfg.map_ports))
    dram = BlackBoxDRAM(cfg.dram)
    fn = MAPPERS[cfg.strategy]
    done_at: list[int] = []
    stats = Counter()

    chunks = [addrs[i :: cfg.n_cores] for i in range(cfg.n_cores)]

    def core(env, queue):
        inflight = []
        idx = 0

        def one(phys):
            nonlocal stats
            with mapper.request() as req:
                yield req
                dmc, bank, *_ = fn(phys)
                bank, extra, pois = pe_retry(cfg.mask, bank, cfg.pe_policy)
                yield env.timeout(cfg.map_lat + extra)
                stats["map_cycles"] += cfg.map_lat + extra
                stats["pe_retries"] += extra
                if pois or bank < 0:
                    stats["poisoned"] += 1
                    return
            finish = dram.complete_at(int(env.now), dmc, bank, phys)
            wait = finish - int(env.now)
            if wait > 0:
                yield env.timeout(wait)
            done_at.append(int(env.now))
            stats["dmc", dmc] += 1
            stats["bank", dmc, bank] += 1

        while idx < len(queue) or inflight:
            while len(inflight) < cfg.outstanding and idx < len(queue):
                inflight.append(env.process(one(queue[idx])))
                idx += 1
            if not inflight:
                yield env.timeout(1)
                continue
            yield env.any_of(list(inflight))
            inflight = [p for p in inflight if not p.triggered]

    for c in range(cfg.n_cores):
        env.process(core(env, chunks[c]))
    env.run()

    done_at.sort()
    n_disc = int(len(done_at) * cfg.warmup_frac)
    useful = done_at[n_disc:]
    if len(useful) >= 2:
        span = useful[-1] - useful[0]
        tpc = (len(useful) - 1) / span if span > 0 else 0.0
        cycles = useful[-1]
    else:
        tpc = 0.0
        cycles = done_at[-1] if done_at else 0
    dmc_ids = {k[1] for k in stats if isinstance(k, tuple) and k[0] == "dmc"}
    bank_ids = {k for k in stats if isinstance(k, tuple) and k[0] == "bank"}
    loads = [stats[("dmc", d)] for d in dmc_ids]
    mm = (min(loads) / (sum(loads) / len(loads))) if loads else 0.0
    rs = dram.row_stats()
    return CycleResult(
        cycles=cycles,
        completed=len(done_at),
        warmup_discarded=n_disc,
        txns_per_cycle=tpc,
        map_cycles=stats["map_cycles"],
        pe_retries=stats["pe_retries"],
        poisoned=stats["poisoned"],
        row_hit=rs["row_hit"],
        row_miss=rs["row_miss"],
        row_empty=rs["row_empty"],
        n_dmc=len(dmc_ids),
        n_bank=len(bank_ids),
        min_mean_occ=mm,
    )


def t2_occupancy(strategy: str, base: int, stride: int, n: int | None = None) -> dict:
    t2 = load_sns_t2()
    fn = getattr(t2, T2_FN[strategy])
    n = issued_count(base, stride, n)
    return t2.run_mapper(fn, base, stride, n)


def compare_occupancy(strategy: str, base: int, stride: int, n: int | None = None) -> dict:
    t3 = occupancy(strategy, base, stride, n)
    t2 = t2_occupancy(strategy, base, stride, n)
    err_dmc = rel_err(t3.n_dmc, t2["n_DMC"])
    err_bank = rel_err(t3.n_bank, t2["n_bank"])
    flag = err_dmc > 0.30 or err_bank > 0.30
    return {
        "strategy": strategy,
        "base": base,
        "stride": stride,
        "t3_n_dmc": t3.n_dmc,
        "t2_n_dmc": t2["n_DMC"],
        "rel_err_n_dmc": err_dmc,
        "t3_n_bank": t3.n_bank,
        "t2_n_bank": t2["n_bank"],
        "rel_err_n_bank": err_bank,
        "t3_min_mean": t3.min_mean,
        "t2_min_mean": t2["min/mean"],
        "flag_gt_30pct": flag,
        "t3_bks": f"{t3.bank_per_min}-{t3.bank_per_max}",
        "t2_bks": f"{t2['bank_per_dmc_min']}-{t2['bank_per_dmc_max']}",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SNS cycle sim (single run)")
    p.add_argument("--strategy", choices=STRATEGIES, default="sns")
    p.add_argument("--base", type=int, default=0)
    p.add_argument("--stride", type=int, default=2 * 1024 * 1024)
    p.add_argument("--n-pts", type=int, default=256)
    p.add_argument("--n-cores", type=int, default=8)
    p.add_argument("--outstanding", type=int, default=16)
    p.add_argument("--map-lat", type=int, default=1)
    p.add_argument("--map-ports", type=int, default=1)
    p.add_argument("--pe-policy", choices=("next", "first"), default="next")
    p.add_argument("--page-policy", choices=("open", "close"), default="open")
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)
    n = issued_count(args.base, args.stride, args.n_pts)
    addrs = ap_addrs(args.base, args.stride, n)
    occ = occupancy(args.strategy, args.base, args.stride, n)
    cfg = SimConfig(
        strategy=args.strategy,
        map_lat=args.map_lat,
        map_ports=args.map_ports,
        pe_policy=args.pe_policy,
        n_cores=args.n_cores,
        outstanding=args.outstanding,
        dram=DramTiming(page_policy=args.page_policy),
    )
    cyc = run_cycles(addrs, cfg)
    cmp_ = compare_occupancy(args.strategy, args.base, args.stride, n)
    mx, mn, cv = covering_bound()
    print(f"SNS T3  strategy={args.strategy} base={args.base:#x} S={args.stride} |I|={n} seed={args.seed}")
    print(f"COVERING_BOUND (NOT golden): max={mx} min={mn} CV={cv:.4f}")
    print(f"occupancy n_DMC={occ.n_dmc} n_bank={occ.n_bank} min/mean={occ.min_mean:.4f} "
          f"bks/DMC={occ.bank_per_min}-{occ.bank_per_max} bank%8={occ.kind8_min}")
    print(f"cycles completed={cyc.completed} span={cyc.cycles} txns/cyc={cyc.txns_per_cycle:.6f} "
          f"row_hit={cyc.row_hit} miss={cyc.row_miss} empty={cyc.row_empty}")
    print(f"T2 compare n_DMC T3={cmp_['t3_n_dmc']} T2={cmp_['t2_n_dmc']} "
          f"rel_err={cmp_['rel_err_n_dmc']:.4f} flag>30%={cmp_['flag_gt_30pct']}")
    print("μ_d UNKNOWN; no GB/s; 0.85 is a pass line not a measured mean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
