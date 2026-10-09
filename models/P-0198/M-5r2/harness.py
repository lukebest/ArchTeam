#!/usr/bin/env python3
"""Unsigned cycle probe: M-5r2 k-slot stitch on existing Snp width.

Reduced bbox (NOT full DV200 soc_sim): N=12, hop=1, Dat beat = 1 txn,
Dat ×2 sub-rings, Snp ×1 ring, no RBRG/HBM/epoch/bind.
Results are UNSIGNED / NOT measured card-claim. Do not paste onto T3.

A Dat beat on the Snp ring occupies k native-width Snp slots (fragments).
KILL is judged at the worst k in the CHI-derived interval.
"""

from __future__ import annotations

import argparse
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field

SEED = 20261009
N = 12
T_PARTIAL = 4 * N  # dest CAM timeout (≈ 2 full circles)
MAX_FRAG_HOPS = 4 * N
N_CAM = N  # one assembling beat per source at dest
LIMIT = 30_000

# CHI-derived sweep (see width.py). KILL at worst.
K_SWEEP = (7, 8, 9, 14, 16, 18)
K_WORST = 18


@dataclass
class Txn:
    tid: int
    src: int
    dst: int
    chi: str
    ready_at: int | None = None
    issue_at: int | None = None
    done_at: int | None = None
    frags_needed: int = 1
    kind: str = ""  # gather / p2p / snp


@dataclass
class Slot:
    kind: str = "empty"
    chi: str = ""
    src: int = -1
    dst: int = -1
    tid: int = -1
    ghost: bool = False
    frag_ix: int = 0
    hops: int = 0


@dataclass
class Stitcher:
    beat: Txn | None = None
    next_frag: int = 0


@dataclass
class CamEnt:
    bits: set[int] = field(default_factory=set)
    alloc_at: int = 0
    ready: bool = False
    src: int = -1
    tid: int = -1


def dir_of(src: int, dst: int) -> str:
    cw = (dst - src) % N
    ccw = (src - dst) % N
    return "CW" if cw <= ccw else "CCW"


def nxt(node: int, d: str) -> int:
    return (node + 1) % N if d == "CW" else (node - 1) % N


def gen_uniform(n: int, chi: str, seed: int, tid0: int, srcs: list[int] | None = None) -> list[Txn]:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        src = srcs[i % len(srcs)] if srcs else rng.randrange(N)
        dst = rng.randrange(N - 1)
        if dst >= src:
            dst += 1
        out.append(Txn(tid0 + i, src, dst, chi, kind="snp" if chi == "Snp" else "p2p"))
    return out


def gen_gather(n: int, tid0: int, sink: int = 0) -> list[Txn]:
    return [
        Txn(tid0 + i, 1 + (i % (N - 1)), sink, "Dat", kind="gather")
        for i in range(n)
    ]


def gen_inference_mix(n_dat: int, n_snp: int, seed: int) -> list[Txn]:
    """15:1 = offered Dat beats : Snp flits. 75% kv_decode gather + 25% P2P.

    Snp sources sit on the last hop into the gather sink (nodes 1 and N-1).
    """
    n_g = int(round(n_dat * 0.75))
    n_p = n_dat - n_g
    txns = gen_gather(n_g, 0, sink=0)
    txns += gen_uniform(n_p, "Dat", seed, 10_000)
    # hot-path last hops toward sink 0
    txns += gen_uniform(n_snp, "Snp", seed + 7919, 20_000, srcs=[1, N - 1])
    return txns


