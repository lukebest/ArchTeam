"""Dr.Sim FSM / drain / barrier cycle tests. Not mean-duty."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim
from _lib.workloads import SEED

crrf = load_sim(_HERE, "p0198_m5_crrf_sim")


def _tick(fab, n):
    for i in range(n):
        fab.step(fab.cycle)
        fab.cycle += 1


def test_arm_drain_stops_new_inject_inflight_continues():
    txns = crrf.gen_txns("gather", 8, 16, SEED)
    cfg = crrf.SimConfig(
        n_nodes=8, arm="7:1", n_txn=16, seed=SEED,
        hold_app_until_aligned=False, t_steady_laps=2, max_cycles=80,
    )
    fab = crrf.Fabric(cfg, txns)
    # plant an in-flight ghost on Snp
    t0 = txns[0]
    fab.slots["Snp"]["CW"][t0.src] = crrf.Slot.payload(t0, "Snp", 0, True)
    fab.inflight[t0.src] += 1
    t0.issue_at = 0
    pos0 = next(
        n for n in range(fab.n) if fab.slots["Snp"]["CW"][n].tid == t0.tid
    )
    # force ARM_DRAIN
    for d in fab.dies:
        d.fsm = "ARM_DRAIN"
        d.block_rebind_inject = True
        d.drain_req = True
        d.bind_snp = "Dat"
    _tick(fab, 1)
    assert any(d.fsm in ("ARM_DRAIN", "DRAIN") for d in fab.dies)
    # ring not instantly empty
    still = any(
        fab.slots["Snp"][dd][n].tid == t0.tid
        for dd in crrf.DIRS for n in range(fab.n)
    )
    assert still, "ARM_DRAIN must not vacuum in-flight flits"
    # in-flight moved
    pos1 = None
    for n in range(fab.n):
        if fab.slots["Snp"]["CW"][n].tid == t0.tid:
            pos1 = n
    if pos1 is not None:
        assert pos1 != pos0 or t0.done_at is not None


def test_no_instant_empty_ring():
    cfg = crrf.SimConfig(n_nodes=6, arm="3:1", n_txn=0, max_cycles=4)
    fab = crrf.Fabric(cfg, [])
    dummy = crrf.Txn(-3, 0, 3, "Dat", "plant")
    fab.txns[-3] = dummy
    fab.slots["Snp"]["CW"][1] = crrf.Slot.payload(dummy, "Snp", 0, True)
    for d in fab.dies:
        d.fsm = "ARM_DRAIN"
        d.block_rebind_inject = True
    fab.step(0)
    occupied = sum(
        1 for dd in crrf.DIRS for n in range(fab.n)
        if fab.slots["Snp"][dd][n].kind == "payload"
    )
    assert occupied >= 1


def test_marker_double_return_via_sync():
    cfg = crrf.SimConfig(
        n_nodes=6, arm="7:1", n_txn=0, max_cycles=40,
        hold_app_until_aligned=False, t_steady_laps=1,
    )
    fab = crrf.Fabric(cfg, [])
    for d in fab.dies:
        d.fsm = "DRAIN"
        d.drain_req = True
        d.block_rebind_inject = True
    _tick(fab, 6 * 3)
    assert any(d.drain_visits >= 2 for d in fab.dies)


def test_local_sniff_ne_global_empty():
    cfg = crrf.SimConfig(
        n_nodes=8, arm="7:1", n_txn=0, plant_old_flit=(5, 0), max_cycles=2,
    )
    fab = crrf.Fabric(cfg, [])
    assert fab.sniff_old(5, 0)
    assert not fab.sniff_old(0, 0)
    assert fab.global_old_present(0)


def test_late_newgen_inject_is_assert():
    cfg = crrf.SimConfig(
        n_nodes=6, arm="7:1", n_txn=4, seed=SEED,
        hold_app_until_aligned=False, strict_commit=True, force_early_newgen=False,
    )
    txns = crrf.gen_txns("gather", 6, 4, SEED)
    fab = crrf.Fabric(cfg, txns)
    # split generations: node 0 flipped, others late
    fab.dies[0].epoch_gen = 1
    fab.dies[0].fsm = "STEADY"
    fab.dies[0].bind_snp = "Dat"
    fab.dies[0].commit_seen_all = False
    for i in range(1, 6):
        fab.dies[i].epoch_gen = 0
        fab.dies[i].fsm = "DRAIN"
        fab.dies[i].commit_seen_all = False
    txn = txns[0]
    try:
        fab._do_inject(0, txn, "Snp", True)
        raised = False
    except crrf.LateNewgenInject:
        raised = True
    assert raised


def test_safe_drain_flip_steady_without_hint():
    r = crrf.run_arm(
        "7:1", "gather", SEED,
        n_nodes=8, n_txn=16, outstanding=8, t_steady_laps=4,
    )
    assert r.hint_used is False
    assert r.correctness_depends_on_hint is False
    assert r.aligned
    assert r.fsm_counts["STEADY"] > 0
    assert r.fsm_counts["DRAIN"] + r.fsm_counts["ARM_DRAIN"] + r.fsm_counts["FLIP"] > 0
