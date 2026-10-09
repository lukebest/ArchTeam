#!/usr/bin/env python3
"""Unsigned cycle probe: M-5 exclusive epoch vs M-5r1 steal-back on Snp 15:1.

Reduced bbox (NOT full DV200 soc_sim): N=12, hop=1, flit=txn, no RBRG/HBM.
Results are UNSIGNED / NOT measured card-claim. Do not paste onto T3.

Arms:
  rebind-off  — static 1:1, no ghost (no congestion control)
  src-fc      — 1:1 bind, Dat outstanding halved (source-side FC)
  m5-15:1     — exclusive DAT_EPOCH (parent M-5)
  m5r1-15:1   — native residual steal-back (this revision)
"""

from __future__ import annotations

import argparse
import random
from collections import defaultdict, deque
from dataclasses import dataclass

SEED = 20260903
N = 12
K_CIRC = 2
N_PIPE = 2
EPOCH_MOD = 4


@dataclass
class Txn:
    tid: int
    src: int
    dst: int
    chi: str
    ready_at: int | None = None
    issue_at: int | None = None
    done_at: int | None = None


@dataclass
class Slot:
    kind: str = "empty"
    chi: str = ""
    src: int = -1
    dst: int = -1
    tid: int = -1
    epoch_tag: int = 0
    ghost: bool = False


@dataclass
class Die:
    fsm: str = "STEADY"
    bind_ghost: bool = False
    epoch: int = 0
    dwell: int = 0
    drain_visits: int = 0
    pipe_left: int = 0
    block_ghost: bool = False
    commit: bool = True


def dir_of(src: int, dst: int) -> str:
    cw = (dst - src) % N
    ccw = (src - dst) % N
    return "CW" if cw <= ccw else "CCW"


def nxt(node: int, d: str) -> int:
    return (node + 1) % N if d == "CW" else (node - 1) % N


def gen_uniform(n: int, chi: str, seed: int, tid0: int) -> list[Txn]:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        src = rng.randrange(N)
        dst = rng.randrange(N - 1)
        if dst >= src:
            dst += 1
        out.append(Txn(tid0 + i, src, dst, chi))
    return out


def gen_gather(n: int, tid0: int) -> list[Txn]:
    return [Txn(tid0 + i, 1 + (i % (N - 1)), 0, "Dat") for i in range(n)]


