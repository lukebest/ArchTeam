# T3 · P-0198/M-1 CBC

Cycle-level SimPy model of Circulating Bubble Calendar on a bufferless bidirectional CHI ring.
Baseline (`calendar-off` / `duty=0`) and proposal (CBC duty arms) share **one driver** and **one seeded workload**.

Envelope: DV200 `tests/soc_sim` / `github:lukebest/bufferless-ring-noc`. **Not** team-384dmc / `team-interleave-microbench`.

## One-command repro

```bash
python3 sims/P-0198/M-1/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-1/tests
python3 sims/P-0198/M-1/sim.py --class gather --arm CBC-coll-1/4 --seed 20260903
```

Seed: **20260903**. Trials use `20260903 + trial`.

## Modeled vs black-box

**Cycle-accurate (Dr.Sim must-verify):**

1. Bubble FSM `IDLE/WATCH/EMIT/HOLD` × every node × CW/CCW × CHI `{Req,Rsp,Snp,Dat}`.
2. 64×8 calendar: high 4b duty density `k/16`, low 4b phase; 1R shared by ≤8 FSMs; `--lookup-lat` 0 (combo) or 1 (SRAM).
3. Bubble tag + 4b age; age++ per hop; `age≥15` → raw empty; cluster-length histogram.
4. Same-cycle arb: collective inject > P2P inject > bubble keep. Counts **steal / raw-inject / fail** are separate columns.
5. Warm-up ≥ one ring lap (`warmup_laps * N`) before sampling. App traffic is held until then.
6. Epoch = static table row / software-posted phase on the **issue** schedule. No message-arrival oracle.

**Black box (parameterized):** hop latency (smoke=1), one flit per txn (512 B), RBRG, HBM, coherence, bottom D2D, clock. Outstanding smoke=16 (not envelope rd 512 / wr 256).

**Not modeled:** gem5; harness-oracle epoch alignment; minting extra highway slots.

## Duty arms (never averaged)

| Arm | d | Role |
|-----|---|------|
| calendar-off | 0 | HARD-1 baseline |
| duty=0 | 0 | same first-order as off |
| CBC-P2P-1/16, CBC-P2P-1/8 | 1/16, 1/8 | P2P epoch |
| CBC-coll-1/4, CBC-coll-1/2 | 1/4, 1/2 | fan-in epoch |
| fixed-high-1/2 | 1/2 | no epoch switch |

## T2 compare

T2 `models/P-0198/M-1/` is **not on main** (draft PR #54). This tree does not land those files.
Compare tables use **signed audit** numbers (director / PR #56) plus spec §3 formulas:

- `sum_ok`
- H-INJ-DOM `T_hat/T_off`: d=1/4 → 0.7368; d=1/2 → 0.5833
- HARD-1: 537.2 > 313.4 (T2 ns; T3 reports the cycle inequality)
- dual-tenant: 1.3333 / 2.0000 `fail_T`
- card-claim **0.55–0.85× is NOT signed / NOT measured**

If `|T3−T2|/T2 > 30%`, the sweep flags the row and **does not** substitute the T2 number.

Results: `results/occupancy.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `inject.csv`, `dual_tenant.csv`, `bw_ci.csv`, `summary.json`.
See `report.md`.
