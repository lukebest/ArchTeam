# T3 report · P-0105/M-4 SNS

Smoke (signed table): `python3 sims/P-0105/M-4/sweep.py --mode smoke --seed 20260903 --n-trials 3`
Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `cycles.csv`, `bw_ci.csv`, `t2_vs_t3_n_dmc.png`, `t2_vs_t3_n_dmc_by_S.png`.

Signed S set (T2 pass-pack, 4608B standalone — not folded into a 2-power row):
`{2MiB, 1MiB, 512KiB, 4608B, 512B}`.

## Scope

Cycle-accurate mapper (12b shear / 256×8 integer ROM / XOR / fold384 / bitmap+PE).
DRAM is 假设 H-DRAM-BB (not silicon, clock UNKNOWN).
T2 (`models/P-0105/M-4/model.py`) is occupancy-only; like-to-like compare is `n_DMC` / `n_bank` with issued-set `I=min(K,Q_tot)`.
`reviews/P-0105/M-4/t2_audit.md` was not in-tree; Dr.Sim + T2 spec were the must-verify list.

## Seeds / CI

SEED=20260903. Trials `SEED+i`. Every BW cell is `mean ± 95% CI (n=trials)`.
Occupancy is a deterministic function of (mapper, base, S) → CI width 0 on n_DMC.

## T2 vs T3 occupancy (signed smoke)

Families: full `GRAIN_BASES` (8) and `ALIGNED_2MIB` (4). Strategies: four baselines (`sns`, `mod384`, `low`/`B-low`, `high`/`B-high`) plus two ablations (`shear`, `sbox`). 4608B is grain-only (no align2MiB fold-in).

Grain512 / base=0x0, `I=min(K,Q_tot)`:

| S | family | strategy | T3 n_DMC | T2 n_DMC | \|T3−T2\|/T2 | T3 n_bank | T2 n_bank | min/mean |
|---|--------|----------|----------|----------|--------------|-----------|-----------|----------|
| 2MiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 | 0.9375 |
| 2MiB | grain512 / 0x0 | mod384 | 3 | 3 | 0 | 3 | 3 | 0.9998 |
| 2MiB | grain512 / 0x0 | low | 1 | 1 | 0 | 1 | 1 | 1.0000 |
| 2MiB | grain512 / 0x0 | high | 384 | 384 | 0 | 384 | 384 | 0.9375 |
| 2MiB | grain512 / 0x0 | sbox | 1 | 1 | 0 | 1 | 1 | 1.0000 |
| 2MiB | grain512 / 0x0 | shear | 384 | 384 | 0 | 2304 | 2304 | 0.9375 |
| 1MiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 | 0.9375 |
| 1MiB | grain512 / 0x0 | mod384 | 3 | 3 | 0 | 3 | 3 | 0.9998 |
| 1MiB | grain512 / 0x0 | low | 1 | 1 | 0 | 1 | 1 | 1.0000 |
| 1MiB | grain512 / 0x0 | high | 384 | 384 | 0 | 384 | 384 | 0.9375 |
| 512KiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 | 0.9000 |
| 512KiB | grain512 / 0x0 | mod384 | 3 | 3 | 0 | 3 | 3 | 1.0000 |
| 512KiB | grain512 / 0x0 | low | 1 | 1 | 0 | 1 | 1 | 1.0000 |
| 512KiB | grain512 / 0x0 | high | 384 | 384 | 0 | 384 | 384 | 1.0000 |
| 4608B | grain512 / 0x0 | sns | 384 | 384 | 0 | 10523 | 10523 | 0.7000 |
| 4608B | grain512 / 0x0 | mod384 | 128 | 128 | 0 | 128 | 128 | 1.0000 |
| 4608B | grain512 / 0x0 | low | 384 | 384 | 0 | 384 | 384 | 0.7500 |
| 4608B | grain512 / 0x0 | high | 34 | 34 | 0 | 34 | 34 | 0.7548 |
| 4608B | grain512 / 0x0 | shear | 200 | 200 | 0 | 840 | 840 | 0.0130 |
| 4608B | grain512 / 0x0 | sbox | 384 | 384 | 0 | 2304 | 2304 | 0.9000 |
| 512B | grain512 / 0x0 | sns | 384 | 384 | 0 | 9008 | 9008 | 0.9000 |
| 512B | grain512 / 0x0 | mod384 | 384 | 384 | 0 | 384 | 384 | 1.0000 |
| 512B | grain512 / 0x0 | low | 384 | 384 | 0 | 384 | 384 | 0.7500 |
| 512B | grain512 / 0x0 | high | 4 | 4 | 0 | 4 | 4 | 0.8000 |

