# T3 report · P-0198/M-4 AODI

Smoke: `python3 sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903`

Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `holes.csv`, `bw_ci.csv`, `t2_vs_t3_t_mix.png`, `hole_buckets.png`, `summary.json`.

Seed **20260903**. Trials `SEED+i` (n=3). Clock UNKNOWN — no TB/s, no silicon ±15%.
card-claim **0.70–0.95× / 0.95–1.05× is NOT measured** (director did not sign). 0.85 is a pass bar, not a mean.

T2 `models/P-0198/M-4/` is **not on main** (draft PR #65). This tree does not land those files. Compare uses signed audit pins + spec §3 formulas.

**Keep separate:** M-1 CBC was **淘汰** at T3 (PR #62 / #64). M-2 CSR and M-5 CRRF are other in-flight T3 builds. Ablation is **deflect-off** on this card only. No mixed ranking or shared speedup.

## Scope

Cycle-accurate: same-cycle 2×2 × node × CHI `{Req,Rsp,Snp,Dat}`, inject-hole with busy mask on the same beat, hole buckets (asymmetric vs dual-busy), per-packet φ (not Σage), AGE_MAX, independent Rejoin, deflect-off ablation, opposite-ring util + completions.

Black box (`假设 H-RING-BB`): hop=1, one flit per 512 B txn, RBRG / HBM / coherence / D2D omitted, outstanding=16 (not envelope rd 512 / wr 256), 12 top nodes (2 bottom not on the smoke ring).

Not modeled: gem5; third highway slot; cross-CHI deflect.

## Seeds / CI

SEED=20260903. Makespan / p_inj cells are `mean ± 95% CI (n=3)`.
Occupancy is deterministic given (arm, class, seed) on this driver.

## Dr.Sim checklist

| # | Must-verify | Status |
|---|-------------|--------|
| 1 | Same-cycle 2×2; single-side empty+pending ⇒ hole; dual-busy ⇒ hole≡0 | **yes** — `truth_row` / `plan_xbar`; hard assert |
| 2 | Per-packet φ, not Σage | **yes** — `t2_phi_walk` age_end=1; cycle tracks per-tid φ |
| 3 | deflect-off column; opposite util + completions | **yes** — `cycles.csv` / `occupancy.csv` |
| 4 | Hole buckets asymmetric vs dual-busy | **yes** — `holes.csv` |
| 5 | alltoall dual-busy-sat separate; expected gain ≈0 | **yes** — plus forced `dual-busy-sat` row |
| 6 | Warm-up; envelope matching sibling sims | **yes** — ≥1 lap; 8 classes; night adds 12+2 |

## T2 vs T3

Signed T2 pins (audit; not T3):

| Pin | T2 signed | T3 | flag>30% |
|-----|-----------|----|----------|
| hole_dual | 0 | 0 (all rows) | no |
| φ→0 age_end | 1 | 1 (`t2_phi_walk`) | no |
| deflect-off HARD | True | see per-class `deflect_off_hard_t3` | — |
| alltoall T_mix | 1.0 | cycle ms_on/ms_off (separate row) | see `t2_compare.csv` |
| gather/reduce T_mix | 0.8448 | cycle ms_on/ms_off | see `t2_compare.csv` |
| uniform_read T_mix | 0.8770 | cycle ms_on/ms_off | see `t2_compare.csv` |
| card-claim | 0.70–0.95× / 0.95–1.05× | **NOT measured** | — |

Numbers below are filled after the signed smoke. If `|T3−T2|/T2 > 30%` the T3 number stands — do not substitute T2.

## Reproduce

```bash
python3 sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-4/tests
python3 sims/P-0198/M-4/sim.py --class gather --arm AODI-on --seed 20260903
```

评估审计: review `results/t2_compare.csv` + `holes.csv` + the >30% section (post-smoke) before weekly report / T4. Do not open T4 from this PR.
