"""Hard invariants: CAM Dat occupancy 0, no payload reject-and-orbit, gate."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SIMS = _HERE.parents[1]
sys.path.insert(0, str(_SIMS))

from _lib.importsim import load_sim

csr = load_sim(_HERE, "p0198_m2_sim")


def test_cam_dat_occupancy_and_retention_zero():
    for arm in ("spine-off", "CSR", "CSR-gate-off"):
        r = csr.run_arm(
            arm, "gather", 20260903,
            n_top=8, n_bottom=2, n_ops=2, outstanding=32,
        )
        assert r.dat_beats_held_max == 0, arm
        assert r.retention_depth_max == 0, arm
        assert r.payload_rbrg_reject == 0, arm
        assert r.invariant_ok, arm
        assert r.n_cam == 4


def test_h_inject_gate_on_has_no_premature_payload():
    r = csr.run_arm(
        "CSR", "gather", 20260903,
        n_top=8, n_bottom=2, n_ops=1, outstanding=16,
    )
    assert r.inject_before_grant == 0


def test_h_inject_gate_off_counts_premature():
    r = csr.run_arm(
        "CSR-gate-off", "gather", 20260903,
        n_top=8, n_bottom=2, n_ops=1, outstanding=16,
    )
    assert r.inject_before_grant > 0


def test_p2p_never_touches_cam():
    r = csr.run_arm(
        "CSR", "uniform_read", 20260903,
        n_top=8, n_bottom=2, n_ops=2, outstanding=16,
    )
    assert r.cam_overflow_fallback == 0
    assert r.collect_timeout_fallback == 0
    assert r.spine_grant == 0
    assert r.grant_emits == 0
    assert r.dat_beats_held_max == 0


def test_fallback_endpoints_are_first_class():
    r = csr.run_arm(
        "CSR", "gather", 20260903,
        n_top=8, n_bottom=2, n_ops=6, outstanding=256,
    )
    # overflow must be counted, not dropped from completions
    assert r.completed > 0
    assert r.cam_overflow_fallback >= 1
    if r.fallback_dominates:
        assert r.card_claim_valid is False


def test_signed_pins_match_director():
    assert csr.T2_SIGNED["cam_dat_occ"] == 0
    assert csr.T2_SIGNED["retention"] == 0
    assert csr.T2_SIGNED["n_cam"] == 4
    assert csr.T2_SIGNED["a8_f_ov"] == 0.5746
    assert csr.T2_SIGNED["a8_card_claim"] == "INVALID"
    assert csr.T2_SIGNED["spine_off_hard"] is True
    assert abs(csr.T2_SIGNED["gate_off_r"] - 1.0362) < 1e-9
    assert csr.T2_SIGNED["a2a_tree"] == 0.6932
    assert csr.T2_SIGNED["a2a_res"] == 1.0
    assert csr.T2_SIGNED["a2a_mix"] == 0.8159
