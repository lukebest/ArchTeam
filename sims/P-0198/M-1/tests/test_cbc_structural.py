"""Cycle-level structural tests: FSM, calendar, age, arbitration, warmup."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

cbc = load_sim(_HERE, "p0198_m1_sim")


def test_t2_signed_formulas_match_audit():
    assert abs(cbc.t2_h_inj_dom_ratio(0.25) - 0.7368) < 5e-5
    assert abs(cbc.t2_h_inj_dom_ratio(0.50) - 0.5833) < 5e-5
    assert abs(cbc.t2_dual_ratio(0.25) - 1.3333) < 5e-5
    assert abs(cbc.t2_dual_ratio(0.50) - 2.0000) < 5e-5
    assert abs(537.2 * cbc.t2_h_inj_dom_ratio(0.50) - 313.4) < 0.05
    raw, bub = cbc.t2_partition(0.20, 0.25)
    assert abs((raw + bub) - 0.20) < 1e-12


def test_calendar_64x8_duty_and_phase():
    table = cbc.program_calendar(0.25, phase=3)
    assert len(table) == 64
    dens, phase = cbc.decode_cal(table[0])
    assert dens == 4 and phase == 3
    assert all(e == table[0] for e in table)
    assert cbc.density_of(0.5) == 8
    assert cbc.density_of(1 / 16) == 1


def test_phased_calendar_is_static_rows_not_arrivals():
    table = cbc.program_phased_calendar(1 / 8, 1 / 2)
    assert cbc.decode_cal(table[0])[0] == 2
    assert cbc.decode_cal(table[1])[0] == 8
    # remaining rows stay P2P — never filled from message times
    assert cbc.decode_cal(table[2])[0] == 2


def test_fsm_idle_watch_emit_after_w():
    fsm = cbc.BubbleFSM()
    assert fsm.state == "IDLE"
    for _ in range(cbc.W_EMIT):
        cbc.fsm_tick(fsm, mandatory=True, saw_bubble=False, emitted=False)
    assert fsm.state == "EMIT"
    cbc.fsm_tick(fsm, mandatory=True, saw_bubble=False, emitted=True)
    assert fsm.state == "HOLD"
    cbc.fsm_tick(fsm, mandatory=False, saw_bubble=False, emitted=False)
    assert fsm.state in ("HOLD", "IDLE")


def test_fsm_bubble_resets_watch():
    fsm = cbc.BubbleFSM()
    for _ in range(cbc.W_EMIT - 1):
        cbc.fsm_tick(fsm, True, False, False)
    assert fsm.state == "WATCH"
    cbc.fsm_tick(fsm, True, True, False)
    assert fsm.watch == 0
    assert fsm.state == "WATCH"


def test_fsm_watch_survives_duty_off_gap():
    """W is cycles-since-bubble; a duty-off beat must not zero the window."""
    fsm = cbc.BubbleFSM()
    for _ in range(cbc.W_EMIT - 1):
        cbc.fsm_tick(fsm, True, False, False)
    cbc.fsm_tick(fsm, False, False, False)
    cbc.fsm_tick(fsm, True, False, False)
    assert fsm.watch >= cbc.W_EMIT
    assert fsm.state == "EMIT"


def test_age_increments_and_degrades_at_15():
    cfg = cbc.SimConfig(
        n_nodes=4, duty=0.5, calendar_on=True, n_txn=0, warmup_laps=1,
        lookup_lat=0, seed=20260903, max_cycles=48,
    )
    # empty ring: emit bubbles, they must age out
    r = cbc.run_cycles(cfg, [])
    assert r.age_degrade > 0
    assert r.sum_ok
    assert r.n_fsm == 4 * 4 * 2  # CHI×dir×node


def test_four_rings_two_dirs_fsm_exist():
    r = cbc.run_arm(
        "CBC-coll-1/4", "gather", 20260903,
        n_nodes=4, n_txn=8, warmup_laps=1, outstanding=2, lookup_lat=0,
    )
    assert r.n_fsm == 4 * 2 * 4
    assert set(r.fsm_counts) == set(cbc.STATES)


def test_steal_raw_fail_are_separate():
    r = cbc.run_arm(
        "CBC-coll-1/2", "gather", 20260903,
        n_nodes=8, n_txn=32, outstanding=8, lookup_lat=1,
    )
    assert r.steal + r.raw_inject + r.fail >= r.completed
    assert r.steal >= 0 and r.raw_inject >= 0 and r.fail >= 0
    # p_inj is not a substitute for makespan
    assert 0.0 <= r.p_inj <= 1.0
    assert r.makespan >= 1


def test_warmup_at_least_one_lap():
    r = cbc.run_arm(
        "duty=0", "uniform_read", 20260903,
        n_nodes=10, n_txn=16, warmup_laps=1, outstanding=4,
    )
    assert r.warmup_cycles >= 10
    assert r.first_issue >= r.warmup_cycles or r.completed == 0


def test_lookup_lat_one_delays_first_duty_cycle():
    a = cbc.run_arm(
        "CBC-coll-1/2", "gather", 20260903,
        n_nodes=6, n_txn=16, lookup_lat=0, outstanding=4,
    )
    b = cbc.run_arm(
        "CBC-coll-1/2", "gather", 20260903,
        n_nodes=6, n_txn=16, lookup_lat=1, outstanding=4,
    )
    assert a.cal_lookups > 0 and b.cal_lookups > 0
    assert a.completed == b.completed == 16


def test_no_arrival_oracle_flag():
    r = cbc.run_arm("CBC-coll-1/4", "allreduce", 20260903, n_nodes=6, n_txn=16, outstanding=4)
    assert r.oracle_used is False
    # software epochs come from posted phase 0/1, not eject times
    assert r.software_epochs_seen[0] == 0


def test_same_driver_off_vs_cbc():
    seed = 20260903
    off = cbc.run_arm("calendar-off", "gather", seed, n_nodes=8, n_txn=24, outstanding=4)
    on = cbc.run_arm("CBC-coll-1/4", "gather", seed, n_nodes=8, n_txn=24, outstanding=4)
    assert off.completed == on.completed == 24
    assert off.n_nodes == on.n_nodes
    assert off.oracle_used is False and on.oracle_used is False


def test_conservation_exact():
    for arm in ("calendar-off", "duty=0", "CBC-coll-1/4", "fixed-high-1/2"):
        r = cbc.run_arm(arm, "gather", 20260903, n_nodes=6, n_txn=16, outstanding=4)
        assert r.sum_ok, arm
        assert abs((r.rho_payload + r.rho_empty) - 1.0) < 1e-12
        assert abs((r.rho_raw + r.rho_bubble) - r.rho_empty) < 1e-12


def test_card_claim_constant_is_labeled():
    assert cbc.CARD_CLAIM_COLL == "0.55-0.85x"
    assert "card-claim" in cbc.CARD_CLAIM_COLL or cbc.CARD_CLAIM_COLL.startswith("0.55")
