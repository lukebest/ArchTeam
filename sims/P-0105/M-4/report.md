# T3 report · P-0105/M-4 SNS

Smoke: `python3 sims/P-0105/M-4/sweep.py --mode smoke --seed 20260903 --n-trials 3`
Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `cycles.csv`, `bw_ci.csv`, `t2_vs_t3_n_dmc.png`.

## Scope

Cycle-accurate mapper (12b shear / 256×8 integer ROM / XOR / fold384 / bitmap+PE).
DRAM is 假设 H-DRAM-BB (not silicon, clock UNKNOWN).
T2 (`models/P-0105/M-4/model.py`) is occupancy-only; like-to-like compare is `n_DMC` / `n_bank`.
`reviews/P-0105/M-4/t2_audit.md` was not in-tree; Dr.Sim + T2 spec were the must-verify list.

## Seeds / CI

SEED=20260903. Trials `SEED+i`. Every BW cell is `mean ± 95% CI (n=trials)`.
Occupancy is a deterministic function of (mapper, base, S) → CI width 0 on n_DMC.

## T2 vs T3 occupancy (smoke)

| S | family | strategy | T3 n_DMC | T2 n_DMC | \|T3−T2\|/T2 | T3 n_bank | T2 n_bank |
|---|--------|----------|----------|----------|--------------|-----------|-----------|
| 2MiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 |
| 2MiB | grain512 / 0x0 | mod384 | 3 | 3 | 0 | 3 | 3 |
| 2MiB | grain512 / 0x0 | sbox | 1 | 1 | 0 | 1 | 1 |
| 2MiB | grain512 / 0x0 | shear | 384 | 384 | 0 | 2304 | 2304 |
| 512B | grain512 / 0x0 | sns | 384 | 384 | 0 | 9008 | 9008 |

All smoke occupancy rows: **flag_gt_30pct = 0**. Mapper is bit-exact vs T2.

SNS n_DMC across grain bases `{0,512,1024,1536}`: `384.00 ± 0.00 (n=4)`, rel_diff=0.
Same on 2MiB-aligned `{0, 2MiB}`.

ABL-sbox at S=2MiB: n_DMC **count** is 1 for every phase (rel_diff=0 on the count), but occupied DMC **id** changes with phase (unit test `test_abl_sbox_varies_phase_id_at_2mib`). That is the shear-necessary ablation.

SNS at S=2MiB: 6 banks/DMC, `bank%8` kinds=1 (6b window collapse). maxload=11 minload=10.

COVERING_BOUND (uniform raw, **not** a golden SNS target): max=11 min=10 CV=0.0442.
SNS at S=2MiB is a 12b permutation, so raw hits every value in `[0,4095]` and fold384 **must** realize that covering. This is fold384 arithmetic, not an S-box discrepancy we tuned toward. ROM was not changed to match.

## Cycle BW (假设 H-DRAM-BB, 8 cores × 16 outstanding, 256-point AP, warmup 10%)

| S | strategy | ports | map_lat | page | mask | txns/cycle |
|---|----------|-------|---------|------|------|------------|
| 2MiB | sns | 1 | 1 | open | full | 1.000000 ± 0.000000 (n=3) |
| 2MiB | mod384 | 1 | 1 | open | full | 0.064953 ± 0.000000 (n=3) |
| 512B | sns | 1 | 1 | open | full | 1.000000 ± 0.000000 (n=3) |
| 512B | mod384 | 1 | 1 | open | full | 1.000000 ± 0.000000 (n=3) |

At S=2MiB, 1D (`mod384`) is DRAM-bound on 3 DMC × 1 bank (≈0.065 txn/cyc). SNS fills 384 DMC and hits the **1-port mapper ceiling** (1 txn/cyc). Absolute txns/cycle is higher for SNS — this is not a “win min/mean, lose absolute” case under this bbox.

At S=512B both strategies are mapper-port bound (1.0). Night `--mode night` adds `map_ports={1,4}` so the 512B DRAM contrast is visible above the 1-port ceiling.

No GB/s. μ_d UNKNOWN. 0.85 is the problem pass line, not a measured mean.
Warm-up discarded the first 10% of completions (cold row-buffer prefix). Refresh is not modeled.

## Discrepancy

None on occupancy (`|T3−T2|/T2 = 0`). T2 has no cycle BW column; T3 does not invent one for T2.
