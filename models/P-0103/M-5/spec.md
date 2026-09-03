# T2 spec · P-0103/M-5 B3CSH

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0103 / M-5 |
| Name | Base-3 Carry-Save Hash (B3CSH) |
| Problem | `problems/P-0103.yaml` |
| Mechanism | `mechanisms/P-0103/M-5.md` |
| T1 | `reviews/P-0103/M-5/tier1_synthesis.md`, `Dr.Sim.md` |
| Envelope | 负载基线 TEAM-SPEC / 问题 YAML (`team-384dmc-18432bank`) |
| Bench | `team-interleave-microbench` |
| Out of scope | CR-MRDR; no silicon ±15% |

The 负载基线 table lives off-repo (shared disk). **Do not cite a GitHub path for it.**

`dmc_odd = (d0+d1+d2) mod 3`. **Forbidden:** using `d0` as the DMC trit. Integer identity: `Σ trit(C_i) = d0 + 3·d1 + 9·d2` ⇒ `Σ mod 3 = d0`. The two formulas differ.

### 负载基线 TEAM-SPEC / 问题 YAML（口径冻结）

**Envelope (only interleave may change):** 2×Die2 × 60 core/die × 96 HA/die × 2 pipe/HA × 1 DMC/pipe × 48 bank/DMC → **120 core / 384 DMC / 18432 bank**.

| Quantity | Value | SOURCE |
|----------|--------|--------|
| grain / page / W | 512B / 4K / 8GiB=2^33 | 负载基线 TEAM-SPEC / 问题 YAML |
| outstanding / in-flight | 128 / core; Q_tot=15360 | 负载基线 TEAM-SPEC / 问题 YAML |
| stride range | 1B–2MiB | 负载基线 TEAM-SPEC / 问题 YAML |
| s_crit | 2^33/18432 ≈ 455.11 KiB | 问题 YAML |
| K @ 2MiB / ceiling | 4096 / 22.2% | 问题 YAML |

**UNKNOWN (do not fill):** clock, μ_d, DRAM type, row-buffer / tCAS, per-bank peak, DMC microarchitecture.

**假设:** H-TXN = 512B/txn (负载基线 TEAM-SPEC); H-MAP-LAT = 1–2 cycle (card self-estimate, not silicon); H-MU-D named only.

No public silicon: no ±15% claim. Occupancy algebra is exact. Absolute BW is a **separate column** `n_DMC·μ_d` (假设 H-MU-D). **0.85** is the problem pass line, not a measured mean. Forbidden: H100 STREAM 91–94%, 353 ns, 10 MC as ×3 proxy.

**Generator:** `team-interleave-microbench`. **Public counterexamples:** STREAM, random p-chase, 2-power-only, resident SRAM/L2, decode-* packs.

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| W, grain, N_DMC, N_bank, Q_tot | — | 2^33, 512, 384, 18432, 15360 | 负载基线 TEAM-SPEC / 问题 YAML |
| s_crit | B | ≈455.11 KiB | 负载基线 TEAM-SPEC / 问题 YAML |
| C0..C7 | 1 | 3b chunks of A[32:9] | card §2.2 |
| trit(c) | 1 | ROM[c] ∈ {0,1,2} | card table |
| (s,cy) | 1 | CSA: a+b+c = s+3·cy | card; integer |
| d0,d1,d2 | 1 | tree digits | card §2.2 |
| dmc_odd | 1 | (d0+d1+d2) mod 3 | card |
| r_hash | 1 | d0+3·d1 ∈ [0,8] | card |
| p_mix[i] | 1 | G[10−i] ⊕ G[11+i], i=0..10 | card |
| DMC | 1 | dmc_odd + 3·p_mix[6:0] | card |
| bank_in | 1 | (r_hash mod 3)+3·p_mix[10:7] | card |
| μ_d | B/s | UNKNOWN | 假设 H-MU-D |

TRIT_ROM (locked, histogram 3,3,2):

```
c    0 1 2 3 4 5 6 7
trit 0 1 2 0 1 2 0 1
```

