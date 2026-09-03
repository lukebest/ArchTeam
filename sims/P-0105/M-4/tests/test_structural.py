"""Cycle-level structural tests: mapper ports, PE retry, SimPy driver."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_SIMS))

from _lib.dram import DramTiming
from sim import SimConfig, mask_full, mask_random_frac, mask_third, occupancy, pe_retry, run_cycles


def test_pe_retry_adds_one_cycle_and_avoids_dead():
    mask = mask_full() & ~(1 << 5)
    bank, extra, pois = pe_retry(mask, 5, "next")
    assert extra == 1 and not pois and bank != 5
    assert (mask >> bank) & 1
    bank0, extra0, pois0 = pe_retry(mask, 4, "next")
    assert extra0 == 0 and bank0 == 4 and not pois0


def test_pe_first_stacks_on_index0():
    mask = mask_full() & ~(1 << 0)
    # bank 1 live; first-policy picks lowest live = 1 when 0 is dead
    bank, extra, pois = pe_retry(mask, 0, "first")
    assert bank == 1 and extra == 1 and not pois


def test_pe_all_dead_poisons():
    bank, extra, pois = pe_retry(0, 3, "next")
    assert pois and bank < 0 and extra == 1


def test_partial_good_third_never_issues_residue0():
    mask = mask_third()
    occ = occupancy("sns", 0, 2 * 1024 * 1024, 256, mask=mask)
    assert occ.poisoned == 0
    assert occ.dead_pre_pe > 0
    # after PE, no DMC should have used bank ≡ 0 (mod 3) from the original map
    # remapped banks are live ⇒ bank % 3 != 0
    # occupancy doesn't expose bank ids; use PE on a known dead
    b, _, pois = pe_retry(mask, 0, "next")
    assert not pois and b % 3 != 0


def test_random_1_16_seed_stable():
    assert mask_random_frac(20260903, 3) == mask_random_frac(20260903, 3)
    assert bin(mask_random_frac(20260903, 3)).count("1") == 45


def test_cycle_mapper_latency_serialized_on_one_port():
    addrs = [i * 512 for i in range(4)]
    cfg = SimConfig(
        strategy="sns",
        map_lat=1,
        map_ports=1,
        n_cores=1,
        outstanding=4,
        warmup_frac=0.0,
        dram=DramTiming(page_policy="close", tRCD=1, tCL=1, tRP=1, tRAS=2, tBURST=1,
                        tRRD_S=1, tRRD_L=1, tCCD_S=1, tCCD_L=1, tFAW=4, tRTP=1),
    )
    r1 = run_cycles(addrs, cfg)
    cfg2 = SimConfig(
        strategy="sns",
        map_lat=2,
        map_ports=1,
        n_cores=1,
        outstanding=4,
        warmup_frac=0.0,
        dram=cfg.dram,
    )
    r2 = run_cycles(addrs, cfg2)
    assert r2.map_cycles > r1.map_cycles
    assert r1.poisoned == 0 and r2.completed == 4


def test_same_driver_two_strategies():
    addrs = [i * 2 * 1024 * 1024 for i in range(32)]
    a = run_cycles(addrs, SimConfig(strategy="sns", n_cores=2, outstanding=4, warmup_frac=0.0))
    b = run_cycles(addrs, SimConfig(strategy="mod384", n_cores=2, outstanding=4, warmup_frac=0.0))
    assert a.completed == b.completed == 32
    # 1D collapses DMC count vs SNS
    assert a.n_dmc > b.n_dmc
