# T2-style spec · P-0198/M-5r2 CRRF-SS（k 槽缝合，不加线）

## 1. Identity

| Field | Value |
|-------|--------|
| ID | P-0198 / M-5r2 |
| Name | CRRF-SS（slot-stitch；无 epoch / bind） |
| Problem | `problems/P-0198.yaml` |
| Mechanism | `mechanisms/P-0198/M-5r2.md` |
| Parent | M-5 排他 epoch（T3 存活、Snp 15:1 KILL）；M-5r1 CRRF-SB（T1 FAIL，PR #95） |
| Envelope | DV200 `tests/soc_sim`（同源 `github:lukebest/bufferless-ring-noc@63163cad`） |

**禁止编辑** `mechanisms/P-0198/M-5.md`、`M-5r1.md`、`reviews/`。

主指标 = **推理** makespan/尾。训练不单独过关。所有数字 UNSIGNED。

## 2. Width (IHI0050E.b)

```
W_snp = 37 + 2N + SAW + M          # Table 13-8; N∈[7,11], SAW∈[41,49], M∈{0,11}
S_keep = 1 + 2 + N + 1 + 1         # valid + ch_disc + dest + i-tag + e-tag
U      = W_snp − S_keep            # plus overview-88 / conserv-U68 pins
D      = Data + BE + H_frag        # H_frag=32; BE=Data/8
k      = ⌈D / U⌉
```

64 B k ∈ [6,9]（Issue E 合法）。128 B k ∈ [12,18]（非法宽度，灵敏度）。
KILL 在 **最坏 k=18**（U=68，D=1184）。

```
C_dat_off = 2
C_snp_off = 1
C_dat_on  = 2 + (1/k)·f_cap     # f_cap≤1
T_dat / T_off ≥ 2 / (2 + 1/k)
```

禁止 `1+duty_dat`。k=1 标 `FAKE_WIDTH`。

## 3. Mix

15:1 = 并发提供的 Dat beat : Snp flit。75% kv_decode gather → sink 0，25% P2P，Snp 源在 sink 最后一跳（节点 1 与 N−1）。

## 4. Ablations

`stitch-off`（无 ghost）、`src-fc`、`stitch`、`cap-off`、`header-only`、`drain-off`、`k1-cheat`。
无 epoch ⇒ `header-only ≡ drain-off ≡ stitch`。必须印出来。
