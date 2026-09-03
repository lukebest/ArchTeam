"""Bit-exact SNS mapper vs frozen T2 and card netlist."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim
from _lib.t2load import load_sns_t2

sns = load_sim(_HERE, "p0105_m4_sim")


def test_sbox_checksum_and_permutation():
    rom = sns.sbox_rom()
    assert rom[:16] == sns.S_CHECK
    assert rom == sns.ROM
    assert len(set(rom)) == 256


def test_not_gf256_aes():
    assert sns.ROM[0] == 0
    assert sns.ROM[1] == 3


def test_shear_12bit_truncate():
    assert sns.shear(0, 1) == 7
    assert sns.shear(4095, 1) == (4095 + 7) & 0xFFF
    y = 0xABC
    seven_y = ((y << 3) - y) & 0xFFF
    assert sns.shear(0, y) == seven_y
    assert 7 % 2 == 1
    assert 7 % 3 != 0


def test_fold384_equiv_mod_on_12bit():
    for raw in (0, 1, 383, 384, 385, 3839, 3840, 4095):
        assert sns.fold384(raw) == raw % 384
    assert sns.fold384(4095) == 4095 - 10 * 384


def test_bit_exact_vs_t2_sample():
    t2 = load_sns_t2()
    for phys in (0, 512, 4096, 2 * 1024 * 1024, 0x12345600, (1 << 32) - 512):
        assert sns.map_sns(phys) == t2.map_sns(phys)
        assert sns.map_shear(phys) == t2.map_shear_only(phys)
        assert sns.map_sbox(phys) == t2.map_sbox_only(phys)


def test_sbox_only_no_xor_y():
    a = sns.map_sbox(0)
    b = sns.map_sbox(2 * 1024 * 1024)
    assert a[0] == b[0]
