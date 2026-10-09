#!/usr/bin/env python3
"""Sanity for M-5r2 width algebra + stitch harness. Not a pass claim."""

from __future__ import annotations

import unittest

from harness import K_WORST, Fabric, gen_inference_mix, one_trial
from width import H_FRAG, d_of, k_of, pin_u, s_keep, w_snp


class Width(unittest.TestCase):
    def test_table_13_8_totals(self):
        # IHI0050E.b: S = 51+SAW+M .. 59+SAW+M
        self.assertEqual(w_snp(7, 41, 0), 51 + 41 + 0)
        self.assertEqual(w_snp(11, 49, 11), 59 + 49 + 11)

    def test_u_interval_and_worst_k(self):
        us = [pin_u(n)[2] for n in ("E.b-narrow", "E.b-mid", "E.b-wide", "overview-88", "conserv-U68")]
        self.assertEqual(min(us), 68)
        self.assertGreaterEqual(max(us), 80)
        self.assertEqual(s_keep(7), 12)
        self.assertEqual(s_keep(11), 16)
        d64 = d_of(64, True)
        d128 = d_of(128, True)
        self.assertEqual(d64, 512 + 64 + H_FRAG)
        self.assertEqual(d128, 1024 + 128 + H_FRAG)
        self.assertEqual(k_of(d128, 68), 18)
        self.assertEqual(K_WORST, 18)

    def test_issue_e_rejects_128b_as_legal_size(self):
        # Table 13-18 Size 0b110 = 64 B; 0b111 reserved. Documented in width.main.
        self.assertGreater(d_of(128, True), d_of(64, True))


class Harness(unittest.TestCase):
    def test_snp_path_constructive(self):
        a = one_trial("stitch-off", "snp_path", 1, K_WORST, 0, 24, 16)
        b = one_trial("stitch", "snp_path", 1, K_WORST, 0, 24, 16)
        self.assertEqual(a["comp_snp"], 24)
        self.assertEqual(b["comp_snp"], 24)
        self.assertEqual(a["ms_snp"], b["ms_snp"])
        self.assertEqual(b["ghost_inject"], 0)

    def test_header_only_identical_to_stitch(self):
        seed, k = 7, 8
        st = one_trial("stitch", "mixed", seed, k, 30, 2, 8)
        ho = one_trial("header-only", "mixed", seed, k, 30, 2, 8)
        dr = one_trial("drain-off", "mixed", seed, k, 30, 2, 8)
        self.assertEqual(st["ms_snp"], ho["ms_snp"])
        self.assertEqual(st["ms_dat"], ho["ms_dat"])
        self.assertEqual(st["ms_snp"], dr["ms_snp"])
        self.assertEqual(st["ghost_itag"], 0)

    def test_no_source_copy_charge(self):
        txns = gen_inference_mix(15, 1, 3)
        fab = Fabric("stitch", txns, k=8, outstanding=8, cap=True)
        # 1-deep stitcher: at most one held beat per node
        fab.run(5000)
        self.assertLessEqual(max(1 if s.beat else 0 for s in fab.stitch), 1)

    def test_ghosts_never_itag(self):
        r = one_trial("stitch", "mixed", 9, 8, 45, 3, 16)
        self.assertEqual(r["ghost_itag"], 0)

    def test_mix_is_15_to_1(self):
        txns = gen_inference_mix(150, 10, 0)
        nd = sum(1 for t in txns if t.chi == "Dat")
        ns = sum(1 for t in txns if t.chi == "Snp")
        self.assertEqual(nd, 150)
        self.assertEqual(ns, 10)
        self.assertEqual(nd / ns, 15.0)
        self.assertEqual(sum(1 for t in txns if t.kind == "gather"), int(round(150 * 0.75)))


if __name__ == "__main__":
    unittest.main()
