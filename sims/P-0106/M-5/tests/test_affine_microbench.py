"""Extreme-case microbenches vs T2 closed-form / gcd theory."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

aff = load_sim(_HERE, "p0106_m5_sim")
sys.path.insert(0, str(_HERE))
import sweep as aff_sweep  # noqa: E402

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


S3X = 3 * 512
S9X = 9 * 512


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


def test_t2_cls_factor3_doc_s_netlist():
    """XOR_fold6 netlist occupancy for Doc S 3×512B / 9×512B (I=min(K,Q_tot))."""
    for s in (S3X, S9X):
        for st in ("skip-dead", "modn-a1", "minimax"):
            for mask, name in (
                (aff.mask_n40(), "n40"),
                (aff.mask_full(), "full"),
                (aff.mask_third_bias(), "third"),
            ):
                cmp = aff.compare_occupancy(st, mask, s, None)
                assert not cmp["flag_gt_30pct"], (s, name, st, cmp)
                assert cmp["t3_dead"] == cmp.get("t2_dead", -1) == 0
                assert math.isclose(cmp["t3_cls_mean"], cmp["t2_cls_mean"], rel_tol=0, abs_tol=1e-9)
                assert math.isclose(cmp["t3_n_bank"], cmp["t2_n_bank"], rel_tol=0, abs_tol=1e-9)


def test_classes_ap_vs_net_printed_separately():
    occ = aff.occupancy("modn-a1", aff.mask_n40(), S2M, 4096)
    assert occ.classes_ap == 5
    assert occ.cls_mean > 0


def test_smoke_strides_include_factor3_doc_s():
    names = {n for n, _ in aff_sweep.SMOKE_STRIDES}
    assert names == {"512B", "3x512B", "9x512B", "2MiB"}
    assert "3x512B" in aff_sweep.SMOKE_CYCLE_S
    assert {n for n, _ in aff_sweep.SMOKE_MASKS} == {"full-good", "n=40", "3-biased(n=32)"}
    assert aff_sweep.SMOKE_STRATEGIES == ("skip-dead", "modn-a1", "minimax")


def test_signed_smoke_tables_include_factor3_doc_s():
    """Signed occupancy/t2_compare must carry XOR_fold6 netlist rows for 3×/9×512B."""
    # Signed smoke fixture. Night occupancy/t2_compare live under results/night/.
    occ_path = _HERE / "results" / "occupancy.csv"
    cmp_path = _HERE / "results" / "t2_compare.csv"
    occ = list(csv.DictReader(occ_path.open()))
    cmp = list(csv.DictReader(cmp_path.open()))
    for rows in (occ, cmp):
        s_vals = {r["S"] for r in rows}
        assert {"512B", "3x512B", "9x512B", "2MiB"} <= s_vals
        for need in ("3x512B", "9x512B"):
            subset = [r for r in rows if r["S"] == need]
            assert len(subset) == 9, (need, len(subset))  # 3 masks × 3 strategies
    for r in cmp:
        if r["S"] in ("3x512B", "9x512B"):
            assert r["flag_gt_30pct"] == "False"
            assert float(r["rel_err_cls"]) == 0.0
            assert float(r["rel_err_n_bank"]) == 0.0
            assert int(r["t3_dead"]) == 0
            assert r["t3_cls_mean"] != ""
            assert r["t2_cls_mean"] != ""
    bw = list(csv.DictReader((_HERE / "results" / "bw_ci.csv").open()))
    assert {r["S"] for r in bw} >= {"512B", "3x512B", "2MiB"}
