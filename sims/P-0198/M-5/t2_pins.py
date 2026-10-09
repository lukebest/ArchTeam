"""Signed T2 pins for P-0198/M-5 CRRF.

Director / 评估审计 — cite, do not invent. card-claim intervals are NOT signed.
T2 model lives on draft PR #63 (`cursor/p-0198-m-5-crrf-t2-4b32`) and is
not on main. This file does not copy `models/P-0198/M-5/`.
"""

from __future__ import annotations

# SOURCE: T2 default assumption set (PR #63 model.py / insight.md) + signed audit list.
T_DRAIN = 77.0
F_STEADY = 0.8666
C_DAT_EFF = {
    "rebind-off": 1.0000,
    "3:1": 1.6099,
    "7:1": 1.7182,
    "15:1": 1.7724,
}
H_COMMIT_HELD = 0
H_COMMIT_VIOLATED = 12
H_DAT_DOM_GATHER = {
    "3:1": 0.6212,
    "7:1": 0.5820,
    "15:1": 0.5642,
}
HARD1_T_OFF = 537.2
HARD1_T_BEST = 303.1  # 15:1 H-DAT-DOM gather ns (T2); T3 compares the inequality
SNP_LAT = {
    "rebind-off": 1.0,
    "3:1": 1.0900,
    "7:1": 1.2450,
    "15:1": 1.5625,
}
SNP_15_1 = 1.5625
SNP_KILL = 1.4
T2_K_CIRC = 2.0
T2_C_RING = 25.0
T2_N_PIPE = 2.0
T2_TAU_SYNC = 0.02
T2_TAU_BIND = 0.02
T2_T_STEADY = 20.0 * T2_C_RING
T2_Q = 1.0
T2_L_SNP = T2_C_RING / 2.0

# Published T_off (ns) — YAML + data.json off. Absolute ns are T2-only.
T_OFF = {
    "uniform_read": 4403.2,
    "uniform_write": 4834.6,
    "broadcast": 492.0,
    "gather": 537.2,
    "reduce": 537.2,
    "allgather": 1668.6,
    "allreduce": 990.6,
    "alltoall": 4098.0,
}

DAT_DOM = {"gather", "reduce", "allgather", "allreduce", "alltoall", "uniform_read"}

# card-claim — print as card-claim only; never treat as measured.
CARD_CLAIM_DAT = "0.55-0.85x"
CARD_CLAIM_WRITE = "0.85-1.05x"
CARD_CLAIM_SNP = "<=1.4x kill"
CARD_CLAIM_BCAST = "n/a-neutral"


def t2_c_dat_eff_formula(duty_dat: float, f_steady: float,
                         tau_sync: float = T2_TAU_SYNC,
                         tau_bind: float = T2_TAU_BIND) -> float:
    """T2 H-TMUX (spec §3.2). Used for like-to-like algebra, not as T3 measured."""
    if duty_dat <= 0:
        return 1.0
    ideal = 1.0 + duty_dat
    ghost = duty_dat * f_steady
    raw = 1.0 + ghost - tau_sync - tau_bind
    return min(ideal, max(1.0, raw))
