#!/usr/bin/env python3
"""Parameter sweep + T2 compare for P-0198/M-2 CSR.

One-command smoke:
  python3 sims/P-0198/M-2/sweep.py --mode smoke --seed 20260903

Night:
  python3 sims/P-0198/M-2/sweep.py --mode night --seed 20260903

T2 model.py is draft PR #66 (not landed). Compare uses signed audit pins
(PR #68) + spec §3 formulas. card-claim bands are NOT measured.
Orthogonal to M-1 CBC (淘汰) and M-5 CRRF — do not mix.
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
    FANIN_DOM,
    N_CAM,
    T2_SIGNED,
    compare_to_t2,
    run_arm,
    signed_t2_rows,
    t2_completion_split,
    t2_fallback_dominates,
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


def _ops_for(cls: str, default: int) -> int:
    if cls in ("allgather", "allreduce"):
        return max(1, min(default, 1 if default <= 2 else 2))
    return default


def sweep(mode: str, out: Path, seed: int, n_trials: int, n_ops: int | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        n_top, n_bottom = 12, 2
        n_ops = n_ops if n_ops is not None else 2
        n_trials = min(n_trials, 3)
        classes = list(CLASSES)
        arms = ("spine-off", "CSR")
        osts = (256, 512)
        extra_probes = True
    else:
        n_top, n_bottom = 12, 2
        n_ops = n_ops if n_ops is not None else 4
        classes = list(CLASSES)
        arms = ARMS
        osts = (256, 512)
        extra_probes = True

    t2_present = try_load_t2_module() is not None
    occ_rows = []
    cmp_rows = []
    cyc_rows = []
    a2a_rows = []
    ms_store: dict[tuple, list[float]] = {}

    for trial in range(n_trials):
        tseed = seed + trial
        for ost in osts:
            off_by_cls: dict[str, object] = {}
            for cls in classes:
                n_op = _ops_for(cls, n_ops)
                for arm in arms:
                    r = run_arm(
                        arm, cls, tseed,
                        n_top=n_top, n_bottom=n_bottom, n_ops=n_op,
                        outstanding=ost,
                    )
                    if arm == "spine-off":
                        off_by_cls[cls] = r
                    key = (cls, arm, ost)
                    ms_store.setdefault(key, []).append(float(r.makespan))
                    cyc_rows.append(
                        {
                            "trial": trial,
                            "seed": tseed,
                            "class": cls,
                            "arm": arm,
                            "outstanding": ost,
                            "n_nodes": r.n_nodes,
                            "n_ops": n_op,
                            "makespan": r.makespan,
                            "completed": r.completed,
                            "collapsed": r.collapsed,
                            "cam_overflow_fallback": r.cam_overflow_fallback,
                            "collect_timeout_fallback": r.collect_timeout_fallback,
                            "spine_grant": r.spine_grant,
                            "f_ov": f"{r.f_overflow:.6f}",
                            "f_to": f"{r.f_timeout:.6f}",
                            "f_grant": f"{r.f_grant:.6f}",
                            "fallback_dominates": r.fallback_dominates,
                            "card_claim": CARD_CLAIM.get(cls, "n/a"),
                            "card_claim_is_measured": False,
                            "card_claim_valid": r.card_claim_valid,
                            "inject_ok": r.inject_ok,
                            "inject_fail": r.inject_fail,
                            "inject_before_grant": r.inject_before_grant,
                            "fold_accepts": r.fold_accepts,
                            "fold_orbits": r.fold_orbits,
                            "grant_emits": r.grant_emits,
                            "warmup": r.warmup_cycles,
                            "oracle_used": r.oracle_used,
                            "goodput_B_per_cyc": f"{r.goodput_b_per_cyc:.4f}",
                            "hypothesis": "H-RING-BB",
                        }
                    )
                    occ_rows.append(
                        {
                            "trial": trial,
                            "class": cls,
                            "arm": arm,
                            "outstanding": ost,
                            "dat_beats_held_max": r.dat_beats_held_max,
                            "retention_depth_max": r.retention_depth_max,
                            "concurrent_live_cam_max": r.concurrent_live_cam_max,
                            "n_cam": r.n_cam,
                            "invariant_ok": r.invariant_ok,
                            "payload_rbrg_reject": r.payload_rbrg_reject,
                            "same_cycle_reclassify": r.same_cycle_reclassify,
                            "hypothesis": "H-CAM-DAT0",
                        }
                    )
                    if cls == "alltoall":
                        a2a_rows.append(
                            {
                                "trial": trial,
                                "seed": tseed,
                                "arm": arm,
                                "outstanding": ost,
                                "tree_makespan": r.tree_makespan,
                                "tree_completed": r.tree_completed,
                                "residual_makespan": r.residual_makespan,
                                "residual_completed": r.residual_completed,
                                "residual_p50": f"{r.residual_p50:.4f}",
                                "residual_p90": f"{r.residual_p90:.4f}",
                                "residual_p99": f"{r.residual_p99:.4f}",
                                "note": "RESIDUAL is RING_P2P; do not average with TREE or gather-family",
                            }
                        )
            for cls in classes:
                off = off_by_cls.get(cls)
                for arm in arms:
                    cyc = next(
                        r for r in reversed(cyc_rows)
                        if r["trial"] == trial and r["class"] == cls
                        and r["arm"] == arm and r["outstanding"] == ost
                    )
                    occ = next(
                        r for r in reversed(occ_rows)
                        if r["trial"] == trial and r["class"] == cls
                        and r["arm"] == arm and r["outstanding"] == ost
                    )

                    class _T:
                        pass

                    t3 = _T()
                    t3.makespan = int(cyc["makespan"])
                    t3.f_overflow = float(cyc["f_ov"])
                    t3.f_timeout = float(cyc["f_to"])
                    t3.f_grant = float(cyc["f_grant"])
                    t3.card_claim_valid = cyc["card_claim_valid"] in (True, "True", "true", 1)
                    t3.fallback_dominates = cyc["fallback_dominates"] in (True, "True", "true", 1)
                    t3.invariant_ok = occ["invariant_ok"] in (True, "True", "true", 1)
                    t3.dat_beats_held_max = int(occ["dat_beats_held_max"])
                    t3.retention_depth_max = int(occ["retention_depth_max"])
                    t3.concurrent_live_cam_max = int(occ["concurrent_live_cam_max"])
                    t3.cam_overflow_fallback = int(cyc["cam_overflow_fallback"])
                    t3.collect_timeout_fallback = int(cyc["collect_timeout_fallback"])
                    t3.collapsed = cyc["collapsed"] in (True, "True", "true", 1)
                    t3.residual_p50 = 0.0
                    t3.residual_p90 = 0.0
                    t3.tree_makespan = 0
                    t3.residual_makespan = 0
                    if cls == "alltoall":
                        ar = next(
                            r for r in reversed(a2a_rows)
                            if r["trial"] == trial and r["arm"] == arm and r["outstanding"] == ost
                        )
                        t3.residual_p50 = float(ar["residual_p50"])
                        t3.residual_p90 = float(ar["residual_p90"])
                        t3.tree_makespan = int(ar["tree_makespan"])
                        t3.residual_makespan = int(ar["residual_makespan"])
                    cmp = compare_to_t2(cls, arm, t3, off)
                    cmp_rows.append(
                        {
                            "trial": trial,
                            "seed": tseed,
                            "class": cls,
                            "arm": arm,
                            "outstanding": ost,
                            **{k: cmp[k] for k in (
                                "t3_makespan", "t3_T_hat_over_T_off", "t2_T_hat_over_T_off",
                                "rel_err_ratio", "t3_f_ov", "t3_f_to", "t3_f_grant",
                                "t2_a2_f_ov", "t2_a8_f_ov", "flag_gt_30pct",
                                "card_claim", "card_claim_is_measured",
                                "t3_card_claim_valid", "t3_fallback_dominates",
                                "t3_invariant_ok", "t3_dat_held_max", "t3_retention_max",
                                "t3_live_cam_max", "t3_cam_overflow_fallback",
                                "t3_collect_timeout_fallback", "t3_collapsed",
                                "t3_residual_p50", "t3_residual_p90",
                                "t3_tree_makespan", "t3_residual_makespan",
                            )},
                        }
                    )

    # ---- extra probes: gate-off, high-ost overflow, timeout (not mixed into class means)
    probe_rows = []
    if extra_probes:
        for trial in range(n_trials):
            tseed = seed + trial
            off = run_arm("spine-off", "gather", tseed, n_top=n_top, n_bottom=n_bottom, n_ops=2, outstanding=256)
            gate_off = run_arm("CSR-gate-off", "gather", tseed, n_top=n_top, n_bottom=n_bottom, n_ops=2, outstanding=256)
            gate_on = run_arm("CSR", "gather", tseed, n_top=n_top, n_bottom=n_bottom, n_ops=2, outstanding=256)
            r_off = gate_off.makespan / off.makespan if off.makespan else float("inf")
            r_on = gate_on.makespan / off.makespan if off.makespan else float("inf")
            err_go = rel_err(r_off, T2_SIGNED["gate_off_r"])
            probe_rows.append(
                {
                    "trial": trial,
                    "seed": tseed,
                    "probe": "gate-off",
                    "t3_r": f"{r_off:.6f}",
                    "t2": T2_SIGNED["gate_off_r"],
                    "rel_err": err_go,
                    "flag_gt_30pct": err_go > 0.30,
                    "t3_inject_before_grant": gate_off.inject_before_grant,
                    "t3_gate_on_r": f"{r_on:.6f}",
                    "note": "H_inject_gate off; T2 ≈1.0362; do not treat card-claim as measured",
                }
            )
            hi = run_arm(
                "CSR", "gather", tseed,
                n_top=n_top, n_bottom=n_bottom, n_ops=8, outstanding=512,
            )
            err_hi = rel_err(hi.f_overflow, T2_SIGNED["a8_f_ov"])
            probe_rows.append(
                {
                    "trial": trial,
                    "seed": tseed,
                    "probe": "high-ost-8ops",
                    "t3_r": f"{hi.f_overflow:.6f}",
                    "t2": T2_SIGNED["a8_f_ov"],
                    "rel_err": err_hi,
                    "flag_gt_30pct": err_hi > 0.30,
                    "t3_inject_before_grant": hi.inject_before_grant,
                    "t3_gate_on_r": "",
                    "note": (
                        f"f_ov={hi.f_overflow:.4f} ov={hi.cam_overflow_fallback} "
                        f"dominates={hi.fallback_dominates} "
                        f"card_claim={'INVALID' if hi.fallback_dominates else 'still-labeled-not-pass'} "
                        f"(T2 a=8 Erlang-B 0.5746 → INVALID)"
                    ),
                }
            )
            to = run_arm(
                "CSR", "gather", tseed,
                n_top=n_top, n_bottom=n_bottom, n_ops=2, outstanding=256, timeout=8,
            )
            probe_rows.append(
                {
                    "trial": trial,
                    "seed": tseed,
                    "probe": "timeout=8",
                    "t3_r": f"{to.f_timeout:.6f}",
                    "t2": "late-fraction (H-TIMEOUT-WINDOW)",
                    "rel_err": "",
                    "flag_gt_30pct": "",
                    "t3_inject_before_grant": to.inject_before_grant,
                    "t3_gate_on_r": "",
                    "note": (
                        f"collect_timeout_fallback={to.collect_timeout_fallback} "
                        f"ff_notify_max={to.ff_notify_cycles_max} "
                        f"dominates={to.fallback_dominates}"
                    ),
                }
            )

    summary = []
    for key, xs in sorted(ms_store.items()):
        cls, arm, ost = key
        m, hw, n = ci95(xs)
        summary.append(
            {
                "class": cls,
                "arm": arm,
                "outstanding": ost,
                "makespan_ci": fmt_ci(xs, 2),
                "mean_makespan": m,
                "ci95_hw": hw,
                "n": n,
                "card_claim": CARD_CLAIM.get(cls, "n/a"),
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
    _write_csv(out / "alltoall_residual.csv", a2a_rows)
    _write_csv(out / "probes.csv", probe_rows)
    _write_csv(out / "bw_ci.csv", summary)
    _write_csv(out / "t2_signed_pins.csv", signed_t2_rows())

    labels, t2v, t3v = [], [], []
    for cls in ("gather", "reduce", "allgather", "allreduce", "alltoall", "broadcast",
                "uniform_read", "uniform_write"):
        rows = [r for r in cmp_rows if r["class"] == cls and r["arm"] == "CSR" and r["outstanding"] == 256]
        if not rows:
            continue
        labels.append(cls)
        t2 = rows[0]["t2_T_hat_over_T_off"]
        t3s = [r["t3_T_hat_over_T_off"] for r in rows if not _nan(r["t3_T_hat_over_T_off"])]
        t2v.append(float(t2) if not _nan(t2) else 0.0)
        t3v.append(sum(t3s) / len(t3s) if t3s else 0.0)
    if labels:
        _plot_bars(
            occ_dir / "t2_vs_t3_ratio.png",
            labels,
            [("T2 signed r", t2v), ("T3 makespan_on/off", t3v)],
            "T_hat/T_off (per class; not averaged)",
            "P-0198/M-2 CSR  T2 vs T3 relative makespan — not card-claim",
        )

    a8 = t2_completion_split(8.0)
    meta = {
        "card": "P-0198/M-2 CSR Rendezvous-Grant",
        "seed": seed,
        "mode": mode,
        "t2_model_on_tree": t2_present,
        "t2_source": "signed audit PR #68 + spec §3; model.py PR #66 not on main",
        "t2_signed": T2_SIGNED,
        "t2_flags_gt_30pct": len(flags),
        "n_occ_rows": len(occ_rows),
        "n_cyc_rows": len(cyc_rows),
        "n_a2a_rows": len(a2a_rows),
        "n_probe_rows": len(probe_rows),
        "occupancy_csv": str(occ_dir / "occupancy.csv"),
        "t2_compare_csv": str(occ_dir / "t2_compare.csv"),
        "bw_ci": summary,
        "t2_a8_replay": {"f_ov": a8[0], "dominates": t2_fallback_dominates(a8[0], a8[1])},
        "bbox": (
            f"{n_top}+{n_bottom} nodes, CHI 4 rings × 2 dirs, N_cam={N_CAM}, "
            f"outstanding∈{list(osts)}, |ops|={n_ops} (allgather/allreduce capped), "
            "warmup≥1 lap, 512 B / 8 beats, fold_ports=1, W_grant=1; "
            "clock UNKNOWN; not tests/soc_sim gem5"
        ),
        "note": (
            "card-claim 0.45-0.80x / 0.60-0.95x+res is NOT measured. "
            "0.85 is a pass bar. Do not average classes. "
            "Do not mix M-1 CBC (淘汰 PR #62/#64) or M-5 CRRF. "
            "If |T3−T2|/T2>30% the T3 number stands; do not substitute T2."
        ),
        "dr_sim": {
            "dat_beats_held_probe": True,
            "same_cycle_reclassify": True,
            "four_fsm_independent_timeout": True,
            "classifier_ff_bounded": True,
            "grant_static_order_table": True,
            "endpoint_fold_ports": True,
            "alltoall_residual_percentiles": True,
            "warmup_12_2_four_ring_512B_ost": True,
        },
        "separate_from": ["P-0198/M-1 CBC (eliminated T3)", "P-0198/M-5 CRRF (separate T3)"],
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"CSR sweep mode={mode} seed={seed} → {out}")
    print(f"occupancy/t2_compare → {occ_dir}")
    print(f"T2 model.py on tree: {t2_present}")
    print(f"T2 |T3-T2|/T2 > 30% flags: {len(flags)}")
    print("card-claim bands are NOT measured")
    for s in summary:
        if s["outstanding"] == 256 and s["class"] in ("gather", "alltoall", "uniform_read"):
            print(f"  {s['class']:14} {s['arm']:14} ost={s['outstanding']} {s['makespan_ci']}")
    if flags:
        print("DISCREPANCY: inspect simulator (do not silently pick T2). Sample:")
        print(flags[0])
    hard = [
        r for r in cmp_rows
        if r["class"] == "gather" and r["outstanding"] == 256 and r["trial"] == 0
    ]
    if hard:
        off_ms = next(r["t3_makespan"] for r in hard if r["arm"] == "spine-off")
        on_ms = next(r["t3_makespan"] for r in hard if r["arm"] == "CSR")
        print(f"HARD spine-off cycle probe: off ({off_ms}) > CSR ({on_ms})? {off_ms > on_ms}")
        print("T2 HARD (ns, not comparable abs): 537.2 > 289.3")
    for row in probe_rows:
        if row["trial"] == 0:
            print(f"probe {row['probe']}: t3={row['t3_r']} t2={row['t2']} {row['note']}")
    return meta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("smoke", "night"), default="smoke")
    p.add_argument("--out", type=Path, default=_HERE / "results")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--n-trials", type=int, default=3)
    p.add_argument("--n-ops", type=int, default=None)
    args = p.parse_args(argv)
    sweep(args.mode, args.out, args.seed, args.n_trials, args.n_ops)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
