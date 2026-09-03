# T2 spec · P-0101/M-3 层次正交放置

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0101 / M-3 |
| Name | 层次正交放置 |
| Problem | `problems/P-0101.yaml` (鸽笼 22.2%；成功禁止 bank 占用 >K/N) |
| Mechanism | `mechanisms/P-0101/M-3.md` |
| T1 | `reviews/P-0101/M-3/tier1_synthesis.md`, `Dr.Sim.md` |
| Envelope | TEAM-SPEC `team-384dmc-18432bank` |
| Bench | `team-interleave-microbench` |
| Style | LIMINAL / roofline: die/HA/DMC/bank occupancy → Little → BW ≤ n·μ |
| Out of scope | CR-MRDR; Python is `model.py` beside this file; no silicon ±15% claim |

This spec is occupancy algebra plus a named-μ roofline. Clock, DRAM type, row-buffer timings, and μ_d are **UNKNOWN**. Absolute GB/s appear only as `μ_d * occupancy` with μ_d labeled 假设, and are not a primary output.

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| W | B | 2^33 | problem YAML; 8GiB shared |
| grain | B | 512 | problem YAML; G = addr>>9 |
| page | B | 4096 | problem YAML |
| N_die | 1 | 2 | YAML: 2×Die2 |
| N_core | 1 | 120 | YAML: 2×60 |
| N_HA | 1 | 192 | YAML: 2×96 |
| N_pipe | 1 | 384 | YAML: HA×2 |
| N_DMC | 1 | 384 | YAML; 1 DMC / pipe |
| N_bank | 1 | 18432 | YAML; 384×48 |
| B_dmc | 1 | 48 | YAML |
| Q_core | 1 | 128 | YAML outstanding/core |
| Q_tot | 1 | 15360 | integer identity 120×128 |
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

Report occupancy ratios. **Do not print 9/384 as a measured speedup.** Do not print GB/s unless an operator explicitly sets μ_d; default model output omits GB/s.

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
| Clock, tRCD/tRAS/tRC/tREFI, DRAM type | UNKNOWN; not filled |
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

Card + T1 + 负载基线:

- S ∈ {512B, 512KiB, 1MiB, 2MiB} × random base (≥8), sequential AP.
- Issued window Q_tot=15360 on the same table as full-AP image when K < Q_tot.
- 100% good banks (this card does not implement partial-good; clip≠mask).
- Bench: `team-interleave-microbench`. STREAM is not a pass line.

## 12. Forbidden

- `core_id` in the map
- Reporting only S=2MiB
- Bank occupancy >K/N as success
- Treating 9 vs 384 Little as measured speedup
- decode-* benches; STREAM as pass line; averaging killer strides
- H100 10 MC as 384-bucket or ×3 proxy
- Hardcoded GB/s; filling ns/TB/s from H100
- hash%384 in place of Stage A
- Tuning SK or ENC3 after seeing occupancy
- Joint ranking vs other Batch A cards
