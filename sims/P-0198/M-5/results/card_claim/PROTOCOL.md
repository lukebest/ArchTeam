# Card-claim protocol · P-0198/M-5 CRRF (unsigned)

One-shot measurement (Luke 2026-10-09). **Not eval-audit signed. Not a conclusion. T4 not opened.**

## Card definition (PR #53 `mechanisms/P-0198/M-5.md` §4; card not on this tree)

- **Interval:** 0.55–0.85×
- **Quantity:** makespan (end-to-end completion time)
- **Relative to:** rebind-off (classic 1:1, no ghost)
- **Load:** Dat-heavy collectives / saturated uniform-read region
- **After:** drain / SYNC / bind tax (already in the cycle model)
- **0.85** is a pass bar, not a measured mean

Snp ≤1.4× rebind-off is a **kill hypothesis**, not this interval. 15:1 remains KILL.

## Command

```bash
python3 sims/P-0198/M-5/sweep.py --mode card_claim --seed 20260903
# equivalent:
python3 sims/P-0198/M-5/card_claim.py --seed 20260903
```

Seed 20260903; trials `20260903+i`; n≥3; report mean ± 95% CI (n).

## Workloads

`workloads/` is absent on this tree (and no P-0198 inference/training tables were found). Every row is an existing driver class, labeled:

| category | workload | existing class | role |
|---|---|---|---|
| inference | decode_kv_p2p | uniform_read | primary |
| inference | decode_kv_gather | gather | primary |
| inference | infer_allgather | allgather | primary |
| inference | infer_allreduce | allreduce | primary |
| training | train_reduce | reduce | secondary |
| training | train_alltoall | alltoall | secondary |

`workload_source=existing_config (负载基线表未到)` on every row. Training is not averaged with inference.

## Baselines (no simulator-structure change)

| type | label | outstanding | meaning |
|---|---|---|---|
| no_cc | 无拥塞控制 | \|I\| | fail-wait only; window never binds |
| source_fc | 源端流控 | 1 | existing per-source outstanding window |

Proposal = CRRF `{3:1, 7:1, 15:1}`, same driver / same txn list / same outstanding / same seed. Arms never averaged.

A destination-credit protocol is **not** in the sim. It is not implemented (would be an inject-path structure change). `source_fc` is the existing window knob.

## Outputs

`sims/P-0198/M-5/results/card_claim/` only. Signed smoke (`results/{capacity,t2_compare}.csv`) and `results/night/` are not written.
