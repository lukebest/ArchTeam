# T2 spec · P-0105/M-4 SNS

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0105 / M-4 |
| Name | Shear + Nonlinear S-box (SNS) |
| Problem | `problems/P-0105.yaml` (start-address phase) |
| Mechanism | `mechanisms/P-0105/M-4.md` |
| T1 | `reviews/P-0105/M-4/tier1_synthesis.md`, `Dr.Sim.md` |
| Envelope | TEAM-SPEC `team-384dmc-18432bank` |
| Bench | `team-interleave-microbench` |
| Out of scope | CR-MRDR; AES/GF(256); no silicon ±15% |

`fold384` covering `4096=10·384+256` ⇒ maxload 11 / min 10 / CV≈0.044 is a **12-bit uniform covering bound**, independent of the S-box. **Forbidden** to calibrate the model against those numbers as golden mechanism results.

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| W, grain, N_DMC, N_bank, Q_tot | — | 2^33, 512, 384, 18432, 15360 | YAML; identities |
| x12 | 1 | phys[20:9] | card §2 |
| y12 | 1 | phys[32:21] | card §2 |
| x' | 1 | (x+7y) mod 2^12 | card; 12b truncate |
| S(u) | 1 | (u^5+u^3+u) mod 256 | card; **integer**, not GF(256) |
| z | 1 | S[x'[11:4]] XOR y[7:0] | card |
| raw | 1 | (z<<4) \| x'[3:0] ∈ [0,4095] | card |
| DMC | 1 | fold384(raw) ∈ [0,383] | card |
| bank_in | 1 | x'[9:4] mod 48 | card; 6b window |
| μ_d | B/s | UNKNOWN | 假设 H-MU-D |

ROM check (locked): `S(0..15)=[0,3,42,17,68,183,62,5,8,139,146,89,204,255,166,141]`. SOURCE: card §2.

## 3. Mapper equations (bit-exact)

Shear uses the card netlist, 12-bit truncate (not arbitrary-precision):

```
seven_y = ((y12 << 3) − y12) & 0xFFF
x'      = (x12 + seven_y) & 0xFFF
```

S-box: ROM[u] = (u^5 + u^3 + u) mod 256, u∈[0,255]. Startup checksum of the first 16 entries. **Not AES. Not GF(256).**

```
z    = ROM[x'[11:4]] XOR y12[7:0]
raw  = (z << 4) | x'[3:0]
```

fold384 (12-bit coarse quotient + one correction; equivalent to raw mod 384 on {0..4095}):

```
q = min(⌊raw/384⌋, 10)     # 384·10=3840, 384·11=4224>4095
r = raw − 384·q
if r ≥ 384: r −= 384        # one correction
DMC = r
```

bank:

```
w = x'[9:4]                 # 6b, 0..63
bank_in = w if w<48 else w−48
```

**Uniform covering bound (not a mechanism result):** if raw is uniform on 4096 values, 4096=10·384+256 ⇒ 256 DMC get 11 hits and 128 get 10; max=11, min=10, CV=√(Var)/mean with that histogram. Print this as `COVERING_BOUND` only. Never use it as a golden target to tune S or fold.

## 4. Baseline and ablation mappers

| Name | Equation | SOURCE |
|------|----------|--------|
| B-mod384 | DMC=G mod 384; bank=G mod 48 | card §4 |
| B-low | DMC=G[8:0] if <384 else G[8:0]−384; bank=G[5:0] mod 48 | sequential low-bit |
| B-high | DMC=y12 mod 384; bank=y12 mod 48 | high-bit-only |
| ABL-shear | x' as above; raw=x'; DMC=fold384(x'); bank from x' | card ablation “shear-only” |
| ABL-sbox | no shear: z=S[x12[11:4]]; raw=(z<<4)\|x12[3:0]; no XOR y | card: S-box(x[11:4]) only |

ABL-sbox at S=2MiB **must** make n_DMC vary with phase (x frozen ⇒ z frozen ⇒ raw frozen). If it does not, the ablation failed to isolate shear.

## 5. Occupancy identities and live bits

S=2MiB: x12 frozen (phase), y12 walks 0..4095 over K=4096. Shear: x'(k)=x+7k (mod 4096) is a permutation of the 4096 points (7 odd). bank_in uses a 6b window of x': 64 values then mod 48 ⇒ **6 banks/DMC** if DMC is already chosen independently — here DMC depends on z and x'[3:0], so report the **per-DMC bank histogram** and `bank%8` kinds; do not assume 48.

S=512B: y frozen in a short issued window; x walks.

S=4608B: 3-adic × phase. Report **alone**.

Issued set I = first min(K,Q_tot) AP points.

Relative occupancy diff across bases:

```
rel = (max_b n_DMC(b) − min_b n_DMC(b)) / mean_b n_DMC(b)
```

and the same for visit-share vectors if needed. T1: n_DMC=384 and occupancy relative-diff <5% at S=2MiB. Winning only min/mean while losing absolute BW = fail — this occupancy model has no DRAM timing, so it **cannot** pass a BW-absolute test; it reports occupancy only and marks the BW clause as an unevaluated CONSTRAINT.

## 6. Little + roofline

```
X_rel = min(384, |I|) / n_DMC_I
BW ≤ n_DMC_I · μ_d          # 假设 H-MU-D; default no GB/s
```

Shear walks the row-buffer axis; occupancy ≠ DRAM BW. Do not convert covering CV into GB/s.

## 7. T1 kill-lines (CONSTRAINTS)

1. ROM locked to the integer polynomial; S=2MiB page-inner bases **and** 2MiB-aligned: n_DMC=384 and occupancy relative-diff across bases <5%. Only winning min/mean while losing absolute BW = fail (absolute BW not computed here).
2. Report bank histogram and bank%8 kinds. 6b window at S=2MiB collapses toward 6 banks/DMC.
3. Ablations: shear-only; S-box(x[11:4]) only — latter **must** vary n_DMC with phase at S=2MiB.
4. Base sweeps: 512B-grain phases **and** 2MiB-aligned, separate. S∈{2MiB,1MiB,512KiB,4608B,512B}. 4608B alone.
5. Covering 11/10/CV≈0.044 is **not** a golden mechanism result.
6. `team-interleave-microbench`; no decode-*; H100 is not a 384-bucket proxy.

## 8. Calibration

| Item | Status |
|------|--------|
| S(0..15) checksum, 12b shear netlist, fold384 on 12b | exact |
| Uniform covering 11/10 | exact **counterfactual** if raw uniform; not a measured SNS output |
| S-box discrepancy vs base | experimental; no Weil bound |
| H-MU-D | 假设 |
| DRAM tRRD/tCCD/tFAW | UNKNOWN; not filled |

## 9. Sensitivity

1. **Presence of shear** (ablation n_DMC vs phase at S=2MiB).
2. **Base alignment** (512B-grain vs 2MiB-aligned).

Sweep: those two base families × S set. Never retune S(u) after seeing CV.

## 10. Magic-gap (CLAIM)

| CLAIM (card §3) | Explainable |
|-----------------|-------------|
| maxload=11, min=10, CV≈0.044 at S=2MiB | CLAIM if presented as SNS. Explainable as uniform-raw covering **only**. |
| cross-base relative-diff = 0 | CLAIM. Model reports the measured occupancy rel-diff. |
| S=4608B CV≈0.13–0.14 | CLAIM; 4608B is its own column. |

## 11. Workloads

- S ∈ {2MiB, 1MiB, 512KiB, 4608B, 512B}.
- Bases: 512B-grain phases in `0..4K−512`, **and** 2MiB-aligned, separate tables.
- Ablation rows on the same S=2MiB bases.
- Bench: `team-interleave-microbench`.

## 12. Forbidden

- AES / GF(256) S-box
- Calibrating against 11/10/0.044 as golden
- Averaging 4608B into a 2-power row
- decode-*; STREAM pass; H100 384-proxy; hardcoded GB/s
- Joint ranking vs other Batch A cards
