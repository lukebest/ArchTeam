# T2 spec · P-0106/M-5 AffineRebind

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0106 / M-5 |
| Name | AffineRebind (per-DMC (α,β,n) + kth-one) |
| Problem | `problems/P-0106.yaml` (partial good / live set) |
| Mechanism | `mechanisms/P-0106/M-5.md` |
| T1 | `reviews/P-0106/M-5/tier1_synthesis.md`, `Dr.Sim.md` |
| Envelope | 负载基线 TEAM-SPEC / 问题 YAML (`team-384dmc-18432bank`) |
| Bench | `team-interleave-microbench` |
| Out of scope | CR-MRDR; no silicon ±15%; no cross-DMC steal |

The 负载基线 table lives off-repo (shared disk). **Do not cite a GitHub path for it.**

Main gain is **modulus 48 → n_live**, not picking α. `gcd(α,n)=1` ⇒ `gcd(α·S_g,n)=gcd(S_g,n)` for any S_g (integer identity). α search is a constant on gcd.

### 负载基线 TEAM-SPEC / 问题 YAML（口径冻结）

**Envelope (only interleave may change):** 2×Die2 × 60 core/die × 96 HA/die × 2 pipe/HA × 1 DMC/pipe × 48 bank/DMC → **120 core / 384 DMC / 18432 bank**.

| Quantity | Value | SOURCE |
|----------|--------|--------|
| grain / page / W | 512B / 4K / 8GiB=2^33 | 负载基线 TEAM-SPEC / 问题 YAML |
| outstanding / in-flight | 128 / core; Q_tot=15360 | 负载基线 TEAM-SPEC / 问题 YAML |
| stride range | 1B–2MiB | 负载基线 TEAM-SPEC / 问题 YAML |
| s_crit | 2^33/18432 ≈ 455.11 KiB | 问题 YAML |
| K @ 2MiB / ceiling | 4096 / 22.2% | 问题 YAML |
| production-like mask | **n=40 → L=32** (+ spare on that DMC), **uniform** | 负载基线 TEAM-SPEC |

**UNKNOWN (do not fill):** clock, μ_d, DRAM type, row-buffer / tCAS, per-bank peak, DMC microarchitecture. **Do not invent a production retire spectrum.**

**假设:** H-TXN = 512B/txn (负载基线 TEAM-SPEC); H-MAP-LAT = 1–2 cycle (card self-estimate, not silicon); H-MU-D named only.

No public silicon: no ±15% claim. Occupancy algebra is exact. Absolute BW is a **separate column** `n_DMC·μ_d` (假设 H-MU-D). **0.85** is the problem pass line, not a measured mean. Forbidden: H100 STREAM 91–94%, 353 ns, H100 row-remap as this-machine calibration.

**Generator:** `team-interleave-microbench`. **Public counterexamples:** STREAM, random p-chase, 2-power-only, resident SRAM/L2, decode-* packs.

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| W, grain, N_DMC, N_bank, Q_tot | — | 2^33, 512, 384, 18432, 15360 | 负载基线 TEAM-SPEC / 问题 YAML |
| s_crit | B | ≈455.11 KiB | 负载基线 TEAM-SPEC / 问题 YAML |
| n_prod | 1 | 40 (L=32+spare), uniform | 负载基线 TEAM-SPEC |
| M[d] | 1 | 48b live mask | card; per DMC |
| n | 1 | popcount(M) ∈ [0,48] | card |
| α | 1 | (Z/nZ)* ∩ listed candidates | card §2 |
| β | 1 | default 0 | card |
| g | 1 | XOR_fold6(G) ∈ [0,63] | T1 + 假设 H-FOLD6 |
| slot | 1 | (α·g+β) mod n | card |
| bank | 1 | kth_one(M, slot) | card |
| S_g | 1 | S>>9 | card |
| μ_d | B/s | UNKNOWN | 假设 H-MU-D |

**假设 H-FOLD6 (PIN).** Card says `g=XOR_fold6(G)` but does not list taps. Freeze forever:

```
for i=0..5:
  g[i] = XOR_{k≥0, i+6k ≤ 55} G[i+6k]
```