class Fabric:
    def __init__(
        self,
        arm: str,
        txns: list[Txn],
        k: int,
        outstanding: int,
        cap: bool,
    ):
        self.arm = arm
        self.k = max(1, k)
        self.ghost_on = arm in ("stitch", "header-only", "drain-off", "cap-off")
        self.cap_on = cap and arm != "cap-off"
        self.g_node = self.k if self.cap_on else 10**9
        self.src_fc = arm == "src-fc"
        self.ost = max(1, outstanding // 2) if self.src_fc else outstanding
        # Dat ×2 sub-rings, Snp ×1; bidirectional; 1 slot / dir / CS
        self.slots = {
            "Dat0": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Dat1": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Snp": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
        }
        self.q: list[dict[str, deque]] = [{"Dat": deque(), "Snp": deque()} for _ in range(N)]
        self.txns = {t.tid: t for t in txns}
        for t in txns:
            t.frags_needed = self.k if t.chi == "Dat" else 1
            self.q[t.src][t.chi].append(t)
        self.inflight = [0] * N
        self.ghost_frags = [0] * N  # per-node fragments on the Snp ring
        self.stitch = [Stitcher() for _ in range(N)]
        self.cam: list[dict[tuple[int, int], CamEnt]] = [dict() for _ in range(N)]
        self.holding: list[int | None] = [None for _ in range(N)]
        self.cycle = 0
        self.aligned = False
        self.stats: dict[str, int] = defaultdict(int)
        self.ghost_itag = 0  # must stay 0

    def _complete(self, tid: int) -> None:
        t = self.txns.get(tid)
        if t is None or t.done_at is not None:
            return
        t.done_at = self.cycle
        self.inflight[t.src] = max(0, self.inflight[t.src] - 1)
        self.stats["complete", t.chi] += 1

    def _cam_timeouts(self, dest: int) -> None:
        dead = []
        for key, ent in self.cam[dest].items():
            if not ent.ready and self.cycle - ent.alloc_at >= T_PARTIAL:
                dead.append(key)
        for key in dead:
            del self.cam[dest][key]
            self.stats["partial_drop"] += 1

    def _try_cam(self, s: Slot) -> bool:
        dest = s.dst
        self._cam_timeouts(dest)
        key = (s.src, s.tid)
        ent = self.cam[dest].get(key)
        if ent is None:
            if len(self.cam[dest]) >= N_CAM:
                self.stats["cam_full_orbit"] += 1
                return False
            ent = CamEnt(alloc_at=self.cycle, src=s.src, tid=s.tid)
            self.cam[dest][key] = ent
        if s.frag_ix in ent.bits:
            # duplicate fragment after orbit; consume it
            return True
        ent.bits.add(s.frag_ix)
        t = self.txns[s.tid]
        if len(ent.bits) >= t.frags_needed:
            ent.ready = True
            if self.holding[dest] is None:
                self.holding[dest] = s.tid
                del self.cam[dest][key]
            # else occupy CAM as ready until holding frees
        return True

    def _drain_holding(self) -> None:
        for n in range(N):
            tid = self.holding[n]
            if tid is None:
                continue
            self._complete(tid)
            self.holding[n] = None
            # promote a ready CAM entry
            for key, ent in list(self.cam[n].items()):
                if ent.ready:
                    self.holding[n] = ent.tid
                    del self.cam[n][key]
                    break

    def _place(self, new, phys: str, dname: str, node: int, t: Txn, ghost: bool, frag_ix: int) -> bool:
        if new[phys][dname][node].kind != "empty":
            return False
        if t.ready_at is None:
            t.ready_at = self.cycle
        if t.issue_at is None:
            t.issue_at = self.cycle
            self.stats["issue", t.chi] += 1
        new[phys][dname][node] = Slot(
            kind="payload",
            chi=t.chi,
            src=t.src,
            dst=t.dst,
            tid=t.tid,
            ghost=ghost,
            frag_ix=frag_ix,
        )
        return True

    def _take_dat(self, node: int) -> Txn | None:
        q = self.q[node]["Dat"]
        if not q or self.inflight[node] >= self.ost:
            return None
        t = q.popleft()
        self.inflight[node] += 1
        if t.ready_at is None:
            t.ready_at = self.cycle
        return t

    def _emit_frag(self, node: int, new) -> bool:
        st = self.stitch[node]
        if st.beat is None:
            return False
        if self.ghost_frags[node] >= self.g_node:
            self.stats["cap_block"] += 1
            return False
        t = st.beat
        dn = dir_of(node, t.dst)
        if not self._place(new, "Snp", dn, node, t, True, st.next_frag):
            return False
        self.ghost_frags[node] += 1
        self.stats["ghost_inject"] += 1
        st.next_frag += 1
        if st.next_frag >= self.k:
            # serializer frees; data now lives only in on-ring fragments
            st.beat = None
            st.next_frag = 0
            self.stats["stitch_done"] += 1
        return True

    def _inject_node(self, node: int, new) -> None:
        snp_q = self.q[node]["Snp"]
        snp_pend = bool(snp_q) and self.inflight[node] < self.ost

        # Native Snp: strict priority on the Snp ring. Never gated by ghost/epoch.
        if snp_pend:
            t = snp_q[0]
            dn = dir_of(node, t.dst)
            if t.ready_at is None:
                t.ready_at = self.cycle
            if new["Snp"][dn][node].kind == "empty":
                snp_q.popleft()
                self.inflight[node] += 1
                self._place(new, "Snp", dn, node, t, False, 0)
                self.stats["snp_inject"] += 1
            else:
                self.stats["snp_stall"] += 1
            snp_pend = bool(self.q[node]["Snp"]) and self.inflight[node] < self.ost

        # Continue stitching a held beat (1-deep serializer — charged).
        if self.ghost_on and self.stitch[node].beat is not None and not snp_pend:
            self._emit_frag(node, new)
            snp_pend = bool(self.q[node]["Snp"]) and self.inflight[node] < self.ost

        # Native Dat: prefer the two Dat sub-rings. Ghost only on overflow.
        if self.q[node]["Dat"] and self.inflight[node] < self.ost:
            t0 = self.q[node]["Dat"][0]
            if t0.ready_at is None:
                t0.ready_at = self.cycle
            dn = dir_of(node, t0.dst)
            placed = False
            for phys in ("Dat0", "Dat1"):
                if new[phys][dn][node].kind == "empty":
                    t = self._take_dat(node)
                    if t is None:
                        break
                    placed = self._place(new, phys, dn, node, t, False, 0)
                    break
            if not placed:
                self.stats["dat_stall"] += 1
                if (
                    self.ghost_on
                    and self.stitch[node].beat is None
                    and not snp_pend
                    and self.ghost_frags[node] < self.g_node
                ):
                    t = self._take_dat(node)
                    if t is not None:
                        self.stitch[node] = Stitcher(beat=t, next_frag=0)
                        self.stats["overflow_to_ghost"] += 1
                        self._emit_frag(node, new)

    def _arrive(self, s: Slot) -> Slot | None:
        """Return None if consumed; the slot (maybe still payload) otherwise."""
        if s.kind != "payload":
            return None
        s.hops += 1
        if s.hops > MAX_FRAG_HOPS:
            self.stats["frag_drop"] += 1
            if s.ghost:
                self.ghost_frags[s.src] = max(0, self.ghost_frags[s.src] - 1)
            # no source-side retry buffer
            return None
        if s.dst != getattr(s, "_at", None):
            # dest check is done by caller with current node
            pass
        return s

    def step(self) -> None:
        cur = self.slots
        new = {
            "Dat0": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Dat1": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Snp": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
        }
        # arrivals at current node, then keep non-ejected
        for phys in ("Dat0", "Dat1", "Snp"):
            for dname in ("CW", "CCW"):
                for n in range(N):
                    s = cur[phys][dname][n]
                    if s.kind != "payload":
                        continue
                    if s.dst == n:
                        if s.ghost:
                            if self._try_cam(s):
                                self.ghost_frags[s.src] = max(0, self.ghost_frags[s.src] - 1)
                                self.stats["ghost_eject"] += 1
                                continue
                            self.stats["ghost_orbit"] += 1
                        else:
                            self._complete(s.tid)
                            continue
                    if s.hops + 1 > MAX_FRAG_HOPS:
                        self.stats["frag_drop"] += 1
                        if s.ghost:
                            self.ghost_frags[s.src] = max(0, self.ghost_frags[s.src] - 1)
                        continue
                    s.hops += 1
                    new[phys][dname][n] = s

        self._drain_holding()

        if not self.aligned and self.cycle >= N:
            self.aligned = True
        if self.aligned:
            for n in range(N):
                self._inject_node(n, new)

        moved = {
            "Dat0": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Dat1": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
            "Snp": {d: [Slot() for _ in range(N)] for d in ("CW", "CCW")},
        }
        for phys in ("Dat0", "Dat1", "Snp"):
            for dname in ("CW", "CCW"):
                for n in range(N):
                    s = new[phys][dname][n]
                    if s.kind == "empty":
                        continue
                    moved[phys][dname][nxt(n, dname)] = s
        self.slots = moved
        self.cycle += 1

    def pending(self) -> int:
        qn = sum(len(x["Dat"]) + len(x["Snp"]) for x in self.q)
        st = sum(1 for s in self.stitch if s.beat is not None)
        return qn + st

    def run(self, limit: int) -> dict:
        while self.cycle < limit:
            self.step()
            if (
                self.aligned
                and self.pending() == 0
                and sum(self.inflight) == 0
                and all(not c for c in self.cam)
                and all(h is None for h in self.holding)
            ):
                break
        dat = [t for t in self.txns.values() if t.chi == "Dat"]
        snp = [t for t in self.txns.values() if t.chi == "Snp"]

        def span(xs: list[Txn]) -> int:
            done = [t for t in xs if t.done_at is not None]
            if not done:
                return 0
            start = min((t.ready_at if t.ready_at is not None else t.issue_at or 0) for t in done)
            return max(1, max(t.done_at for t in done) - start)

        return {
            "arm": self.arm,
            "k": self.k,
            "cycles": self.cycle,
            "ms_dat": span(dat),
            "ms_snp": span(snp),
            "comp_dat": sum(1 for t in dat if t.done_at is not None),
            "comp_snp": sum(1 for t in snp if t.done_at is not None),
            "n_dat": len(dat),
            "n_snp": len(snp),
            "snp_stall": self.stats["snp_stall"],
            "ghost_inject": self.stats["ghost_inject"],
            "ghost_orbit": self.stats["ghost_orbit"],
            "partial_drop": self.stats["partial_drop"],
            "frag_drop": self.stats["frag_drop"],
            "cam_full_orbit": self.stats["cam_full_orbit"],
            "overflow_to_ghost": self.stats["overflow_to_ghost"],
            "ghost_itag": self.ghost_itag,
            "cap_block": self.stats["cap_block"],
        }


def one_trial(arm: str, mode: str, seed: int, k: int, n_dat: int, n_snp: int, ost: int) -> dict:
    if mode == "snp_path":
        txns = gen_uniform(n_snp, "Snp", seed, 0)
    elif mode == "mixed":
        txns = gen_inference_mix(n_dat, n_snp, seed)
    else:
        raise ValueError(mode)
    cap = arm != "cap-off"
    fab = Fabric(arm, txns, k=k, outstanding=ost, cap=cap)
    return fab.run(LIMIT)


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def summarize(arm: str, k: int, mode: str, rs: list[dict], off_snp: float, off_dat: float) -> dict:
    ms_s = mean([r["ms_snp"] for r in rs])
    ms_d = mean([r["ms_dat"] for r in rs])
    return {
        "mode": mode,
        "arm": arm,
        "k": k,
        "ms_snp": ms_s,
        "ms_dat": ms_d,
        "snp_ratio": (ms_s / off_snp) if off_snp else float("nan"),
        "dat_ratio": (ms_d / off_dat) if off_dat and ms_d else float("nan"),
        "comp_snp": mean([r["comp_snp"] for r in rs]),
        "comp_dat": mean([r["comp_dat"] for r in rs]),
        "n_snp": rs[0]["n_snp"],
        "n_dat": rs[0]["n_dat"],
        "ghost_inject": mean([r["ghost_inject"] for r in rs]),
        "partial_drop": mean([r["partial_drop"] for r in rs]),
        "frag_drop": mean([r["frag_drop"] for r in rs]),
        "ghost_orbit": mean([r["ghost_orbit"] for r in rs]),
        "drop_snp": any(r["comp_snp"] < r["n_snp"] for r in rs),
        "drop_dat": any(r["comp_dat"] < r["n_dat"] for r in rs),
        "ghost_itag": sum(r["ghost_itag"] for r in rs),
    }


def run_suite(n_trials: int, seed0: int, n_dat: int, n_snp: int, ost: int) -> list[dict]:
    rows = []
    # snp_path: no Dat ⇒ no ghost. Ratio is constructive 1. Must label.
    by = {"stitch-off": [], "stitch": []}
    for i in range(n_trials):
        seed = seed0 + i
        by["stitch-off"].append(one_trial("stitch-off", "snp_path", seed, K_WORST, 0, 48, ost))
        by["stitch"].append(one_trial("stitch", "snp_path", seed, K_WORST, 0, 48, ost))
    off_s = mean([r["ms_snp"] for r in by["stitch-off"] if r["ms_snp"]])
    for arm in ("stitch-off", "stitch"):
        rows.append(summarize(arm, K_WORST, "snp_path", by[arm], off_s, 1.0))

    # 15:1 inference mix, sweep k. stitch-off is independent of k (run once).
    off_runs = [one_trial("stitch-off", "mixed", seed0 + i, K_WORST, n_dat, n_snp, ost) for i in range(n_trials)]
    off_snp = mean([r["ms_snp"] for r in off_runs if r["ms_snp"]]) or 1.0
    off_dat = mean([r["ms_dat"] for r in off_runs if r["ms_dat"]]) or 1.0
    rows.append(summarize("stitch-off", K_WORST, "mixed", off_runs, off_snp, off_dat))

    srcfc = [one_trial("src-fc", "mixed", seed0 + i, K_WORST, n_dat, n_snp, ost) for i in range(n_trials)]
    rows.append(summarize("src-fc", K_WORST, "mixed", srcfc, off_snp, off_dat))

    for k in K_SWEEP:
        st = [one_trial("stitch", "mixed", seed0 + i, k, n_dat, n_snp, ost) for i in range(n_trials)]
        rows.append(summarize("stitch", k, "mixed", st, off_snp, off_dat))
        cap = [one_trial("cap-off", "mixed", seed0 + i, k, n_dat, n_snp, ost) for i in range(n_trials)]
        rows.append(summarize("cap-off", k, "mixed", cap, off_snp, off_dat))

    # header-only / drain-off ≡ stitch (no epoch). Prove identity at worst k.
    ho = [one_trial("header-only", "mixed", seed0 + i, K_WORST, n_dat, n_snp, ost) for i in range(n_trials)]
    dr = [one_trial("drain-off", "mixed", seed0 + i, K_WORST, n_dat, n_snp, ost) for i in range(n_trials)]
    rows.append(summarize("header-only", K_WORST, "mixed", ho, off_snp, off_dat))
    rows.append(summarize("drain-off", K_WORST, "mixed", dr, off_snp, off_dat))

    k1 = [one_trial("stitch", "mixed", seed0 + i, 1, n_dat, n_snp, ost) for i in range(n_trials)]
    rows.append(summarize("k1-cheat", 1, "mixed", k1, off_snp, off_dat))
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--n-dat", type=int, default=150)
    p.add_argument("--n-snp", type=int, default=10)
    p.add_argument("--ost", type=int, default=16)
    args = p.parse_args(argv)
    assert args.n_dat / args.n_snp == 15.0, "15:1 mix must be exact"
    print("P-0198/M-5r2 UNSIGNED k-slot stitch probe  (reduced bbox; NOT soc_sim; NOT card-claim)")
    print(
        f"SEED={args.seed} n_trials={args.trials} N={N} "
        f"mix={args.n_dat}:{args.n_snp} ost={args.ost}  Dat×2 Snp×1"
    )
    print(f"k sweep={K_SWEEP}  KILL at worst k={K_WORST}  do not paste onto T3")
    print()
    rows = run_suite(args.trials, args.seed, args.n_dat, args.n_snp, args.ost)
    print(
        f"{'mode':8} {'arm':12} {'k':4} {'ms_snp':8} {'ms_dat':8} "
        f"{'T_snp/off':10} {'T_dat/off':10} {'kill1.4':7} {'ghost':7} {'pdrop':6} {'fdrop':6}"
    )
    worst_snp_mix = None
    worst_dat_mix = None
    for r in rows:
        ratio = r["snp_ratio"]
        kill = ratio == ratio and ratio > 1.4
        fake = " FAKE_WIDTH" if r["arm"] == "k1-cheat" or r["k"] == 1 and r["mode"] == "mixed" and r["arm"] != "stitch-off" else ""
        note = ""
        if r["mode"] == "snp_path":
            note = "  constructive" if r["n_dat"] == 0 else ""
        print(
            f"{r['mode']:8} {r['arm']:12} {r['k']:4} {r['ms_snp']:8.1f} {r['ms_dat']:8.1f} "
            f"{r['snp_ratio']:10.3f} {r['dat_ratio']:10.3f} {str(kill):7} "
            f"{r['ghost_inject']:7.1f} {r['partial_drop']:6.1f} {r['frag_drop']:6.1f}{fake}{note}"
        )
        if r["drop_snp"] or r["drop_dat"]:
            print(
                f"  WARN completion drop  snp={r['drop_snp']} dat={r['drop_dat']} "
                f"compS={r['comp_snp']:.1f}/{r['n_snp']} compD={r['comp_dat']:.1f}/{r['n_dat']}"
            )
        if r["ghost_itag"]:
            print("  FATAL: ghost issued i-tag")
        if r["mode"] == "mixed" and r["arm"] == "stitch" and r["k"] == K_WORST:
            worst_snp_mix = r["snp_ratio"]
            worst_dat_mix = r["dat_ratio"]

    print()
    # identity: header-only / drain-off must match stitch at worst k
    def find(arm, k, mode):
        return next(r for r in rows if r["arm"] == arm and r["k"] == k and r["mode"] == mode)

    st = find("stitch", K_WORST, "mixed")
    ho = find("header-only", K_WORST, "mixed")
    dr = find("drain-off", K_WORST, "mixed")
    same = (
        abs(st["ms_snp"] - ho["ms_snp"]) < 1e-9
        and abs(st["ms_dat"] - ho["ms_dat"]) < 1e-9
        and abs(st["ms_snp"] - dr["ms_snp"]) < 1e-9
        and abs(st["ms_dat"] - dr["ms_dat"]) < 1e-9
    )
    print(
        f"ablation identity header-only≡drain-off≡stitch @k={K_WORST}: "
        f"{same}  (no epoch/bind to turn off)"
    )
    print()
    print("UNSIGNED. Completions must not silently drop. Makespan/tail is the endpoint.")
    print("snp_path has no Dat ⇒ T_snp/off is constructive 1. Do not call that a win.")
    print("inference r≈1 (no shortening) eliminates per last-week rule 2.")
    if worst_snp_mix is not None and worst_dat_mix is not None:
        snp_fail = worst_snp_mix > 1.4
        dat_flat = worst_dat_mix >= 0.97
        print(
            f"worst-k={K_WORST} mixed  T_snp/off={worst_snp_mix:.3f} "
            f"{'KILL' if snp_fail else '≤1.4'}  "
            f"T_dat/off={worst_dat_mix:.3f} "
            f"{'r≈1 ELIMINATE' if dat_flat else 'shortened'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
