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

Smoke bbox: 2 collective ops (allgather/allreduce capped to 1), fold_ports=1, W_grant=1.
This is **not** gem5 `tests/soc_sim`.

## Seeds / CI

SEED=20260903. Makespan cells are `mean ± 95% CI (n=3)`.
Classes are never averaged into one pass number.

## Dr.Sim checklist

| # | Must-verify (T2 spec §5) | Status |
|---|--------------------------|--------|
| 1 | Per-cycle per-active-CAM `Dat_beats_held` | **yes** — 96/96 occupancy rows `dat_beats_held_max=0` |
| 2 | Same-cycle reclassify vs payload reject-and-orbit | **yes** — overflow reclass; `payload_rbrg_reject=0`, `retention_depth_max=0` |
| 3 | 4 dedicated FSM × independent timeout; `live ≤ 4` | **yes** — `n_cam=4`, live_max≤4 (smoke gather live_max=1; overflow probe exercises 4) |
| 4 | Classifier + FORCE_FALLBACK notify bounded | **yes** — classifier 1; FF notify ≤1 (unit test `timeout=1`) |
| 5 | GRANT emit + static order-table window | **yes** — predecessor *posted* issue, not eject oracle; `oracle_used=False` |
| 6 | Endpoint fold RF/cache port contention | **yes** — `fold_ports=1`; spine-off gather orbits 111 vs CSR 56 (trial-mean class) |
| 7 | alltoall residual buckets/percentiles | **yes** — `alltoall_residual.csv` p50/p90/p99 |
| 8 | Warm-up + 12+2 / four-ring / 512 B / ost 256\|512 | **yes** — 14 nodes, ost columns 256 and 512 |

Also: H_inject_gate (`inject_before_grant=0` on CSR; 109 on gate-off gather);
`cam_overflow_fallback` / `collect_timeout_fallback` first-class;
if either dominates completions → card_claim INVALID;
spine-off returns collective makespan to **the same magnitude** as CSR (see HARD).

## T2 vs T3 (signed pins — cite, do not invent)