Never retune taps to fit results. Integer-AP gcd tables must **not** substitute for this netlist.

**假设 H-UP-DMC.** M-5 does not specify the DMC extractor (bank-only rebind, no cross-DMC). Freeze a 9-bit XOR-fold of G, then `dmc = x if x<384 else x-384`. Declare it. Do not use a silent `G mod 384` as if it were the card.

## 3. Mapper equations (bit-exact)

RUN:

```
g    = XOR_fold6(G)                 # H-FOLD6
dmc  = fold384_9b(XOR-fold9(G))     # H-UP-DMC
n    = popcount(M[dmc])
slot = (α[dmc] · g + β[dmc]) mod n  # n=0 is illegal config
bank = kth_one(M[dmc], slot)        # 48-wire prefix; 1 cycle in card
```

kth_one: index of the `slot`-th 1-bit (0-based) in M.

REPAIR α search (simulator **must** fill; also keep a true α=1 column):

```
candidates = {1,5,7,11,13,17,19,23,25,31,35,37,41,43,47}
legal      = {α ∈ candidates : gcd(α,n)=1}
score(α)   = max_{S ∈ Doc} gcd(α · S_g, n)
pick       = argmin score, tie → smallest α
```

Doc strides: {512B, 3×512B, 9×512B, 512KiB, 1MiB, 2MiB}, S_g=S>>9.

β=0 default.

## 4. Baseline mappers

| Name | Equation | SOURCE |
|------|----------|--------|
| B-norebind | slot0 = g mod 48; if M[slot0]=0 walk +1 until live (skip-dead) | card §4 “mod 48 + 跳死” |
| B-stack | if dead, nearest live neighbor (stacking) | M-1 sibling negative control |
| B-modn-a1 | (1·g+0) mod n → kth_one | T1 required middle column |
| P-minimax | card search α, then (α·g+β) mod n → kth_one | this card |
| B-fullgood | M=2^48−1, n=48, α=1 | full-good gain vs no-rebind ≈0 |

Primary contrast: **(mod 48 + skip-dead) vs (mod n, α=1)**. On large 2-power: (mod n, α=1) vs (mod n, minimax α) occupancy/BW diff <5% is a CONSTRAINT.

## 5. Occupancy identities and live bits

Integer identity (any S_g):

```
gcd(α,n)=1  ⇒  gcd(α·S_g, n) = gcd(S_g, n)
n_live_classes = n / gcd(S_g, n)     # per DMC, if g were an integer AP
```

The **silicon** g is XOR_fold6, domain 64 points, **not** Z/nZ. Print both:

- `classes_AP = n/gcd(S_g,n)` (sanity, not a substitute)
- `classes_net = |{ kth_one(M, (α·XOR_fold6(G0+k·S_g)+β) mod n) }|` on the issued AP

Dead hits must be 0.

Masks. **Do not invent a production retire spectrum.** SOURCE: 负载基线 TEAM-SPEC / 问题 YAML.

| Label | n | Factor 3? | Role |
|-------|---|-----------|------|
| n=40 uniform (L=32+spare) | 40=8×5 | no 3 | **钉死的生产像对照** — 负载基线 TEAM-SPEC |
| still mod 48 + skip-dead | 48 then skip | uses 48 | **required contrast** |
| full-good | 48 | yes | gain vs no-rebind ≈0 |
| 6.25 / 12.5 / 25% uniform | 45 / 42 / 36 | 36 still has 3 | **optional problem-scan sensitivity**, not yield, not 3-adic |
| 3-residue-biased | e.g. n=32 | 3 removed | T1 3-adic column only; not a invented fab map |

Issued set I = first min(K, Q_tot) AP points.

## 6. Little + roofline

```
X_rel_bank = (n / gcd_eff)  as classes; compare skip-dead vs mod-n
BW ≤ n_DMC_I · μ_d
BW ≤ Σ_d n_live_classes_d · μ_b
```

μ_d, μ_b UNKNOWN. Absolute BW is a **separate column** with μ_d labeled 假设. Default: no GB/s. Class-count ×3 is not BW ×3. Do not fill H100 STREAM 91–94% or 353 ns. **0.85 is the problem pass line, not a measured mean.**

