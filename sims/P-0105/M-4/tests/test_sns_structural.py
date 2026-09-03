"""Cycle-level structural tests: mapper ports, PE retry, SimPy driver."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.dram import DramTiming
from _lib.importsim import load_sim

sns = load_sim(_HERE, "p0105_m4_sim")


def test_pe_retry_adds_one_cycle_and_avoids_dead():
    mask = sns.mask_full() & ~(1 << 5)
    bank, extra, pois = sns.pe_retry(mask, 5, "next")
    assert extra == 1 and not pois and bank != 5
    assert (mask >> bank) & 1
    bank0, extra0, pois0 = sns.pe_retry(mask, 4, "next")
    assert extra0 == 0 and bank0 == 4 and not pois0


def test_pe_first_stacks_on_index0():
    mask = sns.mask_full() & ~(1 << 0)
    bank, extra, pois = sns.pe_retry(mask, 0, "first")
    assert bank == 1 and extra == 1 and not pois


def test_pe_all_dead_poisons():
    bank, extra, pois = sns.pe_retry(0, 3, "next")
    assert pois and bank < 0 and extra == 1


def test_partial_good_third_never_issues_residue0():
    mask = sns.mask_third()
    occ = sns.occupancy("sns", 0, 2 * 1024 * 1024, 256, mask=mask)
    assert occ.poisoned == 0
    assert occ.dead_pre_pe > 0
    b, _, pois = sns.pe_retry(mask, 0, "next")
    assert not pois and b % 3 != 0


def test_random_1_16_seed_stable():
    assert sns.mask_random_frac(20260903, 3) == sns.mask_random_frac(20260903, 3)
    assert bin(sns.mask_random_frac(20260903, 3)).count("1") == 45


def test_cycle_mapper_latency_serialized_on_one_port():
    addrs = [i * 512 for i in range(4)]
    timing = DramTiming(
        page_policy="close", tRCD=1, tCL=1, tRP=1, tRAS=2, tBURST=1,
        tRRD_S=1, tRRD_L=1, tCCD_S=1, tCCD_L=1, tFAW=4, tRTP=1,
    )
    cfg = sns.SimConfig(
        strategy="sns", map_lat=1, map_ports=1, n_cores=1, outstanding=4,
        warmup_frac=0.0, dram=timing,
    )
    r1 = sns.run_cycles(addrs, cfg)
    cfg2 = sns.SimConfig(
        strategy="sns", map_lat=2, map_ports=1, n_cores=1, outstanding=4,
        warmup_frac=0.0, dram=timing,
    )
    r2 = sns.run_cycles(addrs, cfg2)
    assert r2.map_cycles > r1.map_cycles
    assert r1.poisoned == 0 and r2.completed == 4


def test_same_driver_two_strategies():
    addrs = [i * 2 * 1024 * 1024 for i in range(32)]
    a = sns.run_cycles(addrs, sns.SimConfig(strategy="sns", n_cores=2, outstanding=4, warmup_frac=0.0))
    b = sns.run_cycles(addrs, sns.SimConfig(strategy="mod384", n_cores=2, outstanding=4, warmup_frac=0.0))
    assert a.completed == b.completed == 32
    assert a.n_dmc > b.n_dmc