| Pin | T2 signed (PR #68) | T3 smoke | \|T3−T2\|/T2 | flag>30% |
|-----|--------------------|----------|--------------|----------|
| CAM Dat occupancy | 0 | 0 (96/96) | 0 | no |
| retention | 0 | 0 (96/96) | 0 | no |
| N_cam | 4 | 4 | 0 | no |
| gather T_hat/T_off | 0.5386 | **1.0104** (194/192) | 0.876 | **yes** |
| reduce | 0.5386 | **1.0104** | 0.876 | **yes** |
| allgather | 0.5386 | **1.0000** (256/256) | 0.857 | **yes** |
| allreduce | 0.5386 | **1.4660** (151/103) | 1.722 | **yes** |
| alltoall TREE r (vs T2 0.6932) | 0.6932 | **1.326** op-makespan on/off | 0.913 | **yes** |
| alltoall RESIDUAL | 1.0 | residual still RING_P2P (p50/p90/p99 split) | — | residual column only |
| alltoall mix 0.8159 | companion, not pass | **not used as pass** | — | — |
| gate-off r | 1.0362 | **1.0469** | 0.010 | no |
| high-ost f_ov | 0.5746 → INVALID | **0.3750** (ov=3/8, dominates=False) | 0.347 | **yes** (quant) |
| spine-off HARD | True (537.2 > 289.3 ns) | cycle **192 ≯ 194** | n/a (units) | inequality **fails** |
| card-claim | NOT signed | **NOT measured** | — | printed as card-claim only |

`t2_compare.csv` has **30** `flag_gt_30pct=True` rows (96 total). T3 numbers were **not** replaced by T2.

## Per-class makespan (ost=256, n=3) — never averaged

| class | spine-off | CSR | CSR/off | card-claim |
|-------|-----------|-----|---------|------------|
| gather | 192.00 ± 0.00 | 194.00 ± 0.00 | 1.010 | 0.45-0.80x **NOT measured** |
| reduce | 192.00 ± 0.00 | 194.00 ± 0.00 | 1.010 | 0.45-0.80x **NOT measured** |
| allgather | 256.00 ± 0.00 | 257.00 ± 0.00 | 1.004 | 0.45-0.80x **NOT measured** |
| allreduce | 103.00 ± 0.00 | 151.00 ± 0.00 | 1.466 | 0.45-0.80x **NOT measured** |
| alltoall | 147.33 ± 4.71 | 196.67 ± 8.34 | 1.335 | 0.60-0.95x+res **NOT measured** |
| broadcast | 102.00 ± 0.00 | 104.00 ± 0.00 | 1.020 | 0.75-0.98x **NOT measured** |
| uniform_read | 65.33 ± 7.53 | 65.33 ± 7.53 | 1.000 | 0.95-1.05x **NOT measured** |
| uniform_write | 65.33 ± 7.53 | 65.33 ± 7.53 | 1.000 | 0.95-1.05x **NOT measured** |

ost=512 matches ost=256 on every class (outstanding not binding at \|ops\|=2).

### alltoall residual (trial 0, ost=256) — do not average with TREE or gather

| arm | TREE ms / n | RESIDUAL ms / n | p50 / p90 / p99 |
|-----|-------------|-----------------|-----------------|
| spine-off | 96 / 24 | 83 / 48 | 24 / 54 / 83 |
| CSR | 38 / 24 | 117 / 48 | 22 / 65 / 117 |

TREE per-xfer time can drop (38 vs 96) while **op makespan** and residual tail do not. mix is not a pass number.

## Why gather-family misses T2 0.5386 by >30%

T2 `r = f_grant·(r_sched+κ) + f_fb·1` with `r_sched=(1−f_fanin)+f_fanin·(W_grant/N_src)`, `f_fanin=0.60`, `W_grant=1` → 0.5386.

Cycle fabric: 12 sources × 8 beats into **1 fold port** ⇒ Little's-law floor `≈ N_src·N_beats` (96 cycles per gather op; two ops → 192). Spine-off wait-at-endpoint + dest-orbit still drains at 1 fold/cycle. CSR W_grant=1 matches that width and adds a GRANT-lap tax (+2 cycles). **H-FANIN-BOUND's Ω(N) inject collapse is not the makespan bottleneck** once payload stays in RF until a Dat slot exists.

T3 r≈1.01 stands. Do not substitute 0.5386.

### HARD spine-off

T2: `T_hat_off=537.2 > T_hat_on=289.3` (ns, H-REL-SCALE).  
T3: gather off 192 ≯ CSR 194. Attribution to CSR **fails**. Spine-off does return collectives to baseline **magnitude** (they already were).

### gate-off (like-to-like match)

T3 1.0469 vs T2 1.0362, rel_err=1.0%. Premature payload inject (`inject_before_grant=109`) cancels the order table; r returns toward 1. This is the only quantitative T2 schedule pin that cycle-reproduces.

### high-ost f_ov

T2 Erlang-B a=8 → 0.5746, dominates → card_claim INVALID.  
T3 8 concurrent gather ops: f_ov=0.375 (3 overflow), dominates=False. Fast nodes pipeline the next op's RENDZ header while a slow COLLECT still holds a CAM, so demand is not a simultaneous M/M/4/4 arrival. T3 0.375 stands; do not write T2 INVALID onto this wave.

### allreduce / alltoall worse on CSR

allreduce r=1.47: software-posted phase-1 waits for phase-0 *posted* complete, then another serial window — spine-off overlaps fan-in/fan-out on two ring directions.  
alltoall op-makespan r=1.33: TREE GRANT serializes a subset while residual RING_P2P still fights Dat; spine-off sends everything as P2P without the GRANT lap.

## Architect feedback (do not change the card)

Structured, for the architect — T3 does not rewrite `mechanisms/P-0198/M-2.md`.

1. **Invariants hold (T1-return-1 latch kill).** Cycle `Dat_beats_held≡0`, `retention≡0`, N_cam=4 dedicated. Rendezvous-as-header/credit is implementable. That is necessary, not sufficient for makespan.

2. **HARD attribution fails.** spine-off gather is not worse. card-claim 0.45–0.80× is not a cycle number. The fold-port floor plus GRANT citizen tax makes W_grant=1 a **no-win** vs bidirectional conveyor drain.

3. **H-FANIN-BOUND is the wrong bottleneck on this bbox.** Inject-fail counts and dest-orbits are real (spine-off gather fail=high, orbits=111) but they do not lengthen makespan beyond 1 fold/cycle. A cycle win needs either more fold ports (not on the card) or a baseline that *livelocks* (not observed).

4. **Overflow is first-class and discrete.** 8-op wave overflows 3/8 without dominating. Erlang-B a=8 INVALID is a mean-field load, not this issue schedule. Do not sign card-claim as pass either way.

5. **alltoall residual must stay a column.** TREE xfer time can look good while op makespan and residual p99 look worse. A mix/mean would lie.

6. **FORCE_FALLBACK notify is bounded** (unit test timeout=1). Default timeout=255 and smoke timeout=8 do not fire because COLLECT refreshes on each header. Timeout is not the default hot path (agrees with T2 insight).

## Reproduce

```bash
python3 sims/P-0198/M-2/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-2/tests
python3 sims/P-0198/M-2/sim.py --class gather --arm CSR --seed 20260903
```

评估审计: review `results/t2_compare.csv` + `probes.csv` + `alltoall_residual.csv` + this discrepancy section before weekly report / T4. Do **not** open T4 from this PR.
