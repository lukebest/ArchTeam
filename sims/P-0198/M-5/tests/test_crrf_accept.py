"""Accept set, ghost channel-id, NACK/re-inject, H-COMMIT."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim
from _lib.workloads import SEED

crrf = load_sim(_HERE, "p0198_m5_crrf_sim")


def test_accept_set_is_local_and_prev():
    assert crrf.accept_set(1) == {1, 0}
    assert crrf.accept_set(0) == {0, 3}
    late, early = 5, 6
    inter = crrf.accept_set(late) & crrf.accept_set(early)
    assert inter == {late % 4}
    assert (early % 4) not in crrf.accept_set(late)


def test_ghost_header_stays_dat():
    txn = crrf.Txn(1, 0, 3, "Dat", "gather")
    slot = crrf.Slot.payload(txn, "Snp", 0, True)
    assert slot.chi == "Dat"
    assert slot.phys == "Snp"
    assert slot.is_ghost
    assert slot.chi != "Snp"


def test_rbrg_never_decodes_dat_as_snp():
    cfg = crrf.SimConfig(n_nodes=6, arm="7:1", n_txn=0, max_cycles=2)
    fab = crrf.Fabric(cfg, [])
    txn = crrf.Txn(7, 1, 2, "Dat", "gather")
    fab.txns[7] = txn
    slot = crrf.Slot.payload(txn, "Snp", fab.epoch_wire(2), True)
    fab._complete(slot, 2)
    assert txn.via in ("ghost", "main", "nack-reinject")
    assert slot.chi == "Dat"


def test_nack_reinject_charged_to_txn():
    cfg = crrf.SimConfig(
        n_nodes=6, arm="7:1", n_txn=1, seed=SEED,
        hold_app_until_aligned=False, max_cycles=80, t_steady_laps=2,
    )
    txn = crrf.Txn(0, 1, 0, "Dat", "gather")
    fab = crrf.Fabric(cfg, [txn])
    # deliver a tag the dest will reject
    fab.dies[0].epoch_gen = 2
    slot = crrf.Slot.payload(txn, "Dat", 0, False)  # tag 0 not in accept(2)={2,1}
    fab.inflight[1] += 1
    txn.issue_at = 0
    consumed = fab._try_accept(slot, 0)
    assert consumed
    assert fab.stats["bind_mismatch_redirect"] >= 1
    assert txn.nack_hops >= 1
    assert fab.dies[0].holding is not None


def test_h_commit_held_zero_violated_nonzero():
    held = crrf.probe_commit(n_nodes=8, violated=False, seed=SEED)
    viol = crrf.probe_commit(n_nodes=8, violated=True, seed=SEED)
    assert held["bind_mismatch_redirect"] == 0
    assert held["late_newgen_caught"] == 0
    assert held["t2_held"] == 0
    assert viol["t2_violated"] == 12
    # violated probe is allowed to inject early; must not be silently clean
    assert viol["violated"] is True
    assert viol["bind_mismatch_redirect"] + viol["late_newgen_caught"] > 0
