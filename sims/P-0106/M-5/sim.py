#!/usr/bin/env python3
"""P-0106/M-5 AffineRebind — cycle-level SimPy model.

Cycle-accurate (card + Dr.Sim must-verify):
  384×(α,β,n) CSR 1R, XOR_fold6 PIN, 6b×6b + true mod n, 48-wire kth-one,
  repair α search (candidates + gcd score), skip-dead / stacking / α=1 columns.
Black box: DRAM timings (假设 H-DRAM-BB), cores, HA/pipe, refresh.
T2 model is imported read-only from models/P-0106/M-5/model.py.
"""

from __future__ import annotations

import argparse
import math
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
from _lib.t2load import load_affine_t2  # noqa: E402
from _lib.workloads import AFFINE_DOC, SEED, ap_addrs, issued_count  # noqa: E402

N_DMC = 384
N_BANK_PER = 48
CAND = (1, 5, 7, 11, 13, 17, 19, 23, 25, 31, 35, 37, 41, 43, 47)
STRATEGIES = ("skip-dead", "stack", "modn-a1", "minimax")


def xor_fold6(g: int) -> int:
    # 假设 H-FOLD6 PIN — frozen; never retune taps
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
    if n <= 0:
        return 1
    best_a, best_s = None, None
    sgs = [s // 512 for _, s in AFFINE_DOC]
    for a in CAND:
        if math.gcd(a, n) != 1:
            continue
        score = max(math.gcd(a * sg, n) for sg in sgs)
        if best_s is None or score < best_s or (score == best_s and a < best_a):
            best_a, best_s = a, score
    return best_a if best_a is not None else 1


def mask_full() -> int:
    return (1 << 48) - 1


def mask_n40() -> int:
    dead = (0, 6, 12, 18, 24, 30, 36, 42)
    m = (1 << 48) - 1
    for d in dead:
        m &= ~(1 << d)
    return m


def mask_uniform(n_live: int) -> int:
    return (1 << n_live) - 1


def mask_third_bias() -> int:
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


def stack_dead(g6: int, mask: int) -> int:
    slot = g6 % 48
    if (mask >> slot) & 1:
        return slot
    for dist in range(1, 48):
        for s in ((slot + dist) % 48, (slot - dist) % 48):
            if (mask >> s) & 1:
                return s
    return -1


@dataclass
class CSR:
    alpha: list[int] = field(default_factory=lambda: [1] * N_DMC)
    beta: list[int] = field(default_factory=lambda: [0] * N_DMC)
    n: list[int] = field(default_factory=lambda: [48] * N_DMC)
    mask: list[int] = field(default_factory=lambda: [mask_full()] * N_DMC)
    generation: int = 0
    repaired: bool = False

    def repair(self, mask: int, policy: str, beta_mode: str = "zero") -> None:
        """Fence+drain assumed. Fill α via card search; never hand-write α=1 as 'rebound'."""
        n = popcount(mask)
        if policy == "minimax":
            a = alpha_search(n) if n else 1
        else:
            a = 1 if (n == 0 or math.gcd(1, n) == 1) else alpha_search(n)
        for d in range(N_DMC):
            self.mask[d] = mask
            self.n[d] = n
            self.alpha[d] = a
            self.beta[d] = (d & 0x3F) if beta_mode == "dmc" else 0
        self.generation += 1
        self.repaired = True


def map_one(phys: int, strategy: str, csr: CSR) -> tuple[int, int, int, int]:
    g = phys >> 9
    g6 = xor_fold6(g)
    dmc = upstream_dmc(g)
    mask = csr.mask[dmc]
    n = csr.n[dmc]
    if strategy == "skip-dead":
        bank = skip_dead(g6, mask)
        slot = g6 % 48
    elif strategy == "stack":
        bank = stack_dead(g6, mask)
        slot = g6 % 48
    else:
        if n <= 0:
            return dmc, -1, g6, -1
        a = csr.alpha[dmc]
        b = csr.beta[dmc]
        slot = (a * g6 + b) % n
        bank = kth_one(mask, slot)
    return dmc, bank, g6, slot


@dataclass
class Occupancy:
    n_dmc: int
    n_bank: int
    dead: int
    cls_min: int
    cls_max: int
    cls_mean: float
    min_mean: float
    n: int
    alpha: int
    classes_ap: int
    classes_net_min: int


def occupancy(strategy: str, mask: int, stride: int, n_pts: int | None = None,
              base: int = 0, beta_mode: str = "zero") -> Occupancy:
    csr = CSR()
    policy = "minimax" if strategy == "minimax" else "a1"
    csr.repair(mask, policy, beta_mode)
    n = issued_count(base, stride, n_pts)
    dmc_h = [0] * N_DMC
    bank_h = [0] * (N_DMC * N_BANK_PER)
    classes = [set() for _ in range(N_DMC)]
    dead = 0
    live_n = popcount(mask)
    for i in range(n):
        phys = base + i * stride
        dmc, bank, g6, slot = map_one(phys, strategy, csr)
        if bank < 0 or ((mask >> bank) & 1) == 0:
            dead += 1
            continue
        dmc_h[dmc] += 1
        bank_h[dmc * 48 + bank] += 1
        classes[dmc].add(bank)
    occ = [c for c in dmc_h if c]
    n_dmc = len(occ)
    cls = [len(classes[d]) for d in range(N_DMC) if dmc_h[d]]
    sg = stride >> 9
    classes_ap = (live_n // math.gcd(sg, live_n)) if live_n else 0
    return Occupancy(
        n_dmc=n_dmc,
        n_bank=sum(1 for c in bank_h if c),
        dead=dead,
        cls_min=min(cls) if cls else 0,
        cls_max=max(cls) if cls else 0,
        cls_mean=(sum(cls) / len(cls)) if cls else 0.0,
        min_mean=(min(occ) / (sum(occ) / len(occ))) if occ else 0.0,
        n=live_n,
        alpha=csr.alpha[0],
        classes_ap=classes_ap,
        classes_net_min=min(cls) if cls else 0,
    )


def gcd_table(mask: int) -> list[dict]:
    n = popcount(mask)
    a = alpha_search(n) if n else 1
    rows = []
    for name, s in AFFINE_DOC:
        sg = s >> 9
        g = math.gcd(sg, n) if n else 0
        ga = math.gcd(a * sg, n) if n else 0
        rows.append(
            {
                "S": name,
                "S_g": sg,
                "n": n,
                "alpha_minimax": a,
                "gcd_Sg_n": g,
                "gcd_aSg_n": ga,
                "classes_AP": (n // g) if g else 0,
                "identity_holds": ga == g,
            }
        )
    return rows


@dataclass
class CycleResult:
    cycles: int
    completed: int
    warmup_discarded: int
    txns_per_cycle: float
    decode_cycles: int
    dead: int
    row_hit: int
    row_miss: int
    n_dmc: int
    n_bank: int
    cls_mean: float
    repair_done: bool


@dataclass
class SimConfig:
    strategy: str = "minimax"
    mask: int = field(default_factory=mask_n40)
    decode_lat: int = 2
    csr_ports: int = 1
    beta_mode: str = "zero"
    n_cores: int = 8
    outstanding: int = 16
    warmup_frac: float = 0.10
    dram: DramTiming = field(default_factory=DramTiming)
    allow_undrained_repair: bool = False


def run_cycles(addrs: list[int], cfg: SimConfig) -> CycleResult:
    """REPAIR completes before traffic. Same driver for every strategy."""
    csr = CSR()
    policy = "minimax" if cfg.strategy == "minimax" else "a1"
    csr.repair(cfg.mask, policy, cfg.beta_mode)
    if not csr.repaired:
        raise RuntimeError("REPAIR did not complete before RUN")

    env = simpy.Environment()
    csr_port = simpy.Resource(env, capacity=max(1, cfg.csr_ports))
    dram = BlackBoxDRAM(cfg.dram)
    done_at: list[int] = []
    stats = Counter()
    classes = [set() for _ in range(N_DMC)]
    chunks = [addrs[i :: cfg.n_cores] for i in range(cfg.n_cores)]

    def core(env, queue):
        inflight = []
        idx = 0

        def one(phys):
            with csr_port.request() as req:
                yield req
                dmc, bank, g6, slot = map_one(phys, cfg.strategy, csr)
                # 2-cycle decode: mul-mod || CSR/mask read, then kth-one
                yield env.timeout(cfg.decode_lat)
                stats["decode_cycles"] += cfg.decode_lat
                if bank < 0 or ((csr.mask[dmc] >> bank) & 1) == 0:
                    stats["dead"] += 1
                    return
            finish = dram.complete_at(int(env.now), dmc, bank, phys)
            wait = finish - int(env.now)
            if wait > 0:
                yield env.timeout(wait)
            done_at.append(int(env.now))
            stats["dmc", dmc] += 1
            stats["bank", dmc, bank] += 1
            classes[dmc].add(bank)

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
    cls = [len(classes[d]) for d in dmc_ids]
    rs = dram.row_stats()
    return CycleResult(
        cycles=cycles,
        completed=len(done_at),
        warmup_discarded=n_disc,
        txns_per_cycle=tpc,
        decode_cycles=stats["decode_cycles"],
        dead=stats["dead"],
        row_hit=rs["row_hit"],
        row_miss=rs["row_miss"],
        n_dmc=len(dmc_ids),
        n_bank=len(bank_ids),
        cls_mean=(sum(cls) / len(cls)) if cls else 0.0,
        repair_done=csr.repaired,
    )


def t2_run(kind: str, mask: int, alpha: int, stride: int, n_pts: int) -> dict:
    t2 = load_affine_t2()
    return t2.run(kind, mask, alpha, stride, n_pts)


def compare_occupancy(strategy: str, mask: int, stride: int, n_pts: int | None = None,
                      base: int = 0) -> dict:
    t3 = occupancy(strategy, mask, stride, n_pts, base)
    n = issued_count(base, stride, n_pts)
    if strategy == "skip-dead":
        t2 = t2_run("skip-dead", mask, 1, stride, n)
    elif strategy == "stack":
        t2 = None  # T2 has no stacking column
    else:
        t2 = t2_run("modn", mask, t3.alpha, stride, n)
    out = {
        "strategy": strategy,
        "stride": stride,
        "t3_cls_mean": t3.cls_mean,
        "t3_n_bank": t3.n_bank,
        "t3_dead": t3.dead,
        "t3_alpha": t3.alpha,
        "t3_classes_ap": t3.classes_ap,
        "flag_gt_30pct": False,
        "rel_err_cls": 0.0,
        "rel_err_n_bank": 0.0,
    }
    if t2 is not None:
        out["t2_cls_mean"] = t2["cls_mean"]
        out["t2_n_bank"] = t2["n_bank"]
        out["t2_dead"] = t2["dead"]
        out["rel_err_cls"] = rel_err(t3.cls_mean, t2["cls_mean"])
        out["rel_err_n_bank"] = rel_err(t3.n_bank, t2["n_bank"])
        out["flag_gt_30pct"] = out["rel_err_cls"] > 0.30 or out["rel_err_n_bank"] > 0.30
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="AffineRebind cycle sim (single run)")
    p.add_argument("--strategy", choices=STRATEGIES, default="minimax")
    p.add_argument("--mask", choices=("full", "n40", "unif36", "third"), default="n40")
    p.add_argument("--stride", type=int, default=2 * 1024 * 1024)
    p.add_argument("--n-pts", type=int, default=256)
    p.add_argument("--n-cores", type=int, default=8)
    p.add_argument("--outstanding", type=int, default=16)
    p.add_argument("--decode-lat", type=int, default=2)
    p.add_argument("--csr-ports", type=int, default=1)
    p.add_argument("--beta", choices=("zero", "dmc"), default="zero")
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)
    masks = {"full": mask_full(), "n40": mask_n40(), "unif36": mask_uniform(36), "third": mask_third_bias()}
    mask = masks[args.mask]
    n = issued_count(0, args.stride, args.n_pts)
    addrs = ap_addrs(0, args.stride, n)
    occ = occupancy(args.strategy, mask, args.stride, n)
    cfg = SimConfig(
        strategy=args.strategy,
        mask=mask,
        decode_lat=args.decode_lat,
        csr_ports=args.csr_ports,
        beta_mode=args.beta,
        n_cores=args.n_cores,
        outstanding=args.outstanding,
    )
    cyc = run_cycles(addrs, cfg)
    cmp_ = compare_occupancy(args.strategy, mask, args.stride, n)
    print(f"AffineRebind T3 strategy={args.strategy} mask={args.mask} S={args.stride} |I|={n} seed={args.seed}")
    print(f"occupancy n_DMC={occ.n_dmc} n_bank={occ.n_bank} dead={occ.dead} "
          f"cls_mean={occ.cls_mean:.4f} α={occ.alpha} classes_AP={occ.classes_ap}")
    print(f"cycles completed={cyc.completed} txns/cyc={cyc.txns_per_cycle:.6f} "
          f"dead={cyc.dead} repair_done={cyc.repair_done}")
    print(f"T2 compare cls T3={cmp_['t3_cls_mean']:.4f} T2={cmp_.get('t2_cls_mean', float('nan'))} "
          f"rel_err={cmp_['rel_err_cls']:.4f} flag>30%={cmp_['flag_gt_30pct']}")
    print("XOR_fold6 taps frozen; α search is a constant on gcd; no GB/s; no H100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
