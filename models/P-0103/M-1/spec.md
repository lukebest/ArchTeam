# T2 spec · P-0103/M-1 MRFI

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0103 / M-1 |
| Name | Mixed-Radix Feistel Injector (MRFI) |
| Problem | `problems/P-0103.yaml` (3-adic X_rel=3) |
| Mechanism | `mechanisms/P-0103/M-1.md` |
| T1 | `reviews/P-0103/M-1/tier1_synthesis.md`, `Dr.Sim.md` |
| Envelope | TEAM-SPEC `team-384dmc-18432bank` |
| Bench | `team-interleave-microbench` |
| Style | LIMINAL / roofline |
| Out of scope | CR-MRDR; no silicon ±15% |

Two DMC definitions coexist on the card. The model must check them **pointwise**. Neither `G mod 384` nor `r' mod 3` may substitute for assembled DMC.

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| W, grain, N_DMC, N_bank, Q_tot | — | 2^33, 512, 384, 18432, 15360 | problem YAML; identities |
| G | 1 | A[63:9] | card §2.2 |
| p | 1 | G[10:0] ∈ [0,2047] | card §2.2 |
| r | 1 | G mod 9 ∈ [0,8] | card §2.2; 64≡1 (mod 9) |
| p_wide | 1 | A[24:9]=G[15:0] | card §2.2 |
| idx4 | 1 | 4-way 4b XOR ∈ [0,15] | card §2.2 |
| F | 1 | ROM16x4[idx4] ∈ [0,8] | card histogram |
| r' | 1 | (r+F) mod 9 | card §2.2 |
| p' | 1 | p | card §2.2 |
| idx | 1 | CRT in [0,18431] | card §2.2 |
| DMC_div | 1 | ⌊idx/48⌋ | card §2.2 first definition |
| DMC_asm | 1 | (r' mod 3)+3·⌊⌊idx/48⌋/3⌋ | card §2.2 + T1 rewrite of u |
| bank | 1 | idx mod 48 | card §2.2 |
| μ_d | B/s | UNKNOWN | 假设 H-MU-D |

ROM16x4 (locked):

```
F[0..15] = 0,1,2,3,4,5,6,7,8,0,1,2,3,4,5,6
```

Histogram: residues 0..6 twice, 7 and 8 once. SOURCE: card §2.2 table.

## 3. Mapper equations (bit-exact)

```
G      = A >> 9
p      = G[10:0]
r      = G mod 9                 # equivalent: 6b-chunk CSA then reduce; 64≡1 (mod 9)
p_wide = A[24:9]
idx4   = p_wide[3:0] ⊕ p_wide[7:4] ⊕ p_wide[11:8] ⊕ p_wide[15:12]
F      = ROM16x4[idx4]
r'     = (r + F) mod 9
p'     = p
idx    = p' + 2048 · ((2 · ((r' − (p' mod 9)) mod 9)) mod 9)
DMC_div= ⌊idx / 48⌋
bank   = idx mod 48
t'     = r' mod 3
u      = ⌊DMC_div / 3⌋
DMC_asm= t' + 3 · u
```

CRT facts (card): 2048≡5 (mod 9), 5·2≡1 (mod 9), inverse 2. Integer identity: `idx ≡ p' (mod 2048)` and `idx ≡ r' (mod 9)` when the formula is used as written.

**CONSTRAINT:** for every issued A, record `eq = (DMC_div == DMC_asm)`. Occupancy columns that claim “the” DMC must state which definition. Pass line uses DMC_div as the CRT-then-divide path **and** prints the mismatch count. Forbid substituting `G mod 384` or `t'` alone.

Topology after a chosen DMC (card §2.2):

```
u    = ⌊DMC / 3⌋
t    = DMC mod 3
die  = u[6]
local= t + 3·u[5:0]
HA   = ⌊local/2⌋
pipe = local mod 2
```

GOOD_MAP (100% good default): skip SRAM. Partial-good: 384×48 1R shared; XOR retry ≤2; `live5=p_wide[4:0]`; **forbid +1**.

```
b0 = bank
if mask[b0]==0: b1 = (b0 ⊕ live5) mod 48
if mask[b1]==0: b2 = (b1 ⊕ ((live5<<1)|1)) mod 48
bank_out = first live bi; else stay at b2
```

DMC does not change on retry.

## 4. Baseline mappers

Library integer-mod family (problem 同源 + card §4). These output a residue, then a bank slice. They are **not** 384-bucket CRT.

| Name | DMC | bank | SOURCE |
|------|-----|------|--------|
| B-%31 | G mod 31 | ⌊G/31⌋ mod 48 | ModMapper |
| B-%192 | G mod 192 | ⌊G/192⌋ mod 48 | Mod192Mapper; 192=64×3 |
| B-%248 | G mod 248 | ⌊G/248⌋ mod 48 | Mod248Mapper |
| B-XOR2 | 9b XOR-fold of G, then if x≥384: x−384 | 6b XOR-fold of G[>] mod 48 | card “power-of-two-only XOR” |

B-XOR2 (frozen wiring, 假设 H-XOR2 because the lab file is not in-repo):

```
x = XOR of 9-bit chunks of G          # width 9, values 0..511
dmc = x if x<384 else x-384
y = XOR of 6-bit chunks of (G>>1)
bank = y mod 48
```

Uniform on 2^k strides that toggle those chunks; factor-3 strides are the contrast, not a fit.

## 5. Occupancy identities and live bits

```
K = ⌊(W−base)/S⌋+1
|im| ≤ K
For linear f(G)=G mod N: |im| = N / gcd(δ, N), δ=S_g=S/512
```

SOURCE: problem YAML. When δ≡0 (mod 3), gcd(δ,384) eats the factor 3 ⇒ n_DMC ≤ min(384,K)/3, X_rel=3. When δ≡0 (mod 9), bank ×9 is lost.

Per-stride live bits (G):

| S | S_g=δ | 3-adic | p=G[10:0] | p_wide=G[15:0] | r=G mod 9 |
|---|------|--------|-----------|----------------|-----------|
| 512B | 1 | v_3=0 | walks | walks | walks |
| 1KiB | 2 | 0 | walks | walks | walks |
| 1536B | 3 | ≥1 | walks (gcd(3,2048)=1) | walks | walks period 3 |
| 3KiB | 6 | ≥1 | walks | walks | |
| 4608B | 9 | ≥2 | walks | walks | **frozen** |
| 12KiB | 24 | ≥1 | G[2:0] freeze in 8-step | walks | |
| 1.5MiB | 3072=3·2^10 | ≥1 | G[9:0] **frozen**; G[10] walks slow | G[9:0] freeze; G[15:10] walks by 3 | r frozen or slow |
| 2MiB | 4096=2^12 | 0 | G[10:0] frozen | G[11:0] frozen; p_wide high nibble may still move with base | 2-adic |

1.5MiB is **its own column**. Forbid averaging with 1536B into “S=3·2^k returns to 384”.

Issued set I = first min(K, Q_tot) AP points.

## 6. Little + roofline

```
Q_tot = 15360
X_rel = min(384, |I|) / n_DMC_I
BW ≤ n_DMC_I · μ_d                 # 假设 H-MU-D; default: do not print GB/s
```

GOOD_MAP 1R contention: 120 cores × issue cannot each get 1R/cycle. Occupancy recovery that waits on the port is not free BW. 100% good skips SRAM (card). This occupancy model counts map images; it does not invent a queueing closed form beyond Little: inflight / n_DMC vs inflight / 384.

min/mean = occupied-DMC visit min/mean on I. Kill uses that ratio, not a fitted BW.

## 7. T1 kill-lines (CONSTRAINTS)

1. Pointwise equality `idx/48` vs `(r' mod 3)+3·⌊(idx/48)/3⌋`. Forbid substituting `G mod 384` or `r' mod 3` for assembled DMC.
2. 1.5MiB n_DMC / min / mean as its **own** column; forbid averaging with 1536B into “S=3·2^k returns to 384”.
3. S=4608B, 100% good, sequential AP: kill if n_DMC ≤ min(384,K)/3 **OR** min/mean < 0.85.
4. GOOD_MAP 384×48 1R shared; 120-core contention named. XOR retry ≤2; forbid +1.
5. Random 0/6/12% vs 1/3-pattern **separate tables**. 3/9-factor strides vs power-of-two on the **same** table. H100 is not a ×3 proxy.

## 8. Calibration

| Item | Status |
|------|--------|
| CRT formula, ROM histogram, XOR-fold, r=(G mod 9) | exact (card) |
| Pointwise DMC_div vs DMC_asm | exact output; may fail |
| Linear-mod image sizes | exact gcd |
| 1.5MiB F covering all 9 residues | **not** a theorem; card says 6b entropy, “expectation” |
| H-XOR2, H-MU-D | 假设 |
| Silicon / H100 TB/s | forbidden |

## 9. Sensitivity

Most sensitive:

1. **v_3(δ)** — whether r freezes and whether p_wide still supplies F entropy.
2. **Which DMC definition is scored** — mismatch can move n_DMC by an integer factor.

Sweep: S ∈ {512B,1KiB,1536B,3KiB,4608B,12KiB,1.5MiB,2MiB} sequential, never averaged. Partial-good: random {0,6,12}% and 1/3-pattern as separate blocks. No fitted coeffs. Do not retune ROM to pass 4608B.

## 10. Magic-gap (CLAIM)

| CLAIM | Explainable |
|-------|-------------|
| n_DMC ~128 → 384 on S=3·2^k | CLAIM. True only if F mixes Z_3 and DMC_div tracks t'. 1.5MiB is not covered by the δ=3 argument. |
| min/mean 0.9–1.0 | CLAIM. ROM 6:5:5 on F mod 3 can imbalance even if 3 classes appear. |
| P(3 miss)≈1.7e-3 at 12% random | CLAIM (independent-retry sketch); 1/3-pattern is a different measure. |

## 11. Workloads

- S ∈ {512B, 1KiB, 1536B, 3KiB, 4608B, 12KiB, 1.5MiB, 2MiB}, sequential AP, never averaged.
- Partial-good: 100% good; random 0/6/12%; 1/3-pattern. Separate tables.
- 120-core shared GOOD_MAP 1R named on partial-good rows.
- Bench: `team-interleave-microbench`.

## 12. Forbidden

- Substituting G mod 384 or r' mod 3 for assembled DMC
- Averaging 1.5MiB with 1536B
- XOR retry +1
- decode-*; STREAM pass line; H100 ×3 proxy
- Hardcoded GB/s; CLAIM numbers as model inputs
- Joint ranking vs other Batch A cards
