# T3 report · P-0198/M-5 CRRF

Smoke:
`python3 sims/P-0198/M-5/sweep.py --mode smoke --seed 20260903`

**Seed:** 20260903. Trials `SEED+i`.

T2 files are **not** on this PR (draft PR #63, read-only). Compare uses signed director / audit pins. card-claim intervals are **NOT measured**.

This report is filled after the smoke sweep. See `results/summary.json` and `results/t2_compare.csv`.

## Scope

Cycle-accurate five-state Rebind FSM, SYNC drain / `epoch_committed` barrier, skew accept set, ghost Dat channel-id, NACK/re-inject.
Hop latency / flit=txn / clock are 假设 H-RING-BB. Reduced bbox: 12 nodes, outstanding=16.
Ablation vs **rebind-off** only. No mixed ranking with eliminated M-1 CBC (PR #62) or M-2 / M-4.

## Seeds / CI

SEED=20260903. Every makespan / `C_dat_eff` cell is `mean ± 95% CI (n=trials)`.
0.85 is a pass bar, not a measured mean. No GB/s. Clock UNKNOWN.

## T2 vs T3 (to be filled from smoke)

Signed pins and `flag_gt_30pct` live in `results/t2_compare.csv`. T3 numbers are **not** replaced by T2 when `|T3−T2|/T2 > 30%`.

## Dr.Sim checklist

See `results/summary.json` → `dr_sim` and `tests/`.

## 评估审计

Review `results/t2_compare.csv`, `capacity.csv`, `snp_path.csv`, and any `flag_gt_30pct` rows **before** weekly report / T4. T4 is not opened here.
