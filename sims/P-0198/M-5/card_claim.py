#!/usr/bin/env python3
"""Card-claim measurement for P-0198/M-5 CRRF (unsigned; not a conclusion).

Card (PR #53 `mechanisms/P-0198/M-5.md` §4, not on this tree):
  Dat-heavy collectives / saturated uniform-read region:
    **0.55–0.85× makespan** vs rebind-off, after drain tax.
  0.85 is a pass bar, not a measured mean. Director did not sign.

Luke 2026-10-09 one-shot: measure that interval on **inference**
(decode-phase KV / P2P + inference-time collectives). Training is
secondary and is never averaged with inference.

Writes **only** to ``results/card_claim/``. Does not touch signed
``results/`` smoke fixtures or ``results/night/``.

Does **not** change RTL, FSM, arbitration, or timing. Baselines use
existing driver knobs:

  * no_cc display: 信封 outstanding（窗口不绑定）. outstanding = |I|;
    ratio is unchanged for outstanding≥8.
  * source_fc display: 下界敏感性列，过保守. outstanding = 1.

Proposal = CRRF duty arm, **same** outstanding / same txn list / same seed.
Duty arms {3:1, 7:1, 15:1} are never averaged. 15:1 Snp 1.4× remains KILL.
T4 is not opened. Workload tables were not in-repo → existing_config.
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
    SNP_KILL,
    SimConfig,
    gen_mixed,
    gen_txns,
    run_arm,
    run_cycles,
)
from t2_pins import (  # noqa: E402
    CARD_CLAIM_DAT,
    C_DAT_EFF as T2_C_DAT_EFF,
    DAT_DOM,
    H_DAT_DOM_GATHER,
)

WORKLOAD_SOURCE = "existing_config (负载基线表未到)"
CLAIM_LO = 0.55
CLAIM_HI = 0.85
START_SHA = "b0b4cf968f62d95becfb437cc76512784af2e606"

# Card §4 Dat-heavy set, labeled for inference (primary) vs training (secondary).
# No decode-* generator is invented: each row is an existing CLASSES driver.
WORKLOADS = (
    {
        "category": "inference",
        "workload": "decode_kv_p2p",
        "cls": "uniform_read",
        "role": "primary",
        "note": "decode-phase KV / P2P scan; existing uniform_read (problem: KV 扫描)",
    },
    {
        "category": "inference",
        "workload": "decode_kv_gather",
        "cls": "gather",
        "role": "primary",
        "note": "decode-phase KV gather; existing gather (card Dat-heavy collective). gather 与 reduce 同形，不是两条独立证据。",
        "same_shape_as": "reduce",
    },
    {
        "category": "inference",
        "workload": "infer_allgather",
        "cls": "allgather",
        "role": "primary",
        "note": "inference-time allgather; existing allgather",
    },
    {
        "category": "inference",
        "workload": "infer_allreduce",
        "cls": "allreduce",
        "role": "primary",
        "note": "inference-time allreduce; existing allreduce",
    },
    {
        "category": "training",
        "workload": "train_reduce",
        "cls": "reduce",
        "role": "secondary",
        "note": "training-class reduce; secondary only — not averaged with inference. gather 与 reduce 同形，不是两条独立证据。",
        "same_shape_as": "gather",
    },
    {
        "category": "training",
        "workload": "train_alltoall",
        "cls": "alltoall",
        "role": "secondary",
        "note": "training-class alltoall; secondary only — not averaged with inference",
    },
)

# Two baselines. Proposal is CRRF-on with the same outstanding.
BASELINES = (
    {
        "type": "no_cc",
        "label": "信封 outstanding（窗口不绑定）",
        "outstanding_mode": "unbound",  # outstanding = n_txn
        "note": (
            "信封 outstanding（窗口不绑定）：rebind-off; outstanding=|I|。 "
            "outstanding≥8 时比值已不变（与 ost=16/32/96 同一 makespan）。"
        ),
    },
    {
        "type": "source_fc",
        "label": "下界敏感性列，过保守",
        "outstanding_mode": "window1",  # existing per-source outstanding=1
        "note": (
            "下界敏感性列，过保守：rebind-off; outstanding=1 "
            "（现有源端窗口，不是目的端 credit）。"
        ),
    },
)

DUTY_TIE_NOTE = (
    "3:1 / 7:1 / 15:1 makespan 相同是 eject/root 串行封顶所致"
    "（C_dat_eff 和 Snp 都随 duty 变化），不是旋钮失效；3:1 支配。"
)

PROPOSAL_ARMS = ("3:1", "7:1", "15:1")
FORBIDDEN_OUT_NAMES = (
    "capacity.csv",
    "t2_compare.csv",
    "cycles.csv",
    "dat_makespan.csv",
    "snp_path.csv",
    "hard2_dest.csv",
    "bw_ci.csv",
    "t2_signed_pins.csv",
    "summary.json",
)


def _t2_ratio(cls: str, arm: str) -> float | None:
    """Signed / algebraic T2 Dat-heavy T_hat/T_off. None if not a claim class."""
    if cls not in DAT_DOM:
        return None
    if cls == "gather" and arm in H_DAT_DOM_GATHER:
        return float(H_DAT_DOM_GATHER[arm])
    c = T2_C_DAT_EFF.get(arm)
    if not c or c <= 0:
        return None
    return 1.0 / float(c)


def _ost(mode: str, n_txn: int) -> int:
    if mode == "window1":
        return 1
    return max(1, int(n_txn))


def _nan(x) -> bool:
    return isinstance(x, float) and (math.isnan(x) or math.isinf(x))


def _f(x, nd=6):
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        return x
    if x is None:
        return ""
    if _nan(float(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _in_interval(ratio: float | None) -> str:
    if ratio is None or _nan(float(ratio)):
        return "NOT measured"
    r = float(ratio)
    return "yes" if CLAIM_LO - 1e-12 <= r <= CLAIM_HI + 1e-12 else "no"


def _ci_hi_vs_085(mean: float, hw: float) -> tuple[float, str]:
    """CI upper (mean+hw) vs the 0.85 pass bar. Does not rewrite in_0.55_0.85."""
    if _nan(mean) or _nan(hw):
        return float("nan"), "NOT measured"
    hi = float(mean) + float(hw)
    return hi, ("yes" if hi <= CLAIM_HI + 1e-12 else "no")


def _fmt_trial_ratios(xs: list[float]) -> str:
    """Per-trial ratios, 3 d.p., slash-separated (audit example 0.852 / 0.880 / 0.739)."""
    return " / ".join(_f(x, 3) for x in xs)


def _assert_not_signed_dir(out: Path) -> None:
    """Refuse to write into the signed smoke dir or results/night/."""
    resolved = out.resolve()
    smoke = (_HERE / "results").resolve()
    night = (_HERE / "results" / "night").resolve()
    if resolved == smoke:
        raise ValueError("card-claim must not write into signed results/")
    if resolved == night or night in resolved.parents:
        raise ValueError("card-claim must not write into results/night/")
    # also refuse if caller pointed at results and we somehow didn't redirect
    for name in FORBIDDEN_OUT_NAMES:
        if (smoke / name) == (resolved / name) and resolved == smoke:
            raise ValueError(f"refusing to overwrite signed {name}")


def run_card_claim(
    out: Path,
    seed: int = SEED,
    n_trials: int = 3,
    n_txn: int | None = None,
    n_nodes: int = 12,
    n_bottom: int = 2,
    t_steady_laps: int = 12,
) -> dict:
    _assert_not_signed_dir(out)
    out.mkdir(parents=True, exist_ok=True)
    n_txn = 96 if n_txn is None else int(n_txn)
    n_trials = max(3, int(n_trials))
    n = n_nodes + n_bottom
    n_snp = max(8, n_txn // 8)

    trial_rows: list[dict] = []
    snp_rows: list[dict] = []
    # (category, workload, cls, baseline, arm) -> lists
    base_ms: dict[tuple, list[float]] = {}
    crrf_ms: dict[tuple, list[float]] = {}
    ratios: dict[tuple, list[float]] = {}

    for trial in range(n_trials):
        tseed = seed + trial
        for wl in WORKLOADS:
            cls = wl["cls"]
            txns = gen_txns(cls, n, n_txn, tseed)
            for bl in BASELINES:
                ost = _ost(bl["outstanding_mode"], n_txn)
                off = run_arm(
                    "rebind-off", cls, tseed, list(txns),
                    n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                    outstanding=ost, t_steady_laps=t_steady_laps,
                )
                for arm in PROPOSAL_ARMS:
                    on = run_arm(
                        arm, cls, tseed, list(txns),
                        n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                        outstanding=ost, t_steady_laps=t_steady_laps,
                    )
                    ratio = (
                        on.makespan / off.makespan
                        if off.makespan > 0 else float("nan")
                    )
                    key = (wl["category"], wl["workload"], cls, bl["type"], arm)
                    base_ms.setdefault(key, []).append(float(off.makespan))
                    crrf_ms.setdefault(key, []).append(float(on.makespan))
                    ratios.setdefault(key, []).append(float(ratio))
                    trial_rows.append(
                        {
                            "trial": trial,
                            "seed": tseed,
                            "load_category": wl["category"],
                            "workload": wl["workload"],
                            "cls": cls,
                            "role": wl["role"],
                            "baseline_type": bl["type"],
                            "baseline_label": bl["label"],
                            "outstanding": ost,
                            "arm": arm,
                            "metric": "makespan",
                            "baseline_makespan": off.makespan,
                            "crrf_makespan": on.makespan,
                            "ratio": _f(ratio, 4),
                            "completed_dat_base": off.completed_dat,
                            "completed_dat_crrf": on.completed_dat,
                            "completed_snp_crrf": on.completed_snp,
                            "c_dat_eff": _f(on.c_dat_eff, 4),
                            "tax": _f(on.tax, 4),
                            "mismatch": on.bind_mismatch_redirect,
                            "aligned": on.aligned,
                            "card_claim": CARD_CLAIM_DAT if cls in DAT_DOM else "n/a",
                            "card_claim_is_measured": False,
                            "unsigned": True,
                            "workload_source": WORKLOAD_SOURCE,
                            "note": wl["note"],
                        }
                    )

        # Snp companion — 15:1 remains KILL; not a 0.55–0.85 card-claim row.
        for bl in BASELINES:
            ost = _ost(bl["outstanding_mode"], n_txn)
            snp_tx = gen_txns("snp_path", n, n_txn, tseed)
            mixed = gen_mixed(n, n_txn, n_snp, tseed, "gather")
            off_s = run_arm(
                "rebind-off", "snp_path", tseed, list(snp_tx),
                n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                outstanding=ost, t_steady_laps=t_steady_laps,
            )
            off_m = run_cycles(
                SimConfig(
                    arm="rebind-off", traffic_class="gather", seed=tseed,
                    n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn, n_snp=n_snp,
                    outstanding=ost, t_steady_laps=t_steady_laps,
                ),
                list(mixed),
            )
            for arm in PROPOSAL_ARMS:
                on_s = run_arm(
                    arm, "snp_path", tseed, list(snp_tx),
                    n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn,
                    outstanding=ost, t_steady_laps=t_steady_laps,
                )
                on_m = run_cycles(
                    SimConfig(
                        arm=arm, traffic_class="gather", seed=tseed,
                        n_nodes=n_nodes, n_bottom=n_bottom, n_txn=n_txn, n_snp=n_snp,
                        outstanding=ost, t_steady_laps=t_steady_laps,
                    ),
                    list(mixed),
                )
                path_r = (
                    on_s.makespan / off_s.makespan
                    if off_s.makespan > 0 else float("nan")
                )
                mix_r = (
                    on_m.makespan_snp / off_m.makespan_snp
                    if off_m.makespan_snp > 0 and on_m.makespan_snp > 0
                    else float("nan")
                )
                path_kill = (not _nan(path_r)) and path_r > SNP_KILL
                mix_kill = (not _nan(mix_r)) and mix_r > SNP_KILL
                snp_rows.append(
                    {
                        "trial": trial,
                        "seed": tseed,
                        "baseline_type": bl["type"],
                        "baseline_label": bl["label"],
                        "outstanding": ost,
                        "arm": arm,
                        "window": "snp_path",
                        "T_snp_over_off": _f(path_r, 4),
                        "kill_1.4": path_kill,
                        "completed_snp_off": off_s.completed_snp,
                        "completed_snp_on": on_s.completed_snp,
                        "comp_drop": on_s.completed_snp < off_s.completed_snp,
                        "card_claim": "<=1.4x kill",
                        "card_claim_is_measured": False,
                        "note": "15:1 remains KILL; not a 0.55-0.85 interval",
                    }
                )
                snp_rows.append(
                    {
                        "trial": trial,
                        "seed": tseed,
                        "baseline_type": bl["type"],
                        "baseline_label": bl["label"],
                        "outstanding": ost,
                        "arm": arm,
                        "window": "snp_on_gather",
                        "T_snp_over_off": _f(mix_r, 4),
                        "kill_1.4": mix_kill,
                        "completed_snp_off": off_m.completed_snp,
                        "completed_snp_on": on_m.completed_snp,
                        "comp_drop": on_m.completed_snp < off_m.completed_snp,
                        "card_claim": "<=1.4x kill",
                        "card_claim_is_measured": False,
                        "note": "15:1 remains KILL; not a 0.55-0.85 interval",
                    }
                )

    # ---- summary rows (one per workload × baseline × arm) ----
    summary_rows: list[dict] = []
    gt30: list[dict] = []
    for key in sorted(ratios.keys()):
        category, workload, cls, btype, arm = key
        bl = next(b for b in BASELINES if b["type"] == btype)
        wl = next(w for w in WORKLOADS if w["workload"] == workload)
        xs_b = base_ms[key]
        xs_c = crrf_ms[key]
        xs_r = ratios[key]
        mb, hwb, nb = ci95(xs_b)
        mc, hwc, nc = ci95(xs_c)
        mr, hwr, nr = ci95(xs_r)
        t2 = _t2_ratio(cls, arm)
        err = rel_err(mr, t2) if t2 is not None and not _nan(mr) else ""
        flag = bool(err > 0.30) if err != "" and err == err else ""
        ci_hi, ci_hi_vs = _ci_hi_vs_085(mr, hwr)
        row = {
            "load_category": category,
            "workload": workload,
            "cls": cls,
            "role": wl["role"],
            "baseline_type": btype,
            "baseline_label": bl["label"],
            "outstanding": _ost(bl["outstanding_mode"], n_txn),
            "arm": arm,
            "metric": "makespan",
            "baseline_ci": fmt_ci(xs_b, 2),
            "crrf_ci": fmt_ci(xs_c, 2),
            "ratio": _f(mr, 4),
            "ratio_ci": fmt_ci(xs_r, 4),
            "ratio_mean": mr,
            "ratio_ci95_hw": hwr,
            "n": nr,
            "in_0.55_0.85": _in_interval(mr),
            "card_interval": CARD_CLAIM_DAT,
            "card_claim_is_measured": False,
            "unsigned": True,
            "not_a_conclusion": True,
            "t2_ref": _f(t2, 4) if t2 is not None else "",
            "rel_err_vs_t2": _f(err, 4) if err != "" else "",
            "flag_gt_30pct": flag,
            "workload_source": WORKLOAD_SOURCE,
            "note": wl["note"],
            "ci_hi": _f(ci_hi, 4),
            "ci_hi_vs_0.85": ci_hi_vs,
            "trial_ratios": _fmt_trial_ratios(xs_r),
            "same_shape_as": wl.get("same_shape_as", ""),
            "duty_note": DUTY_TIE_NOTE,
        }
        summary_rows.append(row)
        if flag is True:
            gt30.append(row)

    # Snp 15:1 kill rollup — must stay True (KILL)
    snp_kill_15: dict[str, bool] = {}
    for bl in BASELINES:
        rows15 = [r for r in snp_rows if r["baseline_type"] == bl["type"] and r["arm"] == "15:1"]
        killed = any(r["kill_1.4"] for r in rows15)
        snp_kill_15[bl["type"]] = killed

    _write_csv(out / "card_claim_trials.csv", trial_rows)
    _write_csv(out / "card_claim.csv", summary_rows)
    _write_csv(out / "snp_kill.csv", snp_rows)

    infer_rows = [r for r in summary_rows if r["role"] == "primary"]
    train_rows = [r for r in summary_rows if r["role"] == "secondary"]

    def _ratio_table(rows: list[dict]) -> list[dict]:
        keep = (
            "load_category", "workload", "cls", "baseline_type", "arm",
            "baseline_ci", "crrf_ci", "ratio_ci", "in_0.55_0.85",
            "ci_hi", "ci_hi_vs_0.85", "trial_ratios",
            "t2_ref", "rel_err_vs_t2", "flag_gt_30pct", "workload_source",
        )
        return [{k: r[k] for k in keep} for r in rows]

    meta = {
        "card": "P-0198/M-5 CRRF",
        "task": "card-claim measurement (Luke 2026-10-09 one-shot)",
        "start_sha": START_SHA,
        "seed": seed,
        "n_trials": n_trials,
        "trials_seeds": [seed + i for i in range(n_trials)],
        "metric": (
            "makespan (cycle last_complete - first_issue), "
            "CRRF / baseline, same txn list, same outstanding, same seed"
        ),
        "card_claim_definition": {
            "source": "mechanisms/P-0198/M-5.md §4 (PR #53; not on this tree)",
            "interval": CARD_CLAIM_DAT,
            "quantity": "makespan",
            "relative_to": "rebind-off (classic 1:1, no ghost)",
            "load": "Dat-heavy collectives / saturated uniform-read region",
            "after": "drain / SYNC / bind tax already in the cycle model",
            "pass_bar": "0.85 is a pass bar, not a measured mean",
        },
        "primary_focus": "inference (decode KV/P2P + inference collectives)",
        "training": "secondary only; not averaged with inference; no separate report",
        "baselines": [
            {
                "type": b["type"],
                "label": b["label"],
                "outstanding": _ost(b["outstanding_mode"], n_txn),
                "note": b["note"],
                "structure_change": False,
            }
            for b in BASELINES
        ],
        "proposal": (
            "CRRF duty arms {3:1, 7:1, 15:1} — never averaged. "
            + DUTY_TIE_NOTE
        ),
        "gather_reduce_same_shape": True,
        "gather_reduce_independent_evidence": False,
        "not_measured_columns": [],
        "structure_changes": [],
        "structure_change_reason": (
            "源端流控 is expressed as the existing per-source outstanding window "
            "set to 1. A destination-credit protocol is not in the sim; adding "
            "one would be an inject-path structure change. Not implemented."
        ),
        "workload_source": WORKLOAD_SOURCE,
        "workload_tables_present": False,
        "bbox": (
            f"{n_nodes}+{n_bottom} nodes, |I|={n_txn}, |Snp|={n_snp}, "
            f"t_steady_laps={t_steady_laps}, hop_lat=1, flit=txn 512B, "
            "reduced-bbox vs envelope rd512/wr256; clock UNKNOWN"
        ),
        "command": (
            f"python3 sims/P-0198/M-5/sweep.py --mode card_claim --seed {seed}"
        ),
        "commands": [
            f"python3 sims/P-0198/M-5/sweep.py --mode card_claim --seed {seed}",
            f"python3 sims/P-0198/M-5/card_claim.py --seed {seed}",
        ],
        "unsigned": True,
        "card_claim_is_measured": False,
        "not_a_conclusion": True,
        "eval_audit_signed": False,
        "t4_opened": False,
        "eval_audit": {
            "verdict": "部分成立",
            "signed_full_envelope": False,
            "returned": False,
            "detail": (
                "部分成立（gather 0.551、allgather 0.667、alltoall 0.719 过；"
                "decode_kv_p2p 0.824 边缘；allreduce 1.000 不过）"
            ),
            "existing_config_signs_inference_decode": False,
            "existing_config_note": (
                "existing_config 不签推理 / decode 相关性"
            ),
            "card_all_class_0.55_0.85_signed": False,
            "card_all_class_note": "卡上 0.55–0.85× 全类声明不签",
            "snp_15_1": "KILL",
        },
        "snp_15_1_kill": {
            "hypothesis": "T_snp / rebind-off > 1.4 → KILL",
            "no_cc": snp_kill_15.get("no_cc"),
            "source_fc": snp_kill_15.get("source_fc"),
            "softened": False,
            "note": "15:1 Snp remains KILL on both baselines; not folded into Dat mean",
        },
        "inference_rows": _ratio_table(infer_rows),
        "training_secondary_rows": _ratio_table(train_rows),
        "flag_gt_30pct_rows": [
            {
                "workload": r["workload"],
                "baseline_type": r["baseline_type"],
                "arm": r["arm"],
                "ratio": r["ratio"],
                "t2_ref": r["t2_ref"],
                "rel_err_vs_t2": r["rel_err_vs_t2"],
            }
            for r in gt30
        ],
        "gt30_explanations": _gt30_explanations(gt30),
        "note": (
            "These numbers are NOT eval-audit signed and are NOT a conclusion. "
            "card-claim 0.55–0.85× was NOT measured in signed smoke/night; "
            "this directory is a one-shot unsigned measurement. "
            "Do not average duty arms. Do not average inference with training. "
            "Do not hide Snp 15:1 KILL behind a Dat mean. "
            "If |T3−T2|/T2>30% the T3 number stands; do not substitute T2. "
            "T4 is not opened. Not mixed with M-1 CBC / M-2 / M-4."
        ),
        "signed_artifacts_untouched": [
            "sims/P-0198/M-5/results/capacity.csv",
            "sims/P-0198/M-5/results/t2_compare.csv",
            "sims/P-0198/M-5/results/night/",
        ],
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
    _plot(out, infer_rows)

    print(f"CRRF card-claim seed={seed} → {out}")
    print("UNSIGNED — not a conclusion; eval audit has not signed these numbers")
    print(f"workload_source={WORKLOAD_SOURCE}")
    print(f"15:1 Snp KILL no_cc={snp_kill_15.get('no_cc')} source_fc={snp_kill_15.get('source_fc')}")
    print("inference (primary):")
    for r in infer_rows:
        if r["arm"] == "7:1":
            print(
                f"  {r['workload']:18} {r['baseline_type']:10} "
                f"{r['ratio_ci']}  in_interval={r['in_0.55_0.85']}  "
                f"gt30={r['flag_gt_30pct']}"
            )
    return meta


def _gt30_explanations(rows: list[dict]) -> list[dict]:
    """Inspect-the-sim notes. T3 stands; T2 is not substituted."""
    out = []
    for r in rows:
        cls = r["cls"]
        btype = r["baseline_type"]
        why = "see report"
        if cls == "allreduce":
            why = (
                "Existing allreduce driver is half gather-to-root + half root-scatter "
                "(broadcast-like). Night already showed broadcast makespan 1.00× on "
                "every duty arm (dest-0 / root serialize, not Dat-slot limited). "
                "Combined makespan stays at the longer half, so T3 ratio ≈1.0 vs "
                "T2 1/C_dat_eff ≈0.56–0.62. Cycle model, not a T2 substitution."
            )
        elif cls == "uniform_read":
            why = (
                "uniform_read at this bbox is hop / dest-eject limited more than "
                "Dat-slot limited: on-arms share the same makespan (ghost slots do "
                "not keep buying time after eject saturates). T2 H-DAT-DOM algebra "
                "is 1/C_dat_eff; T3 ratio sits near 0.85. Same dest-eject ceiling "
                "already noted for gather duty-tie in the T3 report."
            )
        elif cls in ("gather", "reduce") and btype == "source_fc":
            why = (
                "outstanding=1 serializes each source to one inflight txn. Gather/"
                "reduce already serialize on dest-0 eject, so the ghost Dat ring "
                "has no second inflight to carry. Ratio → 1.0, far from T2 "
                "1/C_dat_eff which assumes unsaturated multi-outstanding Dat."
            )
        elif btype == "source_fc":
            why = (
                "T2 pins assume the default outstanding window (no extra source "
                "throttle). outstanding=1 is a different inject envelope; T2 "
                "1/C_dat_eff is not the right algebraic twin. T3 stands."
            )
        elif cls == "allgather":
            why = (
                "allgather is all-pairs Dat; T3 ratio can sit above T2 1/C_dat_eff "
                "because dest eject + drain tax cap the ghost gain. T3 stands."
            )
        else:
            why = (
                "T3 cycle makespan / rebind-off vs T2 1/C_dat_eff. Inspected the "
                "existing driver (no model swap). T3 stands."
            )
        out.append(
            {
                "workload": r["workload"],
                "baseline_type": btype,
                "arm": r["arm"],
                "ratio": r["ratio"],
                "t2_ref": r["t2_ref"],
                "rel_err_vs_t2": r["rel_err_vs_t2"],
                "reason": why,
            }
        )
    return out


def _plot(out: Path, infer_rows: list[dict]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return
    # 7:1 only (card example); two baseline groups; do not average arms
    rows = [r for r in infer_rows if r["arm"] == "7:1"]
    if not rows:
        return
    labels = []
    seen = []
    for r in rows:
        if r["workload"] not in seen:
            seen.append(r["workload"])
            labels.append(r["workload"])
    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    w = 0.36
    x = range(len(labels))
    for i, btype in enumerate(("no_cc", "source_fc")):
        vals = []
        for wl in seen:
            hit = next((r for r in rows if r["workload"] == wl and r["baseline_type"] == btype), None)
            vals.append(float(hit["ratio"]) if hit and hit["ratio"] not in ("", "nan") else 0.0)
        ax.bar([j + (i - 0.5) * w for j in x], vals, w, label=btype)
    ax.axhline(CLAIM_LO, color="0.4", ls="--", lw=1, label="card 0.55")
    ax.axhline(CLAIM_HI, color="0.4", ls=":", lw=1, label="card 0.85 (bar)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("makespan CRRF 7:1 / baseline")
    ax.set_title("P-0198/M-5 card-claim (inference, unsigned; arms not averaged)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "card_claim_inference_7_1.png", dpi=120)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Unsigned card-claim measurement")
    p.add_argument("--out", type=Path, default=_HERE / "results" / "card_claim")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--n-trials", type=int, default=3)
    p.add_argument("--n-txn", type=int, default=None)
    args = p.parse_args(argv)
    run_card_claim(args.out, args.seed, args.n_trials, args.n_txn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
