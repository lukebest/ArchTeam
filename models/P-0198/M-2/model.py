#!/usr/bin/env python3
"""P-0198/M-2 CSR — Rendezvous–Grant occupancy + schedule model (stdlib).

See spec.md. No CBC empty-slot equations. No curve fitting.
Absolute makespan only via H-REL-SCALE relative scaling of published T_off.
Cycle-level CAM/GRANT FSM is out of scope (Dr.Sim → T3).
"""

from __future__ import annotations

import math
import sys

# ---- Envelope pins (SOURCE in comments) ----
# problems/P-0198.yaml + docs/srcfc_ca_model/data.json scheme=off
# Same T_off table as the M-1 reference (pins only; not CBC math).
T_OFF = {
    "uniform_read": 4403.2,  # YAML + data.json
    "uniform_write": 4834.6,  # YAML + data.json
    "broadcast": 492.0,  # data.json; YAML emphasizes goodput not makespan
    "gather": 537.2,
    "reduce": 537.2,
    "allgather": 1668.6,
    "allreduce": 990.6,
    "alltoall": 4098.0,
}

# collapse_settings.json + YAML narrative
COLLAPSED = {
    "uniform_read": True,  # peak-then-collapse narrative in YAML
    "uniform_write": False,  # YAML: platform ~5.5 TB/s, no reported collapse
    "broadcast": False,
    "gather": True,
    "reduce": True,
    "allgather": True,
    "allreduce": True,
    "alltoall": True,
}

# Fan-in–dominated collapsed classes for H-FANIN-BOUND relative makespan.
# alltoall is collapsed but reported via tree/residual split, not this set.
FANIN_DOM = {"gather", "reduce", "allgather", "allreduce"}
SPINE_ELIGIBLE = FANIN_DOM | {"alltoall", "broadcast"}

# Card-claim bands (NOT measured; NOT a pass signature).
CARD_CLAIM = {
    "gather": "0.45-0.80x",
    "reduce": "0.45-0.80x",
    "allgather": "0.45-0.80x",
    "allreduce": "0.45-0.80x",
    "alltoall": "0.60-0.95x+res",
    "broadcast": "0.75-0.98x",
    "uniform_read": "0.95-1.05x",
    "uniform_write": "0.95-1.05x",
}

N_CAM = 4
N_SRC = 12
N_BEATS = 8  # 512 B / 64 B flit; illustration only
TIMEOUT = 255
BITS_PER_CAM = 16 + 12 + 3 + 8  # txn_id + child_bitmap + state + timeout
CAM_BITS = N_CAM * BITS_PER_CAM
STATES = ("IDLE", "COLLECT", "GRANT_PENDING", "GRANT_SENT", "FORCE_FALLBACK")


def erlang_b(n: int, a: float) -> float:
    """M/M/n/n blocking (no queue). Matches immediate RING_P2P on CAM full."""
    if n < 0:
        raise ValueError("n")
    if a < 0:
        raise ValueError("a")
    if a == 0.0:
        return 0.0
    b = 1.0
    for k in range(1, n + 1):
        b = (a * b) / (k + a * b)
    return b


def overflow_det(c: float, n_cam: int = N_CAM) -> float:
    """Deterministic excess demand / demand. Probe only."""
    if c <= 0:
        return 0.0
    return max(0.0, c - n_cam) / c


def tau_collect(n_src: int, t_hdr: float) -> float:
    return n_src * t_hdr


def p_timeout(t_collect: float, timeout: float = TIMEOUT) -> float:
    """H-TIMEOUT-WINDOW: late fraction if collect window exceeds timeout."""
    if t_collect <= 0:
        return 0.0
    if t_collect <= timeout:
        return 0.0
    return 1.0 - timeout / t_collect


