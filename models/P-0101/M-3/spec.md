# T2 spec · P-0101/M-3 层次正交放置

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0101 / M-3 |
| Name | 层次正交放置 |
| Problem | `problems/P-0101.yaml` (鸽笼 22.2%；成功禁止 bank 占用 >K/N) |
| Mechanism | `mechanisms/P-0101/M-3.md` |
| T1 | `reviews/P-0101/M-3/tier1_synthesis.md`, `Dr.Sim.md` |
| Envelope | 负载基线 TEAM-SPEC / 问题 YAML (`team-384dmc-18432bank`) |
| Bench | `team-interleave-microbench` |
| Style | LIMINAL / roofline: die/HA/DMC/bank occupancy → Little → BW ≤ n·μ |
| Out of scope | CR-MRDR; no silicon ±15% claim |

The 负载基线 table lives off-repo (shared disk). **Do not cite a GitHub path for it.**

### 负载基线 TEAM-SPEC / 问题 YAML（口径冻结）

**Envelope (only interleave may change):** 2×Die2 × 60 core/die × 96 HA/die × 2 pipe/HA × 1 DMC/pipe × 48 bank/DMC → **120 core / 384 DMC / 18432 bank**.

| Quantity | Value | SOURCE |
|----------|--------|--------|
| grain | 512B; G=addr>>9 | 负载基线 TEAM-SPEC / 问题 YAML |
| page | 4K | 负载基线 TEAM-SPEC / 问题 YAML |
| W | 8GiB = 2^33 | 负载基线 TEAM-SPEC / 问题 YAML |
| outstanding / core | 128 | 负载基线 TEAM-SPEC / 问题 YAML |
| in-flight Q_tot | 15360 = 120×128 | integer identity + 负载基线 TEAM-SPEC |
| stride range | 1B–2MiB | 负载基线 TEAM-SPEC / 问题 YAML |
| s_crit | W/N = 2^33/18432 ≈ 455.11 KiB | 问题 YAML |
| K @ S=2MiB | 4096 | 问题 YAML |
| occupancy ceiling | K/N = 4096/18432 ≈ 22.2% | 问题 YAML pigeonhole |

**UNKNOWN (do not fill):** clock, μ_d, DRAM type, row-buffer / tCAS, per-bank peak, DMC microarchitecture.

**假设 (named, not silicon):**

- H-TXN: one issued transaction = 512B (grain). SOURCE: 负载基线 TEAM-SPEC.
- H-MAP-LAT: mapper 1–2 cycle — mechanism-card self-estimate, **not** a silicon measurement.
- H-MU-D: per-DMC peak service rate. Named only.

**This machine has no public measurement.** Do not claim ±15% vs silicon. Occupancy algebra (K, N, gcd, n_DMC upper bounds) is exact. Absolute BW, if shown at all, is a **separate column** `n_DMC·μ_d` with μ_d labeled 假设 H-MU-D. Primary results are relative occupancy.

**0.85** is the **problem pass line** (YAML / T1 CONSTRAINT), **not** a measured mean.

**Forbidden foreign pins:** H100 STREAM 91–94%, H100 353 ns, H100 10 MC as a 384-bucket or ×3 proxy.

