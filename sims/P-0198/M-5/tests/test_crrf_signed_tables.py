"""Signed smoke tables: T2 compare columns, no card-claim-as-measured, no M-1 mix."""

from __future__ import annotations

import csv
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_RESULTS = _HERE / "results"


def _rows(name: str) -> list[dict]:
    path = _RESULTS / name
    if not path.is_file():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def test_signed_t2_compare_schema_and_flags():
    rows = _rows("t2_compare.csv")
    assert rows, "run sweep --mode smoke to write results/t2_compare.csv"
    cols = set(rows[0].keys())
    assert {"metric", "arm", "t3", "t2", "rel_err", "flag_gt_30pct"} <= cols
    metrics = {r["metric"] for r in rows}
    assert "T_drain" in metrics
    assert "C_dat_eff" in metrics
    assert "H-COMMIT held" in metrics
    assert any("H-DAT-DOM" in m for m in metrics)
    assert any("Snp" in m or "H-SNP" in m for m in metrics)
    assert any(r["metric"] == "card-claim" for r in rows)
    claim = next(r for r in rows if r["metric"] == "card-claim")
    assert "NOT measured" in str(claim["t3"])
    assert claim.get("card_claim_is_measured") in ("False", "false", False, "")


def test_signed_capacity_has_all_arms_no_average():
    rows = _rows("capacity.csv")
    assert rows
    arms = {r["arm"] for r in rows}
    assert arms == {"rebind-off", "3:1", "7:1", "15:1"}
    for r in rows:
        assert r["arm"] != "CRRF-mean"
        assert float(r["c_dat_eff"]) <= float(r["c_dat_ideal"]) + 1e-6


def test_snp_path_not_folded_into_dat_mean():
    rows = _rows("snp_path.csv")
    assert rows
    arms = {r["arm"] for r in rows}
    assert "15:1" in arms
    assert all("kill_1.4" in r for r in rows)
    assert all(r.get("card_claim_is_measured") in ("False", "false", False) for r in rows)


def test_summary_isolates_from_cbc():
    meta = json.loads((_RESULTS / "summary.json").read_text())
    assert meta["card"] == "P-0198/M-5 CRRF"
    assert "M-1" not in meta["card"]
    assert "CBC" not in meta["card"]
    note = meta["note"]
    assert "rebind-off" in note
    assert "M-1" in note or "eliminated" in str(meta.get("eliminated_sibling", "")).lower()
    assert meta["seed"] == 20260903
    assert all(meta["dr_sim"].values())


def test_signed_pins_csv_does_not_treat_card_claim_as_measured():
    rows = _rows("t2_signed_pins.csv")
    assert rows
    claim = [r for r in rows if r["metric"] == "card-claim"]
    assert claim
    assert "NOT" in claim[0]["t3"] or "not" in claim[0]["note"].lower()