def completion_split(a: float, t_collect: float, n_cam: int = N_CAM):
    """Return (f_overflow, f_timeout, f_grant). Conserves mass."""
    f_ov = erlang_b(n_cam, a)
    p_to = p_timeout(t_collect)
    f_to = (1.0 - f_ov) * p_to
    f_ok = (1.0 - f_ov) * (1.0 - p_to)
    return f_ov, f_to, f_ok


def r_schedule(
    f_fanin: float,
    w_grant: float,
    n_src: int = N_SRC,
    k_grant: float = 0.0,
    inject_gate: bool = True,
):
    """Amdahl bound on fan-in concurrency. Not CBC T∝1/p_inj."""
    if n_src <= 0:
        raise ValueError("n_src")
    w = min(max(w_grant, 0.0), float(n_src))
    f = min(max(f_fanin, 0.0), 1.0)
    r_sched = (1.0 - f) + f * (w / n_src)
    tax_orbit = 0.0 if inject_gate else f * (1.0 - w / n_src)
    r_ok = r_sched + max(0.0, k_grant) + tax_orbit
    return r_sched, tax_orbit, r_ok


def mix_ratio(f_grant: float, f_ov: float, f_to: float, r_ok: float, r_fb: float = 1.0):
    return f_grant * r_ok + (f_ov + f_to) * r_fb


def fallback_dominates(f_ov: float, f_to: float) -> bool:
    return (f_ov > 0.5) or (f_to > 0.5)


def occupancy_cam_dat(_i: int) -> int:
    """Invariant: CAM holds header/credit state only."""
    return 0


def retention_depth() -> int:
    return 0


def fmt(x: float, nd: int = 4) -> str:
    if isinstance(x, str):
        return x
    if math.isinf(x):
        return "inf"
    return f"{x:.{nd}f}"


def prow(cols, widths):
    print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))


