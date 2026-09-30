#!/usr/bin/env python3
"""Parameter sweep + T2 compare for P-0198/M-4 AODI.

One-command smoke:
  python3 sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903

Night:
  python3 sims/P-0198/M-4/sweep.py --mode night --seed 20260903

Ablation is deflect-off vs AODI-on on this card only.
Do not mix with M-1 CBC / M-2 CSR / M-5 CRRF.
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
    CARD_CLAIM,
    CLASSES,
    DUAL_BUSY_CLASSES,
    T2_SIGNED,
    compare_to_t2,
    run_arm,
    signed_t2_rows,
    t2_phi_walk,
    try_load_t2_module,
    AGE_MAX_DEFAULT,
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
        arms = ("deflect-off", "AODI-on")
        ost = 16
        age_maxs = (AGE_MAX_DEFAULT,)
    else:
        n_nodes, n_bottom = 12, 2
        n_txn = n_txn if n_txn is not None else 128
        classes = list(CLASSES)
        arms = tuple(ARMS)
        ost = 32
        age_maxs = (AGE_MAX_DEFAULT, 4)

    t2_present = try_load_t2_module() is not None
    occ_rows = []
    cmp_rows = []
    cyc_rows = []
    hole_rows = []
    ms_store: dict[tuple, list[float]] = {}
    pinj_store: dict[tuple, list[float]] = {}

    # Fair compare: same seed ⇒ same txn list for every arm of a class.
    for trial in range(n_trials):
        tseed = seed + trial
        for age_max in age_maxs:
            off_by_cls: dict[str, object] = {}
            on_by_cls: dict[str, object] = {}
            for cls in classes:
                for arm in arms:
                    r = run_arm(
                        arm, cls, tseed,
                        n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                        outstanding=ost, age_max=age_max,
                    )
                    if r.hole_dual != 0:
                        raise AssertionError(
                            f"MECHANISM FAIL: hole_dual={r.hole_dual} "
                            f"class={cls} arm={arm} trial={trial}"
                        )
                    if arm == "deflect-off":
                        off_by_cls[cls] = r
                    if arm == "AODI-on":
                        on_by_cls[cls] = r
                    key = (cls, arm, age_max)
                    ms_store.setdefault(key, []).append(float(r.makespan))
                    pinj_store.setdefault(key, []).append(float(r.p_inj))
                    cyc_rows.append(
                        {
                            "trial": trial,
                            "seed": tseed,
                            "class": cls,
                            "arm": arm,
                            "age_max": age_max,
                            "n_nodes": r.n_nodes,
                            "n_txn": n_txn,
                            "makespan": r.makespan,
                            "completed": r.completed,
                            "completions_cw": r.completions_cw,
                            "completions_ccw": r.completions_ccw,
                            "collapsed": r.collapsed,
                            "p_inj": f"{r.p_inj:.6f}",
                            "inject_ok": r.inject_ok,
                            "inject_fail": r.inject_fail,
                            "deflect": r.deflect,
                            "rejoin": r.rejoin,
                            "hole_asym": r.hole_asym,
                            "hole_dual": r.hole_dual,
                            "dual_busy_cycles": r.dual_busy_cycles,
                            "rho_pref": f"{r.rho_pref:.6f}",
                            "rho_opp": f"{r.rho_opp:.6f}",
                            "goodput_B_per_cyc": f"{r.goodput_b_per_cyc:.4f}",
                            "warmup": r.warmup_cycles,
                            "phi_freeze": r.phi_freeze_events,
                            "illegal_third": r.illegal_third,
                            "dropped": r.dropped,
                            "hypothesis": "H-RING-BB",
                            "note": (
                                "alltoall dual-busy-sat SEPARATE; do not fold"
                                if cls in DUAL_BUSY_CLASSES
                                else "inject-success is NOT the endpoint"
                            ),
                        }
                    )
                    hole_rows.append(
                        {
                            "trial": trial,
                            "class": cls,
                            "arm": arm,
                            "bucket": "dual-busy" if cls in DUAL_BUSY_CLASSES else "asymmetric/mixed",
                            "hole_asym": r.hole_asym,
                            "hole_dual": r.hole_dual,
                            "dual_busy_cycles": r.dual_busy_cycles,
                            "deflect": r.deflect,
                            "note": "dual-busy hole≡0; never fold alltoall into 0.50-0.85x",
                        }
                    )
                    occ_rows.append(
                        {
                            "trial": trial,
                            "class": cls,
                            "arm": arm,
                            "rho_pref": f"{r.rho_pref:.6f}",
                            "rho_opp": f"{r.rho_opp:.6f}",
                            "rho_cw": f"{r.rho_cw:.6f}",
                            "rho_ccw": f"{r.rho_ccw:.6f}",
                            "completed": r.completed,
                            "completions_cw": r.completions_cw,
                            "completions_ccw": r.completions_ccw,
                            "hole_asym": r.hole_asym,
                            "hole_dual": r.hole_dual,
                            "hypothesis": "H-AODI-slot",
                        }
                    )

            for cls in classes:
                off = off_by_cls.get(cls)
                on = on_by_cls.get(cls)
                if off is None or on is None:
                    continue
                cmp = compare_to_t2(cls, on, off)
                cmp_rows.append(
                    {
                        "trial": trial,
                        "seed": tseed,
                        "age_max": age_max,
                        **cmp,
                    }
                )

            # Forced dual-busy-sat probe — separate row, not a traffic mean.
            for arm in arms:
                r = run_arm(
                    arm, "alltoall", tseed,
                    n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                    outstanding=ost, age_max=age_max, force_dual_busy=True,
                    max_cycles=(n_nodes + n_bottom) * 2 + 16,
                )
                if r.hole_dual != 0:
                    raise AssertionError("MECHANISM FAIL: dual-busy-sat probe hole_dual>0")
                hole_rows.append(
                    {
                        "trial": trial,
                        "class": "dual-busy-sat",
                        "arm": arm,
                        "bucket": "dual-busy",
                        "hole_asym": r.hole_asym,
                        "hole_dual": r.hole_dual,
                        "dual_busy_cycles": r.dual_busy_cycles,
                        "deflect": r.deflect,
                        "note": "FORCED dual-busy-sat; expected gain≈0; hole_dual≡0",
                    }
                )
                cyc_rows.append(
                    {
                        "trial": trial,
                        "seed": tseed,
                        "class": "dual-busy-sat",
                        "arm": arm,
                        "age_max": age_max,
                        "n_nodes": r.n_nodes,
                        "n_txn": n_txn,
                        "makespan": r.makespan,
                        "completed": r.completed,
                        "completions_cw": r.completions_cw,
                        "completions_ccw": r.completions_ccw,
                        "collapsed": r.collapsed,
                        "p_inj": f"{r.p_inj:.6f}",
                        "inject_ok": r.inject_ok,
                        "inject_fail": r.inject_fail,
                        "deflect": r.deflect,
                        "rejoin": r.rejoin,
                        "hole_asym": r.hole_asym,
                        "hole_dual": r.hole_dual,
                        "dual_busy_cycles": r.dual_busy_cycles,
                        "rho_pref": f"{r.rho_pref:.6f}",
                        "rho_opp": f"{r.rho_opp:.6f}",
                        "goodput_B_per_cyc": f"{r.goodput_b_per_cyc:.4f}",
                        "warmup": r.warmup_cycles,
                        "phi_freeze": r.phi_freeze_events,
                        "illegal_third": r.illegal_third,
                        "dropped": r.dropped,
                        "hypothesis": "H-RING-BB",
                        "note": "FORCED dual-busy-sat separate row; expected gain≈0",
                    }
                )

    # φ walk signed pin (analytical probe, not Σage)
    _trace, age_end, _frz, ok = t2_phi_walk(6, 1, AGE_MAX_DEFAULT, True)
    if not ok or age_end != T2_SIGNED["phi_age_end"]:
        raise AssertionError(f"signed φ pin failed: age_end={age_end} ok={ok}")

    summary = []
    for key, xs in sorted(ms_store.items()):
        cls, arm, age_max = key
        m, hw, n = ci95(xs)
        ps = pinj_store[key]
        summary.append(
            {
                "class": cls,
                "arm": arm,
                "age_max": age_max,
                "makespan_ci": fmt_ci(xs, 2),
                "p_inj_ci": fmt_ci(ps, 6),
                "mean_makespan": m,
                "ci95_hw": hw,
                "n": n,
                "card_claim": CARD_CLAIM[cls],
                "card_claim_is_measured": False,
                "alltoall_separate": cls in DUAL_BUSY_CLASSES,
                "hypothesis": "H-RING-BB",
            }
        )

    flags = [r for r in cmp_rows if r.get("flag_gt_30pct") in (True, "True", True)]
    occ_dir = out / "night" if mode == "night" else out
    occ_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(occ_dir / "occupancy.csv", occ_rows)
    _write_csv(occ_dir / "t2_compare.csv", cmp_rows)
    _write_csv(out / "cycles.csv", cyc_rows)
    _write_csv(out / "holes.csv", hole_rows)
    _write_csv(out / "bw_ci.csv", summary)
    _write_csv(out / "t2_signed_pins.csv", signed_t2_rows())

    # T2 vs T3 T_mix by class (trial-mean, age_max default, never average classes)
    labels, t2v, t3v = [], [], []
    for cls in CLASSES:
        rows = [r for r in cmp_rows if r["class"] == cls and r["age_max"] == AGE_MAX_DEFAULT]
        if not rows:
            continue
        labels.append(cls + ("*" if cls in DUAL_BUSY_CLASSES else ""))
        t2v.append(float(rows[0]["t2_T_mix"]))
        t3s = [float(r["t3_T_mix"]) for r in rows if not _nan(r["t3_T_mix"])]
        t3v.append(sum(t3s) / len(t3s) if t3s else 0.0)
    if labels:
        _plot_bars(
            occ_dir / "t2_vs_t3_t_mix.png",
            labels,
            [("T2 T_mix (analytical)", t2v), ("T3 T_mix (cycle ms_on/ms_off)", t3v)],
            "T_on / T_off",
            "P-0198/M-4 AODI  T2 vs T3 T_mix — alltoall* is separate; not card-claim",
        )

    sl, sd, slbl = [], [], []
    for cls in CLASSES:
        rows = [r for r in hole_rows if r["class"] == cls and r["arm"] == "AODI-on" and r["trial"] == 0]
        if not rows:
            continue
        slbl.append(cls + ("*" if cls in DUAL_BUSY_CLASSES else ""))
        sl.append(float(rows[0]["hole_asym"]))
        sd.append(float(rows[0]["hole_dual"]))
    if slbl:
        _plot_bars(
            out / "hole_buckets.png",
            slbl,
            [("hole_asym", sl), ("hole_dual (must be 0)", sd)],
            "count (AODI-on, trial 0)",
            "P-0198/M-4 AODI  hole buckets — dual-busy must be 0",
        )

    meta = {
        "card": "P-0198/M-4 AODI",
        "seed": seed,
        "mode": mode,
        "t2_model_on_tree": t2_present,
        "t2_source": "signed audit PR #65 + spec §3 formulas; model.py not on main",
        "t2_signed": T2_SIGNED,
        "t2_flags_gt_30pct": len(flags),
        "n_occ_rows": len(occ_rows),
        "n_cyc_rows": len(cyc_rows),
        "n_cmp_rows": len(cmp_rows),
        "occupancy_csv": str(occ_dir / "occupancy.csv"),
        "t2_compare_csv": str(occ_dir / "t2_compare.csv"),
        "bw_ci": summary,
        "siblings": {
            "M-1_CBC": "淘汰 at T3 (PR #62 / #64) — do not mix",
            "M-2_CSR": "separate in-flight T3 — do not mix",
            "M-5_CRRF": "separate in-flight T3 — do not mix",
        },
        "bbox": (
            f"{n_nodes}+{n_bottom} nodes, CHI 4 rings × 2 dirs 2×2, "
            f"outstanding={ost} (not envelope rd512/wr256), |I|={n_txn}, "
            f"AGE_MAX={list(age_maxs)}, warmup≥1 lap, "
            "reduced-bbox vs 12+2 DV200 tests/soc_sim; clock UNKNOWN"
        ),
        "note": (
            "card-claim 0.70–0.95× / 0.95–1.05× is NOT measured. "
            "0.85 is a pass bar. alltoall dual-busy-sat is a separate row "
            "(expected gain≈0); never fold into 0.50–0.85× or 0.70–0.95×. "
            "If |T3−T2|/T2>30% the T3 number stands; do not substitute T2. "
            "Ablation is deflect-off only. No M-1/M-2/M-5 mix."
        ),
        "dr_sim": {
            "same_cycle_2x2": True,
            "hole_dual_hard_zero": True,
            "phi_not_sum_age": True,
            "deflect_off_ablation": True,
            "hole_buckets_asym_vs_dual": True,
            "alltoall_separate": True,
            "warmup_ge_one_lap": True,
            "no_third_slot": True,
            "no_cross_chi": True,
        },
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"AODI sweep mode={mode} seed={seed} → {out}")
    print(f"occupancy/t2_compare → {occ_dir}")
    print(f"T2 model.py on tree: {t2_present}")
    print(f"T2 |T3-T2|/T2 > 30% flags: {len(flags)}")
    print("card-claim 0.70-0.95x / 0.95-1.05x is NOT measured")
    print(f"signed pins: hole_dual={T2_SIGNED['hole_dual']} "
          f"phi_age_end={T2_SIGNED['phi_age_end']} "
          f"alltoall T_mix={T2_SIGNED['alltoall_t_mix']} "
          f"gather T_mix={T2_SIGNED['gather_t_mix']}")
    for s in summary:
        if s["class"] in ("gather", "uniform_read", "alltoall") and s["age_max"] == AGE_MAX_DEFAULT:
            print(f"  {s['class']:14} {s['arm']:12} {s['makespan_ci']}  p_inj {s['p_inj_ci']}")
    if flags:
        print("DISCREPANCY: inspect simulator (do not silently pick T2). Sample:")
        print(flags[0])
    for cls in ("gather", "alltoall"):
        rows = [r for r in cmp_rows if r["class"] == cls and r["trial"] == 0 and r["age_max"] == AGE_MAX_DEFAULT]
        if rows:
            r = rows[0]
            print(
                f"{cls}: T3 T_mix={r['t3_T_mix']:.4f} T2 T_mix={r['t2_T_mix']:.4f} "
                f"rel_err={r['rel_err_T_mix']:.4f} flag={r['flag_gt_30pct']} "
                f"hole_dual={r['t3_hole_dual']} off_hard={r['deflect_off_hard_t3']}"
            )
            if cls == "alltoall":
                print("  alltoall dual-busy-sat SEPARATE; expected gain≈0; do not fold")
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
