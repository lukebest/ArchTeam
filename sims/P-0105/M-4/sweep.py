#!/usr/bin/env python3
"""Parameter sweep + T2 compare for P-0105/M-4 SNS.

One-command smoke:
  python3 sims/P-0105/M-4/sweep.py --mode smoke

Night (21:00) full:
  python3 sims/P-0105/M-4/sweep.py --mode night
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SIMS = _HERE.parents[1]
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_SIMS) not in sys.path:
    sys.path.insert(0, str(_SIMS))

from _lib.dram import DramTiming  # noqa: E402
from _lib.stats import ci95, fmt_ci  # noqa: E402
from _lib.workloads import (  # noqa: E402
    ALIGNED_2MIB,
    GRAIN_BASES,
    SEED,
    SNS_STRIDES,
    ap_addrs,
    issued_count,
)
from sim import (  # noqa: E402
    STRATEGIES,
    SimConfig,
    compare_occupancy,
    covering_bound,
    mask_full,
    mask_random_frac,
    mask_third,
    occupancy,
    rel_diff_n_dmc,
    run_cycles,
)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _plot(path: Path, labels: list[str], t2: list[float], t3: list[float], ylabel: str, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    x = range(len(labels))
    w = 0.38
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar([i - w / 2 for i in x], t2, w, label="T2 occupancy")
    ax.bar([i + w / 2 for i in x], t3, w, label="T3 occupancy")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def sweep(mode: str, out: Path, seed: int, n_trials: int, n_pts: int | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    mx, mn, cv = covering_bound()

    if mode == "smoke":
        strides = [SNS_STRIDES[0], SNS_STRIDES[-1]]  # 2MiB, 512B
        bases_grain = GRAIN_BASES[:4]
        bases_align = ALIGNED_2MIB[:2]
        strategies = ("sns", "mod384", "sbox", "shear")
        cycle_strats = ("sns", "mod384")
        n_pts_cyc = n_pts if n_pts is not None else 256
        n_trials = min(n_trials, 3)
        pe_masks = [("full", mask_full())]
        map_ports_list = (1,)
        map_lats = (1,)
        page_pols = ("open",)
    else:
        strides = list(SNS_STRIDES)
        bases_grain = GRAIN_BASES
        bases_align = ALIGNED_2MIB
        strategies = STRATEGIES
        cycle_strats = ("sns", "mod384", "low", "high")
        n_pts_cyc = n_pts if n_pts is not None else 512
        pe_masks = [
            ("full", mask_full()),
            ("rand1/16", mask_random_frac(seed, 3)),
            ("third", mask_third()),
        ]
        map_ports_list = (1, 4)
        map_lats = (1, 2)
        page_pols = ("open", "close")

    occ_rows = []
    cmp_rows = []
    for s_name, s in strides:
        for fam, bases in (("grain512", bases_grain), ("align2MiB", bases_align)):
            if s_name == "4608B" and fam == "align2MiB":
                continue
            nd_by_strat: dict[str, list[int]] = {st: [] for st in strategies}
            for st in strategies:
                for b in bases:
                    t3 = occupancy(st, b, s, n_pts)
                    cmp = compare_occupancy(st, b, s, n_pts)
                    nd_by_strat[st].append(t3.n_dmc)
                    occ_rows.append(
                        {
                            "S": s_name,
                            "family": fam,
                            "base": hex(b),
                            "strategy": st,
                            "n_DMC": t3.n_dmc,
                            "n_bank": t3.n_bank,
                            "min_mean": f"{t3.min_mean:.4f}",
                            "bks_per_dmc": f"{t3.bank_per_min}-{t3.bank_per_max}",
                            "bank8": t3.kind8_min,
                            "maxload": t3.maxload,
                            "minload": t3.minload,
                            "note": "4608B alone" if s_name == "4608B" else "",
                        }
                    )
                    cmp_rows.append(
                        {
                            "S": s_name,
                            "family": fam,
                            "base": hex(b),
                            "strategy": st,
                            **{k: cmp[k] for k in (
                                "t3_n_dmc", "t2_n_dmc", "rel_err_n_dmc",
                                "t3_n_bank", "t2_n_bank", "rel_err_n_bank",
                                "flag_gt_30pct",
                            )},
                        }
                    )
            for st, vals in nd_by_strat.items():
                occ_rows.append(
                    {
                        "S": s_name,
                        "family": fam,
                        "base": "REL_DIFF",
                        "strategy": st,
                        "n_DMC": f"{fmt_ci(vals, 2)}",
                        "n_bank": "",
                        "min_mean": "",
                        "bks_per_dmc": "",
                        "bank8": "",
                        "maxload": "",
                        "minload": "",
                        "note": f"rel_diff={rel_diff_n_dmc(vals):.4f}",
                    }
                )

    # cycle-level BW: same driver, baseline vs proposal, N seeded trials
    cyc_rows = []
    tpc_store: dict[tuple, list[float]] = {}
    for trial in range(n_trials):
        tseed = seed + trial
        b = GRAIN_BASES[trial % len(GRAIN_BASES)]
        for s_name, s in strides[: 2 if mode == "smoke" else None]:
            n = issued_count(b, s, n_pts_cyc)
            addrs = ap_addrs(b, s, n)
            for st in cycle_strats:
                for ports in map_ports_list:
                    for mlat in map_lats:
                        for pp in page_pols:
                            for mname, mask in pe_masks:
                                cfg = SimConfig(
                                    strategy=st,
                                    map_lat=mlat,
                                    map_ports=ports,
                                    mask=mask,
                                    n_cores=8,
                                    outstanding=16,
                                    dram=DramTiming(page_policy=pp),
                                )
                                r = run_cycles(addrs, cfg)
                                key = (s_name, st, ports, mlat, pp, mname)
                                tpc_store.setdefault(key, []).append(r.txns_per_cycle)
                                cyc_rows.append(
                                    {
                                        "trial": trial,
                                        "seed": tseed,
                                        "S": s_name,
                                        "base": hex(b),
                                        "strategy": st,
                                        "map_ports": ports,
                                        "map_lat": mlat,
                                        "page": pp,
                                        "mask": mname,
                                        "txns_per_cycle": f"{r.txns_per_cycle:.6f}",
                                        "completed": r.completed,
                                        "cycles": r.cycles,
                                        "row_hit": r.row_hit,
                                        "row_miss": r.row_miss,
                                        "n_DMC": r.n_dmc,
                                        "n_bank": r.n_bank,
                                        "pe_retries": r.pe_retries,
                                        "poisoned": r.poisoned,
                                    }
                                )

    summary = []
    for key, xs in sorted(tpc_store.items()):
        s_name, st, ports, mlat, pp, mname = key
        m, hw, n = ci95(xs)
        summary.append(
            {
                "S": s_name,
                "strategy": st,
                "map_ports": ports,
                "map_lat": mlat,
                "page": pp,
                "mask": mname,
                "txns_per_cycle_ci": fmt_ci(xs, 6),
                "mean": m,
                "ci95_hw": hw,
                "n": n,
            }
        )

    flags = [r for r in cmp_rows if r.get("flag_gt_30pct")]
    _write_csv(out / "occupancy.csv", occ_rows)
    _write_csv(out / "t2_compare.csv", cmp_rows)
    _write_csv(out / "cycles.csv", cyc_rows)
    _write_csv(out / "bw_ci.csv", summary)

    # plot: T2 vs T3 n_DMC at S=2MiB base=0
    labels, t2v, t3v = [], [], []
    for r in cmp_rows:
        if r["S"] == "2MiB" and r["base"] == "0x0" and r["family"] == "grain512":
            labels.append(r["strategy"])
            t2v.append(r["t2_n_dmc"])
            t3v.append(r["t3_n_dmc"])
    if labels:
        _plot(
            out / "t2_vs_t3_n_dmc.png",
            labels,
            t2v,
            t3v,
            "n_DMC",
            "P-0105/M-4 SNS  T2 vs T3 n_DMC (S=2MiB, base=0) — occupancy, not BW",
        )

    meta = {
        "card": "P-0105/M-4 SNS",
        "seed": seed,
        "mode": mode,
        "covering_bound": {"max": mx, "min": mn, "cv": cv, "golden": False},
        "t2_flags_gt_30pct": len(flags),
        "n_occ_rows": len(occ_rows),
        "n_cyc_rows": len(cyc_rows),
        "bw_ci": summary,
        "note": "Absolute BW is txns/cycle under 假设 H-DRAM-BB; no GB/s; 0.85 is not a measured mean.",
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"SNS sweep mode={mode} seed={seed} → {out}")
    print(f"COVERING_BOUND (NOT golden) max={mx} min={mn} CV={cv:.4f}")
    print(f"T2 occupancy |T3-T2|/T2 > 30% flags: {len(flags)}")
    for s in summary:
        print(f"  BW {s['S']:8} {s['strategy']:8} ports={s['map_ports']} lat={s['map_lat']} "
              f"{s['page']:5} {s['mask']:8} {s['txns_per_cycle_ci']}")
    if flags:
        print("DISCREPANCY: inspect simulator (do not silently pick T2). Sample:")
        print(flags[0])
    return meta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("smoke", "night"), default="smoke")
    p.add_argument("--out", type=Path, default=_HERE / "results")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--n-trials", type=int, default=3)
    p.add_argument("--n-pts", type=int, default=None, help="cap issued points (occupancy + cycles)")
    args = p.parse_args(argv)
    sweep(args.mode, args.out, args.seed, args.n_trials, args.n_pts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
