# T3 report · P-0198/M-1 CBC

Smoke: `python3 sims/P-0198/M-1/sweep.py --mode smoke --seed 20260903`

Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `inject.csv`, `dual_tenant.csv`, `bw_ci.csv`, `t2_vs_t3_ratio.png`, `steal_raw_fail.png`, `summary.json`.

Seed **20260903**. Trials `SEED+i`. Clock UNKNOWN — no TB/s, no silicon ±15%.

Numbers below are filled after the signed smoke run. card-claim **0.55–0.85× is NOT measured**.

## Scope

Cycle-accurate Bubble FSM × node × direction × four CHI rings, 64×8 calendar + phase, tag/age, same-cycle steal/raw/fail.
Black box: hop=1, flit=txn, RBRG/HBM/coherence, outstanding=16 (not envelope 512/256).
T2 model.py is not on main (PR #54). Compare uses signed audit pins + spec §3.

Do not edit `mechanisms/`, `reviews/`, T2 models, or `FUNNEL.md`.

## Seeds / CI

SEED=20260903. Every makespan / p_inj cell is `mean ± 95% CI (n=trials)`.
Occupancy is a function of (arm, class, seed).

## Dr.Sim checklist

| # | Must-verify | Status |
|---|-------------|--------|
| 1 | FSM IDLE/WATCH/EMIT/HOLD × node × dir × 4 rings | yes (cycle tick, not mean ρ) |
| 2 | 64×8 lookup + phase; 1R / lookup_lat | yes |
| 3 | tag/age hop-by-hop + cluster hist | yes |
| 4 | steal / raw-inject / fail separate | yes (`inject.csv`) |
| 5 | warmup ≥ one lap | yes |
| 6 | no harness arrival-oracle epoch | yes (`oracle_used=False`) |

P2P and collective duties are **never averaged**.

## T2 vs T3 (to be filled from smoke)

Signed T2 pins (do not treat as T3):

| Pin | T2 |
|-----|-----|
| sum_ok | True |
| H-INJ-DOM d=1/4 | 0.7368 |
| H-INJ-DOM d=1/2 | 0.5833 |
| HARD-1 | 537.2 > 313.4 |
| dual-tenant | 1.3333 / 2.0000 fail_T |
| card-claim | 0.55–0.85× **NOT signed** |

If `|T3−T2|/T2 > 30%`, T3 stands; causes go here after the run.

## Architect feedback

(filled after smoke if the mechanism is unrealizable as written)

## Reproduce

```bash
python3 sims/P-0198/M-1/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-1/tests
```
