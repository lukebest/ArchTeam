# T3 report · P-0106/M-5 AffineRebind

Smoke (signed occupancy fixture):
`python3 sims/P-0106/M-5/sweep.py --mode smoke --seed 20260903 --n-trials 3`

Night (2026-09-03):
`python3 sims/P-0106/M-5/sweep.py --mode night --seed 20260903 --n-trials 3`

**Signed smoke occupancy** (do not overwrite): `results/occupancy.csv`, `results/t2_compare.csv`.
**Night occupancy** (distinct): `results/night/occupancy.csv`, `results/night/t2_compare.csv`.
Night cycle BW: `results/cycles.csv`, `results/bw_ci.csv`, `results/summary.json`.
`gcd_table.csv` remains AP sanity and is **not** netlist coverage.

T3 audit (`reviews/P-0106/M-5/t3_audit.md`) bounced the first smoke as incomplete:
occupancy / `t2_compare` had only `{512B, 2MiB}`. The signed smoke fixture expands
strides to `{512B, 3×512B, 9×512B, 2MiB}`. Night writes occupancy to `results/night/`
so that fixture stays distinct.

## Scope

Cycle-accurate CSR + XOR_fold6 PIN + true `mod n` + 48-wire kth-one + card α search.
DRAM is 假设 H-DRAM-BB. REPAIR (fence+drain + CSR fill) completes before RUN.
T2 is occupancy-only; like-to-like compare is `cls_mean` / `n_bank` / `dead`
against frozen `models/P-0106/M-5/model.py` with `I=min(K,Q_tot)`.
XOR_fold6 taps were not changed. α=1 is a true `modn-a1` column, not labeled rebound.

## Seeds / CI

SEED=20260903. Trials `SEED+i`. Every BW cell is `mean ± 95% CI (n=trials)`.
Occupancy is deterministic given (mask, stride, strategy) → CI width 0 on cls_mean.

## T2 vs T3 occupancy (smoke, issued I=min(K,Q_tot))

36 XOR_fold6 netlist rows: S∈{512B, 3×512B, 9×512B, 2MiB} ×
mask∈{full-good, n=40, 3-biased(n=32)} × {skip-dead, modn-a1, minimax}.
All **flag_gt_30pct = 0**, **rel_err_cls = rel_err_n_bank = 0**, **dead = 0**.

S=2MiB (unchanged vs first smoke):

| mask | skip-dead cls / n_bank | modn-α=1 cls / n_bank | minimax cls / n_bank | dead | T2 rel_err |
|------|------------------------|-----------------------|----------------------|------|------------|
| full-good | 9.3333 / 3584 | 9.3333 / 3584 | 9.3333 / 3584 | 0 | 0 |
| n=40 | 9.3333 / 3584 | 10.6667 / 4096 | 10.6667 / 4096 | 0 | 0 |
| 3-biased (n=32) | 9.2500 / 3552 | 10.6667 / 4096 | 10.6667 / 4096 | 0 | 0 |

S=512B (unchanged vs first smoke): same three-mask table as 2MiB
(full-good 9.3333/3584; n=40 skip 9.3333/3584 vs modn 10.6667/4096;
3-biased skip 9.2500/3552 vs modn 10.6667/4096).

S=3×512B (new signed netlist rows):

| mask | skip-dead cls / n_bank | modn-α=1 cls / n_bank | minimax cls / n_bank | dead | T2 rel_err |
|------|------------------------|-----------------------|----------------------|------|------------|
| full-good | 8.9840 / 3369 | 8.9840 / 3369 | 8.9840 / 3369 | 0 | 0 |
| n=40 | 8.9840 / 3369 | 10.1147 / 3793 | 10.1147 / 3793 | 0 | 0 |
| 3-biased (n=32) | 8.8987 / 3337 | 10.1147 / 3793 | 10.1147 / 3793 | 0 | 0 |

S=9×512B (new signed netlist rows):

| mask | skip-dead cls / n_bank | modn-α=1 cls / n_bank | minimax cls / n_bank | dead | T2 rel_err |
|------|------------------------|-----------------------|----------------------|------|------------|
| full-good | 8.2492 / 2648 | 8.2492 / 2648 | 8.2492 / 2648 | 0 | 0 |
| n=40 | 8.2492 / 2648 | 9.0156 / 2894 | 9.0156 / 2894 | 0 | 0 |
| 3-biased (n=32) | 8.2305 / 2642 | 9.0156 / 2894 | 9.0156 / 2894 | 0 | 0 |

