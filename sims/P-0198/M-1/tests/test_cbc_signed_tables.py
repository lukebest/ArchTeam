"""Signed smoke tables: T2 pins, no-average arms, card-claim not measured."""

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
    assert "sum_ok" in metrics
    assert "H-INJ-DOM T_hat/T_off" in metrics
    assert any("HARD-1" in r["metric"] for r in rows)
    assert any("dual-tenant" in r["metric"] for r in rows)
    claim = next(r for r in rows if r["metric"] == "card-claim")
    assert "0.55-0.85" in claim["t2"]
    assert "NOT measured" in claim["t3"]


def test_t2_compare_has_flag_and_all_classes():
    rows = _rows("t2_compare.csv")
    assert rows
    assert {r["class"] for r in rows} >= {
        "uniform_read", "uniform_write", "broadcast",
        "gather", "reduce", "allgather", "allreduce", "alltoall",
    }
    arms = {r["arm"] for r in rows}
    assert "calendar-off" in arms
    assert "CBC-P2P-1/16" in arms and "CBC-coll-1/4" in arms
    assert "CBC-P2P-1/8" in arms and "CBC-coll-1/2" in arms
    for r in rows:
        assert "flag_gt_30pct" in r
        assert r["card_claim_is_measured"] in ("False", "false", "0")
        assert r["t2_sum_ok"] in ("True", "true", "1")


def test_occupancy_conservation_column():
    rows = _rows("occupancy.csv")
    assert rows
    assert all(r["sum_ok"] in ("True", "true", "1") for r in rows)
    assert "delta_rho_empty" in rows[0]


def test_inject_counts_not_collapsed():
    rows = _rows("inject.csv")
    assert rows
    assert {"steal", "raw_inject", "fail"} <= set(rows[0])
    assert any("do not collapse" in r["note"] for r in rows)


def test_dual_tenant_csv():
    rows = _rows("dual_tenant.csv")
    arms = {r["arm"] for r in rows}
    assert {"d_A=1/4", "d_A=1/2"} <= arms
    for r in rows:
        assert r["t2_fail_T"] in ("True", "true", "1")
        assert float(r["t2_T_B_dual_over_solo"]) in (1.3333, 2.0) or abs(
            float(r["t2_T_B_dual_over_solo"]) - (4 / 3 if r["arm"] == "d_A=1/4" else 2.0)
        ) < 1e-3


def test_summary_seed_and_bbox():
    meta = json.loads((_RESULTS / "summary.json").read_text())
    assert meta["seed"] == 20260903
    assert meta["card"] == "P-0198/M-1 CBC"
    assert "0.55" in meta["note"]
    assert meta["dr_sim"]["no_arrival_oracle"] is True
    assert meta["dr_sim"]["warmup_ge_one_lap"] is True
    assert "envelope rd512/wr256" in meta["bbox"]
    assert meta["t2_signed"]["h_inj_dom_d25"] == 0.7368
    assert meta["t2_signed"]["h_inj_dom_d50"] == 0.5833
    assert meta["t2_signed"]["hard1_t_off"] == 537.2
    assert meta["t2_signed"]["hard1_t_cbc"] == 313.4
    assert meta["t2_signed"]["dual_d25"] == 1.3333
    assert meta["t2_signed"]["dual_d50"] == 2.0
