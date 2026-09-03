# T3 report · P-0105/M-4 SNS

Smoke numbers are filled after `sweep.py --mode smoke`. See `results/`.

## Scope

Cycle-accurate mapper (shear / ROM / XOR / fold384 / PE). DRAM is 假设 H-DRAM-BB.
T2 (`models/P-0105/M-4/model.py`) is occupancy-only; like-to-like compare is `n_DMC` / `n_bank`.
`t2_audit.md` was not in-tree; Dr.Sim + T2 spec were the must-verify list.

## Seeds / CI

SEED=20260903. Trials `SEED+i`. Every BW cell is `mean ± 95% CI (n=trials)`.
Occupancy is deterministic given (mapper, base, S) → CI width 0 on n_DMC.

## T2 vs T3 occupancy (smoke)

*(filled after smoke)*

Covering bound 11/10/CV≈0.044 is **not** a golden SNS result. Do not calibrate ROM against it.

## Discrepancy

If `|T3−T2|/T2 > 30%`: inspect this simulator first. Do not silently pick T2.

## Cycle BW note

txns/cycle under H-DRAM-BB is **not** GB/s. Shear walks the row-buffer axis; occupancy ≠ DRAM BW.
Winning only min/mean occupancy while losing absolute txns/cycle vs 1D is a fail condition for the *problem*, but T3 reports both columns and does not convert covering CV into GB/s.
μ_d UNKNOWN. 0.85 is the problem pass line, not a measured mean.
