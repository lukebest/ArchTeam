#!/usr/bin/env python3
"""Parameter sweep + T2 compare for P-0198/M-5 CRRF.

One-command smoke:
  python3 sims/P-0198/M-5/sweep.py --mode smoke --seed 20260903

Night:
  python3 sims/P-0198/M-5/sweep.py --mode night --seed 20260903

Night capacity / t2_compare write to <out>/night/ and do not
overwrite the signed smoke fixture at <out>/{capacity,t2_compare}.csv.

Ablation is rebind-off only. Duty arms are never averaged. Snp is never
folded into a Dat mean. This card is not ranked against M-1 / M-2 / M-4.
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

from _lib.stats import ci95, fmt_ci  # noqa: E402
from _lib.workloads import SEED  # noqa: E402
from sim import (  # noqa: E402
    ARMS,
    CLASSES,
    SNP_KILL,
    SimConfig,
    card_claim_of,
    compare_to_t2,
    gen_mixed,
    gen_txns,
    probe_commit,
    probe_drain,
    run_arm,
    run_cycles,
    signed_t2_rows,
    try_load_t2_module,
)
from t2_pins import (  # noqa: E402
    CARD_CLAIM_DAT,
    C_DAT_EFF as T2_C_DAT_EFF,
    F_STEADY as T2_F_STEADY,
    H_COMMIT_HELD,
    H_COMMIT_VIOLATED,
    H_DAT_DOM_GATHER,
    HARD1_T_BEST,
    HARD1_T_OFF,
    SNP_15_1,
    T_DRAIN as T2_T_DRAIN,
    T_OFF,
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


def _f(x, nd=6):
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        return x
    if _nan(float(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


SMOKE_CLASSES = ("gather", "uniform_read", "uniform_write", "snp_path")
NIGHT_CLASSES = CLASSES


def sweep(mode: str, out: Path, seed: int, n_trials: int, n_txn: int | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        n_nodes, n_bottom = 12, 0
        n_txn = n_txn if n_txn is not None else 48
        n_snp = max(6, n_txn // 8)
        n_trials = min(n_trials, 3)
        classes = list(SMOKE_CLASSES)
        ost = 16
        t_steady_laps = 8
        extra_n25 = True
    else:
        n_nodes, n_bottom = 12, 2
        n_txn = n_txn if n_txn is not None else 96
        n_snp = max(8, n_txn // 8)
        classes = list(NIGHT_CLASSES)
        ost = 32
        t_steady_laps = 12
        extra_n25 = True

    t2_present = try_load_t2_module() is not None
    cap_rows = []
    cmp_rows = []
    cyc_rows = []
    snp_rows = []
    dat_rows = []
    hard2_rows = []
    ms_store: dict[tuple, list[float]] = {}
    cdat_store: dict[tuple, list[float]] = {}

    drain = probe_drain(n_nodes=25 if extra_n25 else n_nodes, n_pipe=2, seed=seed)
    held = probe_commit(n_nodes=12, violated=False, seed=seed)
    viol = probe_commit(n_nodes=12, violated=True, seed=seed)

    for trial in range(n_trials):
        tseed = seed + trial
        off_by_cls: dict[str, object] = {}
        mixed_by_seed = gen_mixed(n_nodes + n_bottom, n_txn, n_snp, tseed, "gather")
        for cls in classes:
            n = n_nodes + n_bottom
            txns = gen_txns(cls, n, n_txn, tseed)
            for arm in ARMS:
                r = run_arm(
                    arm, cls, tseed, txns,
                    n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                    outstanding=ost, t_steady_laps=t_steady_laps,
                )
                if arm == "rebind-off":
                    off_by_cls[cls] = r
                key = (cls, arm)
                ms_store.setdefault(key, []).append(float(r.makespan))
                cdat_store.setdefault(key, []).append(float(r.c_dat_eff))
                cyc_rows.append(
                    {
                        "trial": trial,
                        "seed": tseed,
                        "class": cls,
                        "arm": arm,
                        "duty_dat": _f(r.duty_dat, 4),
                        "n_nodes": r.n_nodes,
                        "n_txn": n_txn,
                        "makespan": r.makespan,
                        "makespan_dat": r.makespan_dat,
                        "makespan_snp": r.makespan_snp,
                        "completed_dat": r.completed_dat,
                        "completed_snp": r.completed_snp,
                        "c_dat_eff": _f(r.c_dat_eff, 4),
                        "c_dat_ideal": _f(r.c_dat_ideal, 4),
                        "f_steady": _f(r.f_steady, 4),
                        "tax": _f(r.tax, 4),
                        "t_drain_mean": _f(r.t_drain_mean, 2),
                        "mismatch": r.bind_mismatch_redirect,
                        "snp_stall": r.snp_stall,
                        "ghost_slots": r.ghost_slots,
                        "aligned": r.aligned,
                        "oracle_used": r.oracle_used,
                        "hint_depends": r.correctness_depends_on_hint,
                        "card_claim": card_claim_of(cls),
                        "card_claim_is_measured": False,
                        "hypothesis": "H-RING-BB",
                    }
                )
                cap_rows.append(
                    {
                        "trial": trial,
                        "class": cls,
                        "arm": arm,
                        "duty_dat": _f(r.duty_dat, 4),
                        "c_dat_eff": _f(r.c_dat_eff, 4),
                        "c_dat_ideal": _f(r.c_dat_ideal, 4),
                        "leq_ideal": r.c_dat_eff <= r.c_dat_ideal + 1e-9,
                        "lt2": r.c_dat_eff < 2.0 - 1e-12,
                        "f_steady": _f(r.f_steady, 4),
                        "tau_drain": _f(r.tau_drain, 4),
                        "tau_sync": _f(r.tau_sync, 4),
                        "tau_bind": _f(r.tau_bind, 4),
                        "tax": _f(r.tax, 4),
                        "tax_gt_0": (r.tax > 0.0) if arm != "rebind-off" else True,
                        "untaxed_double": False if arm == "rebind-off" else (
                            r.c_dat_eff + 1e-12 >= r.c_dat_ideal and r.tax <= 1e-12
                        ),
                        "ghost_slots": r.ghost_slots,
                        "hypothesis": "H-TMUX",
                    }
                )
                hard2_rows.append(
                    {
                        "trial": trial,
                        "class": cls,
                        "arm": arm,
                        "n_dest_main": len(r.dest_main),
                        "n_dest_ghost": len(r.dest_ghost),
                        "hard2_collapsed": r.hard2_collapsed,
                        "note": "512B window = 1 txn; gather dest is workload-collapsed",
                    }
                )

        # mixed Dat gather + Snp, same list every arm (once per trial)
        mixed_off = None
        for arm in ARMS:
            r = run_cycles(
                SimConfig(
                    arm=arm, traffic_class="gather", seed=tseed,
                    n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn, n_snp=n_snp,
                    outstanding=ost, t_steady_laps=t_steady_laps,
                ),
                list(mixed_by_seed),
            )
            if arm == "rebind-off":
                mixed_off = r
            snp_ratio = float("nan")
            if mixed_off is not None and mixed_off.makespan_snp > 0 and r.makespan_snp > 0:
                snp_ratio = r.makespan_snp / mixed_off.makespan_snp
            elif arm == "rebind-off" and r.makespan_snp > 0:
                snp_ratio = 1.0
            kill = (not _nan(snp_ratio)) and snp_ratio > SNP_KILL
            snp_rows.append(
                {
                    "trial": trial,
                    "seed": tseed,
                    "window": "snp_on_gather",
                    "arm": arm,
                    "makespan_snp": r.makespan_snp,
                    "makespan_dat": r.makespan_dat,
                    "completed_snp": r.completed_snp,
                    "completed_dat": r.completed_dat,
                    "snp_stall": r.snp_stall,
                    "T_snp_over_off": _f(snp_ratio, 4) if not _nan(snp_ratio) else "nan",
                    "kill_1.4": kill,
                    "comp_drop": (
                        mixed_off is not None and r.completed_snp < mixed_off.completed_snp
                    ),
                    "card_claim": CARD_CLAIM_DAT,
                    "card_claim_is_measured": False,
                    "note": "Snp column mandatory; 15:1 may KILL",
                }
            )

        for cls in classes:
            off = off_by_cls.get(cls)
            for arm in ARMS:
                cyc = next(
                    r for r in reversed(cyc_rows)
                    if r["trial"] == trial and r["class"] == cls and r["arm"] == arm
                )
                t3_ms = float(cyc["makespan"])
                t3_c = float(cyc["c_dat_eff"])
                ratio = float("nan")
                if off is not None and off.makespan > 0:
                    ratio = t3_ms / off.makespan
                dat_rows.append(
                    {
                        "trial": trial,
                        "class": cls,
                        "arm": arm,
                        "t3_makespan": t3_ms,
                        "t3_C_dat_eff": _f(t3_c, 4),
                        "t3_T_hat_over_T_off": _f(ratio, 4) if not _nan(ratio) else "nan",
                        "t2_T_off_ns": T_OFF.get(cls, ""),
                        "card_claim": card_claim_of(cls),
                        "card_claim_is_measured": False,
                        "note": "cycle makespan; ns T_off is T2-only",
                    }
                )

    # ---- T2 compare (signed pins; T3 numbers stand) ----
    def add_cmp(metric, arm, t3, t2, note=""):
        row = compare_to_t2(metric, arm, float(t3) if not _nan(float(t3)) else float("nan"),
                            float(t2) if not isinstance(t2, str) else float("nan"), note)
        if isinstance(t2, str):
            row["t2"] = t2
            row["rel_err"] = ""
            row["flag_gt_30pct"] = ""
        cmp_rows.append(row)

    add_cmp("T_drain", "C_ring=25", drain["t_drain"], T2_T_DRAIN,
            "cycle probe vs signed 77; formula (k_circ+1)*25+2")
    # f_steady / C_dat_eff from gather trial-0 means
    def mean_field(cls, arm, store):
        xs = store.get((cls, arm), [])
        return sum(xs) / len(xs) if xs else float("nan")

    f7 = []
    for row in cyc_rows:
        if row["class"] == "gather" and row["arm"] == "7:1":
            f7.append(float(row["f_steady"]))
    f_st = sum(f7) / len(f7) if f7 else float("nan")
    add_cmp("f_steady", "7:1", f_st, T2_F_STEADY, "cycle fraction in STEADY vs T2 0.8666")

    for arm in ARMS:
        t3c = mean_field("gather", arm, cdat_store)
        add_cmp("C_dat_eff", arm, t3c, T2_C_DAT_EFF[arm],
                "cycle ghost-up fraction+1 vs signed T2")

    add_cmp("H-COMMIT held", "barrier on", held["bind_mismatch_redirect"], H_COMMIT_HELD,
            "redirect count")
    add_cmp("H-COMMIT violated", "early inject",
            max(viol["bind_mismatch_redirect"], viol["late_newgen_caught"], 1 if viol["violated"] else 0),
            H_COMMIT_VIOLATED, "T2 counts late receivers=12; T3 counts events")

    off_g = mean_field("gather", "rebind-off", ms_store)
    for arm in ("3:1", "7:1", "15:1"):
        on_g = mean_field("gather", arm, ms_store)
        ratio = on_g / off_g if off_g and off_g > 0 else float("nan")
        add_cmp("H-DAT-DOM gather T_hat/T_off", arm, ratio, H_DAT_DOM_GATHER[arm],
                "cycle makespan ratio vs T2 1/C_dat_eff; do not substitute T2")

    on_best = min(mean_field("gather", a, ms_store) for a in ("3:1", "7:1", "15:1"))
    hard1_ok = off_g > on_best
    cmp_rows.append(
        {
            "metric": "HARD-1 cycle inequality",
            "arm": "gather",
            "t3": f"{off_g}>{on_best}",
            "t2": f"{HARD1_T_OFF}>{HARD1_T_BEST}",
            "rel_err": "",
            "flag_gt_30pct": (not hard1_ok),
            "card_claim": "NOT measured",
            "card_claim_is_measured": False,
            "note": "T3 is cycle makespan; T2 is ns H-DAT-DOM. flag if off ≯ best on-arm",
        }
    )

    # Snp 15:1 kill hyp — dedicated snp_path + mixed window (never fold into Dat mean)
    off_s = mean_field("snp_path", "rebind-off", ms_store)
    on_s15 = mean_field("snp_path", "15:1", ms_store)
    snp_path_ratio = on_s15 / off_s if off_s and off_s > 0 else float("nan")
    add_cmp("H-SNP-LAT snp_path", "15:1", snp_path_ratio, SNP_15_1,
            "dedicated Snp class; 15:1 must be allowed to KILL 1.4×; T2 q=1 algebra")
    snp15 = [r for r in snp_rows if r["arm"] == "15:1"]
    if snp15:
        ratios = [float(r["T_snp_over_off"]) for r in snp15 if r["T_snp_over_off"] != "nan"]
        t3s = sum(ratios) / len(ratios) if ratios else float("nan")
        add_cmp("H-SNP-LAT", "15:1", t3s, SNP_15_1,
                "Snp-on-gather window; 15:1 must be allowed to KILL 1.4×; T2 q=1 algebra")
        path_kill = (not _nan(snp_path_ratio)) and snp_path_ratio > SNP_KILL
        mixed_kill = any(r["kill_1.4"] for r in snp15)
        killed = path_kill or mixed_kill
        cmp_rows.append(
            {
                "metric": "Snp 15:1 kill_1.4",
                "arm": "15:1",
                "t3": killed,
                "t2": True,
                "rel_err": 0.0 if killed else 1.0,
                "flag_gt_30pct": not killed,
                "card_claim": "NOT measured",
                "card_claim_is_measured": False,
                "note": "kill hyp is T3>1.4 vs rebind-off (snp_path or mixed); not a card-claim interval",
            }
        )

    cmp_rows.append(
        {
            "metric": "card-claim",
            "arm": "Dat-heavy",
            "t3": "NOT measured",
            "t2": CARD_CLAIM_DAT,
            "rel_err": "",
            "flag_gt_30pct": "",
            "card_claim": CARD_CLAIM_DAT,
            "card_claim_is_measured": False,
            "note": "card-claim only; director did not sign",
        }
    )

    summary = []
    for key, xs in sorted(ms_store.items()):
        cls, arm = key
        m, hw, n = ci95(xs)
        cs = cdat_store[key]
        summary.append(
            {
                "class": cls,
                "arm": arm,
                "makespan_ci": fmt_ci(xs, 2),
                "c_dat_eff_ci": fmt_ci(cs, 4),
                "mean_makespan": m,
                "ci95_hw": hw,
                "n": n,
                "card_claim": card_claim_of(cls),
                "card_claim_is_measured": False,
                "hypothesis": "H-RING-BB",
            }
        )

    flags = [r for r in cmp_rows if r.get("flag_gt_30pct") in (True, "True", True)]
    occ_dir = out / "night" if mode == "night" else out
    occ_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(occ_dir / "capacity.csv", cap_rows)
    _write_csv(occ_dir / "t2_compare.csv", cmp_rows)
    _write_csv(out / "cycles.csv", cyc_rows)
    _write_csv(out / "dat_makespan.csv", dat_rows)
    _write_csv(out / "snp_path.csv", snp_rows)
    _write_csv(out / "hard2_dest.csv", hard2_rows)
    _write_csv(out / "bw_ci.csv", summary)
    _write_csv(out / "t2_signed_pins.csv", signed_t2_rows())
    _write_csv(out / "drain_probe.csv", [drain])
    _write_csv(out / "h_commit_probe.csv", [held, viol])

    labels, t2v, t3v = [], [], []
    for arm in ARMS:
        rows = [r for r in cmp_rows if r["metric"] == "C_dat_eff" and r["arm"] == arm]
        if not rows:
            continue
        labels.append(arm)
        t2v.append(float(rows[0]["t2"]))
        t3v.append(float(rows[0]["t3"]) if not _nan(float(rows[0]["t3"])) else 0.0)
    if labels:
        _plot_bars(
            occ_dir / "t2_vs_t3_c_dat_eff.png",
            labels,
            [("T2 C_dat_eff", t2v), ("T3 C_dat_eff", t3v)],
            "C_dat_eff (slots)",
            "P-0198/M-5 CRRF  T2 vs T3 C_dat_eff — not card-claim; not M-1",
        )

    glabels, gt2, gt3 = [], [], []
    for arm in ("3:1", "7:1", "15:1"):
        rows = [r for r in cmp_rows if r["metric"].startswith("H-DAT-DOM") and r["arm"] == arm]
        if not rows:
            continue
        glabels.append(arm)
        gt2.append(float(rows[0]["t2"]))
        gt3.append(float(rows[0]["t3"]) if not _nan(float(rows[0]["t3"])) else 0.0)
    if glabels:
        _plot_bars(
            occ_dir / "t2_vs_t3_gather_ratio.png",
            glabels,
            [("T2 H-DAT-DOM", gt2), ("T3 makespan_on/off", gt3)],
            "T_hat/T_off (gather)",
            "P-0198/M-5 CRRF  gather ratio vs rebind-off — not card-claim",
        )

    slabels, s3, skill = [], [], []
    for arm in ARMS:
        rows = [r for r in snp_rows if r["arm"] == arm]
        if not rows:
            continue
        xs = [float(r["T_snp_over_off"]) for r in rows if r["T_snp_over_off"] != "nan"]
        slabels.append(arm)
        s3.append(sum(xs) / len(xs) if xs else 0.0)
        skill.append(1.4)
    if slabels:
        _plot_bars(
            out / "snp_ratio.png",
            slabels,
            [("T3 Snp / rebind-off", s3), ("1.4× kill hyp", skill)],
            "T_snp / T_off",
            "P-0198/M-5 CRRF  Snp makespan ratio (15:1 may KILL)",
        )

    meta = {
        "card": "P-0198/M-5 CRRF",
        "seed": seed,
        "mode": mode,
        "t2_model_on_tree": t2_present,
        "t2_source": "signed audit pins (director) + PR #63 spec; model.py not on main",
        "t2_signed": {
            "T_drain": T2_T_DRAIN,
            "f_steady": T2_F_STEADY,
            "C_dat_eff": T2_C_DAT_EFF,
            "H-COMMIT": {"held": H_COMMIT_HELD, "violated": H_COMMIT_VIOLATED},
            "H-DAT-DOM gather": H_DAT_DOM_GATHER,
            "HARD-1": f"{HARD1_T_OFF}>{HARD1_T_BEST}",
            "Snp 15:1": SNP_15_1,
        },
        "t2_flags_gt_30pct": len(flags),
        "n_cap_rows": len(cap_rows),
        "n_cyc_rows": len(cyc_rows),
        "n_snp_rows": len(snp_rows),
        "capacity_csv": str(occ_dir / "capacity.csv"),
        "t2_compare_csv": str(occ_dir / "t2_compare.csv"),
        "bw_ci": summary,
        "drain_probe": drain,
        "h_commit": {"held": held, "violated": viol},
        "bbox": (
            f"{n_nodes}+{n_bottom} nodes, CHI 4 rings × 2 dirs, "
            f"outstanding={ost} (not envelope rd512/wr256), |I|={n_txn}, "
            f"|Snp|={n_snp}, t_steady_laps={t_steady_laps}, "
            "warmup until SYNC-aligned STEADY, "
            "reduced-bbox vs 12+2 DV200 tests/soc_sim; clock UNKNOWN"
        ),
        "note": (
            "card-claim 0.55–0.85× is NOT measured. 0.85 is a pass bar. "
            "Do not average duty arms. Do not hide Snp behind Dat mean. "
            "Ablation vs rebind-off only — not M-1 CBC / M-2 / M-4. "
            "If |T3−T2|/T2>30% the T3 number stands; do not substitute T2."
        ),
        "dr_sim": {
            "five_state_fsm": True,
            "marker_double_return": True,
            "local_sniff_ne_global": True,
            "epoch_committed_barrier": True,
            "accept_set": True,
            "ghost_channel_id_dat": True,
            "nack_reinject": True,
            "no_hint_required": True,
            "sync_not_oracle": True,
            "hard2_dest": True,
            "warmup_sync_aligned": True,
        },
        "eliminated_sibling": "P-0198/M-1 CBC T3 REJECT (PR #62) — not mixed here",
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
    print(f"CRRF sweep mode={mode} seed={seed} → {out}")
    print(f"capacity/t2_compare → {occ_dir}")
    print(f"T2 model.py on tree: {t2_present}")
    print(f"T2 |T3-T2|/T2 > 30% flags: {len(flags)}")
    print(f"card-claim {CARD_CLAIM_DAT} is NOT measured")
    print(f"drain probe n=25 T_drain={drain['t_drain']} T2={T2_T_DRAIN} formula={drain['formula']}")
    print(f"H-COMMIT held mismatch={held['bind_mismatch_redirect']}  "
          f"violated mismatch={viol['bind_mismatch_redirect']} late={viol['late_newgen_caught']}")
    print(f"HARD-1 cycle: rebind-off ({off_g}) > best on-arm ({on_best})? {hard1_ok}")
    for s in summary:
        if s["class"] in ("gather", "snp_path") :
            print(f"  {s['class']:14} {s['arm']:11} {s['makespan_ci']}  C_dat {s['c_dat_eff_ci']}")
    for row in snp_rows:
        if row["trial"] == 0:
            print(
                f"  Snp-on-gather {row['arm']:11} T/T_off={row['T_snp_over_off']} "
                f"kill={row['kill_1.4']} comp={row['completed_snp']}"
            )
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
    p.add_argument("--n-txn", type=int, default=None)
    args = p.parse_args(argv)
    sweep(args.mode, args.out, args.seed, args.n_trials, args.n_txn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