**Generator:** `team-interleave-microbench`. **Public counterexamples (not pass lines):** STREAM, random p-chase, 2-power-only, working set resident in SRAM/L2, decode-* packs.

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| W | B | 2^33 | 负载基线 TEAM-SPEC / 问题 YAML |
| grain | B | 512 | 负载基线 TEAM-SPEC / 问题 YAML; G = addr>>9 |
| page | B | 4096 | 负载基线 TEAM-SPEC / 问题 YAML |
| N_die | 1 | 2 | 负载基线 TEAM-SPEC / 问题 YAML: 2×Die2 |
| N_core | 1 | 120 | 负载基线 TEAM-SPEC / 问题 YAML: 2×60 |
| N_HA | 1 | 192 | 负载基线 TEAM-SPEC / 问题 YAML: 2×96 |
| N_pipe | 1 | 384 | 负载基线 TEAM-SPEC / 问题 YAML: HA×2 |
| N_DMC | 1 | 384 | 负载基线 TEAM-SPEC / 问题 YAML; 1 DMC / pipe |
| N_bank | 1 | 18432 | 负载基线 TEAM-SPEC / 问题 YAML; 384×48 |
| B_dmc | 1 | 48 | 负载基线 TEAM-SPEC / 问题 YAML |
| Q_core | 1 | 128 | 负载基线 TEAM-SPEC / 问题 YAML |
| Q_tot | 1 | 15360 | integer identity 120×128 |
| s_crit | B | 2^33/18432 ≈ 455.11 KiB | 负载基线 TEAM-SPEC / 问题 YAML |
| S | B | {512, 2^19, 2^20, 2^21} | card §4 + T1 |
| base | B | [0, W) grain-aligned | card §4 random base |
| K | 1 | ⌊(W−base)/S⌋+1 | problem YAML; pigeonhole |
| G | 1 | addr>>9 | YAML grain |
| p | 1 | addr[32:26] ∈ [0,127] | card §2 Stage A |
| t | 1 | ENC3(addr[25:24]) ∈ {0,1,2} | card §2 |
| dmc0 | 1 | t·128+p ∈ [0,384) | card §2 |
| SK[dmc0] | 1 | {0,1,2,3}; default 0 | card §2; T1 SK=0 |
| dmc | 1 | (dmc0+3s) mod 384 | card §2 |
| b4 | 1 | 4b, see H-B4 | card §2 Stage B |
| b3 | 1 | ENC3(addr[20:19]) ∈ {0,1,2} | card §2 |
| bank | 1 | clip(b3·16+(b4 mod 16), 0..47) | card §2 |
| die | 1 | dmc/192 | card §2.4 |
| ha_in_die | 1 | (dmc/2) mod 96 | card §2.4 |
| pipe | 1 | dmc mod 2 | card §2.4 |
| n_DMC | 1 | \|π_DMC(set)\| | integer image size |
| n_bank | 1 | \|π_bank(set)\| | global bank = dmc·48+bank |
| X_rel | 1 | min(N_DMC, \|set\|) / n_DMC | problem P-0103-style occupancy ratio; here vs 384 |
| μ_d | B/s | UNKNOWN | 假设 H-MU-D; never a numeric GB/s constant |

**假设 H-B4 (width freeze).** Card writes `b4[3:0]=addr[23:21]⊕addr[14:11]` (3b⊕4b). T1 Archi notes the width is unfrozen. This spec LSB-aligns and zero-extends the 3b field:

`b4 = ((addr>>21)&7) XOR ((addr>>11)&15)`.

Never retune the alignment to fit a result.

**假设 H-ENC9 (baseline M-1 only).** M-1’s 16→9 encoder table is not listed. Freeze `ENC9[0..15]=[0,1,2,3,4,5,6,7,8,0,1,2,3,4,5,6]`. P=0 (card reset). This is the real M-1 wiring (distinguish bits into `flat`, then `/48`), not a strawman “86 DMC” constant.

**假设 H-MU-D.** Per-DMC peak service rate. Named, not filled.

## 3. Mapper equations (bit-exact)

ENC3 (card example, now the only legal table):

```
ENC3(00)=0, ENC3(01)=1, ENC3(10)=2, ENC3(11)=0
```

Histogram 2:1:1 on a uniform 2b input.

Stage A (SK=0 default):

```
p      = addr[32:26]
t      = ENC3(addr[25:24])
dmc0   = t·128 + p
s      = SK[dmc0]          # default 0
dmc    = (dmc0 + 3·s) mod 384
```

Stage B:

```
b4     = ((addr>>21)&7) XOR ((addr>>11)&15)     # H-B4
b3     = ENC3(addr[20:19])
bank0  = b3·16 + (b4 mod 16)
bank   = min(bank0, 47)                          # clip 0..47; not partial-good
```

Topology (issued request):

```
die        = ⌊dmc / 192⌋
ha_in_die  = ⌊dmc / 2⌋ mod 96
ha         = die·96 + ha_in_die
pipe       = dmc mod 2
```

No `core_id` port. SK is boot-time only; this model keeps SK≡0.

## 4. Baseline mappers (algebraic)

| Name | Equation | SOURCE |
|------|----------|--------|
| B-modN | flat = G mod 18432; dmc=⌊flat/48⌋; bank=flat mod 48 | card §4 |
| B-M1 | d=addr[32:21]; v=d (P=0); c=ENC9(addr[16:13]); flat=(c·4096+v) mod 18432; dmc=⌊flat/48⌋; bank=flat mod 48 | mechanisms/P-0101/M-1.md; H-ENC9 |
| B-low | dmc = addr[17:9] mod 384; bank = addr[14:9] mod 48 | card §4 `addr[17:9]%384` |

