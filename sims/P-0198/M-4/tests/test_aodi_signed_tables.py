"""Signed smoke tables: T2 pins, per-class rows, card-claim not measured."""

from __future__ import annotations

import csv
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_RESULTS = _HERE / "results"


def _rows(name: str) -> list[dict]:
    with (_RESULTS / name).open(newline="") as f:
        return list(csv.DictReader(f))


def test_signed_t2_pins_present():
    rows = _rows("t2_signed_pins.csv")
    metrics = {r["metric"] for r in rows}
    assert "hole_dual" in metrics
    assert "phi_age_end" in metrics
    assert "deflect-off HARD" in metrics
    assert "alltoall T_mix" in metrics
    assert "gather T_mix" in metrics
    hole = next(r for r in rows if r["metric"] == "hole_dual")
    assert hole["t2"] in ("0", "0.0")
    phi = next(r for r in rows if r["metric"] == "phi_age_end")
    assert phi["t2"] in ("1", "1.0")
    a2a = next(r for r in rows if r["metric"] == "alltoall T_mix")
    assert float(a2a["t2"]) == 1.0
    g = next(r for r in rows if r["metric"] == "gather T_mix")
    assert abs(float(g["t2"]) - 0.8448) < 1e-6
    u = next(r for r in rows if r["metric"] == "uniform_read T_mix")
    assert abs(float(u["t2"]) - 0.8770) < 1e-6
    claim = next(r for r in rows if r["metric"] == "card-claim")
    assert "NOT measured" in claim["t3"]


def test_t2_compare_has_flag_and_all_classes():
    rows = _rows("t2_compare.csv")
    assert rows
    assert {r["class"] for r in rows} >= {
        "uniform_read", "uniform_write", "broadcast",
        "gather", "reduce", "allgather", "allreduce", "alltoall",
    }
    for r in rows:
        assert "flag_gt_30pct" in r
        assert r["card_claim_is_measured"] in ("False", "false", "0")
        assert int(float(r["t2_hole_dual"])) == 0
        assert int(float(r["t3_hole_dual"])) == 0
        if r["class"] == "alltoall":
            assert r["alltoall_separate"] in ("True", "true", "1")
            assert "do not fold" in r["note"]
            assert abs(float(r["t2_T_mix"]) - 1.0) < 1e-6


def test_holes_dual_busy_zero_and_sat_row_separate():
    rows = _rows("holes.csv")
    assert rows
    assert all(int(r["hole_dual"]) == 0 for r in rows)
    classes = {r["class"] for r in rows}
    assert "alltoall" in classes
    assert "dual-busy-sat" in classes
    assert "dual-busy-sat" != "alltoall"


def test_cycles_have_deflect_off_and_opposite_completions():
    rows = _rows("cycles.csv")
    arms = {r["arm"] for r in rows}
    assert "deflect-off" in arms
    assert "AODI-on" in arms
    assert {"completions_cw", "completions_ccw", "rho_opp", "hole_asym", "hole_dual"} <= set(rows[0])
    assert any("inject-success is NOT" in r["note"] or "SEPARATE" in r["note"] for r in rows)


def test_summary_seed_and_bbox():
    meta = json.loads((_RESULTS / "summary.json").read_text())
    assert meta["seed"] == 20260903
    assert meta["card"] == "P-0198/M-4 AODI"
    assert meta["t2_signed"]["hole_dual"] == 0
    assert meta["t2_signed"]["phi_age_end"] == 1
    assert meta["t2_signed"]["deflect_off_hard"] is True
    assert meta["t2_signed"]["alltoall_t_mix"] == 1.0
    assert meta["t2_signed"]["gather_t_mix"] == 0.8448
    assert meta["t2_signed"]["uniform_read_t_mix"] == 0.8770
    assert meta["dr_sim"]["same_cycle_2x2"] is True
    assert meta["dr_sim"]["hole_dual_hard_zero"] is True
    assert meta["dr_sim"]["phi_not_sum_age"] is True
    assert meta["dr_sim"]["alltoall_separate"] is True
    assert meta["dr_sim"]["warmup_ge_one_lap"] is True
    assert "淘汰" in meta["siblings"]["M-1_CBC"]
    assert "do not mix" in meta["siblings"]["M-2_CSR"]
    assert "NOT measured" in meta["note"]
