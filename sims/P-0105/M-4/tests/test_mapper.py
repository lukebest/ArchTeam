"""Bit-exact SNS mapper vs frozen T2 and card netlist."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_SIMS))

from _lib.t2load import load_sns_t2
from sim import ROM, S_CHECK, fold384, map_sns, map_sbox, map_shear, sbox_rom, shear


def test_sbox_checksum_and_permutation():
    rom = sbox_rom()
    assert rom[:16] == S_CHECK
    assert rom == ROM
    assert len(set(rom)) == 256


def test_not_gf256_aes():
    # AES S-box first bytes are 0x63, 0x7c — must not match
    assert ROM[0] == 0
    assert ROM[1] == 3


def test_shear_12bit_truncate():
    # y=1 → 7*y = 8-1 = 7, not arbitrary precision overflow
    assert shear(0, 1) == 7
    assert shear(4095, 1) == (4095 + 7) & 0xFFF
    y = 0xABC
    seven_y = ((y << 3) - y) & 0xFFF
    assert shear(0, y) == seven_y
    # 7 is odd and 7 ≢ 0 (mod 3)
    assert 7 % 2 == 1
    assert 7 % 3 != 0


def test_fold384_equiv_mod_on_12bit():
    for raw in (0, 1, 383, 384, 385, 3839, 3840, 4095):
        assert fold384(raw) == raw % 384
    # 384*11 = 4224 > 4095 so q capped at 10
    assert fold384(4095) == 4095 - 10 * 384


def test_bit_exact_vs_t2_sample():
    t2 = load_sns_t2()
    for phys in (0, 512, 4096, 2 * 1024 * 1024, 0x12345600, (1 << 32) - 512):
        assert map_sns(phys) == t2.map_sns(phys)
        assert map_shear(phys) == t2.map_shear_only(phys)
        assert map_sbox(phys) == t2.map_sbox_only(phys)


def test_sbox_only_no_xor_y():
    # ABL-sbox: z = S[x[11:4]] with no XOR y — same x ⇒ same DMC
    a = map_sbox(0)
    b = map_sbox(2 * 1024 * 1024)  # y walks, x frozen
    assert a[0] == b[0]
