#!/usr/bin/env python3
"""Structural checks for CRRF-SB. Not a performance sign-off."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import SEED, run_suite


def test_exclusive_kills_snp_15_1() -> None:
    rows = { (r["mode"], r["arm"]): r for r in run_suite(3, SEED) }
    m5 = rows[("snp_path", "m5-15:1")]
    assert m5["comp_snp"] == m5["n_snp"], "completions must not drop"
    assert m5["snp_ratio"] > 1.4, "sb-off/exclusive must still miss the 1.4× kill hyp"


def test_steal_back_restores_snp_and_keeps_dat() -> None:
    rows = { (r["mode"], r["arm"]): r for r in run_suite(3, SEED) }
    sb = rows[("mixed", "m5r1-15:1")]
    off = rows[("mixed", "rebind-off")]
    m5 = rows[("mixed", "m5-15:1")]
    assert sb["comp_snp"] == sb["n_snp"]
    assert sb["comp_dat"] == sb["n_dat"]
    assert sb["snp_ratio"] <= 1.4
    assert sb["steal_back"] > 0
    # Dat makespan must shrink vs no-CC; p_inj-only does not count
    assert sb["ms_dat"] < off["ms_dat"]
    # Ablation: exclusive Snp worse than SB
    assert m5["ms_snp"] > sb["ms_snp"]


def test_source_fc_does_not_mint_dat_slots() -> None:
    rows = { (r["mode"], r["arm"]): r for r in run_suite(3, SEED) }
    fc = rows[("mixed", "src-fc")]
    off = rows[("mixed", "rebind-off")]
    # This bbox is dest-eject limited; source FC must not claim a Dat win
    assert fc["ms_dat"] >= off["ms_dat"]


if __name__ == "__main__":
    test_exclusive_kills_snp_15_1()
    test_steal_back_restores_snp_and_keeps_dat()
    test_source_fc_does_not_mint_dat_slots()
    print("test_sb: 3 structural checks passed (UNSIGNED bbox)")
