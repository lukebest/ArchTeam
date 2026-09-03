# T3 report · P-0106/M-5 AffineRebind

Smoke: `python3 sims/P-0106/M-5/sweep.py --mode smoke --seed 20260903 --n-trials 3`
Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `gcd_table.csv`, `cycles.csv`, `bw_ci.csv`, `t2_vs_t3_cls_mean.png`.

## Scope

Cycle-accurate CSR + XOR_fold6 PIN + true `mod n` + 48-wire kth-one + card α search.
DRAM is 假设 H-DRAM-BB. REPAIR (fence+drain + CSR fill) completes before RUN.
T2 is occupancy-only; like-to-like compare is `cls_mean` / `n_bank` / `dead`.
`reviews/P-0106/M-5/t2_audit.md` was not in-tree; Dr.Sim + T2 spec were the must-verify list.

## Seeds / CI

SEED=20260903. Trials `SEED+i`. Every BW cell is `mean ± 95% CI (n=trials)`.
Occupancy is deterministic given (mask, stride, strategy) → CI width 0 on cls_mean.

## T2 vs T3 occupancy (smoke, issued I=min(K,Q_tot))

S=2MiB snapshot (three-mask table):

| mask | skip-dead cls | modn-α=1 cls | minimax cls | dead | T2 rel_err |
|------|---------------|--------------|-------------|------|------------|
| full-good | 9.3333 | 9.3333 | 9.3333 | 0 | 0 |
| n=40 | 9.3333 | 10.6667 | 10.6667 | 0 | 0 |
| 3-biased (n=32) | 9.2500 | 10.6667 | 10.6667 | 0 | 0 |

n_bank: full-good 3584=3584 (gain vs no-rebind ≈0). n=40: skip-dead 3584 vs mod-n 4096.
α_minimax = 1 on these n (gcd identity: search is a constant). True α=1 column matches minimax (rel-diff=0 < 5%).

All smoke occupancy rows: **flag_gt_30pct = 0**. Dead hits = 0.

## gcd table vs XOR_fold6

`results/gcd_table.csv` prints `classes_AP = n/gcd(S_g,n)` (integer AP sanity).
At n=40, S=2MiB: `classes_AP=5` but netlist `cls_mean=10.6667`. That gap is **legal**: `g` is XOR_fold6 on 64 points, not `Z/nZ`. T2 reports the same netlist number. We did not substitute the AP table for silicon g, and we did not retune taps.

Uniform 25% (`n=36`) still has factor 3 — not treated as 3-adic. 3-adic only from the 3-residue-biased column.

## Cycle BW (假设 H-DRAM-BB, decode_lat=2, csr_ports=1, 256-point AP, warmup 10%)

| S | mask | strategy | txns/cycle |
|---|------|----------|------------|
| 2MiB | n=40 | skip-dead | 0.477178 ± 0.000000 (n=3) |
| 2MiB | n=40 | modn-a1 | 0.500000 ± 0.000000 (n=3) |
| 2MiB | n=40 | minimax | 0.500000 ± 0.000000 (n=3) |
| 2MiB | full-good | skip-dead / a1 / minimax | 0.477178 ± 0.000000 (n=3) |
| 2MiB | 3-biased | skip-dead | 0.477178 ± 0.000000 (n=3) |
| 2MiB | 3-biased | modn-a1 / minimax | 0.500000 ± 0.000000 (n=3) |
| 512B | all smoke cells | all | 0.500000 ± 0.000000 (n=3) |

2-cycle decode × 1 CSR port caps throughput at 0.5 txn/cyc. On that ceiling, n=40 / 3-biased `mod n` is slightly above skip-dead at S=2MiB (0.500 vs 0.477) — class-count ×3 is **not** BW ×3. Full-good gain vs no-rebind ≈0 on both occupancy and this bbox BW.

No GB/s. μ_d UNKNOWN. 0.85 is the problem pass line, not a measured mean.

## Discrepancy

None on occupancy (`|T3−T2|/T2 = 0`). T2 has no cycle BW column.
The AP vs netlist class-count gap is documented above and matches T2; it is not a T3 bug and we did not “pick” the AP number.
