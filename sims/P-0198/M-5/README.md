# T3 · P-0198/M-5 CRRF

Cycle-level SimPy model of Channel–Ring Rebind Fabric on a bufferless bidirectional CHI ring.
Baseline (`rebind-off`, 1:1, no ghost) and proposal duty arms `{3:1, 7:1, 15:1}` share **one driver** and **one seeded workload**.
Ablation is **rebind-off only**. Duty arms are never averaged. Snp is never folded into a Dat mean.
This tree is not ranked against eliminated **P-0198/M-1 CBC** (T3 REJECT, PR #62) or M-2 / M-4.

Envelope: DV200 `tests/soc_sim` / `github:lukebest/bufferless-ring-noc`. **Not** team-384dmc / `team-interleave-microbench`.

## One-command repro

```bash
python3 sims/P-0198/M-5/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-5/tests
python3 sims/P-0198/M-5/sim.py --class gather --arm 7:1 --seed 20260903
```

Seed: **20260903**. Trials use `20260903 + trial`.

## Modeled vs black-box

**Cycle-accurate (Dr.Sim must-verify; T2 spec §4 — not mean duty):**

1. Per-die five-state FSM `IDLE / ARM_DRAIN / DRAIN / FLIP / STEADY`. ARM_DRAIN stops new inject on the rebound ring; in-flight continues; no instant-empty.
2. DRAIN marker double-return rides the circulating Req SYNC token; highway sniff is local. Local sniff ≠ global empty.
3. After FLIP, `epoch_committed` travels with SYNC. New-generation inject before the all-node barrier is an assert (`LateNewgenInject`).
4. Skew-window accept set `{local, local−1}` (mod 4), bound ≤ ring circumference.
5. Ghost Dat keeps header channel-id = Dat. RBRG decodes by bind + tag; never reinterprets Dat as Snp.
6. Out-of-accept-set → NACK / depth-1 holding / Dat re-inject; time charged to that txn.
7. Safe drain/flip/steady with `hint=None`. `correctness_depends_on_hint == False`.
8. SYNC carries epoch / DRAIN / commit bits only — not a traffic oracle.
9. HARD-2: 512 B (1 txn) ghost vs main Dat destination histograms.
10. Warm-up until SYNC-aligned STEADY after the first committed generation, then sample.

**Black box:** hop latency (smoke=1), one flit per txn (512 B), RBRG, HBM, coherence, bottom D2D, clock. Outstanding smoke=16 (not envelope rd 512 / wr 256).

**Not modeled:** gem5; runtime `COLL_EP` as a correctness input; minting a second permanent Dat port.

## Duty arms (never averaged)

| Arm | Dat:Snp | Role |
|-----|---------|------|
| rebind-off | 1:1, no ghost | HARD-1 baseline |
| 3:1 | 3/4 : 1/4 | duty scan |
| 7:1 | 7/8 : 1/8 | card example |
| 15:1 | 15/16 : 1/16 | allergy arm; Snp 1.4× kill hyp may fire |

## T2 compare

T2 `models/P-0198/M-5/` is **not on main** (draft PR #63). This tree does not land those files.
Compare tables use **signed audit** pins (director / T2 default):

- `T_drain=77`; `f_steady=0.8666`
- `C_dat_eff`: 1.000 / 1.6099 / 1.7182 / 1.7724
- H-COMMIT: held=0, violated=12
- H-DAT-DOM gather: 0.6212 / 0.5820 / 0.5642
- HARD-1: 537.2 > 303.1 (T2 ns; T3 reports the cycle inequality)
- Snp 15:1 = 1.5625 **KILL**
- card-claim **0.55–0.85× is NOT signed / NOT measured**

If `|T3−T2|/T2 > 30%`, the sweep flags the row and **does not** substitute the T2 number.

Results: `results/capacity.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `dat_makespan.csv`, `snp_path.csv`, `hard2_dest.csv`, `bw_ci.csv`, `summary.json`.
See `report.md`.
