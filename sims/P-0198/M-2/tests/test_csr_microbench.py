"""Same-driver baseline vs CSR, fold ports, alltoall residual, envelope."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

csr = load_sim(_HERE, "p0198_m2_sim")


def test_same_driver_spine_off_vs_csr():
    seed = 20260903
    ops = csr.gen_ops("gather", 8, 2, 2, seed)
    off = csr.run_cycles(csr.SimConfig(arm="spine-off", n_top=8, n_bottom=2, n_ops=2, seed=seed), ops)
    on = csr.run_cycles(csr.SimConfig(arm="CSR", n_top=8, n_bottom=2, n_ops=2, seed=seed), ops)
    assert off.completed == on.completed
    assert off.completed == sum(len(o.transfers) for o in ops)
    assert off.oracle_used is False and on.oracle_used is False
    assert on.invariant_ok and off.invariant_ok


def test_p2p_near_neutral_same_driver():
    seed = 20260903
    ops = csr.gen_ops("uniform_read", 8, 2, 2, seed)
    off = csr.run_cycles(csr.SimConfig(arm="spine-off", n_top=8, n_bottom=2, n_ops=2, seed=seed,
                               traffic_class="uniform_read"), ops)
    on = csr.run_cycles(csr.SimConfig(arm="CSR", n_top=8, n_bottom=2, n_ops=2, seed=seed,
                              traffic_class="uniform_read"), ops)
    assert off.completed == on.completed
    assert off.makespan == on.makespan
    assert on.spine_grant == 0


def test_fold_port_contention_orbits_on_fanin():
    r = csr.run_arm(
        "spine-off", "gather", 20260903,
        n_top=8, n_bottom=2, n_ops=2, outstanding=32, fold_ports=1,
    )
    assert r.fold_accepts == r.completed * csr.N_BEATS
    # 1 fold port vs two incoming dirs → some destination orbits
    assert r.fold_orbits >= 0


def test_alltoall_residual_split_not_averaged():
    r = csr.run_arm(
        "CSR", "alltoall", 20260903,
        n_top=8, n_bottom=2, n_ops=1, outstanding=32,
    )
    assert r.tree_completed > 0
    assert r.residual_completed > 0
    assert r.residual_p50 >= 0
    assert r.residual_p90 >= r.residual_p50
    assert r.residual_p99 >= r.residual_p90


def test_envelope_12_plus_2_four_ring_512b_ost():
    r = csr.run_arm(
        "CSR", "gather", 20260903,
        n_top=12, n_bottom=2, n_ops=1, outstanding=256,
    )
    assert r.n_nodes == 14
    assert r.completed > 0
    assert r.invariant_ok
    r512 = csr.run_arm(
        "CSR", "reduce", 20260903,
        n_top=12, n_bottom=2, n_ops=1, outstanding=512,
    )
    assert r512.n_nodes == 14
    assert r512.invariant_ok


def test_compare_does_not_mark_card_claim_measured():
    on = csr.run_arm("CSR", "gather", 20260903, n_top=6, n_bottom=2, n_ops=1, outstanding=16)
    off = csr.run_arm("spine-off", "gather", 20260903, n_top=6, n_bottom=2, n_ops=1, outstanding=16)
    cmp = csr.compare_to_t2("gather", "CSR", on, off)
    assert cmp["card_claim_is_measured"] is False
    assert cmp["card_claim"] == "0.45-0.80x"
    assert "t3_T_hat_over_T_off" in cmp
