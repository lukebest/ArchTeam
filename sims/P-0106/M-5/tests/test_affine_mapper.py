"""Bit-exact AffineRebind primitives vs frozen T2."""

from __future__ import annotations

import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim
from _lib.t2load import load_affine_t2
from _lib.workloads import AFFINE_DOC

aff = load_sim(_HERE, "p0106_m5_sim")


def test_xor_fold6_pin_matches_t2():
    t2 = load_affine_t2()
    for g in (0, 1, 0x3F, 0x123456789ABCDEF, (1 << 56) - 1, 4096, 7):
        assert aff.xor_fold6(g) == t2.xor_fold6(g)
        assert aff.xor_fold9(g) == t2.xor_fold9(g)
        assert aff.upstream_dmc(g) == t2.upstream_dmc(g)


def test_kth_one_bijection_on_n40():
    m = aff.mask_n40()
    n = aff.popcount(m)
    assert n == 40
    seen = []
    for slot in range(n):
        b = aff.kth_one(m, slot)
        assert b >= 0 and (m >> b) & 1
        seen.append(b)
    assert len(set(seen)) == n
    assert aff.kth_one(m, n) == -1


def test_alpha_search_matches_t2_and_gcd_identity():
    t2 = load_affine_t2()
    for n in (32, 36, 40, 42, 45, 48):
        assert aff.alpha_search(n) == t2.alpha_search(n)
        a = aff.alpha_search(n)
        assert math.gcd(a, n) == 1
        for _, s in AFFINE_DOC:
            sg = s >> 9
            assert math.gcd(a * sg, n) == math.gcd(sg, n)


def test_n40_and_third_masks_match_t2():
    t2 = load_affine_t2()
    assert aff.mask_n40() == t2.mask_n40()
    assert aff.mask_third_bias() == t2.mask_third_bias()
    assert aff.mask_full() == t2.mask_full()