B-M1 saturates distinguish bits into a *flat* index, then `/48`. That is DMC-second. Do not replace it with a hardcoded “4096/48≈86 DMC” strawman; the image size is an output.

## 5. Occupancy identities and live bits

Pigeonhole (problem YAML):

```
K = ⌊(W − base)/S⌋ + 1
|π(AP)| ≤ K                    # any mapper
bank occupancy ≤ K / N_bank    # S=2MiB ⇒ K=4096, ≤ 4096/18432 = 2/9 ≈ 22.2%
```

If a run reports bank occupancy > K/N, the *model* is wrong (problem falsified only if a reversible map truly exceeds this). Success of M-3 is **DMC occupancy ≈ 1.0**, not bank > K/N.

AP: `addr_k = base + k·S`, `k=0..K−1`, grain-aligned base.

**Issued / inflight set (T1 probe).** Little window `Q_tot=15360`. Issued set I(base,S) is the first `min(K, Q_tot)` AP points (sequential issue, no dependency). Four-layer histograms are counted on **issued** addresses, not on a claimed DRAM completion trace.

Live-bit table (addr bits that change along the AP):

| S | S_g | frozen addr bits | walking bits | Stage A (addr[32:24]) | Stage B notes |
|---|-----|------------------|--------------|------------------------|---------------|
| 512B | 1 | — (full window walks everything) | all G | inflight span = 15360×512 = 7.5MiB < 2^24 ⇒ addr[32:24] **constant** unless the window crosses a 16MiB boundary | low XOR bits walk |
| 512KiB | 2^10 | addr[18:0] | addr[32:19] | walks | mixed |
| 1MiB | 2^11 | addr[19:0] | addr[32:20] | walks | addr[20:19] may walk |
| 2MiB | 2^12 | addr[20:0] | addr[32:21] | 9 distinguish bits walk; ENC3 input walks | b3 frozen; b4 uses addr[23:21] (walk) ⊕ addr[14:11] (freeze) |

S=2MiB ENC3 2:1:1 (integer, not a fit):

- addr[25:24] is uniform on {00,01,10,11} over the 4096-point cube addr[32:21].
- t=0 gets two residues ⇒ 2048 points; t=1 and t=2 get 1024 each.
- die = ⌊dmc/192⌋ splits t=1 across the die cut (dmc 128–191 on die0, 192–255 on die1).
- Visit counts: die0 = 2048+512 = 2560, die1 = 512+1024 = 1536 ⇒ **5:3**. Source: ENC3 table + die=⌊dmc/192⌋, not a measurement.

HA fair share = 2/384 (each HA owns 2 DMC). Hog line = 1.5×(2/384)=3/384.

mod-N live bits at S=2MiB: gcd(S_g, 18432)=2^11 ⇒ |im|≤9 flats ⇒ n_DMC≤9 (card §1). That 9 vs 384 is an occupancy ratio, not a speedup.

## 6. Little + roofline

```
Q_tot = 15360                                            # identity
n_DMC_I = |π_DMC(I)|
n_HA_I  = |π_HA(I)|
n_die_I = |π_die(I)|
n_bank_I= |π_bank(I)|
X_rel   = min(384, |I|) / n_DMC_I                       # ≥1; collapse penalty
BW      ≤ n_DMC_I · μ_d                                  # 假设 H-MU-D
BW      ≤ n_bank_I · μ_b                                 # μ_b UNKNOWN; do not fill
BW      ≤ n_HA_I · μ_ha                                  # UNKNOWN
```

Report occupancy ratios. **Do not print 9/384 as a measured speedup.** Absolute BW is a **separate optional column** `n_DMC_I · μ_d` (假设 H-MU-D). Default model output omits GB/s. Do not fill H100 STREAM 91–94% or 353 ns as this machine’s pins.

min/mean structural: visit histogram over the 384 DMC slots on set I (zeros included for `min_all`; occupied-only for `min_occ/mean_occ`). Primary balance number is `min_occ/mean_occ`.

## 7. T1 kill-lines (CONSTRAINTS, not measured numbers)

Copied as constraints. Verdict is not rewritten.

