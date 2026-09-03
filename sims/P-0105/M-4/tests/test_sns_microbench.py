"""Extreme-case microbenches vs T2 closed-form / theory."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim
from _lib.stats import rel_err
from _lib.workloads import GRAIN, GRAIN_BASES

sns = load_sim(_HERE, "p0105_m4_sim")

S2M = 2 * 1024 * 1024


def test_1d_mod384_collapses_to_3_dmc_at_2mib():
    occ = sns.occupancy("mod384", 0, S2M, 4096)
    assert occ.n_dmc == 3


def test_sns_covers_384_at_2mib():
    occ = sns.occupancy("sns", 0, S2M, 4096)
    assert occ.n_dmc == 384
    assert occ.bank_per_min == 6 and occ.bank_per_max == 6
    assert occ.kind8_min == 1


def test_abl_sbox_varies_phase_id_at_2mib():
    ids = []
    for b in (0, GRAIN, 2 * GRAIN, 7 * GRAIN):
        occ = sns.occupancy("sbox", b, S2M, 4096)
        ids.append(tuple(i for i, c in enumerate(occ.dmc_h) if c))
        assert occ.n_dmc == 1
    assert len(set(ids)) > 1


def test_sns_rel_diff_across_grain_bases():
    vals = [sns.occupancy("sns", b, S2M, 4096).n_dmc for b in GRAIN_BASES]
    assert all(v == 384 for v in vals)
    assert sns.rel_diff_n_dmc(vals) < 0.05


def test_covering_bound_not_used_as_golden():
    mx, mn, cv = sns.covering_bound()
    assert mx == 11 and mn == 10
    assert abs(cv - 0.0442) < 0.001
    occ = sns.occupancy("sns", 0, S2M, 4096)
    assert occ.maxload >= 1


def test_t2_occupancy_within_30pct():
    for st in ("sns", "mod384", "low", "high", "shear", "sbox"):
        cmp = sns.compare_occupancy(st, 0, S2M, 4096)
        assert not cmp["flag_gt_30pct"], cmp
        assert rel_err(cmp["t3_n_dmc"], cmp["t2_n_dmc"]) < 1e-12


def test_t2_512b_sns_matches():
    cmp = sns.compare_occupancy("sns", 0, 512, 512)
    assert not cmp["flag_gt_30pct"]
    assert cmp["t3_n_dmc"] == cmp["t2_n_dmc"]


def test_t2_pass_pack_s_like_to_like():
    """I=min(K,Q_tot) occupancy vs frozen T2 for the signed S set, 4608B alone."""
    from _lib.workloads import SNS_STRIDES

    names = [n for n, _ in SNS_STRIDES]
    assert names == ["2MiB", "1MiB", "512KiB", "4608B", "512B"]
    for s_name, s in SNS_STRIDES:
        for st in ("sns", "mod384", "low", "high", "shear", "sbox"):
            cmp = sns.compare_occupancy(st, 0, s)
            assert not cmp["flag_gt_30pct"], (s_name, st, cmp)
            assert cmp["t3_n_dmc"] == cmp["t2_n_dmc"], (s_name, st, cmp)
            assert cmp["t3_n_bank"] == cmp["t2_n_bank"], (s_name, st, cmp)
            if s_name == "4608B" and st == "sns":
                assert cmp["t3_n_dmc"] == 384
