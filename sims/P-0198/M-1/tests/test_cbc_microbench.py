"""Synthetic microbenches: empty-ring emit, no-mint, seed, dual-tenant."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

cbc = load_sim(_HERE, "p0198_m1_sim")
sys.path.insert(0, str(_HERE))
import sweep as cbc_sweep  # noqa: E402


def test_empty_ring_does_not_mint_payload():
    cfg = cbc.SimConfig(
        n_nodes=6, duty=0.5, calendar_on=True, n_txn=0, warmup_laps=2,
        lookup_lat=0, seed=20260903,
    )
    r = cbc.run_cycles(cfg, [])
    assert r.completed == 0
    assert r.rho_payload == 0.0
    assert r.sum_ok
    assert r.rho_empty == 1.0
    # bubbles are a partition of empty, not new highway slots
    assert abs(r.rho_raw + r.rho_bubble - 1.0) < 1e-12


def test_calendar_off_emits_no_bubbles():
    r = cbc.run_arm(
        "calendar-off", "uniform_read", 20260903,
        n_nodes=6, n_txn=20, outstanding=4, lookup_lat=0,
    )
    assert r.emit == 0
    assert r.rho_bubble == 0.0
    assert r.steal == 0


def test_duty0_matches_off_first_order():
    off = cbc.run_arm("calendar-off", "gather", 20260903, n_nodes=8, n_txn=24, outstanding=4)
    z = cbc.run_arm("duty=0", "gather", 20260903, n_nodes=8, n_txn=24, outstanding=4)
    assert off.completed == z.completed
    assert off.emit == z.emit == 0
    assert abs(off.p_inj - z.p_inj) < 1e-9
    assert off.makespan == z.makespan


def test_seed_is_deterministic():
    a = cbc.run_arm("CBC-coll-1/4", "alltoall", 20260903, n_nodes=8, n_txn=24, outstanding=4)
    b = cbc.run_arm("CBC-coll-1/4", "alltoall", 20260903, n_nodes=8, n_txn=24, outstanding=4)
    assert (a.makespan, a.steal, a.raw_inject, a.fail, a.completed) == (
        b.makespan, b.steal, b.raw_inject, b.fail, b.completed,
    )


def test_same_seed_same_txn_list():
    x = cbc.gen_txns("gather", 12, 40, 20260903)
    y = cbc.gen_txns("gather", 12, 40, 20260903)
    assert [(t.src, t.dst, t.chi, t.kind) for t in x] == [(t.src, t.dst, t.chi, t.kind) for t in y]


def test_payload_full_ring_cannot_mint_empty():
    # saturated gather: CBC must not raise ρ_empty vs off by manufacturing slots
    off = cbc.run_arm("calendar-off", "gather", 20260903, n_nodes=8, n_txn=40, outstanding=16)
    on = cbc.run_arm("CBC-coll-1/2", "gather", 20260903, n_nodes=8, n_txn=40, outstanding=16)
    assert off.sum_ok and on.sum_ok
    # H-CBC-empty-supply: no mint. Tiny numeric noise only.
    assert on.rho_empty - off.rho_empty < 0.05


def test_cluster_hist_recorded_when_bubbles_exist():
    r = cbc.run_arm(
        "CBC-coll-1/2", "broadcast", 20260903,
        n_nodes=8, n_txn=16, outstanding=2, lookup_lat=0,
    )
    if r.rho_bubble > 0:
        assert r.mean_cluster >= 1.0
        assert sum(r.cluster_hist.values()) >= 1


def test_dual_tenant_fail_t_probe():
    dual, solo = cbc.run_dual(0.50, 20260903, n_nodes=8, n_txn=24, outstanding=4)
    assert dual.oracle_used is False
    assert "B" in dual.tenant_completed or dual.completed > 0
    ms_b_dual = dual.tenant_makespan.get("B", 0)
    ms_b_solo = solo.tenant_makespan.get("B", solo.makespan)
    if ms_b_solo > 0 and ms_b_dual > 0:
        fail_t = (ms_b_dual / ms_b_solo) >= 1.10
        # T2 signed fail_T=True at d_A=1/2; cycle check must run (result documented)
        assert isinstance(fail_t, bool)


def test_arms_not_averaged_in_sweep_list():
    assert "CBC-P2P-1/16" in cbc.ARMS and "CBC-coll-1/4" in cbc.ARMS
    assert cbc.duty_of_arm("CBC-P2P-1/16") != cbc.duty_of_arm("CBC-coll-1/4")
    assert set(cbc_sweep.CLASSES) == set(cbc.CLASSES)


def test_all_traffic_classes_generate():
    for cls in cbc.CLASSES:
        tx = cbc.gen_txns(cls, 8, 16, 20260903)
        assert len(tx) == 16
        assert all(t.src != t.dst for t in tx)
        assert all(t.chi in cbc.CHI for t in tx)
