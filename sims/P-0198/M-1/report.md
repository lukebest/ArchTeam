# T3 report · P-0198/M-1 CBC

Smoke: `python3 sims/P-0198/M-1/sweep.py --mode smoke --seed 20260903`

Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `inject.csv`, `dual_tenant.csv`, `bw_ci.csv`, `t2_vs_t3_ratio.png`, `steal_raw_fail.png`, `summary.json`.

Seed **20260903**. Trials `SEED+i` (n=3). Clock UNKNOWN — no TB/s, no silicon ±15%.
card-claim **0.55–0.85× is NOT measured** (director did not sign). 0.85 is a pass bar, not a mean.

T2 `models/P-0198/M-1/` is **not on main** (draft PR #54). This tree does not land those files. Compare uses signed audit pins (FUNNEL / PR #56) + spec §3 formulas.

## Scope

Cycle-accurate: Bubble FSM `IDLE/WATCH/EMIT/HOLD` × node × CW/CCW × CHI `{Req,Rsp,Snp,Dat}` (96 FSMs at N=12), 64×8 calendar 1R + phase, 1b tag + 4b age, cluster-length histogram, same-cycle steal / raw-inject / fail.

Black box (`假设 H-RING-BB`): hop=1, one flit per 512 B txn, RBRG / HBM / coherence / D2D omitted, outstanding=16 (not envelope rd 512 / wr 256), 12 top nodes (2 bottom not on the smoke ring).

Not modeled: gem5; message-arrival oracle; minting extra highway slots.

## Seeds / CI

SEED=20260903. Makespan / p_inj cells are `mean ± 95% CI (n=3)`.
Occupancy is deterministic given (arm, class, seed) on this driver.

## Dr.Sim checklist

| # | Must-verify | Status |
|---|-------------|--------|
| 1 | FSM IDLE/WATCH/EMIT/HOLD × node × dir × 4 rings | **yes** — per-cycle tick, 96 FSMs; not mean ρ |
| 2 | 64×8 lookup + phase; 1R / lookup_lat | **yes** — smoke `lookup_lat=1` |
| 3 | tag/age hop-by-hop + cluster hist | **yes** — `mean_cluster` 1.0–5.7 on CBC gather |
| 4 | steal / raw-inject / fail separate | **yes** — `inject.csv`; gather CBC-coll-1/4: 32 / 32 / 149 |
| 5 | warmup ≥ one lap | **yes** — 12 cycles before issue/sample |
| 6 | no harness arrival-oracle epoch | **yes** — `oracle_used=False`; software-posted phase only |

P2P duties `{1/16,1/8}` and collective duties `{1/4,1/2}` are **never averaged**.

## T2 vs T3

Signed T2 pins (audit; not T3):

| Pin | T2 signed | T3 smoke (gather / dual) | \|T3−T2\|/T2 | flag>30% |
|-----|-----------|--------------------------|--------------|----------|
| sum_ok | True | True on all 168 compare rows; `delta_rho_empty=0` | 0 | no |
| H-INJ-DOM d=1/4 | 0.7368 | **1.0000** (`p_inj_off/p_inj_cbc`, gather) | 0.357 | **yes** |
| H-INJ-DOM d=1/2 | 0.5833 | **1.0000** | 0.714 | **yes** |
| HARD-1 T_off > T_cbc | 537.2 > 313.4 (ns) | cycle makespan **34 ≯ 34** | n/a (units differ) | inequality **fails** |
| dual-tenant d_A=1/4 | 1.3333 fail_T | makespan ratio **2.59** fail_T=True; p_inj ratio 0.85 | 0.36 on p_inj | **yes** (quant); fail_T agrees |
| dual-tenant d_A=1/2 | 2.0000 fail_T | makespan ratio **2.59** fail_T=True; p_inj ratio 0.85 | 0.57 on p_inj | **yes** (quant); fail_T agrees |
| card-claim | 0.55–0.85× | **NOT measured** (T3 gather ratio = 1.00) | — | printed as card-claim only |

`t2_compare.csv` has **105** `flag_gt_30pct=True` rows (168 total). T3 numbers were **not** replaced by T2.

### Conservation / no-mint (like-to-like)

Gather trial 0, all arms: `ρ_empty=0.746429`, `delta_rho_empty=0.000000`, `sum_ok=True`.
CBC only retags empty → bubble (`ρ_bubble` 0.107–0.237). H-CBC-empty-supply holds at cycle level.

### Why H-INJ-DOM / HARD-1 miss T2 by >30%

T2 `T_hat/T_off = η0 / ((1−d)η0 + d·η)` with `η0=0.35`, `η=0.85` (H-PLACE).
Cycle fabric: a bubble is an empty slot with a tag. Local inject already uses any empty (raw or steal). Single-tenant gather therefore has **identical** `p_inj=0.300469`, fail=149, makespan=34 on every arm including calendar-off.

Cause: **H-PLACE is not a distinct geometric motion on a bufferless ring.** Raw empties already circulate with the same hop law as bubbles. Tagging does not create a new inject opportunity. T2's η>η0 gain is a mean-field assumption, not observed here. This is a model finding, not a silent substitution.

Steal counts do rise with duty (gather trial 0: 0 / 15 / 30 / 32 / 28) while `steal+raw=64` stays fixed — redistribution, not mint.

### Dual-tenant (Sys)

A = gather (collective), B = uniform_read, same outstanding pool.

| trial | d_A | T3 ms_B dual/solo | T3 p_inj solo/dual | T2 | fail_T |
|-------|-----|-------------------|--------------------|----|--------|
| 0 | 1/4 | 44/17 = 2.59 | 0.85 | 1.33 | True |
| 0 | 1/2 | 44/17 = 2.59 | 0.85 | 2.00 | True |
| 1 | both | 43/13 = 3.31 | 0.65 | 1.33 / 2.00 | True |
| 2 | both | 45/15 = 3.00 | 0.77 | 1.33 / 2.00 | True |

Cycle **fail_T=True** (Sys <10% worsen is violated) — same qualitative probe as T2.
Quantitative 1.3333 / 2.0000 is T2's `1/(1−d)` empty-partition, not cycle makespan. B's p_inj can rise in dual (fewer recorded attempts while queued behind A) while B makespan still blows up. Do not treat T2 1.33/2.0 as measured.

d_A=1/4 and 1/2 produced the **same** dual ratios in this bbox: A already saturates the shared inject/outstanding path; extra bubble duty does not change B's wait. That is additional evidence that the T2 d-linear partition is not the cycle mechanism.

### ρ_bubble vs T2 `d·ρ_empty`

T2 partition assumes H-EMIT-SAT tagging of fraction `d` of empties. Cycle FSM + W=8 + 16-cycle phase + age + steal leaves `ρ_bubble` near 0.11–0.24 on gather, vs `d·0.746` (0.047–0.373). Several rows flag. T3 occupancy stands.

## Cycle BW (reduced bbox)

Selected gather / uniform_read (`lookup_lat=1`, n=3):

| class | arm | makespan | p_inj |
|-------|-----|----------|-------|
| gather | all seven arms | 34.00 ± 0.00 | 0.300469 ± 0.000000 |
| uniform_read | all seven arms | 16.33 ± 3.46 | 0.506730 ± 0.011380 |

Broadcast / allgather / allreduce / alltoall / reduce likewise share one makespan across arms (see `cycles.csv`). Class-mean speedup is **not** reported.

Goodput is B/cycle under H-RING-BB. Clock UNKNOWN; YAML 2.8–3.4 TB/s collapse band is **not** reproduced as TB/s.

## Architect feedback (do not change the card)

Structured, for the architect — T3 does not "fix" `mechanisms/P-0198/M-1.md`.

1. **No mint (confirms Archi H-CBC-empty-supply).** Cycle `Δρ_empty=0`. Card §1 "制造并循环空槽" is tag redistribution only. If T4 is ever opened, do not claim manufactured highway slots.

2. **HARD-1 fails at cycle level.** calendar-off gather is not worse than CBC. Little-law / H-INJ-DOM 0.55–0.85× is not realized without an extra placement oracle. Unrealizable as a single-tenant inject-fail cure on this bufferless ring.

3. **Dual-tenant ABI hole is real and larger than T2.** Collective-over-P2P priority + shared outstanding yields B makespan ×2.6–3.3. Cannot be a default whole-fabric policy (Sys T1). T2's `1/(1−d)` understates the wait.

4. **W vs duty frame vs SRAM latency.** If WATCH requires *W consecutive mandatory* ticks, `lookup_lat=1` plus a 8/16 duty window never reaches EMIT. This sim counts W as cycles-since-bubble (card wording) so the FSM is exercisable. The card should nail that interpretation.

5. **AGE_MAX=15 vs 25-CS bottom ring** (T2 spec note): a bubble dies before one bottom lap. Smoke did not run N=25; night arm is in `sweep.py --mode night`.

## Reproduce

```bash
python3 sims/P-0198/M-1/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-1/tests
python3 sims/P-0198/M-1/sim.py --class gather --arm CBC-coll-1/4 --seed 20260903
```

评估审计: review `results/t2_compare.csv` + `dual_tenant.csv` + this discrepancy section before weekly report / T4. Do not open T4 from this PR.