n_bank full-good = skip-dead = minimax on every S (gain vs no-rebind ≈0).
Primary contrast remains skip-dead vs mod n α=1 (n=40 / 3-biased), not α search.
α_minimax = 1 on these n; true α=1 column matches minimax (rel-diff=0 < 5%).
Hand-written α=1 is not labeled “rebound”.

## gcd table vs XOR_fold6

`results/gcd_table.csv` prints `classes_AP = n/gcd(S_g,n)` (integer AP sanity).
It lists 3×512B / 9×512B but that is **not** occupancy coverage.

Netlist `cls_mean` (XOR_fold6 + kth-one) is a different column:

| S | mask | classes_AP | netlist cls_mean (modn-a1) |
|---|------|------------|----------------------------|
| 2MiB | n=40 | 5 | 10.6667 |
| 3×512B | n=40 | 40 | 10.1147 |
| 3×512B | full-good | 16 | 8.9840 |
| 9×512B | n=40 | 40 | 9.0156 |
| 9×512B | full-good | 16 | 8.2492 |

The AP vs netlist gap is legal: `g` is XOR_fold6 on 64 points, not `Z/nZ`.
T2 reports the same netlist numbers. We did not substitute the AP table for silicon g,
and we did not retune taps.

Uniform 25% (`n=36`) still has factor 3 — not treated as 3-adic. 3-adic only from the 3-residue-biased column.

## Cycle BW (假设 H-DRAM-BB, night reduced bbox, AP=512)

Night bbox: **8 cores × 16 outstanding**, AP **512** points, warmup 10%,
`csr_ports∈{1,4}`, `decode_lat∈{2,1}`, `beta∈{zero,dmc}`, `page∈{open,close}`,
masks `{full-good, n=40, 3-biased(n=32)}`, cycle S `{512B, 3×512B, 2MiB}`,
n_trials=3, seed=`20260903+trial`.
This is **not** the 120-core / `Q_tot=15360` envelope. 0.85 is the problem pass
line, **not** a measured mean; reduced-bbox night is **not** signed as envelope 0.85.
Every cell `mean ± 95% CI (n=3)`. No GB/s. μ_d UNKNOWN. `hypothesis=H-DRAM-BB`.

Selected cells (`decode_lat=2`, `csr_ports=1`, `beta=zero`, `page=open`) from
`results/bw_ci.csv`:

| S | mask | strategy | txns/cycle |
|---|------|----------|------------|
| 2MiB | n=40 | skip-dead | 0.489362 ± 0.000000 (n=3) |
| 2MiB | n=40 | modn-a1 | 0.500000 ± 0.000000 (n=3) |
| 2MiB | n=40 | minimax | 0.500000 ± 0.000000 (n=3) |
| 2MiB | full-good | skip-dead / a1 / minimax | 0.489362 ± 0.000000 (n=3) |
| 2MiB | 3-biased | skip-dead | 0.489362 ± 0.000000 (n=3) |
| 2MiB | 3-biased | modn-a1 / minimax | 0.500000 ± 0.000000 (n=3) |
| 512B | all night cells at this bbox | all | 0.500000 ± 0.000000 (n=3) |
| 3×512B | all night cells at this bbox | all | 0.500000 ± 0.000000 (n=3) |

2-cycle decode × 1 CSR port caps throughput at 0.5 txn/cyc. On that ceiling,
3×512B sits at 0.500 for every mask/strategy — class-count ×3 is **not** BW ×3
(n=40 3×512B occupancy 10.1147/8.9840 ≈ ×1.13; cycle BW ratio = 1.00, both at the cap).
Cycle `cls_mean` at `|I|=512` must not be mixed with full-occupancy `cls_mean`.
Cycle `dead=0`, `repair_done=True`.

Full-good gain vs no-rebind ≈0 on occupancy; on this 512-point bbox the three
full-good strategies share `0.489362 ± 0.000000 (n=3)`.

## Discrepancy

None on occupancy (`|T3−T2|/T2 = 0` on all 36 signed rows, including 3×512B / 9×512B).
T2 has no cycle BW column.
The AP vs netlist class-count gap is documented above and matches T2; it is not a T3 bug and we did not “pick” the AP number.