## 7. T1 kill-lines (CONSTRAINTS)

1. RUN netlist pins `g=XOR_fold6(G)`. Fail if any request hits M=0, or per-DMC class count vs `n/gcd(S_g,n)` differs by ≥2 **as a sanity flag** (netlist may legally differ — print both), or min/mean < 0.85 (BW clause unevaluated without timings).
2. Large 2-power: (mod n, α=1) vs (mod n, minimax) occupancy diff <5%. Main gain in (mod 48+skip-dead) vs (mod n, α=1). Uniform 25% is **not** 3-adic.
3. Dead hits=0. Simulator fills α via the card search **and** keeps a true α=1 column.
4. `team-interleave-microbench` three masks on one table: full-good, n=40 uniform, 1/3-residue-biased. Full-good gain vs no-rebind ≈0. No H100 row-remap calibration.
5. Never retune XOR_fold6 taps.

## 8. Calibration

| Item | Status |
|------|--------|
| gcd identity under gcd(α,n)=1 | exact |
| kth_one bijection onto live set | exact |
| XOR_fold6 image of an AP | exact only via the netlist |
| n=40 → L=32 uniform | 负载基线 TEAM-SPEC (not measured yield) |
| 6.25/12.5/25% | optional problem-scan sensitivity; not a production spectrum |
| H-FOLD6, H-UP-DMC, H-MU-D, H-TXN, H-MAP-LAT | 假设; not silicon |
| Clock / DRAM type / tCAS / per-bank peak | UNKNOWN; not filled |

## 9. Sensitivity

1. **n versus 48** (whether 3 remains in n).
2. **g netlist vs integer AP** (XOR_fold6 can change class occupancy vs the gcd table).

Sweep: Doc S (must include factor-3 strides) × **required** {n=40 uniform, mod-48 skip-dead} plus optional {full-good, 6.25/12.5/25%, 3-biased}. Columns: skip-dead, mod-n α=1, minimax. No fitted α. Do not invent a fab retire map.

## 10. Magic-gap (CLAIM)

| CLAIM | Explainable |
|-------|-------------|
| ×1.5–×3 class gain on large 2-power | CLAIM vs skip-dead; equals `n/gcd(S_g,n)` vs leftover live classes after skip-dead |
| 3-biased BW 0.7–0.95 | CLAIM (has 0.85 in it); occupancy model reports classes + min/mean visits only |
| α search improves gcd | **false** under gcd(α,n)=1; CLAIM if someone attributes gain to α |

## 11. Workloads

SOURCE: 负载基线 TEAM-SPEC / 问题 YAML + card §4 + T1. Generator: `team-interleave-microbench`.

**Pass pack (this card) — 钉死:**

- Mask: **n=40 → L=32**, **uniform**. Contrast: **still `mod 48` + skip-dead**.
- Documented S **must include factor 3:** {512B, 3×512B, 9×512B, 512KiB, 1MiB, 2MiB}, S_g=S>>9.
- Full-good row: gain vs no-rebind ≈0.
- **Do not invent a production retire spectrum.**

**Optional sensitivity (problem-scan TEAM-SPEC, not yield):** uniform 6.25% / 12.5% / 25%. Uniform 25% (n=36) still has factor 3 — not a 3-adic test. T1 3-residue-biased remains a separate diagnostic column, not a fab map.

**Public counterexamples (not pass lines):** STREAM, random p-chase, 2-power-only, resident SRAM/L2, decode-* packs, H100 row-remap as silicon.

## 12. Forbidden

- Cross-DMC borrow; `core_id`
- Substituting integer-AP gcd tables for XOR_fold6
- Calling uniform 25% (n=36) a 3-adic test
- Hand-writing α=1 and labeling it “rebound”
- Retuning fold taps; H100 row remap as calibration
- Inventing a production retire spectrum
- decode-*; STREAM / p-chase / 2-power-only / resident as pass lines
- H100 row remap; H100 STREAM 91–94%; H100 353 ns; hardcoded GB/s
- Treating 0.85 as a measured mean
- Joint ranking vs other Batch A cards
