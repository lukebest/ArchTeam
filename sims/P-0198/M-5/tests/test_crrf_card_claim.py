"""Unsigned card-claim tables: schema, no signed overwrite, 15:1 still KILL."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
_RESULTS = _HERE / "results"
_CLAIM = _RESULTS / "card_claim"
sys.path.insert(0, str(_SIMS))
sys.path.insert(0, str(_HERE))

from card_claim import WORKLOAD_SOURCE, run_card_claim  # noqa: E402

# Smoke / night fixtures that must stay byte-identical (PR #75 / #76).
_SIGNED = (
    _RESULTS / "capacity.csv",
    _RESULTS / "t2_compare.csv",
    _RESULTS / "summary.json",
    _RESULTS / "night" / "capacity.csv",
    _RESULTS / "night" / "t2_compare.csv",
    _RESULTS / "night" / "summary.json",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(name: str) -> list[dict]:
    path = _CLAIM / name
    if not path.is_file():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def signed_hashes():
    return {p: _sha(p) for p in _SIGNED if p.is_file()}


def test_card_claim_refuses_signed_out_dir():
    with pytest.raises(ValueError, match="signed|night"):
        run_card_claim(_RESULTS, seed=20260903, n_trials=3, n_txn=4)
    with pytest.raises(ValueError, match="night"):
        run_card_claim(_RESULTS / "night", seed=20260903, n_trials=3, n_txn=4)


def test_signed_smoke_night_untouched_by_card_claim_dir(signed_hashes):
    """card_claim/ existing must not have rewritten signed fixtures."""
    for p, h in signed_hashes.items():
        assert _sha(p) == h


def test_card_claim_csv_schema_and_unsigned():
    rows = _rows("card_claim.csv")
    if not rows:
        pytest.skip("run sweep --mode card_claim to write results/card_claim/")
    need = {
        "load_category", "workload", "baseline_type", "metric",
        "baseline_ci", "crrf_ci", "ratio", "in_0.55_0.85", "workload_source",
        "ci_hi", "ci_hi_vs_0.85", "trial_ratios",
    }
    assert need <= set(rows[0].keys())
    p2p = next(
        r for r in rows
        if r["workload"] == "decode_kv_p2p" and r["baseline_type"] == "no_cc" and r["arm"] == "7:1"
    )
    assert p2p["trial_ratios"] == "0.852 / 0.880 / 0.739"
    assert p2p["in_0.55_0.85"] == "yes"
    assert p2p["ci_hi_vs_0.85"] == "no"
    g = next(r for r in rows if r["workload"] == "decode_kv_gather")
    red = next(r for r in rows if r["workload"] == "train_reduce")
    assert g.get("same_shape_as") == "reduce"
    assert red.get("same_shape_as") == "gather"
    cats = {r["load_category"] for r in rows}
    assert "inference" in cats
    # inference and training must never be collapsed into one mean arm
    assert all(r["arm"] != "CRRF-mean" for r in rows)
    assert all(r.get("card_claim_is_measured") in ("False", "false", False) for r in rows)
    assert all(r["workload_source"] == WORKLOAD_SOURCE for r in rows)
    infer = [r for r in rows if r["load_category"] == "inference"]
    train = [r for r in rows if r["load_category"] == "training"]
    assert infer
    if train:
        assert all(r.get("role") == "secondary" for r in train)


def test_summary_is_unsigned_not_a_conclusion():
    path = _CLAIM / "summary.json"
    if not path.is_file():
        pytest.skip("run sweep --mode card_claim")
    meta = json.loads(path.read_text())
    assert meta["card"] == "P-0198/M-5 CRRF"
    assert meta["unsigned"] is True
    assert meta["card_claim_is_measured"] is False
    assert meta["not_a_conclusion"] is True
    assert meta["eval_audit_signed"] is False
    assert meta["t4_opened"] is False
    assert "NOT" in meta["note"] or "not a conclusion" in meta["note"].lower()
    assert meta["workload_source"] == WORKLOAD_SOURCE
    assert meta["snp_15_1_kill"]["softened"] is False
    assert meta["structure_changes"] == []
    audit = meta["eval_audit"]
    assert audit["verdict"] == "部分成立"
    assert audit["signed_full_envelope"] is False
    assert audit["returned"] is False
    assert audit["existing_config_signs_inference_decode"] is False
    assert audit["card_all_class_0.55_0.85_signed"] is False
    assert audit["snp_15_1"] == "KILL"
    assert meta["gather_reduce_independent_evidence"] is False
    labels = {b["type"]: b["label"] for b in meta["baselines"]}
    assert "信封 outstanding" in labels["no_cc"]
    assert "过保守" in labels["source_fc"]


def test_snp_15_1_still_kill():
    rows = _rows("snp_kill.csv")
    if not rows:
        pytest.skip("run sweep --mode card_claim")
    rows15 = [r for r in rows if r["arm"] == "15:1"]
    assert rows15
    assert any(str(r["kill_1.4"]) in ("True", "true") for r in rows15)
    # do not soften: at least one window per baseline must kill
    for btype in {r["baseline_type"] for r in rows15}:
        subset = [r for r in rows15 if r["baseline_type"] == btype]
        assert any(str(r["kill_1.4"]) in ("True", "true") for r in subset)


def test_baselines_are_separate_columns():
    rows = _rows("card_claim.csv")
    if not rows:
        pytest.skip("run sweep --mode card_claim")
    types = {r["baseline_type"] for r in rows}
    assert "no_cc" in types
    assert "source_fc" in types
    # no merged baseline
    assert "mean_baseline" not in types
