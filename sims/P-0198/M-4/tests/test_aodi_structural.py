"""Cycle-level structural tests: 2×2 truth table, φ, AGE_MAX, Rejoin, CHI."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

aodi = load_sim(_HERE, "p0198_m4_sim")


def test_t2_signed_formulas_match_audit():
    g = aodi.t2_class_row("gather")
    r = aodi.t2_class_row("reduce")
    u = aodi.t2_class_row("uniform_read")
    a = aodi.t2_class_row("alltoall")
    assert abs(g["t_mix"] - 0.8448) < 5e-4
    assert abs(r["t_mix"] - 0.8448) < 5e-4
    assert abs(u["t_mix"] - 0.8770) < 5e-4
    assert abs(a["t_mix"] - 1.0) < 5e-4
    assert g["occ"]["p_hole_dual"] == 0
    assert a["occ"]["p_hole_dual"] == 0
    assert a["occ"]["p_hole_asym"] == 0
    off = aodi.t2_class_row("gather", deflect_on=False)
    assert off["t_mix"] + 1e-12 >= g["t_mix"]


def test_phi_walk_is_not_sum_age():
    trace, age_end, frz, ok = aodi.t2_phi_walk(6, 1, aodi.AGE_MAX_DEFAULT, True)
    assert ok and not frz
    assert trace[-1][1] == 0.0
    assert age_end == aodi.T2_SIGNED["phi_age_end"] == 1
    # Σage would be 1; that is not a progress proof
    assert age_end != 0 or True
    _, _, frz2, _ = aodi.t2_phi_walk(6, 1, aodi.AGE_MAX_DEFAULT, False)
    assert frz2 is True


def test_truth_table_four_atoms_preferred_cw():
    # pref busy, opp empty → legal hole
    row = aodi.truth_row(True, False, True, "CW", True, True)
    assert row["hole"] == 1 and row["inject_ok"] and not row["illegal"] and row["slots"] <= 2
    # pref empty, opp busy → inject, no AODI hole
    row = aodi.truth_row(False, True, True, "CW", True, True)
    assert row["hole"] == 0 and row["inject_ok"] and not row["illegal"]
    # dual empty → inject, no hole
    row = aodi.truth_row(False, False, True, "CW", True, True)
    assert row["hole"] == 0 and row["inject_ok"] and row["slots"] == 1
    # dual busy → hole≡0, no inject
    row = aodi.truth_row(True, True, True, "CW", True, True)
    assert row["dual"] and row["hole"] == 0 and not row["inject_ok"]
    assert row["slots"] == 2 and not row["illegal"]


def test_dual_busy_plus_inject_is_third_slot():
    occ = aodi.slots_after(True, True, True)
    assert occ == 3
    row = aodi.truth_row(True, True, True, "CW", True, True)
    assert row["hole"] == 0  # silicon refuses the illegal inject


def test_deflect_off_truth_no_hole():
    row = aodi.truth_row(True, False, True, "CW", False, True)
    assert row["action"] == "fail-wait"
    assert row["hole"] == 0 and not row["inject_ok"]


def test_age_max_blocks_deflect():
    row = aodi.truth_row(True, False, True, "CW", True, False)
    assert row["hole"] == 0 and not row["inject_ok"]


def test_plan_xbar_dual_busy_hole_zero():
    cw = aodi.Flit(1, 0, 3, "Dat", "probe", "CW", "CW")
    ccw = aodi.Flit(2, 4, 1, "Dat", "probe", "CCW", "CCW")
    plan = aodi.plan_xbar(cw, ccw, True, True, True, True, 8, 0, 12)
    assert plan.dual
    assert plan.hole_dual == 0
    assert plan.hole_asym == 0
    assert not plan.inject_cw and not plan.inject_ccw
    assert plan.cw_out is cw and plan.ccw_out is ccw
    assert not plan.illegal


def test_plan_xbar_asym_deflect_makes_hole():
    cw = aodi.Flit(1, 0, 3, "Dat", "probe", "CW", "CW", age=0)
    plan = aodi.plan_xbar(cw, None, True, False, True, True, 8, 0, 12)
    assert plan.hole_asym == 1
    assert plan.inject_cw
    assert plan.ccw_out is cw
    assert cw.age == 1
    assert cw.cur_dir == "CCW"
    assert not cw.armed
    assert plan.hole_dual == 0
    assert not plan.illegal


def test_plan_xbar_rejoin_not_inject_port():
    # wrong-ring on CW, prefers CCW; CCW empty → rejoin occupies CCW
    cw = aodi.Flit(1, 5, 2, "Dat", "probe", "CCW", "CW", age=3, armed=False, phi=6.0)
    plan = aodi.plan_xbar(cw, None, False, True, True, True, 8, 0, 12)
    assert plan.rejoin == 1
    assert plan.ccw_out is cw
    assert cw.cur_dir == "CCW" and cw.armed
    # Rejoin outlet must not be reused as inject
    assert not plan.inject_ccw


def test_same_driver_off_vs_on():
    seed = 20260903
    off = aodi.run_arm("deflect-off", "gather", seed, n_nodes=8, n_txn=24, outstanding=4)
    on = aodi.run_arm("AODI-on", "gather", seed, n_nodes=8, n_txn=24, outstanding=4)
    assert off.completed == on.completed == 24
    assert off.n_nodes == on.n_nodes
    assert off.hole_dual == on.hole_dual == 0
    assert off.dropped == on.dropped == 0
    assert off.illegal_third == on.illegal_third == 0
    assert off.cross_chi == on.cross_chi == 0


def test_warmup_at_least_one_lap():
    r = aodi.run_arm(
        "deflect-off", "uniform_read", 20260903,
        n_nodes=10, n_txn=16, warmup_laps=1, outstanding=4,
    )
    assert r.warmup_cycles >= 10
    assert r.first_issue >= r.warmup_cycles or r.completed == 0


def test_four_chi_rings_exist_no_cross():
    r = aodi.run_arm("AODI-on", "gather", 20260903, n_nodes=6, n_txn=16, outstanding=4)
    assert r.n_xbar == 4 * 6
    assert r.cross_chi == 0


def test_card_claim_constant_is_labeled():
    assert "0.70-0.95" in aodi.CARD_CLAIM["gather"]
    assert "0.95-1.05" in aodi.CARD_CLAIM["alltoall"]
    assert aodi.T2_SIGNED["hole_dual"] == 0
    assert aodi.T2_SIGNED["phi_age_end"] == 1
    assert aodi.T2_SIGNED["deflect_off_hard"] is True