All 336 `t2_compare.csv` rows: **flag_gt_30pct = false**, `rel_err_n_dmc = rel_err_n_bank = 0`. Mapper is bit-exact vs T2. 4608B is a standalone `S` column (`note=4608B alone`); it is not averaged into 512B or 4KiB.

SNS n_DMC across full `GRAIN_BASES` (n=8) and `ALIGNED_2MIB` (n=4): `384.00 ± 0.00`, rel_diff=0.0000 at every signed S (4608B grain-only).

ABL-sbox at S=2MiB: n_DMC **count** is 1 for every phase (rel_diff=0 on the count), but occupied DMC **id** changes with phase (unit test `test_abl_sbox_varies_phase_id_at_2mib`). That is the shear-necessary ablation.

SNS at S=2MiB: 6 banks/DMC, `bank%8` kinds=1 (6b window collapse). maxload=11 minload=10.

COVERING_BOUND (uniform raw, **not** a golden SNS target): max=11 min=10 CV=0.0442; `summary.json` `"golden": false`.
SNS at S=2MiB is a 12b permutation, so raw hits every value in `[0,4095]` and fold384 **must** realize that covering. This is fold384 arithmetic, not an S-box discrepancy we tuned toward. ROM was not changed to match.

## Cycle BW (假设 H-DRAM-BB, reduced bbox)

Bbox (signed smoke): **8 cores × 16 outstanding**, AP **256 points**, `map_ports∈{1,4}`, map_lat=1, page=open, masks `{full, rand1/16, third}`, warmup 丢前 10% completions, n_trials=3, seed=`20260903+trial`.
This is **not** the 120-core / `Q_tot=15360` envelope. 0.85 is the problem pass line, not a measured mean. No GB/s. μ_d UNKNOWN.

Selected cells (full table: `results/bw_ci.csv`, every row labeled `hypothesis=H-DRAM-BB`):

| S | strategy | ports | mask | txns/cycle mean ± 95% CI |
|---|----------|-------|------|--------------------------|
| 2MiB | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 2MiB | mod384 | 1 | full | 0.064953 ± 0.000000 (n=3) |
| 2MiB | sns | 1 | rand1/16 | 0.940068 ± 0.005007 (n=3) |
| 2MiB | sns | 1 | third | 0.745953 ± 0.003168 (n=3) |
| 2MiB | sns | 4 | full | 3.709677 ± 0.000000 (n=3) |
| 1MiB | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 1MiB | mod384 | 1 | full | 0.064953 ± 0.000000 (n=3) |
| 512KiB | sns | 1 | full | 0.843531 ± 0.004032 (n=3) |
| 512KiB | mod384 | 1 | full | 0.064953 ± 0.000000 (n=3) |
| 4608B | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 4608B | mod384 | 1 | full | 0.942623 ± 0.000000 (n=3) |
| 512B | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 512B | mod384 | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 512B | sns | 4 | full | 3.709677 ± 0.000000 (n=3) |

At S=2MiB / 1MiB, 1D (`mod384`) is DRAM-bound on 3 DMC × 1 bank (≈0.065 txn/cyc). SNS fills 384 DMC and hits the **1-port mapper ceiling** (1 txn/cyc); 4-port lifts that ceiling (≈3.71). Absolute txns/cycle is higher for SNS under this bbox — not a “win min/mean, lose absolute” case.

At S=512B both strategies are mapper-port bound on full mask (1.0 @ 1-port, 3.71 @ 4-port). `rand1/16` and `third` drop SNS below the port ceiling (PE retry + fewer live banks).

S=512KiB SNS @ 1-port full is 0.844 txn/cyc (below the 1.0 ceiling) vs mod384 0.065 — still a reduced-bbox H-DRAM-BB number, not an envelope 0.85.

S=4608B is its own BW row (not folded). Cycle occupancy n_DMC on the 256-point AP ≠ occupancy-table 384; do not mix the two.

Refresh is not modeled. Warm-up discarded the first 10% of completions (cold row-buffer prefix).

## Discrepancy

None on occupancy (`|T3−T2|/T2 = 0` on every signed cell). T2 has no cycle BW column; T3 does not invent one for T2.
T3 BW remains 假设 H-DRAM-BB and is not signed as the 120-core / Q_tot=15360 envelope 0.85.
