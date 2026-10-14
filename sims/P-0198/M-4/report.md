# T3 report · P-0198/M-4 AODI

Smoke: `python3 sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903`

Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `holes.csv`, `bw_ci.csv`, `t2_vs_t3_t_mix.png`, `hole_buckets.png`, `summary.json`.

Seed **20260903**. Trials `SEED+i` (n=3). Clock UNKNOWN — no TB/s, no silicon ±15%.
card-claim **0.70–0.95× / 0.95–1.05× is NOT measured** (director did not sign). 0.85 is a pass bar, not a mean.

T2 `models/P-0198/M-4/` is **not on main** (draft PR #65). This tree does not land those files. Compare uses signed audit pins + spec §3 formulas.

**Keep separate:** M-1 CBC was **淘汰** at T3 (PR #62 / #64). M-2 CSR and M-5 CRRF are other in-flight T3 builds. Ablation is **deflect-off** on this card only. No mixed ranking or shared speedup.

## Scope

Cycle-accurate: same-cycle 2×2 × node × CHI `{Req,Rsp,Snp,Dat}`, inject-hole with busy mask on the same beat, hole buckets (asymmetric vs dual-busy), per-packet φ (not Σage), AGE_MAX=8, independent Rejoin, deflect-off ablation, opposite-ring util + CW/CCW completions.

Black box (`假设 H-RING-BB`): hop=1, one flit per 512 B txn, RBRG / HBM / coherence / D2D omitted, outstanding=16 (not envelope rd 512 / wr 256), 12 top nodes (2 bottom not on the smoke ring).

Not modeled: gem5; third highway slot; cross-CHI deflect.

## Seeds / CI

SEED=20260903. Makespan / p_inj cells are `mean ± 95% CI (n=3)`.
Occupancy is deterministic given (arm, class, seed) on this driver.

## Dr.Sim checklist

| # | Must-verify | Status |
|---|-------------|--------|
| 1 | Same-cycle 2×2; single-side empty+pending ⇒ hole; dual-busy ⇒ hole≡0 | **yes** — `truth_row` / `plan_xbar`; hard assert. Forced dual-busy-sat: 288 dual-busy cycles, `hole_dual=0`, `hole_asym=0`, no inject |
| 2 | Per-packet φ, not Σage | **yes** — `t2_phi_walk` φ→0, `age_end=1`; cycle tracks per-tid φ / freeze |
| 3 | deflect-off column; opposite util + completions | **yes** — `cycles.csv` / `occupancy.csv` |
| 4 | Hole buckets asymmetric vs dual-busy | **yes** — `holes.csv`; every `hole_dual=0` |
| 5 | alltoall dual-busy-sat separate; expected gain ≈0 | **yes** — class row + forced `dual-busy-sat` row; never folded |
| 6 | Warm-up; envelope matching sibling sims | **yes** — ≥1 lap (12 cycles); 8 classes; night adds 12+2 |

P2P / collective / alltoall are **never averaged** into one pass number.

## T2 vs T3

Signed T2 pins (audit; not T3):

| Pin | T2 signed | T3 smoke | \|T3−T2\|/T2 | flag>30% |
|-----|-----------|----------|--------------|----------|
| hole_dual | 0 | **0** on all 24 compare rows + forced probe | 0 | no |
| φ→0 age_end | 1 | **1** (`t2_phi_walk(6,1,8,rejoin)`) | 0 | no |
| deflect-off HARD | True | gather/reduce/broadcast/allreduce **True** (34≥34, 41≥41, 23≥23); uniform / allgather / alltoall **False** | — | HARD fails where AODI lengthens last-completion |
| alltoall T_mix | 1.0 | trial 0 **1.529**; trial 1 **1.105**; trial 2 **1.294** (separate row) | 0.53 / 0.11 / 0.29 | **yes** (trial 0 only) |
| gather/reduce T_mix | 0.8448 | **1.0000** (34/34) | 0.184 | no |
| uniform_read T_mix | 0.8770 | 1.105 / 1.471 / 1.923 | 0.26 / 0.68 / 1.19 | **yes** (trials 1–2) |
| card-claim | 0.70–0.95× / 0.95–1.05× | **NOT measured** | — | printed as card-claim only |

`t2_compare.csv` has **8** `flag_gt_30pct=True` rows (24 total). T3 numbers were **not** replaced by T2.

Forced dual-busy-sat (sticky both rings): `hole_asym=hole_dual=0`, `deflect=0` on both arms. That is the Archi atom: **dual-busy ⇒ inject-hole≡0**. Traffic-class alltoall is **not** that atom — residual one-sided empties still produce `hole_asym` (12–15 on AODI-on).

### Why several T_mix rows miss T2 by >30%

T2 `T_mix` is H-INJ-DOM `p_off/p_on` mixed with an H-VICTIM tax at `H=6` hops (`η_use=0.25`). T3 `T_mix` is **last-completion / first-issue** on the same seeded txn list.

1. **Victim detour dominates last-completion.** A legal 1-cycle hole sends a near-dest transit flit the long way (up to 11 hops on N=12) plus a Rejoin wait. Makespan is the tail, not mean inject opportunity. T2's `extra/H` mix understates a single long victim.
2. **H-INJ-DOM is not last-completion.** Gather p_inj rises 0.300 → 0.356 (`hole_asym=43`) but makespan stays **34**. Sink serialization (one eject/dir/cycle into node 0) is unchanged. Rel_err vs 0.8448 is 18% — no flag — but the card-claim 0.70–0.95× band is **not** realized as makespan.
3. **alltoall is not Frechet c=+1 every cycle.** T2 closes `P(pref_only)` with `c=+1`. The cycle generator still has one-sided empties, so AODI fires (`hole_asym=12–15`) and migrates load onto the opposite ring (`ρ_opp` 0→0.06–0.08). Last-completion **worsens** (17→26 on trial 0). T2 expected gain ≈0 (`T_mix=1`); cycle shows **negative** gain. Still a **separate row** — not folded into 0.50–0.85×.
4. **uniform_read/write** are not a stable asym occupancy window. Random pairs + AODI create victims; T3 T_mix 1.11–1.92 vs T2 0.877. Flag. T3 stands.
5. **allgather** T3=1.24 vs T2=0.822 (rel_err 0.51) on every trial. Same victim-tail cause. Flag. T3 stands.

Opposite completions are split (`completions_cw` / `completions_ccw`); no silent drop (`dropped=0`, `illegal_third=0`). Do not read inject-success as the endpoint.

### Cycle makespan (reduced bbox)

Selected cells (`AGE_MAX=8`, n=3). Class-mean speedup is **not** reported.

| class | arm | makespan | p_inj | hole_asym (t0) |
|-------|-----|----------|-------|----------------|
| gather | deflect-off | 34.00 ± 0.00 | 0.300469 | 0 |
| gather | AODI-on | 34.00 ± 0.00 | 0.355556 | 43 |
| reduce | both | 34.00 ± 0.00 | same as gather | same |
| broadcast | both | 41.00 ± 0.00 | 1.000000 | 0 |
| allreduce | both | 23.00 ± 0.00 | 0.46 off / 0.58 on | 17 |
| allgather | deflect-off | 25.00 ± 0.00 | 0.488550 | 0 |
| allgather | AODI-on | 31.00 ± 0.00 | 0.369942 | 24 |
| alltoall (separate) | deflect-off | 17.67 ± 1.31 | 0.573456 | 0 |
| alltoall (separate) | AODI-on | 23.00 ± 2.99 | 0.567410 | 12 |
| uniform_read | deflect-off | 16.33 ± 3.46 | 0.506730 | 0 |
| uniform_read | AODI-on | 23.67 ± 2.61 | 0.486683 | 16–26 |

Goodput is B/cycle under H-RING-BB. Clock UNKNOWN; YAML 2.8–3.4 TB/s collapse band is **not** reproduced as TB/s.

## Architect feedback (do not change the card)

Structured, for the architect — T3 does not rewrite `mechanisms/P-0198/M-4.md`.

1. **Dual-busy hole≡0 holds.** Forced both-rings-full + pending inject never sets `inject-hole`. No third slot, no silent drop. The silicon contract that closed T1 is cycle-real.
2. **Asymmetric holes exist and do not shorten last-completion.** Gather/reduce fire 43 holes/run and raise p_inj, yet makespan is identical to deflect-off. H-INJ-DOM 0.8448 is a mean-field inject ratio, not a cycle tail. Unrealizable as a fan-in makespan cure on this bufferless ring without a placement rule that refuses to deflect near-dest flits.
3. **Residual alltoall holes are harmful, not ≈0.** Unless occupancy is *identically* dual-busy (the forced probe), AODI still deflects and the opposite ring pays. T2's "gain ≈0" is optimistic relative to last-completion; cycle T_mix is 1.11–1.53. Keep the separate row; do not advertise 0.95–1.05× as measured.
4. **deflect-off HARD fails on P2P / allgather / alltoall.** Attribution to AODI is allowed only where off ≥ on (gather/reduce/broadcast/allreduce). Elsewhere AODI is a tail regression.
5. **φ / Rejoin are conditional.** age_end=1 on the signed walk. Preferred-full freeze is implemented (wrong-ring wait, no side queue). That is delay, not progress — do not use Σage.

## Reproduce

```bash
python3 sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-4/tests
python3 sims/P-0198/M-4/sim.py --class gather --arm AODI-on --seed 20260903
```

评估审计: review `results/t2_compare.csv` + `holes.csv` + this discrepancy section before weekly report / T4. Do not open T4 from this PR.
