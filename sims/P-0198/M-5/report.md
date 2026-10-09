# T3 report · P-0198/M-5 CRRF

Smoke (signed fixture):
`python3 sims/P-0198/M-5/sweep.py --mode smoke --seed 20260903`

```bash
python3 -m pytest sims/P-0198/M-5/tests
python3 sims/P-0198/M-5/sim.py --class gather --arm 7:1 --seed 20260903
```

**Seed:** 20260903. Trials `20260903+i` (n=3). Clock UNKNOWN. 假设 H-RING-BB.

T2 `models/P-0198/M-5/` is **not** on this PR (draft PR #63, read-only). Compare uses signed director / audit pins. card-claim intervals are **NOT measured**.

Ablation is **rebind-off only**. Duty arms are never averaged. Snp is never folded into a Dat mean.
This card is not ranked against eliminated **P-0198/M-1 CBC** (T3 REJECT, PR #62) or M-2 / M-4.

## Scope

Cycle-accurate five-state Rebind FSM, SYNC drain / `epoch_committed` barrier, skew accept set `{local, local−1}`, ghost Dat channel-id, NACK/re-inject.
Hop latency / flit=txn (512 B) / RBRG / HBM / coherence / D2D / clock are black-box.
Reduced bbox: 12 nodes, outstanding=16 (not envelope rd 512 / wr 256). Drain-timing probe uses N=25 so `T_drain` is like-to-like with T2 `C_ring=25`.

## Seeds / CI

Every makespan / `C_dat_eff` cell is `mean ± 95% CI (n=3)`.
0.85 is a pass bar, not a measured mean. No GB/s. No team-384dmc.

## T2 vs T3 (smoke, seed 20260903)

Signed pins from director / T2 default. T3 is **not** replaced when `|T3−T2|/T2 > 30%`.

| Metric | Arm | T3 | T2 (signed) | rel_err | flag>30% |
|--------|-----|----|-------------|---------|----------|
| T_drain | C_ring=25 | 75 | 77 | 2.6% | no |
| f_steady | 7:1 | 0.709 | 0.8666 | 18.2% | no |
| C_dat_eff | rebind-off | 1.000 | 1.000 | 0 | no |
| C_dat_eff | 3:1 | 1.419 | 1.6099 | 11.9% | no |
| C_dat_eff | 7:1 | 1.507 | 1.7182 | 12.3% | no |
| C_dat_eff | 15:1 | 1.551 | 1.7724 | 12.5% | no |
| H-COMMIT held | barrier on | 0 | 0 | 0 | no |
| H-COMMIT violated | early inject | 12 | 12 | 0 | no |
| H-DAT-DOM gather | 3:1 | 0.583 | 0.6212 | 6.1% | no |
| H-DAT-DOM gather | 7:1 | 0.583 | 0.5820 | 0.2% | no |
| H-DAT-DOM gather | 15:1 | 0.583 | 0.5642 | 3.4% | no |
| HARD-1 | gather | 24 > 14 | 537.2 > 303.1 | n/a (inequality) | no |
| H-SNP-LAT snp_path | 15:1 | **11.67 KILL** | 1.5625 KILL | **647%** | **yes** |
| H-SNP-LAT mixed | 15:1 | **23.22 KILL** | 1.5625 KILL | **1386%** | **yes** |
| Snp 15:1 kill_1.4 | 15:1 | True | True | 0 | no |
| card-claim | Dat-heavy | **NOT measured** | 0.55–0.85× | — | — |

Gather cycle makespan (same driver, |I|=48):

| Arm | makespan | C_dat_eff | T / rebind-off |
|-----|----------|-----------|----------------|
| rebind-off | 24.00 ± 0.00 | 1.000 | 1.00 |
| 3:1 | 14.00 ± 0.00 | 1.419 | 0.583 |
| 7:1 | 14.00 ± 0.00 | 1.507 | 0.583 |
| 15:1 | 14.00 ± 0.00 | 1.551 | 0.583 |

The three on-arms share the same 14-cycle gather span at this bbox (destination-0 eject limit, not duty limit). They are **not** averaged into one “CRRF speedup”.

Snp (mandatory columns; completions do not drop):

| Window | Arm | T_snp / off | kill 1.4× | Snp completions |
|--------|-----|-------------|-----------|-----------------|
| snp_path | rebind-off | 1.00 | no | 48 issued class |
| snp_path | 3:1 | 15.00/15.00 ≈ 1.0 | no | same class size |
| snp_path | 7:1 | 118.67/15 ≈ 7.9 | **yes** (wide CI) | same |
| snp_path | 15:1 | 175/15 = 11.67 | **yes** | same |
| snp_on_gather | 3:1 / 7:1 / 15:1 | 18.8 / 20.8 / 21.8 | **yes** | 6/6, no drop |

## >30% deltas (causes; T3 stands)

1. **H-SNP-LAT 15:1 (snp_path 11.67 and mixed 23.22 vs T2 1.5625).**
   T2 uses **q=1** fine TDM (`E[wait]=(r/(r+1))·(r·q/2)`, `L_snp=C_ring/2`). Cycle-level bind change **must** run Epoch Drain (marker double-return + `epoch_committed` lap). That forces a coarse quantum ≈ `T_steady` / duty, not q=1. Snp sources stall with no ring queue during DAT_EPOCH. T3 does **not** substitute 1.5625. The 1.4× kill hyp **fires**, as required.

2. **Related (not a T2 pin, but architect-visible):** dedicated `snp_path` 7:1 is already ~7.9× (KILL) with a wide trial CI; mixed Snp-on-gather also kills **3:1**. T2’s default (q=1, L=12.5) only killed 15:1. The cycle model is harsher because drain cannot be amortized into a 1-cycle TDM slot.

`f_steady` (0.709 vs 0.8666, 18%) and `C_dat_eff` (~12%) stay under 30%. Cause of the remaining gap: T2 counts **one** drain per `T_steady`; T3 drains on every DAT↔SNP bind change (two-sided), so lifetime STEADY fraction is lower. T_drain 75 vs 77 is the N=25 probe (SYNC visit phasing), not a model substitution.

## Dr.Sim checklist (T2 spec §4)

| # | Requirement | Evidence |
|---|-------------|----------|
| 1 | Five-state FSM beat-by-beat; ARM_DRAIN stops new inject; in-flight continues; no instant-empty | `tests/test_crrf_fsm.py`; `fsm_counts` in `cycles.csv` |
| 2 | Marker double-return / highway sniff; local sniff ≠ global empty | `test_marker_double_return_via_sync`, `test_local_sniff_ne_global_empty` |
| 3 | `epoch_committed` around the ring; late new-gen inject = assert | `LateNewgenInject`; `h_commit_probe.csv` held=0 / violated=12 |
| 4 | SYNC skew accept set `{local, local−1}` | `test_accept_set_is_local_and_prev` |
| 5 | Ghost header channel-id stays Dat; RBRG by bind+tag | `test_ghost_header_stays_dat`, `test_rbrg_never_decodes_dat_as_snp` |
| 6 | Out-of-accept-set NACK/re-inject charged to that txn | `test_nack_reinject_charged_to_txn` |
| 7 | Safe drain/flip/steady with no hint | `test_safe_drain_flip_steady_without_hint`; `correctness_depends_on_hint=False` |
| 8 | SYNC ≠ traffic oracle | `test_sync_is_not_traffic_oracle`; `oracle_used=False` |
| 9 | HARD-2 512 B ghost vs main dest | `hard2_dest.csv`; uniform not mechanism-collapsed |
| 10 | Warm-up until SYNC-aligned STEADY | `aligned=True` on every smoke cycle row |

Also: `C_dat_eff ≤ 1+duty_dat`; drain/SYNC/bind tax > 0 on on-arms; 15:1 allowed to fail 1.4×.

## Structured architect feedback (do not rewrite the card)

The cycle model is **realizable as specified** (barrier, accept set, ghost id, NACK path all close). What the T2 algebra hid:

- **Time-mux ≠ q=1.** A correct drain/flip/`epoch_committed` sequence costs ~`T_drain≈(k_circ+1)·C_ring+n_pipe` per bind change. Fine-slot TDM that T2 used for H-SNP-LAT is not a legal cycle schedule. Anyone quoting 15:1 = 1.5625 as a *measured* Snp ratio is using the algebraic q=1 line, not a ring.
- **Snp 1.4× kill is not 15:1-only** once drain is paid. Mixed Snp-on-gather kills 3:1 and 7:1 as well; dedicated `snp_path` still passes 3:1 and fails 7:1/15:1. Completions did not drop (duty floor eventually injects). Makespan is the failing endpoint.
- **Dat gather HARD-1 holds** (24 > 14) but the three duty arms are **tied** at this bbox. Extra ghost slots do not keep buying Dat makespan after dest-0 eject saturates. Do not publish a duty-average speedup.
- **card-claim 0.55–0.85×** is still **not measured**. T3 gather 0.583 sits in the interval; that does not sign the claim, and Snp is outside 1.4× on every on-arm in the mixed window.
- **hint / SYNC oracle:** correctness path ignores `COLL_EP`; SYNC carries epoch/DRAIN/commit only.

Mechanism card text is not edited here.

## 评估审计

Paths for vs-T2 review (before weekly report / T4 — T4 is **not** opened):

- `sims/P-0198/M-5/results/t2_compare.csv` (`flag_gt_30pct`)
- `sims/P-0198/M-5/results/capacity.csv`
- `sims/P-0198/M-5/results/snp_path.csv`
- `sims/P-0198/M-5/results/dat_makespan.csv`
- `sims/P-0198/M-5/results/hard2_dest.csv`
- `sims/P-0198/M-5/results/t2_signed_pins.csv`
- `sims/P-0198/M-5/results/summary.json`
- plots: `t2_vs_t3_c_dat_eff.png`, `t2_vs_t3_gather_ratio.png`, `snp_ratio.png`

T2 files remain on PR #63. This PR does not land `models/P-0198/`.