## 3. Mapper equations (bit-exact)

Chunks:

```
C0=A[11:9]=G[2:0]   C1=A[14:12]=G[5:3]
C2=A[17:15]=G[8:6]  C3=A[20:18]=G[11:9]
C4=A[23:21]=G[14:12] C5=A[26:24]=G[17:15]
C6=A[29:27]=G[20:18] C7=A[32:30]=G[23:21]
```

w0[i] = TRIT_ROM[C_i].

CSA tree (copy card; 0-padded 3:2):

```
(s0,c0)=CSA(w0[0],w0[1],w0[2])
(s1,c1)=CSA(w0[3],w0[4],w0[5])
p0=w0[6]; p1=w0[7]
(s2,c2)=CSA(s0,s1,p0)
(s3,c3)=CSA(s2,p1,0)          # s3 = d0
(s4,c4)=CSA(c0,c1,c2)
(s5,c5)=CSA(s4,c3,0)          # s5 = d1
(d2,_)=CSA(c4,c5,0)
```

Each CSA: `s=(a+b+c) mod 3`, `cy=⌊(a+b+c)/3⌋`. Sanity: `d0+3·d1+9·d2 == Σ w0[i]` (integer).

```
r_hash  = d0 + 3·d1
dmc_odd = (d0 + d1 + d2) mod 3          # NOT d0; NOT d2 alone
p_mix[i]= ((G>>(10-i))&1) XOR ((G>>(11+i))&1)   # i=0..10
DMC     = dmc_odd + 3 · p_mix[6:0]      # p_mix[0] is LSB
bank_in = (r_hash mod 3) + 3 · p_mix[10:7]
die     = p_mix[6]
local   = dmc_odd + 3 · p_mix[5:0]
HA      = ⌊local/2⌋
pipe    = local mod 2
```

GF(2) rank of the 11×22 map G[0..21] → p_mix[0..10] is computed **once** at start. Do not claim rank 11.

Partial-good select-k (card §2.4):

```
k = (r_hash mod 3) + 3 · p_mix[10:7]
i* = min{ i | prefix_pop(mask,i) == (k mod N_good) + 1 }
```

**After `k mod N_good`, forbid another mod 3.** N_good=32 vs N_good=36 are separate tables.

## 4. Baseline mappers

Same family as MRFI §4: B-%31, B-%192, B-%248, B-XOR2 (9b XOR-fold, 假设 H-XOR2 identical freeze). Plus a **control** mapper that uses `G mod 3` as the DMC trit and the same p_mix[6:0]:

```
DMC_ctrl = (G mod 3) + 3 · p_mix[6:0]
```

SOURCE: T1 Sim kill-line (“G mod 3 as DMC trit control n_DMC≈128”).

## 5. Occupancy identities and live bits

Named flip probes (card §3; must print C0..C7 flip counts on sequential AP):

| δ = S_g | S | Named live chunks |
|---------|---|-------------------|
| 3 | 1536B | C0 (gcd(3,8)=1) |
| 9 | 4608B | C0 and C1 (`9=8+1`) |
| 24 | 12KiB | C0 frozen; C1 always; C2 on carry |
| 3072 | 1.5MiB | C0..C2 frozen; C3 += 6 |

S=2MiB: G[11:0] frozen ⇒ `p_mix[0]=G[10]⊕G[11]` both dead. 2-adic rank of p_mix[6:0] **may drop**. Declare `|p_mix[0]|=1` and the computed rank; do not hide a 192-bucket image as n_DMC=384.

Issued set I = first min(K, Q_tot) AP points.

Cramér-V on I at δ=9:

```
V = sqrt( χ² / (n · min(r-1,c-1)) )   on 3×3 table (dmc_odd, G mod 3)
```

Integer identity, not a fit. Control: same I, DMC_ctrl n_DMC ≈ 128 when 3|δ.

## 6. Little + roofline

```
X_rel = min(384, |I|) / n_DMC_I
BW ≤ n_DMC_I · μ_d          # 假设 H-MU-D; ABSOLUTE BW is a separate column
```