def main() -> int:
    print("P-0198/M-2 CSR  Rendezvous-Grant occupancy + schedule model")
    print("envelope DV200 tests/soc_sim  repo lukebest/bufferless-ring-noc")
    print("SOURCE T_off: problems/P-0198.yaml + docs/srcfc_ca_model/data.json off")
    print("no silicon ±15%; no team-384dmc; no decode-*; no STREAM; no team-interleave-microbench")
    print("0.85 is pass bar not mean; card-claim bands are NOT measured / NOT signed pass")
    print("orthogonal to M-1 CBC / M-4 AODI / M-5 CRRF — do not mix conclusions")
    print()

    # ---- Default assumption set (named; scanned below) ----
    t_hdr = 15.0  # H-COLLECT: header spacing (cycles)
    a_fanin = 2.0  # H-CAM-LOAD: gather-family offered Erlangs
    a_a2a = 5.0  # H-A2A-LOAD: segmented GRANT presses CAM
    a_bcast = 0.5
    f_fanin = 0.60  # H-FANIN-BOUND
    w_grant = 1.0  # static order table serial window
    k_grant = 0.04  # H-GRANT-TAX
    inject_gate = True  # H_inject_gate
    ff_notify = True  # H-FF-NOTIFY
    w_tree = 0.60  # H-A2A-SPLIT
    w_res = 1.0 - w_tree
    tree_arity = 4
    n_seg = math.ceil(N_SRC / tree_arity)

    t_col = tau_collect(N_SRC, t_hdr)
    tau_hold = t_col + 1.0

    print("=== ASSUMPTIONS (labeled; not silicon) ===")
    print(f"H-CAM-DAT0 occupancy(CAM_i, Dat_beats)==0  N_cam={N_CAM} bits={CAM_BITS}")
    print(f"H-RETENTION0 RBRG_reject_retention_depth==0")
    print(f"H_inject_gate={inject_gate}  (payload inject before GRANT == 0 if true)")
    print(f"H-FF-NOTIFY={ff_notify}  (FORCE_FALLBACK endpoint reclass observable)")
    print(f"H-COLLECT T_hdr={t_hdr}  tau_collect={t_col}  timeout={TIMEOUT}")
    print(f"H-CAM-RELEASE tau_hold={tau_hold} (CAM freed at GRANT_SENT; fold not in CAM)")
    print(f"H-CAM-LOAD a_fanin={a_fanin}  a_a2a={a_a2a}  a_bcast={a_bcast}")
    print(f"H-FANIN-BOUND f_fanin={f_fanin}  W_grant={w_grant}  N_src={N_SRC}")
    print(f"H-GRANT-TAX k_grant={k_grant}")
    print(f"H-A2A-SPLIT w_tree={w_tree} w_res={w_res}  arity={tree_arity} N_seg={n_seg}")
    print(f"H-REL-SCALE T_hat = T_off * r   N_beats={N_BEATS} (illustration, not ns)")
    print(f"FSM states: {'/'.join(STATES)}")
    print()

    # ---- Invariants (exact, by construction) ----
    print("=== INVARIANTS (exact; violation = mechanism fail) ===")
    occ = [occupancy_cam_dat(i) for i in range(N_CAM)]
    ret = retention_depth()
    live = min(N_CAM, N_CAM)  # analytical: never instantiate >N_cam
    ok_occ = all(x == 0 for x in occ)
    ok_ret = ret == 0
    ok_live = live <= N_CAM
    print(
        f"  occupancy(CAM_i, Dat_beats)={occ}  all_zero={ok_occ}"
    )
    print(f"  RBRG_reject_retention_depth={ret}  ok={ok_ret}")
    print(f"  concurrent_live_cam<={N_CAM} modeled_live={live}  ok={ok_live}")
    print(f"  invariant_ok={ok_occ and ok_ret and ok_live}")
    print("  rendezvous modeled as header/credit CAM only; never payload latch")
    print()

    # ---- Completion conservation ----
    print("=== COMPLETION CONSERVATION (unit arrival mass) ===")
    for name, a in (("fanin_default", a_fanin), ("alltoall_seg", a_a2a), ("broadcast", a_bcast), ("p2p", 0.0)):
        f_ov, f_to, f_ok = completion_split(a, t_col)
        s = f_ov + f_to + f_ok
        print(
            f"  {name:16} a={a:.2f}  f_ov={fmt(f_ov)}  f_to={fmt(f_to)}  "
            f"f_grant={fmt(f_ok)}  sum={fmt(s)}  "
            f"dominates={fallback_dominates(f_ov, f_to)}"
        )
    print("CONSTRAINT: overflow is Erlang-B (no queue); timeout is late-fraction")
    print()

    r_sched, tax_orbit_on, r_ok_on = r_schedule(
        f_fanin, w_grant, N_SRC, k_grant, inject_gate=True
    )
    _, tax_orbit_off, r_ok_gate_off = r_schedule(
        f_fanin, w_grant, N_SRC, k_grant, inject_gate=False
    )

    # ---- Per-class (no averaging) ----
    print("=== PER-CLASS (no averaging) H-FANIN-BOUND where collapsed gather-family ===")
    widths = (14, 8, 6, 8, 8, 8, 10, 10, 12, 14, 12)
    prow(
        (
            "class",
            "collaps",
            "a",
            "f_ov",
            "f_to",
            "f_grant",
            "T_off",
            "T_hat",
            "T_hat/T_off",
            "card-claim",
            "claim_valid",
        ),
        widths,
    )

    per_class_r = {}
    for cls in (
        "uniform_read",
        "uniform_write",
        "broadcast",
        "gather",
        "reduce",
        "allgather",
        "allreduce",
        "alltoall",
    ):
        t_off = T_OFF[cls]
        if cls in FANIN_DOM:
            a = a_fanin
            f_ov, f_to, f_ok = completion_split(a, t_col)
            r = mix_ratio(f_ok, f_ov, f_to, r_ok_on)
            t_hat = t_off * r
            valid = not fallback_dominates(f_ov, f_to)
            per_class_r[cls] = {
                "a": a,
                "f_ov": f_ov,
                "f_to": f_to,
                "f_ok": f_ok,
                "r": r,
                "t_hat": t_hat,
                "valid": valid,
            }
            prow(
                (
                    cls,
                    str(COLLAPSED[cls]),
                    fmt(a, 2),
                    fmt(f_ov),
                    fmt(f_to),
                    fmt(f_ok),
                    fmt(t_off, 1),
                    fmt(t_hat, 1),
                    fmt(r),
                    CARD_CLAIM[cls],
                    "ok" if valid else "INVALID",
                ),
                widths,
            )
            print(
                f"           r_sched={fmt(r_sched)} r_ok={fmt(r_ok_on)} "
                f"tax_orbit={fmt(tax_orbit_on)} "
                f"(card-claim column is NOT measured)"
            )
        elif cls == "alltoall":
            f_ov, f_to, f_ok = completion_split(a_a2a, t_col)
            r_tree = mix_ratio(f_ok, f_ov, f_to, r_ok_on)
            r_res = 1.0
            r_mix = w_tree * r_tree + w_res * r_res
            valid = not fallback_dominates(f_ov, f_to)
            per_class_r[cls] = {
                "a": a_a2a,
                "f_ov": f_ov,
                "f_to": f_to,
                "f_ok": f_ok,
                "r_tree": r_tree,
                "r_res": r_res,
                "r_mix": r_mix,
                "valid": valid,
            }
            prow(
                (
                    cls,
                    str(COLLAPSED[cls]),
                    fmt(a_a2a, 2),
                    fmt(f_ov),
                    fmt(f_to),
                    fmt(f_ok),
                    fmt(t_off, 1),
                    "see-split",
                    "see-split",
                    CARD_CLAIM[cls],
                    "ok" if valid else "INVALID",
                ),
                widths,
            )
            print(
                f"           TREE r_tree={fmt(r_tree)} T_tree={fmt(t_off * r_tree, 1)}  "
                f"RESIDUAL r_res={fmt(r_res)} T_res={fmt(t_off * r_res, 1)}  "
                f"w_tree={fmt(w_tree)} w_res={fmt(w_res)}"
            )
            print(
                f"           companion mix r={fmt(r_mix)} T_mix={fmt(t_off * r_mix, 1)}  "
                f"(NOT a pass number; do not average with gather-family)"
            )
        else:
            a = a_bcast if cls == "broadcast" else 0.0
            f_ov, f_to, f_ok = completion_split(a, t_col)
            per_class_r[cls] = {
                "a": a,
                "f_ov": f_ov,
                "f_to": f_to,
                "f_ok": f_ok,
                "r": None,
                "valid": True,
            }
            prow(
                (
                    cls,
                    str(COLLAPSED[cls]),
                    fmt(a, 2),
                    fmt(f_ov),
                    fmt(f_to),
                    fmt(f_ok) if cls == "broadcast" else "n/a",
                    fmt(t_off, 1),
                    "n/a",
                    "n/a",
                    CARD_CLAIM[cls],
                    "n/a-H-FANIN",
                ),
                widths,
            )
    print()

    # ---- Fallback-dominates probe ----
    print("=== FALLBACK-DOMINATES PROBE (card-claim kill switch) ===")
    print("kill if f_ov>0.5 OR f_to>0.5 on that class; do not sign card-claim as pass")
    for name, a in (
        ("single-ish a=1.0", 1.0),
        ("default a=2.0", 2.0),
        ("dual-collectives a=2.0", 2.0),
        ("segmented a=5.0", 5.0),
        ("high-ost a=8.0", 8.0),
    ):
        f_ov, f_to, f_ok = completion_split(a, t_col)
        r = mix_ratio(f_ok, f_ov, f_to, r_ok_on)
        dom = fallback_dominates(f_ov, f_to)
        sys_fb = (f_ov + f_to) > 0.10
        print(
            f"  {name:24} f_ov={fmt(f_ov)} f_to={fmt(f_to)} f_grant={fmt(f_ok)}  "
            f"r={fmt(r)}  dominates={dom}  flag_sys_fb(>10%)={sys_fb}  "
            f"card_claim={'INVALID' if dom else 'still-labeled-not-pass'}"
        )
    print("Sys T1 budget (two concurrent allreduce): combined fallback <=10% is a probe, not a pass")
    print()

    # ---- H_inject_gate / FORCE_FALLBACK ----
    print("=== H_inject_gate AND FORCE_FALLBACK PROBES ===")
    print(
        f"  gate ON:  I_payload_before_GRANT=0  tax_orbit={fmt(tax_orbit_on)}  "
        f"r_ok={fmt(r_ok_on)}"
    )
    print(
        f"  gate OFF: I_payload_before_GRANT>0  tax_orbit={fmt(tax_orbit_off)}  "
        f"r_ok={fmt(r_ok_gate_off)}  (premature orbit cancels fan-in term)"
    )
    f_ov, f_to, f_ok = completion_split(a_fanin, t_col)
    r_gate_off = mix_ratio(f_ok, f_ov, f_to, r_ok_gate_off)
    print(
        f"  gather-family default a={a_fanin}: r_gate_on={fmt(per_class_r['gather']['r'])}  "
        f"r_gate_off={fmt(r_gate_off)}  "
        f"returns_toward_1={r_gate_off >= 0.90}"
    )
    # congested headers → timeout
    t_col_cong = tau_collect(N_SRC, 28.0)
    f_ov_c, f_to_c, f_ok_c = completion_split(a_fanin, t_col_cong)
    flag_orphan = (f_to_c > 0.0) and (not ff_notify)
    print(
        f"  congested T_hdr=28 tau_collect={t_col_cong:.1f}  "
        f"f_ov={fmt(f_ov_c)} f_to={fmt(f_to_c)} f_grant={fmt(f_ok_c)}  "
        f"timeout_dominates={f_to_c > 0.5}"
    )
    print(
        f"  H-FF-NOTIFY={ff_notify}  flag_orphan={flag_orphan}  "
        f"(FORCE_FALLBACK must be observable; parse as named assumption/probe)"
    )
    print(
        "  if H-FF-NOTIFY were false and f_to>0: half-collective waits GRANT → invalidate"
    )
    print()

    # ---- Ablation spine-off ----
    print("=== ABLATION spine-off (HARD causal probe) ===")
    print("spine-off: force RING_P2P; CAM unused; r_off=1; collapse returns to baseline magnitude")
    for cls in ("gather", "reduce", "allgather", "allreduce", "alltoall"):
        t_off = T_OFF[cls]
        t_off_arm = t_off * 1.0
        if cls == "alltoall":
            t_on = t_off * per_class_r[cls]["r_tree"]
            ratio_on = per_class_r[cls]["r_tree"]
            note = "tree-arm (residual already ~1)"
        else:
            t_on = per_class_r[cls]["t_hat"]
            ratio_on = per_class_r[cls]["r"]
            note = "H-FANIN-BOUND"
        better = t_on < t_off_arm
        print(
            f"  {cls:12} T_off={fmt(t_off, 1)}  T_hat_off={fmt(t_off_arm, 1)}  "
            f"T_hat_on={fmt(t_on, 1)}  on/off={fmt(ratio_on)}  "
            f"on_better={better}  {note}"
        )
    g_on = per_class_r["gather"]["t_hat"]
    g_off = T_OFF["gather"]
    print(
        f"HARD probe: spine-off gather T_hat ({fmt(g_off, 1)}) > spine-on T_hat "
        f"({fmt(g_on, 1)})? {g_off > g_on}  (must be true to attribute)"
    )
    print("uniform_read/write remain RING_P2P either arm (near-neutral; not H-FANIN-BOUND)")
    print()

    # ---- Sensitivity ----
    print("=== SENSITIVITY (gather): (a, N_cam) and (f_fanin, W_grant) ===")
    print("-- vary a (N_cam=4, f_fanin/W_grant default, gate on) --")
    for a_i in (0.5, 1.0, 2.0, 4.0, 5.0, 8.0):
        f_ov, f_to, f_ok = completion_split(a_i, t_col)
        r = mix_ratio(f_ok, f_ov, f_to, r_ok_on)
        print(
            f"  a={a_i:.2f}  f_ov={fmt(f_ov)}  f_grant={fmt(f_ok)}  "
            f"T_hat/T_off={fmt(r)}  dominates={fallback_dominates(f_ov, f_to)}"
        )
    print("-- vary N_cam (a=2.0 fixed) --")
    for n in (2, 4, 8):
        f_ov, f_to, f_ok = completion_split(a_fanin, t_col, n_cam=n)
        r = mix_ratio(f_ok, f_ov, f_to, r_ok_on)
        print(
            f"  N_cam={n}  f_ov={fmt(f_ov)}  T_hat/T_off={fmt(r)}  "
            f"(silicon is N_cam=4; 8 is counterfactual, not the card)"
        )
    print("-- vary f_fanin (W_grant=1, a=2.0) --")
    for ff in (0.30, 0.45, 0.60, 0.75, 0.90):
        _, _, r_ok_i = r_schedule(ff, w_grant, N_SRC, k_grant, True)
        f_ov, f_to, f_ok = completion_split(a_fanin, t_col)
        r = mix_ratio(f_ok, f_ov, f_to, r_ok_i)
        print(f"  f_fanin={ff:.2f}  r_ok={fmt(r_ok_i)}  T_hat/T_off={fmt(r)}")
    print("-- vary W_grant (f_fanin=0.60, a=2.0) --")
    for w in (1.0, 2.0, 3.0, 4.0, 12.0):
        _, _, r_ok_i = r_schedule(f_fanin, w, N_SRC, k_grant, True)
        f_ov, f_to, f_ok = completion_split(a_fanin, t_col)
        r = mix_ratio(f_ok, f_ov, f_to, r_ok_i)
        print(
            f"  W_grant={w:.1f}  r_ok={fmt(r_ok_i)}  T_hat/T_off={fmt(r)}  "
            f"{'(serial order-table default)' if w == 1 else ''}"
        )
    print()
    print("most sensitive: a (overflow → kill switch); f_fanin/W_grant set r_ok if grant path wins")
    print("N_cam is a silicon constant=4; raising it is a redesign, not a knob on this card")
    print()

    # ---- Magic-gap flag ----
    print("=== MAGIC-GAP FLAG ===")
    r_g = per_class_r["gather"]["r"]
    in_band = 0.45 <= r_g <= 0.80
    print(
        f"gather default assumptions: T_hat/T_off={fmt(r_g)} "
        f"in card-claim[0.45,0.80]? {in_band}  (label only; not a pass)"
    )
    r_a2a = per_class_r["alltoall"]["r_tree"]
    r_res = per_class_r["alltoall"]["r_res"]
    print(
        f"alltoall TREE T_hat/T_off={fmt(r_a2a)}  RESIDUAL={fmt(r_res)}  "
        f"mix={fmt(per_class_r['alltoall']['r_mix'])}  "
        f"(residual must stay a separate column)"
    )
    if per_class_r["alltoall"]["f_ov"] > 0.3:
        print(
            "GAP: alltoall segmented a=5 already has material overflow; "
            "card 0.60-0.95x is optimistic unless N_seg/a drops"
        )
    f_ov8, f_to8, _ = completion_split(8.0, t_col)
    print(
        f"high-ost a=8: f_ov={fmt(f_ov8)} dominates={fallback_dominates(f_ov8, f_to8)}  "
        f"→ card-claim bands INVALID on that load"
    )
    print(
        "GAP: card 0.45-0.80x needs H_inject_gate + modest a + large f_fanin; "
        "do not treat card interval as model output or measured"
    )
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