class Fabric:
    def __init__(self, arm: str, txns: list[Txn], outstanding: int, t_steady_laps: int):
        self.arm = arm
        self.sb = arm.startswith("m5r1")
        self.exclusive = arm.startswith("m5-")
        self.on = self.sb or self.exclusive
        self.src_fc = arm == "src-fc"
        self.ost = max(1, outstanding // 2) if self.src_fc else outstanding
        self.t_steady = max(1, t_steady_laps * N)
        # 15:1 dwell split (used only when rebind is on)
        self.dat_dwell = max(1, int(round(self.t_steady * 15 / 16)))
        self.snp_dwell = max(1, self.t_steady - self.dat_dwell)
        self.slots = {
            "Dat": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Snp": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Req": {"CW": [Slot() for _ in range(N)]},
        }
        self.slots["Req"]["CW"][0] = Slot(kind="sync")
        self.dies = [Die() for _ in range(N)]
        self.q = [{"Dat": deque(), "Snp": deque()} for _ in range(N)]
        self.txns = {t.tid: t for t in txns}
        for t in txns:
            self.q[t.src][t.chi].append(t)
        self.inflight = [0] * N
        self.cycle = 0
        self.stats: dict[str, int] = defaultdict(int)
        self.aligned = False
        self.want_ghost = True
        self.flips = 0
        self.commit_mask = 0
        self.committed = not self.on
        if not self.on:
            for d in self.dies:
                d.bind_ghost = False
                d.commit = True

    def _sync_at(self) -> int | None:
        for i, s in enumerate(self.slots["Req"]["CW"]):
            if s.kind == "sync":
                return i
        return None

    def _sniff_ghost(self, node: int, tag: int) -> bool:
        for d in ("CW", "CCW"):
            s = self.slots["Snp"][d][node]
            if s.kind == "payload" and s.ghost and (s.epoch_tag % EPOCH_MOD) == (tag % EPOCH_MOD):
                return True
        return False

    def _start_wave(self) -> None:
        self.commit_mask = 0
        self.committed = False
        for d in self.dies:
            d.fsm = "ARM_DRAIN"
            d.drain_visits = 0
            d.block_ghost = True
            d.commit = False
            d.dwell = 0

    def _fsm(self, node: int) -> None:
        if not self.on:
            return
        d = self.dies[node]
        if d.fsm == "STEADY":
            d.dwell += 1
            d.block_ghost = False
        if d.fsm == "ARM_DRAIN":
            d.block_ghost = True
            d.fsm = "DRAIN"
        if d.fsm == "DRAIN":
            d.block_ghost = True
            if d.drain_visits >= K_CIRC and not self._sniff_ghost(node, d.epoch):
                d.fsm = "FLIP"
                d.pipe_left = N_PIPE
        if d.fsm == "FLIP":
            d.block_ghost = True
            if d.pipe_left == N_PIPE:
                d.epoch += 1
                d.bind_ghost = self.want_ghost
                self.flips += 1
            d.pipe_left -= 1
            if d.pipe_left <= 0:
                d.fsm = "STEADY"
                d.block_ghost = False
                d.dwell = 0

    def _maybe_wave(self) -> None:
        if not self.on:
            return
        if any(d.fsm != "STEADY" for d in self.dies):
            return
        if self.flips == 0:
            self.want_ghost = True
            self._start_wave()
            return
        if not self.committed:
            return
        target = self.dat_dwell if self.dies[0].bind_ghost else self.snp_dwell
        if all(d.dwell >= target for d in self.dies):
            self.want_ghost = not self.want_ghost
            self._start_wave()

    def _complete(self, slot: Slot) -> None:
        t = self.txns.get(slot.tid)
        if t is None:
            return
        t.done_at = self.cycle
        self.inflight[t.src] = max(0, self.inflight[t.src] - 1)
        self.stats["complete", t.chi] += 1

    def _inject(self, node: int, chi: str, phys: str, dname: str, new, ghost: bool) -> bool:
        q = self.q[node][chi]
        if not q or self.inflight[node] >= self.ost:
            return False
        if new[phys][dname][node].kind != "empty":
            return False
        t = q.popleft()
        if t.ready_at is None:
            t.ready_at = self.cycle
        if t.issue_at is None:
            t.issue_at = self.cycle
            self.stats["issue", chi] += 1
        self.inflight[node] += 1
        new[phys][dname][node] = Slot(
            kind="payload",
            chi=chi,
            src=t.src,
            dst=t.dst,
            tid=t.tid,
            epoch_tag=self.dies[node].epoch,
            ghost=ghost,
        )
        if ghost:
            self.stats["ghost_inject"] += 1
        if chi == "Snp" and ghost is False and self.dies[node].bind_ghost:
            self.stats["steal_back"] += 1
        return True

    def _inject_node(self, node: int, new) -> None:
        d = self.dies[node]
        snp_q = self.q[node]["Snp"]
        dat_q = self.q[node]["Dat"]
        snp_pend = bool(snp_q) and self.inflight[node] < self.ost

        # Native Snp residual: never gated by epoch/drain in r1.
        # M-5 exclusive: only when bind is Snp identity (not ghost) and STEADY.
        if snp_pend:
            t = snp_q[0]
            dn = dir_of(node, t.dst)
            if self.exclusive:
                snp_ok = (not d.bind_ghost) and d.fsm == "STEADY" and not d.block_ghost
            else:
                snp_ok = True  # rebind-off, src-fc, and m5r1
            if t.ready_at is None:
                t.ready_at = self.cycle
            if snp_ok:
                if not self._inject(node, "Snp", "Snp", dn, new, False):
                    self.stats["snp_stall"] += 1
            else:
                self.stats["snp_stall"] += 1
            snp_pend = bool(self.q[node]["Snp"]) and self.inflight[node] < self.ost

        # Dat: main ring, plus ghost if eligible and (r1: no local Snp pending)
        if dat_q and self.inflight[node] < self.ost:
            t = dat_q[0]
            if t.ready_at is None:
                t.ready_at = self.cycle
            dn = dir_of(node, t.dst)
            ghost_ok = (
                self.on
                and d.bind_ghost
                and d.fsm == "STEADY"
                and not d.block_ghost
                and self.committed
            )
            if self.sb and snp_pend:
                ghost_ok = False
                self.stats["ghost_gated"] += 1
            placed = False
            if ghost_ok:
                placed = self._inject(node, "Dat", "Snp", dn, new, True)
            if not placed:
                if not self._inject(node, "Dat", "Dat", dn, new, False):
                    self.stats["dat_stall"] += 1

    def step(self) -> None:
        cur = self.slots
        new = {
            "Dat": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Snp": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Req": {"CW": [Slot() for _ in range(N)]},
        }
        # arrivals
        for phys in ("Dat", "Snp"):
            for dname in ("CW", "CCW"):
                for n in range(N):
                    s = cur[phys][dname][n]
                    if s.kind != "payload":
                        continue
                    if s.dst == n:
                        self._complete(s)
                    else:
                        new[phys][dname][n] = s
        # SYNC citizen on Req CW
        for n in range(N):
            s = cur["Req"]["CW"][n]
            if s.kind == "sync":
                die = self.dies[n]
                if die.fsm == "DRAIN":
                    die.drain_visits += 1
                if die.fsm == "STEADY" and not die.commit and self.on:
                    self.commit_mask |= 1 << n
                new["Req"]["CW"][n] = s
        if self.on and self.commit_mask == (1 << N) - 1:
            self.committed = True
            for die in self.dies:
                die.commit = True

        self._maybe_wave()
        for n in range(N):
            self._fsm(n)
        if not self.aligned and self.cycle >= N:
            if (not self.on) or (self.committed and all(d.fsm == "STEADY" for d in self.dies)):
                self.aligned = True

        if self.aligned:
            for n in range(N):
                self._inject_node(n, new)

        # rotate
        moved = {
            "Dat": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Snp": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Req": {"CW": [Slot() for _ in range(N)]},
        }
        for phys in ("Dat", "Snp"):
            for dname in ("CW", "CCW"):
                for n in range(N):
                    s = new[phys][dname][n]
                    if s.kind == "empty":
                        continue
                    moved[phys][dname][nxt(n, dname)] = s
        for n in range(N):
            s = new["Req"]["CW"][n]
            if s.kind == "sync":
                moved["Req"]["CW"][nxt(n, "CW")] = s
        self.slots = moved
        self.cycle += 1

    def pending(self) -> int:
        return sum(len(x["Dat"]) + len(x["Snp"]) for x in self.q)

    def run(self, limit: int) -> dict:
        while self.cycle < limit:
            self.step()
            if self.aligned and self.pending() == 0 and sum(self.inflight) == 0:
                break
        dat = [t for t in self.txns.values() if t.chi == "Dat"]
        snp = [t for t in self.txns.values() if t.chi == "Snp"]

        def span(xs: list[Txn]) -> int:
            # Ready→done, not inject→done: exclusive-epoch stall before the
            # first successful inject is part of Snp makespan (T3 endpoint).
            done = [t for t in xs if t.done_at is not None]
            if not done:
                return 0
            start = min((t.ready_at if t.ready_at is not None else t.issue_at or 0) for t in done)
            return max(1, max(t.done_at for t in done) - start)

        return {
            "arm": self.arm,
            "cycles": self.cycle,
            "aligned": self.aligned,
            "ms_dat": span(dat),
            "ms_snp": span(snp),
            "comp_dat": sum(1 for t in dat if t.done_at is not None),
            "comp_snp": sum(1 for t in snp if t.done_at is not None),
            "n_dat": len(dat),
            "n_snp": len(snp),
            "snp_stall": self.stats["snp_stall"],
            "steal_back": self.stats["steal_back"],
            "ghost_inject": self.stats["ghost_inject"],
            "ghost_gated": self.stats["ghost_gated"],
        }


def one_trial(arm: str, mode: str, seed: int, n_dat: int, n_snp: int, ost: int, laps: int) -> dict:
    if mode == "snp_path":
        txns = gen_uniform(n_snp, "Snp", seed, 0)
    elif mode == "mixed":
        txns = gen_gather(n_dat, 0) + gen_uniform(n_snp, "Snp", seed + 7919, 10_000)
    else:
        raise ValueError(mode)
    fab = Fabric(arm, txns, outstanding=ost, t_steady_laps=laps)
    return fab.run(limit=20_000)


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def run_suite(n_trials: int, seed0: int) -> list[dict]:
    arms = ("rebind-off", "src-fc", "m5-15:1", "m5r1-15:1")
    rows = []
    for mode, n_dat, n_snp in (("snp_path", 0, 48), ("mixed", 48, 6)):
        by_arm: dict[str, list[dict]] = {a: [] for a in arms}
        for i in range(n_trials):
            seed = seed0 + i
            for arm in arms:
                by_arm[arm].append(
                    one_trial(arm, mode, seed, n_dat, n_snp, ost=16, laps=8)
                )
        off_snp = mean([r["ms_snp"] for r in by_arm["rebind-off"] if r["ms_snp"]])
        off_dat = mean([r["ms_dat"] for r in by_arm["rebind-off"] if r["ms_dat"]]) or 1.0
        for arm in arms:
            rs = by_arm[arm]
            ms_s = mean([r["ms_snp"] for r in rs])
            ms_d = mean([r["ms_dat"] for r in rs])
            rows.append(
                {
                    "mode": mode,
                    "arm": arm,
                    "ms_snp": ms_s,
                    "ms_dat": ms_d,
                    "snp_ratio": (ms_s / off_snp) if off_snp else float("nan"),
                    "dat_ratio": (ms_d / off_dat) if ms_d else float("nan"),
                    "comp_snp": mean([r["comp_snp"] for r in rs]),
                    "comp_dat": mean([r["comp_dat"] for r in rs]),
                    "n_snp": rs[0]["n_snp"],
                    "n_dat": rs[0]["n_dat"],
                    "snp_stall": mean([r["snp_stall"] for r in rs]),
                    "steal_back": mean([r["steal_back"] for r in rs]),
                    "ghost_inject": mean([r["ghost_inject"] for r in rs]),
                    "drop_snp": any(r["comp_snp"] < r["n_snp"] for r in rs),
                }
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--trials", type=int, default=3)
    args = p.parse_args(argv)
    print("P-0198/M-5r1 UNSIGNED cycle probe  (reduced bbox; NOT soc_sim; NOT card-claim)")
    print(f"SEED={args.seed} n_trials={args.trials} N={N}  do not paste onto T3")
    print()
    rows = run_suite(args.trials, args.seed)
    print(
        f"{'mode':8} {'arm':12} {'ms_snp':8} {'ms_dat':8} {'T_snp/off':10} "
        f"{'T_dat/off':10} {'kill1.4':7} {'<1.5625':8} {'compS':5} {'steal':7} {'ghost':7}"
    )
    for r in rows:
        kill = r["snp_ratio"] > 1.4 if r["snp_ratio"] == r["snp_ratio"] else False
        below = r["snp_ratio"] < 1.5625 if r["snp_ratio"] == r["snp_ratio"] else False
        print(
            f"{r['mode']:8} {r['arm']:12} {r['ms_snp']:8.1f} {r['ms_dat']:8.1f} "
            f"{r['snp_ratio']:10.3f} {r['dat_ratio']:10.3f} {str(kill):7} {str(below):8} "
            f"{r['comp_snp']:5.1f} {r['steal_back']:7.1f} {r['ghost_inject']:7.1f}"
        )
        if r["drop_snp"]:
            print("  WARN: Snp completion drop")
    print()
    print("UNSIGNED. Completions must not drop. Makespan/tail is the endpoint.")
    print("sb-off is the m5-15:1 column. ghost-off ≈ rebind-off Dat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
