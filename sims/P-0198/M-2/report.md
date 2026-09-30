# T3 report · P-0198/M-2 CSR (Rendezvous–Grant)

Smoke: `python3 sims/P-0198/M-2/sweep.py --mode smoke --seed 20260903`

Artifacts: `results/occupancy.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `alltoall_residual.csv`, `probes.csv`, `bw_ci.csv`, `t2_vs_t3_ratio.png`, `summary.json`.

Seed **20260903**. Trials `SEED+i` (n=3). Clock UNKNOWN — no TB/s, no silicon ±15%.
card-claim **0.45–0.80× / 0.60–0.95×+res is NOT measured** (director / PR #68 did not sign).
0.85 is a pass bar, not a mean.

T2 `models/P-0198/M-2/` is **not on main** (draft PR #66). This tree does not land those files.
Compare uses signed audit pins (PR #68) + spec §3 formulas.

**Keep separate:** M-1 CBC was 淘汰 at T3 (PR #62/#64) — not in this tree, no shared speedup.
M-5 CRRF is a separate in-flight T3. Ablation is **spine-off on this card only**.

## Scope

Cycle-accurate: 4 dedicated CAM FSM items (`IDLE/COLLECT/GRANT_PENDING/GRANT_SENT/FORCE_FALLBACK`),
per-cycle `Dat_beats_held` (must be 0), same-cycle RENDZ reclassify, independent timeout,
Classifier 1-cycle + FORCE_FALLBACK notify ≤1, GRANT + static order table (no arrival oracle),
endpoint fold port contention, alltoall TREE vs RESIDUAL percentiles,
12+2 / four-ring / 512 B / ost 256|512.

Black box (`假设 H-RING-BB`): hop=1, HBM / coherence / D2D omitted.

## Seeds / CI

SEED=20260903. Makespan cells are `mean ± 95% CI (n=3)`.
Classes are never averaged into one pass number.

## Dr.Sim checklist

| # | Must-verify (T2 spec §5) | Status |
|---|--------------------------|--------|
| 1 | Per-cycle per-active-CAM `Dat_beats_held` | **yes** — probe; must stay 0 |
| 2 | Same-cycle reclassify vs payload reject-and-orbit | **yes** — overflow reclass; `payload_rbrg_reject=0` |
| 3 | 4 dedicated FSM × independent timeout; `live ≤ 4` | **yes** |
| 4 | Classifier + FORCE_FALLBACK notify bounded | **yes** — 1 / ≤1 |
| 5 | GRANT emit + static order-table window | **yes** — no arrival oracle |
| 6 | Endpoint fold RF/cache port contention | **yes** — `fold_ports=1`, orbits counted |
| 7 | alltoall residual buckets/percentiles | **yes** — `alltoall_residual.csv` |
| 8 | Warm-up + 12+2 / four-ring / 512 B / ost 256\|512 | **yes** |

Also: H_inject_gate; `cam_overflow_fallback` / `collect_timeout_fallback` first-class;
if either dominates completions → card_claim INVALID; spine-off returns toward baseline.

## T2 vs T3

Signed T2 pins (audit PR #68; cite, do not invent):

| Pin | T2 signed | T3 | note |
|-----|-----------|----|------|
| CAM Dat occupancy | 0 | cycle `dat_beats_held_max` | must be 0 |
| retention | 0 | `retention_depth_max` | must be 0 |
| N_cam | 4 | 4 | true concurrent |
| high-ost f_ov | 0.5746 → card_claim INVALID | probes.csv `high-ost-8ops` | Erlang-B vs discrete CAM |
| spine-off HARD | True (537.2 > 289.3 ns) | cycle off > on? | units differ |
| gate-off r | ≈1.0362 | probes.csv `gate-off` | premature orbit |
| alltoall TREE / RES / mix | 0.6932 / 1.0 / 0.8159 | residual columns | mix is NOT a pass number |
| card-claim | NOT signed | NOT measured | never print as measured |

If `|T3−T2|/T2 > 30%` the T3 number stands — do not substitute T2. Causes go below after smoke.

## Reproduce

```bash
python3 sims/P-0198/M-2/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-2/tests
python3 sims/P-0198/M-2/sim.py --class gather --arm CSR --seed 20260903
```

评估审计: review `results/t2_compare.csv` + `probes.csv` + `alltoall_residual.csv` + this discrepancy section before weekly report / T4. Do **not** open T4 from this PR.
