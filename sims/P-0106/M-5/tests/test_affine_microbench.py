"""Extreme-case microbenches vs T2 closed-form / gcd theory."""

from __future__ import annotations

import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

aff = load_sim(_HERE, "p0106_m5_sim")

S2M = 2 * 1024 * 1024


def test_full_good_gain_vs_norebind_approx_zero():
    a = aff.occupancy("skip-dead", aff.mask_full(), S2M, 4096)
    b = aff.occupancy("minimax", aff.mask_full(), S2M, 4096)
    assert a.n_bank == b.n_bank
    assert a.dead == b.dead == 0
    if a.cls_mean:
        assert abs(a.cls_mean - b.cls_mean) / a.cls_mean < 0.05


def test_primary_contrast_modn_vs_skip_n40_2mib():
    skip = aff.occupancy("skip-dead", aff.mask_n40(), S2M, 4096)
    a1 = aff.occupancy("modn-a1", aff.mask_n40(), S2M, 4096)
    mm = aff.occupancy("minimax", aff.mask_n40(), S2M, 4096)
    assert skip.dead == a1.dead == mm.dead == 0
    assert a1.n_bank >= skip.n_bank
    assert a1.cls_mean == mm.cls_mean
    assert mm.alpha == 1


def test_uniform_25_still_has_factor_3():
    n = aff.popcount(aff.mask_uniform(36))
    assert n == 36
    assert n % 3 == 0


def test_third_bias_drops_factor_3():
    n = aff.popcount(aff.mask_third_bias())
    assert n == 32
    assert n % 3 != 0


def test_gcd_table_identity():
    for mask in (aff.mask_n40(), aff.mask_full(), aff.mask_third_bias(), aff.mask_uniform(36)):
        for row in aff.gcd_table(mask):
            assert row["identity_holds"]
            if row["n"] and row["gcd_Sg_n"]:
                assert row["classes_AP"] == row["n"] // row["gcd_Sg_n"]


def test_t2_cls_within_30pct():
    for st in ("skip-dead", "modn-a1", "minimax"):
        for mask, name in (
            (aff.mask_n40(), "n40"),
            (aff.mask_full(), "full"),
            (aff.mask_third_bias(), "third"),
        ):
            cmp = aff.compare_occupancy(st, mask, S2M, 4096)
            assert not cmp["flag_gt_30pct"], (name, st, cmp)
            assert math.isclose(cmp["t3_cls_mean"], cmp["t2_cls_mean"], rel_tol=0, abs_tol=1e-9)


def test_classes_ap_vs_net_printed_separately():
    occ = aff.occupancy("modn-a1", aff.mask_n40(), S2M, 4096)
    assert occ.classes_ap == 5
    assert occ.cls_mean > 0
