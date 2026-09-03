"""Signed smoke tables must cover the T2 pass-pack S set."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.workloads import ALIGNED_2MIB, GRAIN_BASES, SNS_STRIDES

_RESULTS = Path(__file__).resolve().parents[1] / "results"
_PASS_PACK = [n for n, _ in SNS_STRIDES]


def _rows(name: str) -> list[dict]:
    with (_RESULTS / name).open(newline="") as f:
        return list(csv.DictReader(f))


def test_signed_occupancy_covers_pass_pack_s():
    rows = _rows("occupancy.csv")
    s_set = {r["S"] for r in rows}
    assert s_set == set(_PASS_PACK)
    assert "4608B" in s_set
    # 4608B is its own S name, not folded into a power-of-two row
    alone = [r for r in rows if r["S"] == "4608B" and r["base"] != "REL_DIFF"]
    assert alone
    assert all(r["note"] == "4608B alone" for r in alone)
    assert all(r["family"] == "grain512" for r in alone)
    grain = {r["base"] for r in rows if r["family"] == "grain512" and r["base"] != "REL_DIFF"}
    align = {r["base"] for r in rows if r["family"] == "align2MiB" and r["base"] != "REL_DIFF"}
    assert grain == {hex(b) for b in GRAIN_BASES}
    assert align == {hex(b) for b in ALIGNED_2MIB}
    strats = {r["strategy"] for r in rows if r["base"] != "REL_DIFF"}
    assert strats == {"sns", "mod384", "low", "high", "shear", "sbox"}


def test_signed_t2_compare_covers_pass_pack_s():
    rows = _rows("t2_compare.csv")
    assert {r["S"] for r in rows} == set(_PASS_PACK)
    assert all(r["flag_gt_30pct"] == "False" for r in rows)
    assert all(float(r["rel_err_n_dmc"]) == 0.0 for r in rows)
    assert all(float(r["rel_err_n_bank"]) == 0.0 for r in rows)
    assert any(r["S"] == "4608B" for r in rows)
    strats = {r["strategy"] for r in rows}
    assert strats == {"sns", "mod384", "low", "high", "shear", "sbox"}


def test_signed_bw_hypothesis_and_masks_not_envelope():
    rows = _rows("bw_ci.csv")
    s_set = {r["S"] for r in rows}
    assert s_set == set(_PASS_PACK)
    assert {r["mask"] for r in rows} >= {"full", "rand1/16", "third"}
    assert {int(r["map_ports"]) for r in rows} >= {1, 4}
    assert all(r["hypothesis"] == "H-DRAM-BB" for r in rows)
    meta = json.loads((_RESULTS / "summary.json").read_text())
    assert meta["covering_bound"]["golden"] is False
    assert meta["signed_S"] == _PASS_PACK
    assert "envelope 0.85" in meta["bbox"]
    assert "H-DRAM-BB" in meta["note"]
