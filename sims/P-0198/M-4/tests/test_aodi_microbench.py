"""Cycle microbenches: dual-busy-sat, hole buckets, completions, no mean-ρ."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

aodi = load_sim(_HERE, "p0198_m4_sim")


def test_forced_dual_busy_sat_hole_zero_and_no_inject():
    r = aodi.run_arm(
        "AODI-on", "alltoall", 20260903,
        n_nodes=8, n_txn=16, outstanding=4, force_dual_busy=True,
        max_cycles=40, warmup_laps=1,
    )
    assert r.hole_dual == 0
    assert r.hole_dual_fail is False
    assert r.dual_busy_cycles > 0
    assert r.inject_ok == 0
    assert r.illegal_third == 0
    assert r.dropped == 0


def test_alltoall_is_separate_from_asym_and_gain_near_zero():
    seed = 20260903
    off = aodi.run_arm("deflect-off", "alltoall", seed, n_nodes=8, n_txn=32, outstanding=4)
    on = aodi.run_arm("AODI-on", "alltoall", seed, n_nodes=8, n_txn=32, outstanding=4)
    assert off.completed == on.completed == 32
    assert off.hole_dual == on.hole_dual == 0
    mix = on.makespan / off.makespan
    # expected gain ≈0 — do not fold into 0.50–0.85×
    assert mix > 0.70
    assert "alltoall" in aodi.DUAL_BUSY_CLASSES
    assert "alltoall" not in aodi.ASYM_CLASSES


def test_hole_buckets_and_opposite_completions_reported():
    r = aodi.run_arm("AODI-on", "gather", 20260903, n_nodes=8, n_txn=32, outstanding=8)
    assert r.hole_dual == 0
    assert r.completions_cw + r.completions_ccw == r.completed
    assert r.rho_opp >= 0.0
    assert r.inject_ok + r.inject_fail >= r.completed
    # p_inj is a diagnostic, not the endpoint
    assert 0.0 <= r.p_inj <= 1.0
    assert r.makespan >= 1


def test_age_increments_only_on_deflect():
    on = aodi.run_arm("AODI-on", "gather", 20260903, n_nodes=8, n_txn=24, outstanding=4)
    off = aodi.run_arm("deflect-off", "gather", 20260903, n_nodes=8, n_txn=24, outstanding=4)
    if on.deflect > 0:
        assert on.age_at_complete_sum > 0
    assert off.deflect == 0
    assert off.hole_asym == 0


def test_rejoin_off_is_diagnostic_not_main_ablation():
    on = aodi.run_arm("AODI-on", "gather", 20260903, n_nodes=6, n_txn=16, outstanding=4)
    diag = aodi.run_arm("rejoin-off", "gather", 20260903, n_nodes=6, n_txn=16, outstanding=4)
    assert on.completed == 16
    assert diag.completed == 16
    assert on.hole_dual == diag.hole_dual == 0


def test_gen_txns_seed_stable_fair_compare():
    a = aodi.gen_txns("gather", 12, 32, 20260903)
    b = aodi.gen_txns("gather", 12, 32, 20260903)
    assert [(t.src, t.dst, t.chi) for t in a] == [(t.src, t.dst, t.chi) for t in b]
    assert all(t.src != t.dst for t in a)


def test_signed_pins_cited_not_invented():
    s = aodi.T2_SIGNED
    assert s["hole_dual"] == 0
    assert s["phi_age_end"] == 1
    assert s["deflect_off_hard"] is True
    assert s["alltoall_t_mix"] == 1.0
    assert s["gather_t_mix"] == 0.8448
    assert s["reduce_t_mix"] == 0.8448
    assert s["uniform_read_t_mix"] == 0.8770
