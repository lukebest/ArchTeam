# T3 · P-0106/M-5 AffineRebind

Cycle-level SimPy model of per-DMC `(α,β,n)` + kth-one. Baseline (`skip-dead`, `stack`) and proposal (`modn-a1`, `minimax`) share **one driver** and **one AP workload**. REPAIR (fence+drain + α search) finishes before RUN.

## One-command repro

```bash
python3 sims/P-0106/M-5/sweep.py --mode smoke --seed 20260903 --n-trials 3
python3 -m pytest sims/P-0106/M-5/tests
python3 sims/P-0106/M-5/sim.py --strategy minimax --mask n40 --stride 2097152 --n-pts 256
```

Seed: **20260903**. Trials use `20260903 + trial`.

## Modeled vs black-box

**Cycle-accurate (Dr.Sim must-verify):**

1. 384×(α,β,n) CSR, 1R on the decode path (`--csr-ports` sweeps capacity).
2. `g = XOR_fold6(G)` with T2-pinned taps `g[i] = XOR G[i+6k]` (`i+6k ≤ 55`). Never retuned.
3. DMC via 假设 H-UP-DMC: 9-bit XOR-fold then `x if x<384 else x-384`. Not silent `G mod 384`.
4. `slot = (α·g+β) mod n` — true variable modulus, not mod 48 then mask.
5. kth-one: 48-wire prefix, index of the `slot`-th live bit. 1 cycle of the 2-cycle decode.
6. α filled by card search `{1,5,…,47}`, `gcd(α,n)=1`, `score=max_S gcd(α·S_g,n)`, tie → smallest α.
   A **true α=1 column** is always present (`modn-a1`). Hand-writing α=1 is not labeled “rebound”.
7. gcd table (evaluation script, same CSR): `n, α, gcd, classes_AP=n/gcd`. Sanity only — not a substitute for XOR_fold6.
8. Masks reported separately: full-good, n=40 uniform (L=32+spare), optional 6.25/12.5/25%, 3-residue-biased.
   Uniform 25% (`n=36`) still has factor 3 — **not** a 3-adic test.
9. Dead hits = 0 hard assert on live paths. No cross-DMC steal. `n=0` poisons that DMC.
10. REPAIR before traffic. Warm-up drops first 10% of completions. Refresh not modeled.

**Black box:** DRAM timings (`假设 H-DRAM-BB`), page policy, cores. Clock / μ_d UNKNOWN. No GB/s.
Class-count ×3 is not BW ×3.

## Workload

No in-repo trace. Synthetic AP + Doc strides `{512B, 3×512B, 9×512B, 512KiB, 1MiB, 2MiB}`.
Generator: `sims/_lib/workloads.py`.

## Sweep knobs

`--mode night` scans CSR ports `{1,4}`, decode latency `{2,1}`, β `{0, dmc[5:0]}`, page `{open,close}`.

## T2 compare

`models/P-0106/M-5/model.py` is imported read-only. Compare `cls_mean`, `n_bank`, `dead` (like-to-like).
If `|T3−T2|/T2 > 30%`, inspect this simulator; do not silently pick T2.
`stack` has no T2 column (sibling negative control only).

Results: `results/occupancy.csv`, `t2_compare.csv`, `gcd_table.csv`, `cycles.csv`, `bw_ci.csv`, `t2_vs_t3_cls_mean.png`, `summary.json`.
See `report.md`.
