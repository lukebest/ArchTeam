"""Conservation, hint isolation, same driver, SYNC≠oracle, HARD-2, 15:1 kill."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim
from _lib.workloads import SEED

crrf = load_sim(_HERE, "p0198_m5_crrf_sim")


def test_c_dat_eff_leq_ideal_and_tax_positive():
    r = crrf.run_arm(
        "7:1", "gather", SEED,
        n_nodes=8, n_txn=16, outstanding=8, t_steady_laps=4,
    )
    assert r.c_dat_eff <= r.c_dat_ideal + 1e-9
    assert r.c_dat_eff < 2.0
    assert r.tax > 0.0
    assert r.duty_dat == 7 / 8


def test_rebind_off_has_no_ghost():
    r = crrf.run_arm(
        "rebind-off", "gather", SEED,
        n_nodes=8, n_txn=16, outstanding=8,
    )
    assert r.ghost_slots == 0
    assert r.c_dat_eff == 1.0
    assert r.duty_dat == 0.0


def test_correctness_ignores_hint():
    kwargs = dict(n_nodes=8, n_txn=12, outstanding=8, t_steady_laps=4)
    a = crrf.run_arm("7:1", "gather", SEED, hint=None, **kwargs)
    b = crrf.run_arm("7:1", "gather", SEED, hint="COLL_EP", **kwargs)
    assert a.correctness_depends_on_hint is False
    assert b.correctness_depends_on_hint is False
    assert a.completed_dat == b.completed_dat
    assert a.makespan == b.makespan
    assert a.c_dat_eff == b.c_dat_eff
    # request_duty itself ignores hint
    assert crrf.request_duty(0.9, 0.0, hint=None) == crrf.request_duty(0.9, 0.0, hint="COLL_EP")


def test_same_driver_all_arms():
    n, n_txn = 8, 12
    txns = crrf.gen_txns("gather", n, n_txn, SEED)
    results = []
    for arm in crrf.ARMS:
        r = crrf.run_arm(
            arm, "gather", SEED, list(txns),
            n_nodes=n, n_txn=n_txn, outstanding=8, t_steady_laps=4,
        )
        results.append(r)
        assert r.oracle_used is False
        assert r.sync_read_queues is False
    # same issued work
    assert all(r.issued_dat == results[0].issued_dat for r in results)


def test_sync_is_not_traffic_oracle():
    r = crrf.run_arm("3:1", "uniform_read", SEED, n_nodes=8, n_txn=12, outstanding=8)
    assert r.oracle_used is False
    assert r.sync_read_queues is False
    # SYNC handler never assigned oracle_used
    cfg = crrf.SimConfig(n_nodes=6, arm="7:1", n_txn=0)
    fab = crrf.Fabric(cfg, [])
    fab._handle_sync(0)
    assert fab.oracle_used is False
    assert fab.sync_read_queues is False


def test_warmup_until_aligned():
    r = crrf.run_arm("7:1", "gather", SEED, n_nodes=8, n_txn=12, t_steady_laps=4)
    assert r.aligned is True
    assert r.first_issue >= 0


def test_hard2_uniform_not_single_dest_on_both_rings():
    r = crrf.run_arm(
        "7:1", "uniform_read", SEED,
        n_nodes=8, n_txn=24, outstanding=8, t_steady_laps=4,
    )
    # mechanism must not force a single dest when traffic is uniform
    assert r.hard2_collapsed is False


def test_snp_makespan_and_completions_present():
    n, n_dat, n_snp = 8, 16, 8
    txns = crrf.gen_mixed(n, n_dat, n_snp, SEED, "gather")
    off = crrf.run_arm(
        "rebind-off", "gather", SEED, list(txns),
        n_nodes=n, n_txn=n_dat, n_snp=n_snp, outstanding=8,
    )
    on = crrf.run_arm(
        "15:1", "gather", SEED, list(txns),
        n_nodes=n, n_txn=n_dat, n_snp=n_snp, outstanding=8, t_steady_laps=4,
    )
    assert off.completed_snp >= 0 and on.completed_snp >= 0
    assert off.makespan_snp >= 0 and on.makespan_snp >= 0
    # 15:1 is allowed to stall / miss the 1.4× hyp (must not be hidden)
    assert on.snp_stall >= off.snp_stall


def test_t2_pins_are_cited_not_invented():
    assert crrf.T2_T_DRAIN == 77.0
    assert abs(crrf.T2_F_STEADY - 0.8666) < 1e-9
    assert crrf.T2_C_DAT_EFF["rebind-off"] == 1.0
    assert crrf.H_COMMIT_HELD == 0
    assert crrf.H_COMMIT_VIOLATED == 12
    assert crrf.SNP_15_1 == 1.5625
    assert crrf.HARD1_T_OFF == 537.2
    assert crrf.HARD1_T_BEST == 303.1
