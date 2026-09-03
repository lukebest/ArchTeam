"""CSR / decode / REPAIR-before-RUN / dead-hit structural tests."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.dram import DramTiming
from _lib.importsim import load_sim

aff = load_sim(_HERE, "p0106_m5_sim")


def test_repair_fills_minimax_not_handwritten():
    csr = aff.CSR()
    assert not csr.repaired
    csr.repair(aff.mask_n40(), "minimax")
    assert csr.repaired
    assert csr.n[0] == 40
    assert csr.alpha[0] == 1
    csr.repair(aff.mask_third_bias(), "minimax")
    assert csr.n[0] == 32
    assert csr.alpha[0] >= 1


def test_true_alpha1_column_is_separate():
    a = aff.occupancy("modn-a1", aff.mask_n40(), 2 * 1024 * 1024, 256)
    b = aff.occupancy("minimax", aff.mask_n40(), 2 * 1024 * 1024, 256)
    assert a.alpha == 1
    if a.cls_mean:
        assert abs(b.cls_mean - a.cls_mean) / a.cls_mean < 0.05


def test_dead_hits_zero_on_live_paths():
    for st in ("skip-dead", "stack", "modn-a1", "minimax"):
        for mask in (aff.mask_n40(), aff.mask_third_bias()):
            occ = aff.occupancy(st, mask, 2 * 1024 * 1024, 512)
            assert occ.dead == 0, (st, occ.dead)


def test_n0_poisons_without_cross_dmc():
    csr = aff.CSR()
    csr.repair(0, "minimax")
    assert csr.n[0] == 0
    dmc, bank, _, _ = aff.map_one(0, "minimax", csr)
    assert bank < 0
    assert 0 <= dmc < 384


def test_repair_before_run_flag():
    addrs = [i * 512 for i in range(16)]
    r = aff.run_cycles(
        addrs,
        aff.SimConfig(
            strategy="minimax",
            mask=aff.mask_n40(),
            n_cores=2,
            outstanding=4,
            warmup_frac=0.0,
            dram=DramTiming(
                page_policy="close", tRCD=1, tCL=1, tRP=1, tRAS=2, tBURST=1,
                tRRD_S=1, tRRD_L=1, tCCD_S=1, tCCD_L=1, tFAW=4, tRTP=1,
            ),
        ),
    )
    assert r.repair_done
    assert r.dead == 0
    assert r.completed == 16


def test_two_cycle_decode_costs_more_than_one():
    addrs = [i * 512 for i in range(8)]
    timing = DramTiming(
        page_policy="close", tRCD=1, tCL=1, tRP=1, tRAS=2, tBURST=1,
        tRRD_S=1, tRRD_L=1, tCCD_S=1, tCCD_L=1, tFAW=4, tRTP=1,
    )
    a = aff.run_cycles(addrs, aff.SimConfig(decode_lat=2, n_cores=1, outstanding=1, warmup_frac=0.0, dram=timing))
    b = aff.run_cycles(addrs, aff.SimConfig(decode_lat=1, n_cores=1, outstanding=1, warmup_frac=0.0, dram=timing))
    assert a.decode_cycles == 16
    assert b.decode_cycles == 8
