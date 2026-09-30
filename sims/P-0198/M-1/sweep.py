#!/usr/bin/env python3
"""Parameter sweep + T2 compare for P-0198/M-1 CBC.

One-command smoke:
  python3 sims/P-0198/M-1/sweep.py --mode smoke --seed 20260903

Night:
  python3 sims/P-0198/M-1/sweep.py --mode night --seed 20260903
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SIMS = _HERE.parents[1]
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_SIMS) not in sys.path:
    sys.path.insert(0, str(_SIMS))

from _lib.stats import ci95, fmt_ci, rel_err  # noqa: E402
from _lib.workloads import SEED  # noqa: E402
from sim import (  # noqa: E402
    ARMS,
    CARD_CLAIM_COLL,
    CLASSES,
    INJ_DOM,
    T2_SIGNED,
    compare_to_t2,
    duty_of_arm,
    run_arm,
    run_dual,
    signed_t2_rows,
    t2_dual_ratio,
    try_load_t2_module,
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


def _plot_bars(path: Path, labels: list[str], series: list[tuple[str, list[float]]],
               ylabel: str, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    x = range(len(labels))
    w = 0.8 / max(1, len(series))
    fig, ax = plt.subplots(figsize=(11, 4.4))
    for i, (name, vals) in enumerate(series):
        ax.bar([j + (i - (len(series) - 1) / 2) * w for j in x], vals, w, label=name)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _nan(x) -> bool:
    return isinstance(x, float) and (math.isnan(x) or math.isinf(x))


def sweep(mode: str, out: Path, seed: int, n_trials: int, n_txn: int | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        n_nodes, n_bottom = 12, 0
        n_txn = n_txn if n_txn is not None else 64
        n_trials = min(n_trials, 3)
        classes = list(CLASSES)
        arms = list(ARMS)
        lookup_lats = (1,)
        ost = 16
        extra_n25 = False
    else:
        n_nodes, n_bottom = 12, 2
        n_txn = n_txn if n_txn is not None else 128
        classes = list(CLASSES)
        arms = list(ARMS)
        lookup_lats = (1, 0)
        ost = 32
        extra_n25 = True

    t2_present = try_load_t2_module() is not None
    occ_rows = []
    cmp_rows = []
    cyc_rows = []
    inject_rows = []
    ms_store: dict[tuple, list[float]] = {}
    pinj_store: dict[tuple, list[float]] = {}

    # Fair compare: same seed ⇒ same txn list for every arm of a class.
    for trial in range(n_trials):
        tseed = seed + trial
        for lat in lookup_lats:
            off_by_cls: dict[str, object] = {}
            for cls in classes:
                for arm in arms:
                    r = run_arm(
                        arm, cls, tseed,
                        n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                        outstanding=ost, lookup_lat=lat,
                    )
                    if arm == "calendar-off":
                        off_by_cls[cls] = r
                    key = (cls, arm, lat)
                    ms_store.setdefault(key, []).append(float(r.makespan))
                    pinj_store.setdefault(key, []).append(float(r.p_inj))
                    cyc_rows.append(
                        {
                            "trial": trial,
                            "seed": tseed,
                            "class": cls,
                            "arm": arm,
                            "d": f"{duty_of_arm(arm):.4f}",
                            "lookup_lat": lat,
                            "n_nodes": r.n_nodes,
                            "n_txn": n_txn,
                            "makespan": r.makespan,
                            "completed": r.completed,
                            "collapsed": r.collapsed,
                            "p_inj": f"{r.p_inj:.6f}",
                            "steal": r.steal,
                            "raw_inject": r.raw_inject,
                            "fail": r.fail,
                            "emit": r.emit,
                            "goodput_B_per_cyc": f"{r.goodput_b_per_cyc:.4f}",
                            "warmup": r.warmup_cycles,
                            "oracle_used": r.oracle_used,
                            "hypothesis": "H-RING-BB",
                        }
                    )
                    inject_rows.append(
                        {
                            "trial": trial,
                            "class": cls,
                            "arm": arm,
                            "steal": r.steal,
                            "raw_inject": r.raw_inject,
                            "fail": r.fail,
                            "p_inj": f"{r.p_inj:.6f}",
                            "note": "counts are separate; do not collapse to one success rate as endpoint",
                        }
                    )
                    occ_rows.append(
                        {
                            "trial": trial,
                            "class": cls,
                            "arm": arm,
                            "d": f"{duty_of_arm(arm):.4f}",
                            "rho_payload": f"{r.rho_payload:.6f}",
                            "rho_empty": f"{r.rho_empty:.6f}",
                            "rho_raw": f"{r.rho_raw:.6f}",
                            "rho_bubble": f"{r.rho_bubble:.6f}",
                            "sum_ok": r.sum_ok,
                            "mean_cluster": f"{r.mean_cluster:.4f}",
                            "delta_rho_empty": "",
                            "hypothesis": "H-CBC-empty-supply",
                        }
                    )
            # fill delta vs calendar-off (same trial/class)
            for row in occ_rows:
                if row["trial"] != trial:
                    continue
                if row.get("delta_rho_empty") != "":
                    continue
                off = off_by_cls.get(row["class"])
                if off is None:
                    continue
                # match this row's run: re-read from just-appended is messy; compute from stored
            # second pass after all arms of this trial+lat
            # handled below using last results per (cls,arm) in this inner loop — see next block

            for cls in classes:
                off = off_by_cls.get(cls)
                if off is None:
                    continue
                for arm in arms:
                    # last matching occ row for this trial/cls/arm
                    for row in reversed(occ_rows):
                        if row["trial"] == trial and row["class"] == cls and row["arm"] == arm:
                            # need on.rho_empty; stored as string
                            on_empty = float(row["rho_empty"])
                            row["delta_rho_empty"] = f"{on_empty - off.rho_empty:.6f}"
                            break
                    r_on = None
                    # compare using a fresh handle: pull from cyc_rows
                    for cr in reversed(cyc_rows):
                        if (cr["trial"] == trial and cr["class"] == cls and cr["arm"] == arm
                                and cr["lookup_lat"] == lat):
                            # rebuild a tiny namespace for compare_to_t2
                            break
                # proper compare from re-run is wasteful; use stored CycleResult via off + pinj
                for arm in arms:
                    t3_p = pinj_store[(cls, arm, lat)][-1]
                    t3_ms = ms_store[(cls, arm, lat)][-1]
                    # occupancy from last occ row
                    occ = next(
                        r for r in reversed(occ_rows)
                        if r["trial"] == trial and r["class"] == cls and r["arm"] == arm
                    )
                    cyc = next(
                        r for r in reversed(cyc_rows)
                        if r["trial"] == trial and r["class"] == cls and r["arm"] == arm
                        and r["lookup_lat"] == lat
                    )

                    class _T:
                        pass

                    t3 = _T()
                    t3.p_inj = t3_p
                    t3.rho_empty = float(occ["rho_empty"])
                    t3.rho_raw = float(occ["rho_raw"])
                    t3.rho_bubble = float(occ["rho_bubble"])
                    t3.sum_ok = occ["sum_ok"] in (True, "True", "true", 1)
                    t3.makespan = int(t3_ms)
                    t3.steal = int(cyc["steal"])
                    t3.raw_inject = int(cyc["raw_inject"])
                    t3.fail = int(cyc["fail"])
                    cmp = compare_to_t2(cls, arm, t3, off)
                    cmp_rows.append(
                        {
                            "trial": trial,
                            "seed": tseed,
                            "class": cls,
                            "arm": arm,
                            "lookup_lat": lat,
                            **{k: cmp[k] for k in (
                                "d", "t3_p_inj", "t3_T_hat_over_T_off", "t2_T_hat_over_T_off",
                                "rel_err_ratio", "t3_rho_empty", "t3_rho_bubble", "t2_rho_bubble",
                                "rel_err_rho_bubble", "t3_sum_ok", "t2_sum_ok", "flag_gt_30pct",
                                "card_claim", "card_claim_is_measured", "t3_makespan",
                                "t3_steal", "t3_raw_inject", "t3_fail",
                            )},
                        }
                    )

    # Dual-tenant cycle probe (Sys T1)
    dual_rows = []
    for trial in range(n_trials):
        tseed = seed + trial
        for d_a, arm in ((0.25, "d_A=1/4"), (0.50, "d_A=1/2")):
            dual, solo = run_dual(
                d_a, tseed,
                n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                outstanding=ost, lookup_lat=1,
            )
            p_b_dual = dual.tenant_p_inj.get("B", 0.0)
            p_b_solo = solo.tenant_p_inj.get("B", solo.p_inj)
            ms_b_dual = dual.tenant_makespan.get("B", 0)
            ms_b_solo = solo.tenant_makespan.get("B", solo.makespan)
            if p_b_dual > 0 and p_b_solo > 0:
                pinj_ratio = p_b_solo / p_b_dual
            else:
                pinj_ratio = float("inf")
            if ms_b_solo > 0:
                ms_ratio = ms_b_dual / ms_b_solo
            else:
                ms_ratio = float("inf")
            t2 = t2_dual_ratio(d_a)
            err = rel_err(pinj_ratio, t2) if not _nan(pinj_ratio) else float("inf")
            fail_t = (ms_ratio >= 1.10) if not _nan(ms_ratio) else True
            dual_rows.append(
                {
                    "trial": trial,
                    "seed": tseed,
                    "arm": arm,
                    "d_A": d_a,
                    "t3_p_inj_B_solo": f"{p_b_solo:.6f}",
                    "t3_p_inj_B_dual": f"{p_b_dual:.6f}",
                    "t3_pinj_ratio": f"{pinj_ratio:.6f}" if not _nan(pinj_ratio) else "inf",
                    "t3_makespan_B_solo": ms_b_solo,
                    "t3_makespan_B_dual": ms_b_dual,
                    "t3_ms_ratio": f"{ms_ratio:.6f}" if not _nan(ms_ratio) else "inf",
                    "t2_T_B_dual_over_solo": t2,
                    "rel_err_pinj_ratio": err if not _nan(err) else "inf",
                    "flag_gt_30pct": (err > 0.30) if not _nan(err) else True,
                    "fail_T": fail_t,
                    "t2_fail_T": True,
                    "card_claim": "NOT measured",
                    "note": "Sys <10%; T2 signed fail_T at 1.3333/2.0000",
                }
            )

    if extra_n25:
        r25 = run_arm(
            "CBC-coll-1/2", "gather", seed,
            n_nodes=25, n_bottom=0, n_txn=min(n_txn, 64), outstanding=ost,
        )
        age_note = {
            "n_nodes": 25,
            "AGE_MAX": 15,
            "mean_cluster": r25.mean_cluster,
            "age_degrade": r25.age_degrade,
            "note": "AGE_MAX=15 < 25-hop lap: bubbles die before one bottom-ring lap",
        }
    else:
        age_note = {"n_nodes": 25, "ran": False, "note": "night-only N=25 age probe"}

    # CI summary (do not average P2P and collective duties)
    summary = []
    for key, xs in sorted(ms_store.items()):
        cls, arm, lat = key
        m, hw, n = ci95(xs)
        ps = pinj_store[key]
        summary.append(
            {
                "class": cls,
                "arm": arm,
                "lookup_lat": lat,
                "makespan_ci": fmt_ci(xs, 2),
                "p_inj_ci": fmt_ci(ps, 6),
                "mean_makespan": m,
                "ci95_hw": hw,
                "n": n,
                "card_claim": CARD_CLAIM_COLL if cls in INJ_DOM else "n/a",
                "card_claim_is_measured": False,
                "hypothesis": "H-RING-BB",
            }
        )

    flags = [r for r in cmp_rows if r.get("flag_gt_30pct") in (True, "True", True)]
    occ_dir = out / "night" if mode == "night" else out
    occ_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(occ_dir / "occupancy.csv", occ_rows)
    _write_csv(occ_dir / "t2_compare.csv", cmp_rows)
    _write_csv(out / "cycles.csv", cyc_rows)
    _write_csv(out / "inject.csv", inject_rows)
    _write_csv(out / "dual_tenant.csv", dual_rows)
    _write_csv(out / "bw_ci.csv", summary)
    _write_csv(out / "t2_signed_pins.csv", signed_t2_rows())

    # gather T2 vs T3 ratio bars (trial 0, lookup_lat=1)
    labels, t2v, t3v = [], [], []
    for arm in ("calendar-off", "CBC-coll-1/4", "CBC-coll-1/2", "fixed-high-1/2"):
        rows = [r for r in cmp_rows if r["class"] == "gather" and r["arm"] == arm and r["lookup_lat"] == 1]
        if not rows:
            continue
        labels.append(arm)
        t2 = rows[0]["t2_T_hat_over_T_off"]
        t3s = [r["t3_T_hat_over_T_off"] for r in rows if not _nan(r["t3_T_hat_over_T_off"])]
        t2v.append(float(t2) if not _nan(t2) else 0.0)
        t3v.append(sum(t3s) / len(t3s) if t3s else 0.0)
    if labels:
        _plot_bars(
            occ_dir / "t2_vs_t3_ratio.png",
            labels,
            [("T2 H-INJ-DOM", t2v), ("T3 p_inj_off/p_inj_cbc", t3v)],
            "T_hat/T_off (gather)",
            "P-0198/M-1 CBC  T2 vs T3 relative makespan — not card-claim",
        )

    # steal / raw / fail for gather, trial 0
    sl, sr, sf, slbl = [], [], [], []
    for arm in ARMS:
        rows = [r for r in cyc_rows if r["class"] == "gather" and r["arm"] == arm and r["trial"] == 0]
        if not rows:
            continue
        slbl.append(arm)
        sl.append(float(rows[0]["steal"]))
        sr.append(float(rows[0]["raw_inject"]))
        sf.append(float(rows[0]["fail"]))
    if slbl:
        _plot_bars(
            out / "steal_raw_fail.png",
            slbl,
            [("steal", sl), ("raw-inject", sr), ("fail", sf)],
            "count (gather, trial 0)",
            "P-0198/M-1 CBC  same-cycle arbitration counts (not a single success proxy)",
        )

    meta = {
        "card": "P-0198/M-1 CBC",
        "seed": seed,
        "mode": mode,
        "t2_model_on_tree": t2_present,
        "t2_source": "signed audit PR #56 + spec §3 formulas; model.py PR #54 not on main",
        "t2_signed": T2_SIGNED,
        "t2_flags_gt_30pct": len(flags),
        "n_occ_rows": len(occ_rows),
        "n_cyc_rows": len(cyc_rows),
        "n_dual_rows": len(dual_rows),
        "occupancy_csv": str(occ_dir / "occupancy.csv"),
        "t2_compare_csv": str(occ_dir / "t2_compare.csv"),
        "bw_ci": summary,
        "age_n25": age_note,
        "bbox": (
            f"{n_nodes}+{n_bottom} nodes, CHI 4 rings × 2 dirs FSM, "
            f"outstanding={ost} (not envelope rd512/wr256), |I|={n_txn}, "
            f"lookup_lat={list(lookup_lats)}, warmup≥1 lap, "
            "reduced-bbox vs 12+2 DV200 tests/soc_sim; clock UNKNOWN"
        ),
        "note": (
            "card-claim 0.55–0.85× is NOT measured. 0.85 is a pass bar. "
            "Do not average P2P and collective duties. "
            "If |T3−T2|/T2>30% the T3 number stands; do not substitute T2."
        ),
        "dr_sim": {
            "fsm_node_dir_chi": True,
            "calendar_64x8_phase": True,
            "tag_age_cluster": True,
            "steal_raw_fail_separate": True,
            "warmup_ge_one_lap": True,
            "no_arrival_oracle": True,
        },
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"CBC sweep mode={mode} seed={seed} → {out}")
    print(f"occupancy/t2_compare → {occ_dir}")
    print(f"T2 model.py on tree: {t2_present}")
    print(f"T2 |T3-T2|/T2 > 30% flags: {len(flags)}")
    print(f"card-claim {CARD_CLAIM_COLL} is NOT measured")
    for s in summary:
        if s["class"] in ("gather", "uniform_read") and s["lookup_lat"] == 1:
            print(f"  {s['class']:14} {s['arm']:16} {s['makespan_ci']}  p_inj {s['p_inj_ci']}")
    if flags:
        print("DISCREPANCY: inspect simulator (do not silently pick T2). Sample:")
        print(flags[0])
    hard = [r for r in cmp_rows if r["class"] == "gather" and r["arm"] in ("calendar-off", "CBC-coll-1/2") and r["trial"] == 0]
    if len(hard) >= 2:
        off_ms = next(r["t3_makespan"] for r in hard if r["arm"] == "calendar-off")
        cbc_ms = next(r["t3_makespan"] for r in hard if r["arm"] == "CBC-coll-1/2")
        print(f"HARD-1 cycle probe: off makespan ({off_ms}) > CBC-coll-1/2 ({cbc_ms})? {off_ms > cbc_ms}")
        print(f"T2 HARD-1 (ns, not comparable abs): 537.2 > 313.4")
    for row in dual_rows:
        if row["trial"] == 0:
            print(
                f"dual {row['arm']} pinj_ratio={row['t3_pinj_ratio']} "
                f"ms_ratio={row['t3_ms_ratio']} fail_T={row['fail_T']} "
                f"t2={row['t2_T_B_dual_over_solo']}"
            )
    return meta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("smoke", "night"), default="smoke")
    p.add_argument("--out", type=Path, default=_HERE / "results")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--n-trials", type=int, default=3)
    p.add_argument("--n-txn", type=int, default=None)
    args = p.parse_args(argv)
    sweep(args.mode, args.out, args.seed, args.n_trials, args.n_txn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
