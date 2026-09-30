"""Signed T2 pins and smoke table shape. card-claim is never measured."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

csr = load_sim(_HERE, "p0198_m2_sim")
_RESULTS = _HERE / "results"


def test_signed_pin_table_cites_audit():
    rows = csr.signed_t2_rows()
    metrics = {r["metric"] for r in rows}
    assert "CAM Dat occupancy" in metrics
    assert "high-ost f_ov (a=8)" in metrics
    assert "spine-off HARD" in metrics
    assert "gate-off r" in metrics
    assert "alltoall TREE / RESIDUAL / mix" in metrics
    assert "card-claim" in metrics
    high = next(r for r in rows if r["metric"].startswith("high-ost"))
    assert high["t2"] == 0.5746
    a2a = next(r for r in rows if r["metric"].startswith("alltoall"))
    assert "0.6932" in str(a2a["t2"]) and "1.0" in str(a2a["t2"]) and "0.8159" in str(a2a["t2"])


def test_no_mix_with_m1_or_m5_in_module():
    text = Path(_HERE / "sim.py").read_text()
    assert "Orthogonal to M-1 CBC" in text
    assert "M-5 CRRF" in text
    assert "empty-slot" not in text.lower() or "Not CBC" in text or "No CBC" in text


def test_smoke_results_if_present():
    if not (_RESULTS / "t2_compare.csv").is_file():
        return
    with (_RESULTS / "t2_compare.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    classes = {r["class"] for r in rows}
    assert classes == set(csr.CLASSES)
    arms = {r["arm"] for r in rows}
    assert "spine-off" in arms and "CSR" in arms
    assert all(r["card_claim_is_measured"] in ("False", "false", "") for r in rows)
    assert "flag_gt_30pct" in rows[0]
    with (_RESULTS / "occupancy.csv").open(newline="") as f:
        occ = list(csv.DictReader(f))
    assert all(int(r["dat_beats_held_max"]) == 0 for r in occ)
    assert all(int(r["retention_depth_max"]) == 0 for r in occ)
    assert all(int(r["n_cam"]) == 4 for r in occ)
    meta = json.loads((_RESULTS / "summary.json").read_text())
    assert meta["seed"] == 20260903
    assert "M-1" in str(meta["separate_from"])
    assert "M-5" in str(meta["separate_from"])