Default: no GB/s. Do not fill H100 STREAM 91–94% or 353 ns. **0.85 is the problem pass line, not a measured mean.**

LUT 3,3,2 bias is visible in the issued histogram. “Covered Z_3 ⇒ min/mean≥0.9” is forbidden as an implication.

## 7. T1 kill-lines (CONSTRAINTS)

1. Copy `dmc_odd=(d0+d1+d2) mod 3`; forbid d0 stand-in. If any S∈{1536B,4608B,12KiB,1.5MiB,2MiB} has n_DMC<384, **or** at S=2MiB `|{p_mix[0]}|=1`, **declare** (do not hide).
2. δ=9 (S=4608B): C0,C1 flips match the name; Cramér-V(dmc_odd, G mod 3)<0.3; G-mod-3 trit control n_DMC≈128. Correlation ≥0.8 **fails**.
3. After `k mod N_good`, forbid another mod 3. N_good=32 vs 36 separate tables.
4. Print C0..C7 flips every S. Main bench `team-interleave-microbench`. H100 is not a ×3 proxy.
5. Compute GF2_11 rank once; do not claim 11.

## 8. Calibration

| Item | Status |
|------|--------|
| CSA integer identity, ROM table, chunk cuts, p_mix wiring | exact |
| GF(2) rank | exact (computed) |
| “one live trit ⇒ d0 full Z_3” | exact for isolated full-run chunk; **not** a theorem for dmc_odd under carry correlation |
| expander / Weil / min/mean 0.9 | not theorems |
| H-XOR2, H-MU-D, H-TXN, H-MAP-LAT (card 1–2 cycle) | 假设; not silicon |
| Clock / DRAM type / tCAS / per-bank peak | UNKNOWN; not filled |

## 9. Sensitivity

1. **Whether dmc_odd stays independent of G mod 3** (Cramér-V at δ=9).
2. **Frozen p_mix taps at S=2MiB** (rank drop).

Sweep: same S set as MRFI, never averaged; print flips + V + rank. No retune of ROM or p_mix taps.

## 10. Magic-gap (CLAIM)

| CLAIM | Explainable |
|-------|-------------|
| n_DMC 128→384 on named δ | CLAIM. Requires dmc_odd full Z_3 **and** p_mix[6:0] full 128. S=2MiB may fail the second. |
| min/mean 0.9–1.0 | CLAIM. 3,3,2 ROM + carry correlation. |
| “3-value expander” | CLAIM / analogy; no spectral gap. |

## 11. Workloads

SOURCE: 负载基线 TEAM-SPEC / 问题 YAML + card §4 + T1. Generator: `team-interleave-microbench`.

**Pass pack (this card):**

- **Named δ ∈ {3, 9, 24, 3072}** ⇒ S ∈ {1536B, 4608B, 12KiB, 1.5MiB}, plus the rest of **3·2^k** and 2-power contrast on the same never-averaged table: {512B, 1KiB, 3KiB, 2MiB}.
- Print C0..C7 flip counts every S; named rows must match δ=3→C0, δ=9→C0+C1, δ=24→C1+C2, δ=3072→C3.
- **After `k mod N_good`, forbid another mod 3.** N_good=32 vs 36 remain separate tables.
- Control column: G mod 3 as DMC trit.
- Sequential AP.

**Public counterexamples (not pass lines):** STREAM, random p-chase, 2-power-only, resident SRAM/L2, decode-* packs.

## 12. Forbidden

- d0 as DMC trit; d2 as DMC trit
- Another mod 3 after k mod N_good
- Claiming GF(2) rank 11 without the computed number
- Hiding S=2MiB p_mix[0] death as n_DMC=384
- decode-*; STREAM / p-chase / 2-power-only / resident as pass lines
- H100 ×3; H100 STREAM 91–94%; H100 353 ns; hardcoded GB/s
- Treating 0.85 as a measured mean
- Joint ranking vs other Batch A cards
