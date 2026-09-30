"""Cycle-level structural tests: CAM FSM, GRANT, classifier, timeout."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

csr = load_sim(_HERE, "p0198_m2_sim")


def test_t2_signed_formulas_match_audit():
    f_ov, f_to, f_ok = csr.t2_completion_split(2.0)
    assert abs(f_ov - 0.0952) < 5e-4
    assert abs(f_to - 0.0) < 1e-12
    assert abs(f_ok - 0.9048) < 5e-4
    f8, _, _ = csr.t2_completion_split(8.0)
    assert abs(f8 - 0.5746) < 5e-4
    assert csr.t2_fallback_dominates(f8, 0.0)
    _, tax, r_off = csr.t2_r_schedule(inject_gate=False)
    assert abs(tax - 0.5500) < 5e-4
    f_ov, f_to, f_ok = csr.t2_completion_split(2.0)
    r = csr.t2_mix_ratio(f_ok, f_ov, f_to, r_off)
    assert abs(r - 1.0362) < 5e-4
    _, _, r_ok = csr.t2_r_schedule(inject_gate=True)
    r_on = csr.t2_mix_ratio(f_ok, f_ov, f_to, r_ok)
    assert abs(r_on - 0.5386) < 5e-4
    f5, f5t, f5g = csr.t2_completion_split(5.0)
    r_tree = csr.t2_mix_ratio(f5g, f5, f5t, r_ok)
    assert abs(r_tree - 0.6932) < 5e-4
    mix = 0.60 * r_tree + 0.40 * 1.0
    assert abs(mix - 0.8159) < 5e-4
    assert abs(f5 - 0.3983) < 5e-4


def test_classifier_rom_p2p_vs_spine():
    assert csr.classify("uniform_read") == "RING_P2P"
    assert csr.classify("uniform_write") == "RING_P2P"
    assert csr.classify("gather") == "SPINE_RENDZ"
    assert csr.classify("alltoall") == "SPINE_RENDZ"
    assert csr.classify("gather", spine_off=True) == "RING_P2P"
    assert csr.classify("gather", force_p2p=True) == "RING_P2P"


def test_n_cam_is_four_dedicated():
    assert csr.N_CAM == 4
    assert csr.CAM_BITS == 156
    assert set(csr.CAM_STATES) == {
        "IDLE", "COLLECT", "GRANT_PENDING", "GRANT_SENT", "FORCE_FALLBACK",
    }


def test_four_rings_exist_and_warmup_one_lap():
    r = csr.run_arm(
        "CSR", "gather", 20260903,
        n_top=6, n_bottom=2, n_ops=1, outstanding=16, warmup_laps=1,
    )
    assert r.n_nodes == 8
    assert r.warmup_cycles >= 8
    assert r.first_issue >= r.warmup_cycles or r.completed == 0
    assert r.n_cam == 4


def test_concurrent_live_cam_capped():
    r = csr.run_arm(
        "CSR", "gather", 20260903,
        n_top=8, n_bottom=2, n_ops=6, outstanding=256,
    )
    assert r.concurrent_live_cam_max <= 4
    assert r.cam_overflow_fallback >= 1
    assert r.same_cycle_reclassify >= 1


def test_independent_timeout_force_fallback():
    r = csr.run_arm(
        "CSR", "gather", 20260903,
        n_top=12, n_bottom=2, n_ops=2, outstanding=32, timeout=1,
    )
    assert r.collect_timeout_fallback >= 1
    assert r.ff_notify_cycles_max <= 2
    assert r.classifier_cycles_max == 1


def test_no_arrival_oracle_flag():
    r = csr.run_arm(
        "CSR", "allreduce", 20260903,
        n_top=6, n_bottom=2, n_ops=1, outstanding=16,
    )
    assert r.oracle_used is False


def test_grant_emits_on_spine():
    r = csr.run_arm(
        "CSR", "gather", 20260903,
        n_top=6, n_bottom=2, n_ops=1, outstanding=16, timeout=255,
    )
    assert r.grant_emits >= 1
    assert r.spine_grant >= 1


def test_card_claim_constant_is_labeled():
    assert csr.CARD_CLAIM["gather"] == "0.45-0.80x"
    assert csr.CARD_CLAIM["alltoall"] == "0.60-0.95x+res"
    pins = csr.signed_t2_rows()
    claim = next(p for p in pins if p["metric"] == "card-claim")
    assert claim["t3"] == "NOT measured"
    assert "NOT signed" in str(claim["t2"])
