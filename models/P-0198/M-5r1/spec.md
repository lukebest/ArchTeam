# T2-style spec · P-0198/M-5r1 CRRF-SB（Snp 本征残留抢回）

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0198 / M-5r1 |
| Name | CRRF-SB（Channel–Ring Rebind + Snp Steal-Back） |
| Problem | `problems/P-0198.yaml` |
| Mechanism | `mechanisms/P-0198/M-5r1.md` |
| Parent | P-0198/M-5 CRRF T1-return-1；T3 night 审计 `reviews/P-0198/M-5/t3_night_audit.md` |
| Envelope | DV200 `tests/soc_sim`（同源 `github:lukebest/bufferless-ring-noc`） |
| Style | 物理槽守恒 + 本征残留 + 宾客 ghost 税（非曲线拟合） |

**禁止编辑** `mechanisms/P-0198/M-5.md`、`reviews/`、`problems/`、`FUNNEL.md`。

**禁止混结论**：不与 M-1/M-2/M-4 排名。消融：`rebind-off`、`sb-off`（M-5 排他）、`ghost-off`、源端 FC。

主指标 = **推理** makespan/尾。训练集合不单独过关。

### 信封

与 M-5 T2 spec 同一组公开钉：12+2、512 B、ost 读 512 / 写 256、duty∈{3:1,7:1,15:1}+rebind-off。Snp **无公开 ns**，只报相对比。

T3 night **已测、未签字、不得贴**：`snp_path` 15:1 = 17.0533；mixed 15:1 = 32.5873；T2 代数 1.5625；gather on-arm 0.551。本模型重算 M-5 排他窗（粗量子）与 M-5r1 等空槽，对照这些钉子，**不替换** 它们。

0.85 = pass bar ≠ mean。无硅 ±15%。

## 2. Variables

沿用 M-5：`r`、`duty_dat`、`C_ring`、`T_drain`、`f_steady`、`C_dat_eff`。新增：

| Symbol | 含义 | SOURCE |
|--------|------|--------|
| ρ_wire | Snp 物理环占用（在途本征 + 在途 ghost） | 假设 H-WIRE |
| λ_snp | Snp 提供负载（稀疏默认 0.05） | H-SNP-SPARSE |
| E[wait_epoch] | M-5 等 SNP_EPOCH（粗量子） | T3 报告；H-EPOCH-COARSE |
| E[wait_empty] | M-5r1 等本地空槽 | H-SNP-LAT-SB |
| p_steal | 有 Snp pending 时空槽被本征抢走的份额 | 定义 ≈ λ_snp 上界 |
| C_dat_eff_sb | 扣 steal-back 后的 Dat 有效槽 | `1 + duty_dat·f_steady·(1-p_steal) − τ_*` |

`q_coarse = T_steady / (r+1)`（一次 bind 世代的 DAT 段，含随后 drain 摊还到等待）。T2 默认 `q=1` **只作对照列**，标明 `NOT a legal cycle schedule`。

## 3. Equations

### 3.1 槽守恒（精确）

```
S_phys = 1
C_dat_ideal = 1 + duty_dat          # 上界；duty_dat=1 禁
C_dat_eff_sb ≤ C_dat_ideal
C_dat_eff_sb < 2
```

steal-back 税：

```
p_steal = min(1, λ_snp / max(duty_snp, ε))   # 稀疏 → 小
C_ghost_sb = duty_dat · f_steady · (1 - p_steal)
C_dat_eff_sb = clamp(1 + C_ghost_sb - τ_sync - τ_bind, 1, 1+duty_dat)
```

`flag_untaxed_double` 必须为假。

### 3.2 M-5 排他窗（对照，粗量子）

T3 已说明合法周期量子不是 `q=1`：

```
T_period_coarse = T_steady + T_drain          # 一次 DAT 世代 + 为切到 SNP 付的 drain
E[wait_epoch]   = duty_dat · (T_period_coarse / 2)
T_snp_m5 / T_off = (L_snp + E[wait_epoch]) / L_snp
```

`q=1` 细槽公式保留为「T2 曾用、周期不合法」列，15:1 = 1.5625 仅作历史对照。

### 3.3 M-5r1 等空槽（H-SNP-LAT-SB）

本征 Snp 不看 epoch。无缓冲、过路赢：

```
ρ_wire = clamp(ρ_ghost_inflight + ρ_snp_transit, 0, 1-ε)
E[wait_empty] = ρ_wire / (1 - ρ_wire)          # 几何，假设 H-GEO
T_snp_sb / T_off = (L_snp + E[wait_empty]) / L_snp
```

稀疏推理：`ρ_wire ≈ duty_dat · f_steady · (1-p_steal)` 的在途份额，默认再乘占用因子 `α_occ∈(0,1)`（H-WIRE）。杀假设：`T_snp_sb/T_off > 1.4` → 该臂失败。

Snp 饱和对照（H-SNP-CAP）仍用 `1/C_snp_native`；本征残留下 `C_snp_native→1`（不受 duty 削），饱和比应变回 ~1，而不是 M-5 的 `1/(duty_snp·f_steady)`。

### 3.4 Dat 相对 makespan（H-DAT-DOM，推理）

仅 Dat 重已坍 / 均匀读饱和 / 推理 KV-P2P 代理：

```
T / T_off = 1 / C_dat_eff_sb
```

card-claim 0.55–0.85× **NOT measured**。broadcast 中性。禁止把 0.551/0.583 写入本列当签字。

源端 FC 对照：`C_dat=1`，只减 outstanding（本解析不缩短 Dat 槽上界）→ `T/T_off=1`（假设 H-SRC-FC-NO-SLOT）。若某实现靠节流改善崩塌，必须 cycle 证明 makespan/尾缩短，不得用 `p_inj`。

## 4. 必须留给 cycle / soc_sim 的

1. 同拍残留仲裁 vs 过路
2. Drain 不停本征 Snp
3. RBRG 以 channel-id 为权威
4. 15:1 混合推理窗的 Snp 尾
5. `sb-off` / `ghost-off` / 源端 FC / 无 CC 四臂
6. 满 12+2 四环（本解析是单环代理）

## 5. model.py contract

- stdlib；`python3 models/P-0198/M-5r1/model.py`
- 打印守恒、M-5 粗量子 vs T2 q=1 vs SB 等空槽、Dat 相对比、四臂对照
- 所有相对比标 `hypothesis` / `NOT measured`
- 退出码 0