1. S=512B sequential unique DMC must not collapse to ≪128 (Archi fail=1; Sys wants occupancy still ≥0.95). Same table as S=2MiB; forbid only reporting 2MiB.
2. SK=0, S=2MiB, ≥8 random bases: no HA issued share > 1.5×(2/384). ENC3 bias ⇒ die load ~5:3 even when \|DMC\|=384.
3. Main bench `team-interleave-microbench`. Forbid decode-*. H100 is not a 384-bucket proxy.
4. Four-layer probes on **issued** requests. Bank occupancy ≤K/N. 9 vs 384 Little ratio is not a measured speedup.

## 8. Calibration: exact vs 假设

| Item | Status |
|------|--------|
| K, gcd, pigeonhole, ENC3 2:1:1, die 5:3 at S=2MiB SK=0 | exact (integer / wiring) |
| inflight unique DMC at S=512B sequential (typically 1 if no 16MiB crossing) | exact for this issued-window definition |
| B-modN image size N/gcd(S_g,N) | exact |
| H-B4, H-ENC9, H-MU-D | 假设 |
| Clock, μ_d, DRAM type, row-buffer/tCAS, per-bank peak, DMC microarchitecture | UNKNOWN; not filled |
| H-TXN (512B/txn), H-MAP-LAT (1–2 cycle, card self-estimate) | 假设; not silicon |
| Public silicon for this machine | none; no ±15% claim |

## 9. Sensitivity (two parameters; sweep, no fitted coeffs)

Gain (DMC occupancy vs B-modN / B-low) is most sensitive to:

1. **S relative to 2^24** (whether addr[32:24] walks inside the issued window).
2. **ENC3 table / SK** (2:1:1 hog vs a balanced 3-way; SK≠0 can rotate but this run freezes SK=0).

Sweep plan: S ∈ {512B, 512KiB, 1MiB, 2MiB} × ≥8 random grain-aligned bases, SK=0. Optionally (off the pass line) flip ENC3 to a balanced 1:1:1 leftover map as a *counterfactual*, never as this card. No fitted coefficients.

## 10. Magic-gap (CLAIM vs model-explainable)

| CLAIM (card §3–4) | Model-explainable range |
|-------------------|-------------------------|
| DMC occupancy 0.95–1.00 at S=2MiB | \|π_DMC\|=384 is a wiring claim on 9 live bits; issued-set n_DMC is 384 when K≥384 and Stage A is onto. Not a BW. |
| bank occupancy 0.18–0.222 | ≤K/N=22.2% is a pigeonhole ceiling, not a fit. |
| BW ×20–×42 vs mod-N | CLAIM. Explainable only as n_DMC ratio (e.g. 384/9) times μ_d/μ_d; **not** a measured speedup. |
| vs M-1 ×1.0–×2 or ×3–×4.5 | CLAIM. Branch on *measured* B-M1 n_DMC, do not award both. |

## 11. Workloads

SOURCE: 负载基线 TEAM-SPEC / 问题 YAML + card §4 + T1. Generator: `team-interleave-microbench`.

**Pass pack (this card):**

- S ∈ {512B, 512KiB, 1MiB, 2MiB} × random grain-aligned base (≥8), sequential AP.
- Four-layer probes on **issued** requests: die / HA / DMC / bank.
- Success = **DMC occupancy ≈ 1.0** and **bank occupancy ≤ 22.2%** (K/N at S=2MiB). Filling 18432 banks at S=2MiB is **not** a pass item.
- Issued window Q_tot=15360 on the same table (when K < Q_tot the image is the full AP).
- 100% good banks (clip ≠ partial-good).

**Public counterexamples (not pass lines):** STREAM, random p-chase, 2-power-only, resident SRAM/L2, decode-* packs.

## 12. Forbidden

- `core_id` in the map
- Reporting only S=2MiB
- Bank occupancy >K/N as success
- Treating 9 vs 384 Little as measured speedup
- decode-* benches; STREAM / p-chase / 2-power-only / resident as pass lines
- H100 10 MC as 384-bucket or ×3 proxy; H100 STREAM 91–94%; H100 353 ns
- Hardcoded GB/s; treating 0.85 as a measured mean
- hash%384 in place of Stage A
- Tuning SK or ENC3 after seeing occupancy
- Joint ranking vs other Batch A cards
