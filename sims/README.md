# sims/ — Tier 3 cycle-level simulators

Batch A (T2-audited DRAM mappers): **P-0105/M-4 SNS** and **P-0106/M-5 AffineRebind**.

P-0198 new cards (DV200 `tests/soc_sim` / `github:lukebest/bufferless-ring-noc`; **not** team-384dmc):

- **P-0198/M-4 AODI** — `sims/P-0198/M-4/`. Ablation vs **deflect-off** only.
- P-0198/M-1 CBC was **淘汰** at T3 (PR #62 / #64). Not in this tree. Do not mix.
- P-0198/M-2 CSR and P-0198/M-5 CRRF are separate in-flight T3 builds. Do not mix conclusions, ranking, or shared speedup.

Mechanism cards and T2 models are frozen (read-only). T2 AODI (`models/P-0198/M-4/`) is draft PR #65 and is **not** landed here.

`reviews/*/t2_audit.md` was not in-tree at implementation time. Frozen inputs used:
T2 spec/model (read-only fetch for compare), T1 `Dr.Sim.md` (must-verify list), problem YAML.

No in-repo `team-interleave-microbench` trace. SNS / Affine use `sims/_lib/workloads.py`.
AODI uses a ring-class synthetic driver in `sims/P-0198/M-4/sim.py`. **SEED=20260903**.

Shared helpers in `sims/_lib/`: DRAM black box (假设 H-DRAM-BB), CI, T2 importer, AP generator.
Results live next to each sim (`sims/P-0105/M-4/results/`, `sims/P-0106/M-5/results/`,
`sims/P-0198/M-4/results/`).
FUNNEL.md does not define `results/P-xxxx/`; we did not invent that tree.

## 21:00 sweep — exact commands

From repo root, after `pip install -r sims/requirements.txt`:

```bash
# smoke (small N, writes tables + T2 overlay plot; minutes)
python3 sims/P-0105/M-4/sweep.py --mode smoke --seed 20260903 --n-trials 3 --out sims/P-0105/M-4/results
python3 sims/P-0106/M-5/sweep.py --mode smoke --seed 20260903 --n-trials 3 --out sims/P-0106/M-5/results
python3 sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903 --n-trials 3 --out sims/P-0198/M-4/results

# night (capacity / ports / policy variants)
python3 sims/P-0105/M-4/sweep.py --mode night --seed 20260903 --n-trials 5 --out sims/P-0105/M-4/results
python3 sims/P-0106/M-5/sweep.py --mode night --seed 20260903 --n-trials 5 --out sims/P-0106/M-5/results
python3 sims/P-0198/M-4/sweep.py --mode night --seed 20260903 --n-trials 5 --out sims/P-0198/M-4/results
```

One-liner tests:

```bash
python3 -m pytest
```

Every printed BW number is `mean ± 95% CI` over the seeded trials (`SEED+i`).
Occupancy vs T2 is bit-exact on the mapper; if `|T3−T2|/T2 > 30%` the sweep flags it and does **not** substitute the T2 number.
Absolute GB/s are not printed (μ_d UNKNOWN). 0.85 is the problem pass line, not a measured mean.

## What is cycle-accurate vs black-box

| Card | Cycle-accurate | Black-box (parameterized latency) |
|------|----------------|-----------------------------------|
| SNS | 12b shear, 256×8 ROM, XOR, fold384, bitmap+PE | DRAM tRCD/tCL/tFAW/…, cores, HA, refresh |
| AffineRebind | CSR 1R, XOR_fold6, `mod n`, kth-one, α search, REPAIR-before-RUN | same DRAM bbox, cores, HA, refresh |
| AODI (P-0198/M-4) | same-cycle 2×2, hole buckets, per-packet φ, AGE_MAX, Rejoin | hop=1, flit=txn, RBRG/HBM/coherence, clock |
