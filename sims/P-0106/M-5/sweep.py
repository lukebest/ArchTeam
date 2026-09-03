#!/usr/bin/env python3
"""Parameter sweep + T2 compare for P-0106/M-5 AffineRebind.

One-command smoke:
  python3 sims/P-0106/M-5/sweep.py --mode smoke

Night (21:00) full:
  python3 sims/P-0106/M-5/sweep.py --mode night
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
from _lib.workloads import AFFINE_DOC, SEED, ap_addrs, issued_count  # noqa: E402
from sim import (  # noqa: E402
    STRATEGIES,
    SimConfig,
    compare_occupancy,
    gcd_table,
    mask_full,
    mask_n40,
    mask_third_bias,
    mask_uniform,
    occupancy,
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
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.bar([i - w / 2 for i in x], t2, w, label="T2 occupancy")
    ax.bar([i + w / 2 for i in x], t3, w, label="T3 occupancy")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


MASKS = (
    ("full-good", mask_full()),
    ("n=40", mask_n40()),
    ("unif-25%(n=36)", mask_uniform(36)),
    ("unif-12.5%(n=42)", mask_uniform(42)),
    ("unif-6.25%(n=45)", mask_uniform(45)),
    ("3-biased(n=32)", mask_third_bias()),
)

# Signed smoke occupancy: Doc S 512B + factor-3 (3×512B, 9×512B) + 2MiB.
# gcd_table.csv is AP sanity only and does not count as XOR_fold6 netlist coverage.
SMOKE_STRIDES = (AFFINE_DOC[0], AFFINE_DOC[1], AFFINE_DOC[2], AFFINE_DOC[-1])
SMOKE_MASKS = (MASKS[0], MASKS[1], MASKS[-1])  # full-good, n=40, 3-biased
SMOKE_STRATEGIES = ("skip-dead", "modn-a1", "minimax")
SMOKE_CYCLE_S = ("2MiB", "512B", "3x512B")


def sweep(mode: str, out: Path, seed: int, n_trials: int, n_pts: int | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        strides = list(SMOKE_STRIDES)
        masks = list(SMOKE_MASKS)
        strategies = SMOKE_STRATEGIES
        n_pts_cyc = n_pts if n_pts is not None else 256
        n_trials = min(n_trials, 3)
        csr_ports_list = (1,)
        decode_lats = (2,)
        betas = ("zero",)
        pages = ("open",)
    else:
        strides = list(AFFINE_DOC)
        masks = list(MASKS)
        strategies = STRATEGIES
        n_pts_cyc = n_pts if n_pts is not None else 512
        csr_ports_list = (1, 4)
        decode_lats = (2, 1)
        betas = ("zero", "dmc")
        pages = ("open", "close")

    gcd_rows = []
    for label, mask in masks:
        for row in gcd_table(mask):
            gcd_rows.append({"mask": label, **row, "note": "AP sanity; not a substitute for XOR_fold6"})
    _write_csv(out / "gcd_table.csv", gcd_rows)

    occ_rows = []
    cmp_rows = []
    for s_name, s in strides:
        for label, mask in masks:
            for st in strategies:
                t3 = occupancy(st, mask, s, n_pts)
                cmp = compare_occupancy(st, mask, s, n_pts)
                note = ""
                if "25%" in label:
                    note = "n=36 still has factor 3 — not a 3-adic test"
                if "3-biased" in label:
                    note = "3-adic column only"
                occ_rows.append(
                    {
                        "S": s_name,
                        "mask": label,
                        "strategy": st,
                        "alpha": t3.alpha,
                        "n": t3.n,
                        "n_DMC": t3.n_dmc,
                        "n_bank": t3.n_bank,
                        "dead": t3.dead,
                        "cls_min": t3.cls_min,
                        "cls_mean": f"{t3.cls_mean:.4f}",
                        "classes_AP": t3.classes_ap,
                        "min_mean": f"{t3.min_mean:.4f}",
                        "note": note,
                    }
                )
                cmp_rows.append(
                    {
                        "S": s_name,
                        "mask": label,
                        "strategy": st,
                        "t3_cls_mean": cmp["t3_cls_mean"],
                        "t2_cls_mean": cmp.get("t2_cls_mean", ""),
                        "rel_err_cls": cmp["rel_err_cls"],
                        "t3_n_bank": cmp["t3_n_bank"],
                        "t2_n_bank": cmp.get("t2_n_bank", ""),
                        "rel_err_n_bank": cmp["rel_err_n_bank"],
                        "t3_dead": cmp["t3_dead"],
                        "t2_dead": cmp.get("t2_dead", ""),
                        "flag_gt_30pct": cmp["flag_gt_30pct"],
                    }
                )

    cyc_rows = []
    tpc_store: dict[tuple, list[float]] = {}
    cycle_masks = [m for m in masks if m[0] in ("n=40", "full-good", "3-biased(n=32)")]
    cycle_S = [st for st in strides if st[0] in SMOKE_CYCLE_S]
    for trial in range(n_trials):
        tseed = seed + trial
        for s_name, s in cycle_S:
            n = issued_count(0, s, n_pts_cyc)
            addrs = ap_addrs(0, s, n)
            for label, mask in cycle_masks:
                for st in ("skip-dead", "modn-a1", "minimax"):
                    for ports in csr_ports_list:
                        for dlat in decode_lats:
                            for beta in betas:
                                for pp in pages:
                                    cfg = SimConfig(
                                        strategy=st,
                                        mask=mask,
                                        decode_lat=dlat,
                                        csr_ports=ports,
                                        beta_mode=beta,
                                        dram=DramTiming(page_policy=pp),
                                    )
                                    r = run_cycles(addrs, cfg)
                                    key = (s_name, label, st, ports, dlat, beta, pp)
                                    tpc_store.setdefault(key, []).append(r.txns_per_cycle)
                                    cyc_rows.append(
                                        {
                                            "trial": trial,
                                            "seed": tseed,
                                            "S": s_name,
                                            "mask": label,
                                            "strategy": st,
                                            "csr_ports": ports,
                                            "decode_lat": dlat,
                                            "beta": beta,
                                            "page": pp,
                                            "txns_per_cycle": f"{r.txns_per_cycle:.6f}",
                                            "completed": r.completed,
                                            "dead": r.dead,
                                            "cls_mean": f"{r.cls_mean:.4f}",
                                            "n_DMC": r.n_dmc,
                                            "n_bank": r.n_bank,
                                            "repair_done": r.repair_done,
                                        }
                                    )

    summary = []
    for key, xs in sorted(tpc_store.items()):
        s_name, label, st, ports, dlat, beta, pp = key
        m, hw, n = ci95(xs)
        summary.append(
            {
                "S": s_name,
                "mask": label,
                "strategy": st,
                "csr_ports": ports,
                "decode_lat": dlat,
                "beta": beta,
                "page": pp,
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

    labels, t2v, t3v = [], [], []
    for r in cmp_rows:
        if r["S"] == "2MiB" and r["mask"] in ("full-good", "n=40", "3-biased(n=32)") and r["t2_cls_mean"] != "":
            labels.append(f"{r['mask']}/{r['strategy']}")
            t2v.append(float(r["t2_cls_mean"]))
            t3v.append(float(r["t3_cls_mean"]))
    if labels:
        _plot(
            out / "t2_vs_t3_cls_mean.png",
            labels,
            t2v,
            t3v,
            "cls_mean (XOR_fold6 netlist)",
            "P-0106/M-5 AffineRebind  T2 vs T3 cls_mean (S=2MiB)",
        )

    meta = {
        "card": "P-0106/M-5 AffineRebind",
        "seed": seed,
        "mode": mode,
        "t2_flags_gt_30pct": len(flags),
        "n_occ_rows": len(occ_rows),
        "n_cyc_rows": len(cyc_rows),
        "bw_ci": summary,
        "note": "Main gain is mod 48→n, not α. Uniform 25% is not 3-adic. No GB/s.",
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"AffineRebind sweep mode={mode} seed={seed} → {out}")
    print(f"T2 occupancy |T3-T2|/T2 > 30% flags: {len(flags)}")
    for s in summary:
        print(f"  BW {s['S']:8} {s['mask']:16} {s['strategy']:10} ports={s['csr_ports']} "
              f"lat={s['decode_lat']} {s['txns_per_cycle_ci']}")
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
    p.add_argument("--n-pts", type=int, default=None)
    args = p.parse_args(argv)
    sweep(args.mode, args.out, args.seed, args.n_trials, args.n_pts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
