# T3 · P-0198/M-4 AODI

Cycle-level SimPy model of Age-Bounded Opposite-Ring Deflection Inject on a bufferless bidirectional CHI ring.
Baseline (`deflect-off`) and proposal (`AODI-on`) share **one driver** and **one seeded workload**.
`rejoin-off` is a diagnostic arm, not the main ablation.

Envelope: DV200 `tests/soc_sim` / `github:lukebest/bufferless-ring-noc`. **Not** team-384dmc / `team-interleave-microbench`.

**Keep separate:** M-1 CBC was **淘汰** at T3 (PR #62). M-2 CSR and M-5 CRRF are other in-flight T3 builds. This tree is `sims/P-0198/M-4/` only. Ablation is vs **deflect-off** on this card. No shared speedup / ranking with siblings.

## One-command repro

```bash
python3 sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-4/tests
python3 sims/P-0198/M-4/sim.py --class gather --arm AODI-on --seed 20260903
```

Seed: **20260903**. Trials use `20260903 + trial`.

## Modeled vs black-box

**Cycle-accurate (Dr.Sim must-verify; not mean ρ):**

1. Same-cycle 2×2 truth table × node × CHI `{Req,Rsp,Snp,Dat}`. Single-side empty + pending ⇒ legal deflect hole; **dual-busy ⇒ inject-hole≡0** (hard assert).
2. `inject-hole` sampled with the busy mask on the **same beat**. Buckets: asymmetric vs dual-busy.
3. Per-packet **φ** = remaining preferred hops after rejoin arming. **Not** Σage.
4. Age 4b; `age++` only on committed deflect; `AGE_MAX` (default 8) gates further deflect.
5. Independent Rejoin: wrong-ring flit, preferred outlet empty, depth 0. Not an inject port.
6. deflect-off ablation; opposite-ring util + CW/CCW completions. Ban inject-success-only.
7. alltoall dual-busy-sat is a **separate row** (plus a forced dual-busy probe). Expected gain ≈0. Never fold into 0.50–0.85× or 0.70–0.95×.
8. Warm-up ≥ one ring lap before issue/sample.

**Black box (parameterized):** hop latency (smoke=1), one flit per txn (512 B), RBRG, HBM, coherence, bottom D2D, clock. Outstanding smoke=16 (not envelope rd 512 / wr 256).

**Not modeled:** gem5; minting a third highway slot; cross-CHI deflect.

## Arms

| Arm | deflect | rejoin | Role |
|-----|---------|--------|------|
| deflect-off | 0 | on | **main ablation / baseline** |
| AODI-on | 1 | on | proposal |
| rejoin-off | 1 | off | diagnostic φ-freeze; not main attribution |

## T2 compare

T2 `models/P-0198/M-4/` is **not on main** (draft PR #65). This tree does not land those files.
Compare tables use **signed audit** pins (director / PR #65) plus spec §3 formulas:

- `hole_dual = 0`
- φ→0 `age_end = 1`
- deflect-off HARD `True`
- alltoall `T_mix = 1.0` (gain ≈0, separate row)
- default `T_mix`: gather/reduce **0.8448**; uniform_read **0.8770**
- card-claim bands (**0.70–0.95×** / **0.95–1.05×**) are **NOT signed** — print as card-claim only

If `|T3−T2|/T2 > 30%`, the sweep flags the row and **does not** substitute the T2 number.

Results: `results/occupancy.csv`, `t2_compare.csv`, `t2_signed_pins.csv`, `cycles.csv`, `holes.csv`, `bw_ci.csv`, `summary.json`.
See `report.md`.
