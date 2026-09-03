# T3 · P-0105/M-4 SNS

Cycle-level SimPy model of Shear + Nonlinear S-box. Baseline (`mod384` / `low` / `high`) and proposal (`sns`) plus ablations (`shear`, `sbox`) share **one driver** and **one AP workload**.

## One-command repro

```bash
python3 sims/P-0105/M-4/sweep.py --mode smoke --seed 20260903 --n-trials 3
python3 -m pytest sims/P-0105/M-4/tests
python3 sims/P-0105/M-4/sim.py --strategy sns --stride 2097152 --n-pts 256
```

Seed: **20260903**. Trials use `20260903 + trial`.

## Modeled vs black-box

**Cycle-accurate (Dr.Sim must-verify):**

1. `x' = (x + ((y<<3)−y)) & 0xFFF` — 12-bit truncate, not arbitrary precision.
2. 256×8 ROM = `u^5+u^3+u mod 256` (integer). Startup checksum `S(0..15)`.
3. `z = ROM[x'[11:4]] XOR y[7:0]`; `raw = (z<<4)|x'[3:0]`; fold384 coarse-q + one correction.
4. `bank_in = x'[9:4] mod 48` (6b window). Per-DMC bank histogram and `bank%8` kinds.
5. Ablations: shear-only; S-box(x[11:4]) only (must vary DMC id with phase at S=2MiB).
6. Base families reported separately: 512B-grain (`GRAIN_BASES`) and 2MiB-aligned (`ALIGNED_2MIB`). Signed smoke S=`{2MiB,1MiB,512KiB,4608B,512B}`; 4608B alone.
7. Partial-good: random 1/16 (3/48) and 1/3 residue. Bitmap + PE 1-cycle retry; S-box does not remap.
8. Inflight occupies mapper/DRAM slots by cycle. Warm-up drops the first 10% of completions (cold row-buffer prefix). Refresh is not modeled.

**Black box:** DRAM timings (`假设 H-DRAM-BB`: tRCD/tCL/tRP/tRAS/tRRD_L/tCCD_L/tFAW/tBURST), page policy, core issue (n_cores × outstanding). Clock / DRAM type / μ_d UNKNOWN. No GB/s.

**Not modeled:** HA packing, die floorplan, 120-core mapper replicas, buddy+ASLR allocator (Sys T1 condition — needs a different driver).

## Workload

No in-repo trace. Synthetic AP: `phys[i] = base + i*stride`, `W=2^33`, `I=min(K, Q_tot, --n-pts)`.
Generator: `sims/_lib/workloads.py` (stand-in for off-repo `team-interleave-microbench`).

## Sweep knobs

`--mode smoke` is the signed table: full T2 pass-pack S, `GRAIN_BASES` + `ALIGNED_2MIB`, all six mappers, plus cycle rows for `map_ports∈{1,4}` and PE masks `{full, rand1/16, third}` (假设 H-DRAM-BB). `--mode night` adds map latency `{1,2}`, page `{open,close}`, and B-low/B-high on the cycle driver.

## T2 compare

`models/P-0105/M-4/model.py` is imported read-only. Occupancy `n_DMC` / `n_bank` must match.
Covering 11/10/CV≈0.044 is printed as `COVERING_BOUND` and is **not** a golden SNS target.
If `|T3−T2|/T2 > 30%`, inspect this simulator; do not silently pick T2.

Results: `results/occupancy.csv`, `t2_compare.csv`, `cycles.csv`, `bw_ci.csv`, `t2_vs_t3_n_dmc.png`, `summary.json`.
See `report.md`.
