# T2 spec · P-0198/M-5 CRRF（通道–环重绑织物）

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0198 / M-5 |
| Name | Channel–Ring Rebind Fabric (CRRF) |
| Problem | `problems/P-0198.yaml` |
| Mechanism | `mechanisms/P-0198/M-5.md`（PR #53 tip；main 尚未着陆卡正文，本 spec 摘自该卡 T1-return-1 + T1） |
| T1 | `reviews/P-0198/M-5/tier1_synthesis.md`（PR #61 已合 main） |
| Envelope | DV200 `tests/soc_sim`（同源 `github:lukebest/bufferless-ring-noc`） |
| Style | LIMINAL / roofline（物理槽守恒 + 时间复用记账 + drain/SYNC 税；非吞吐曲线拟合） |
| Out of scope | 每 die FSM 按拍推进；SYNC 采样偏斜窗内的逐 flit 注入/弹出；RBRG 对侧多桥共识；消息级到达神谕；team-384dmc / decode-* / STREAM 代理 |

**禁止编辑** `mechanisms/`、`reviews/`、`problems/`、`FUNNEL.md`。本树只新增 `models/P-0198/M-5/{spec.md,model.py,insight.md}`。

**禁止混结论**：本卡不与 M-1 / M-2 / M-4 做联合排名、联合加速比或「哪张更好」叙事。消融只对 **rebind-off（本卡 1:1）**。

### 信封（口径冻结）

| Quantity | Value | SOURCE |
|----------|--------|--------|
| 拓扑 | 12 top + 2 bottom；CHI Req/Rsp/Snp/Dat 各自独立成环；环间经 RBRG | 问题 YAML / bufferless-ring-noc README |
| highway | 每方向每拍 **1** 槽；无片上 flit 队列 | 问题 YAML；卡 §1 |
| 请求粒 | 512 B（均匀读/写基线） | 问题 YAML |
| outstanding | 读 512 / 写 256（AIC；额外流控关） | 问题 YAML；卡 §4 |
| 底环 CS 数（文档例） | 25 CS / FullRing（bottom manyring） | `docs/topology.md`；解析用 `C_ring` 扫描，不把周长钉成绝对 makespan |
| 端点 | 分流量类 makespan、完成事务数、collapsed；**Snp makespan 与 Snp completions** | 问题 YAML；T1 条件 3 |
| duty 扫描 | `{3:1, 7:1, 15:1}` + rebind-off | 卡 §4；T1 条件 3 |
| runtime hint | 至多 advisory；正确性不依赖 `COLL_EP` | 卡 §0 / §2.4；T1 条件 4 |

### 公开基线钉（harness 输出，非硅）

Makespan（与 M-1 同钉：`docs/srcfc_ca_model/data.json` scheme=`off`，与问题 YAML 一致处优先 YAML）：

| 流量类 | T_off (ns) | collapsed（公开扫描） | SOURCE |
|--------|------------|----------------------|--------|
| uniform_read | 4403.2 | 峰值后坍至 ~2.8–3.4 TB/s（YAML）；collapse_settings 亦标 true | 问题 YAML；data.json |
| uniform_write | 4834.6 | 平台 ~5.5 TB/s（YAML） | 问题 YAML；data.json |
| broadcast | 492.0（data.json）；YAML 强调 peak goodput ~117.76 B/ns、collapsed=false | false | YAML + data.json |
| gather | 537.2 | true（8192B / ost 512） | data.json + collapse_settings |
| reduce | 537.2 | true | 同上 |
| allgather | 1668.6 | true | 同上 |
| allreduce | 990.6 | true | 同上 |
| alltoall | 4098.0 | true | 同上 |
| snp_path | **无公开 ns** | n/a | 问题 YAML 未报 Snp makespan；本卡只报 **相对比** `T_hat/T_off` |

均匀读负载曲线钉：offered ~5767 B/ns → goodput ~5761 → 崩至 ~2.8–3.4 TB/s。SOURCE: 问题 YAML。

**0.85** = 问题及格线 / 卡约束条，**不是**测得均值。禁止用各类平均加速或 min/mean≥0.85 叙事过关。禁止用 Dat 均值藏 Snp 退化。

**无公开硅**：不得做 ±15% vs silicon。占用代数（物理槽守恒 + 时间复用记账）精确；绝对 makespan 仅在假设 H-DAT-DOM 下由相对比缩放 T_off，并分列标注。

**禁止外卡钉**：H100、team-384dmc、decode-*、team-interleave-microbench 不进本卡评测。

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| N_dir | 1 | 2（CW/CCW） | 卡 / 拓扑 |
| N_chi | 1 | 4（Req/Rsp/Snp/Dat） | 卡 §2 |
| S | slot/cycle | 1 per direction × physical ring | 卡 §1；H-SLOT |
| C_ring | cycle | 文档例 25；扫描参数 | `docs/topology.md` |
| r | 1 | {3, 7, 15}（Dat:Snp = r:1） | 卡 §4 |
| duty_dat | 1 | r/(r+1) ∈ {3/4, 7/8, 15/16} | 定义 |
| duty_snp | 1 | 1/(r+1) ∈ {1/4, 1/8, 1/16} | 定义；SNP duty floor 例 min 1/8 |
| q | cycle | ≥1；epoch 量子（一个 DAT 或 SNP 单元） | **假设 H-EPOCH-Q** |
| k_circ | 1 | ≥2（marker 双回） | 卡 §2.2 / §2.6 |
| n_pipe | cycle | {1, 2} | 卡 §2.1 bind pipe |
| T_drain | cycle | (k_circ+1)·C_ring + n_pipe | 卡 §2.6；H-DRAIN |
| T_steady | cycle | ≥ min dwell | **假设 H-FLIP**；压力臂迟滞 |
| f_steady | 1 | T_steady / (T_steady + T_drain) | 定义 |
| τ_sync | 1 | [0,1) | SYNC/DRAIN marker 摊还占用；**假设** |
| τ_bind | 1 | [0,1) | bind pipe 摊还；**假设** |
| C_dat_ideal | slot | 1 + duty_dat | 卡 §2.1；上界 |
| C_dat_eff | slot | ≤ C_dat_ideal | 扣税后；H-TMUX |
| C_snp_eff | slot | duty_snp · f_steady | SNP_EPOCH 才注 Snp |
| epoch | 1 | 2b；0..3 | 卡 §2.1 |
| accept | set | {local_epoch, local_epoch−1} (mod 4) | 卡 §2.2 |
| bind_mismatch_redirect | 1 | 稳态目标 0 | 卡 §4；T1 条件 2 |
| ρ_dat_ema | 1 | [0,1] | 本地 Dat util EMA；主臂 |
| n_snp_pend | 1 | 有界计数 | 本地 Snp pending；主臂 |
| λ_snp | 1 | [0,1] | Snp 提供负载（占槽需求 / 墙钟）；**假设 H-SNP-SPARSE** |
| L_snp | cycle | ~C_ring/2 默认 | Snp 服务时延；**假设 H-SNP-LAT** |
| f_dat | 1 | [0,1] | Dat 槽争用时间占比；Amdahl；**假设 H-AMDAHL** |
| β_write | 1 | [0,1] | 均匀写对称阻尼；**假设 H-WRITE-SYM** |
| T_off | ns | 上表 | 公开基线 |
| T_hat | ns | — | 模型预测 makespan（相对缩放） |
| hint | — | None 或 advisory | **不得**进正确性路径 |

rebind-off：经典 1:1，`duty_dat=0` 额外槽，`C_dat_eff=1`，`C_snp_eff=1`。

## 3. First-principles equations

### 3.1 物理槽守恒（精确，无拟合）

每物理环、每方向、每拍：

```
S_phys = 1
ρ_payload + ρ_empty = 1     # 该物理环
```

**CONSTRAINT (H-SLOT):** CRRF **不能**增加物理槽。时间复用只改 Snp **物理导线**在 DAT_EPOCH 上的逻辑身份（ghost Dat），不是第二永久 Dat 端口。

```
C_dat_ideal = 1 + duty_dat          # Dat 环始终 1 + DAT_EPOCH 借用 Snp 导线
C_dat_ideal ≤ 2                     # 等号只在 duty_dat=1（禁：饿死 Snp）
C_dat_eff   ≤ C_dat_ideal           # 税必须扣
```

若某叙述隐含「近乎双 Dat 且 drain/SYNC/pipe 税 = 0」，判为因果失败（卡 §3：谁宣称谁在撒谎）。解析探针：

```
flag_untaxed_double = (C_dat_eff >= 1 + duty_dat - ε) and (τ_drain + τ_sync + τ_bind <= ε)
causal_fail_tmux    = (C_dat_eff > 1 + duty_dat + ε)
```

Req / Rsp 保持 1:1（卡 §2.1 绑定表）。本模型不把它们算进 Dat 有效槽。

### 3.2 Epoch Drain Protocol（代数，非按拍 FSM）

Flip 序列（卡 §2.2；每节点 FSM：IDLE / ARM_DRAIN / DRAIN / FLIP / STEADY）：

1. **ARM_DRAIN**：Req SYNC 路径注入 DRAIN marker；**停止**将对「即将被重绑环」的**新**注入（在途继续）。
2. **DRAIN**：≥ 1–2 环周（marker **返回两次**或 highway sniff 无 `epoch_tag==old`）。
3. **FLIP**：仅本地 DRAIN 完成后更新 4×4 one-hot（+1–2 拍 bind pipe）。
4. **`epoch_committed`**：SYNC 载荷绕全环。**全员** drain+flip 聚合之后才允许**新世代**注入（T1 Archi / Sys：早节点不得在全员 flip 前按新绑定注入）。本地 sniff ≠ 全局瞬时清空。

死时间（H-DRAIN；卡 §2.6）：

```
T_drain = k_circ · C_ring          # ARM_DRAIN→DRAIN，k_circ≥2
        + C_ring                   # epoch_committed 全环
        + n_pipe                   # FLIP + bind pipe
        = (k_circ + 1) · C_ring + n_pipe

f_steady = T_steady / (T_steady + T_drain)
τ_drain  = 1 - f_steady
```

DRAIN / 提交期间 **ghost Dat 新注入为 0**（ARM_DRAIN 已停）。因此额外 Dat 槽只在 STEADY 的 DAT_EPOCH 存在：

```
C_ghost_net = duty_dat · f_steady
C_dat_eff   = 1 + C_ghost_net - τ_sync - τ_bind
C_dat_eff   = clamp(C_dat_eff, 1, 1 + duty_dat)
```

`τ_sync`：Req 环上 SYNC/DRAIN marker 的摊还占用（SYNC ≠ 流量预测；只对齐 epoch / 传播屏障）。`τ_bind`：NIC/RBRG 1–2 拍 pipe 摊还。二者默认小，但**不得省略**。

### 3.3 Skew 接受集与 `bind_mismatch_redirect`

2b epoch。接收方：

```
accept(local) = { local mod 4, (local - 1) mod 4 }
```

- `flit.epoch_tag ∈ accept(local)` → 按 **绑定表 + tag** 译码；**永不**把 Dat 载荷按 Snp 语义重解释。
- 接受集外 → **NACK / 原 Dat 环 re-inject**，`bind_mismatch_redirect++`。禁止静默丢，禁止永久 inject stall。

偏斜窗（长度 ≤ 环周）内早节点 `local=E+1`、晚节点 `local=E`：

```
accept_early ∩ accept_late = {E}     # 旧世代双方仍收
(E+1) ∉ accept_late                  # 新世代会被晚节点拒 → 必须屏障拦住
```

**H-COMMIT / H-MISMATCH0：**

```
new_gen_inject_allowed ⇔ epoch_committed_all_nodes
mismatch_steady = 0     if H-COMMIT
mismatch_steady > 0     if 早节点在全员 committed 前注入 tag=E+1
```

稳态目标 `bind_mismatch_redirect == 0`（卡 §4）。非零必须解释（屏障 bug 或偏斜窗外乱 tag）。Flip 窗内 redirect 有上界；本解析用「屏障开/关」二值探针，不冒充 cycle 计数。

**H-STAGING（Archi 条件，解析只记账不实现）：** 失配 flit 等原 Dat 环空槽时住在有界（深度 1）holding register / 等价端口占用——**不是** highway 突发吸收队列。本模型把 redirect 计为控制路径事件，不把 staging 算成额外物理槽。

### 3.4 相位臂（杀预言）

主臂 **仅** 本地压力计数（卡 §2.4）：

```
# 正确性路径：忽略 hint
if n_snp_pend ≥ θ_snp:
    request duty 3:1          # 拉回 Snp
elif ρ_dat_ema ≥ θ_dat and n_snp_pend < θ_snp:
    request duty 7:1 或 15:1  # 抬 Dat
else:
    request duty 3:1
```

- Runtime `COLL_EP` hint：**至多 advisory**。无 hint 时仍必须安全 ARM_DRAIN → DRAIN → FLIP → STEADY。
- **SYNC ≠ 流量预测**。SYNC 只传播 epoch / DRAIN / `epoch_committed`。
- 解析探针：`correctness_depends_on_hint == False`（hint 开/关不改变屏障、接受集、redirect 规则）。

过频 flip 吃光 Dat 净利（Archi：需最小 STEADY 驻留）。`T_steady` 过小 → `f_steady` 下降 → `C_dat_eff` 回落到 ~1。

### 3.5 Dat 有效容量主导的相对 makespan（H-DAT-DOM）

对 T1/卡标明 **Dat 重 / 已坍集合** 与 **均匀读饱和区**，Little 前置：同事务数、同服务体，makespan 由 Dat 有效槽主导：

```
T ∝ 1 / C_dat_eff
T_hat / T_off = 1 / C_dat_eff          # C_dat_off = 1
```

**Amdahl**（`f_dat` 假设）：

```
speedup_amdahl = 1 / (1 - f_dat + f_dat / C_dat_eff)
T_hat_amdahl   = T_off / speedup_amdahl
```

卡宣称 Dat 重集合 / 均匀读饱和 **0.55–0.85×** 仅当扣税后的 `C_dat_eff` 与 `f_dat` 使比值落入该区间；否则记入 insight「魔法缺口」。**0.85 是 bar≠mean。**

对 **broadcast（基线未坍）**：不以 H-DAT-DOM 强行缩 makespan；主列打印 `C_dat_eff`，T_hat 标 n/a 或中性对照。

对 **均匀写 / 已对称负载**（H-WRITE-SYM）：

```
C_write = 1 + β_write · (C_dat_eff - 1)
T_hat / T_off = 1 / C_write
```

卡区间 **0.85–1.05×** 为对照列，不是测得。

### 3.6 Snp 活体、completions、1.4× 杀假设

DAT_EPOCH 期间 Snp 源可 stall，但 SNP_EPOCH / duty floor 给出有界注入机会。**时间复用 ≠ 1/duty 容量风暴**——仅当 Snp **饱和** 时 `T_snp ∝ 1/C_snp_eff`。

**H-SNP-LAT（混合负载、Snp 稀疏）：** 周期 `T_period = (r+1)·q`，DAT 段 `T_dat = r·q`。均匀到达时期望等 SNP_EPOCH：

```
E[wait] = duty_dat · (T_dat / 2) = (r/(r+1)) · (r · q / 2)
T_snp_on  / T_snp_off = (L_snp + E[wait]) / L_snp
```

**H-SNP-CAP（Snp 风暴，对照杀）：** `T_snp_on / T_snp_off = 1 / C_snp_eff`。7:1 / 15:1 下该比远超 1.4×——用来暴露「Snp 若饱和则机制失败」，**不是**默认混合负载主列。

**杀假设（卡 §2.5 / T1）：**

```
flag_snp_kill = (T_snp_on / T_snp_off > 1.4)
```

超出 = 该 duty **失败**（重调或机制失败）。禁止只报 7:1 甜区。15:1 过敏必须在扫描中暴露。

**Completions（H-SNP-SPARSE）：** 固定 Dat 重作业墙钟下，Snp 提供需求 `W_snp = λ_snp · T_off`（以 off 跑长度为参照的槽·拍需求）：

```
A_off = 1 · T_off
A_on  = C_snp_eff · T_hat_dat          # Dat 变快则窗更短
N_comp_off = min(W_snp, A_off)
N_comp_on  = min(W_snp, A_on)
flag_snp_comp_drop = (N_comp_on < N_comp_off)
```

Dat 侧固定工作：completions = 发行数（不因更快而少完成）。禁止把 Dat completions 与 Snp completions 平均。

### 3.7 消融臂（必须分列，禁止平均）

| Arm | duty Dat:Snp | 含义 |
|-----|----------------|------|
| rebind-off | 1:1（无 ghost） | HARD-1：Dat 侧应变差；Snp 对照基线 |
| 3:1 | 3/4 : 1/4 | duty 扫描 |
| 7:1 | 7/8 : 1/8 | 卡例；SNP floor 例 |
| 15:1 | 15/16 : 1/16 | 过敏臂；须暴露 Snp |

**禁止**把三档 duty 平均成一个「CRRF 加速比」。**禁止**只报 Dat 均值。

## 4. What must stay cycle-level（Dr.Sim；本解析禁止替代）

下列不得用「平均 duty × 有效槽」冒充测得 makespan（本 spec 只给守恒、税与相对界）：

1. 每 die FSM 五态按拍：ARM_DRAIN 起停新注入，在途继续；禁止瞬间空环  
2. DRAIN marker 双回 / highway sniff；跨 die 本地 sniff ≠ 全局清空  
3. FLIP 后 `epoch_committed` 绕环；晚节点提前新绑定注入 = 断言失败  
4. SYNC 采样偏斜窗内逐 flit 接受集（上界 ≤ 环周）  
5. Ghost Dat header channel-id 仍为 Dat；RBRG 按绑定+tag 译码  
6. 接受集外 NACK/re-inject 的完成时间计入当事事务  
7. 无 hint 时的安全 drain/flip/steady  
8. SYNC 不得当流量神谕  
9. HARD-2：512 B 窗 ghost vs 主 Dat 目的分布  
10. Warm-up 至 SYNC 对齐稳态后再采  

## 5. Calibration / PASS lines for this analytical artifact

| Check | Rule |
|-------|------|
| 守恒 | 每物理环 `S=1`；`C_dat_eff ≤ 1+duty_dat`；`C_dat_eff < 2` |
| 税 | 默认假设下 `τ_drain+τ_sync+τ_bind > 0`；`flag_untaxed_double` 必须为假 |
| 屏障 | H-COMMIT 开 → `mismatch_steady==0`；关 → mismatch>0 |
| 分列 | 每流量类、每 duty 臂单独一行；无均值过关 |
| H-DAT-DOM 适用范围 | 仅 Dat 重已坍集合 + 均匀读饱和打印 T_hat；broadcast 打印 n/a |
| Snp | 每 duty 打印 Snp makespan 比 **与** completions；1.4× 为杀假设 |
| 卡区间 | 0.55–0.85× / 0.85–1.05× / ≤1.4× 标为 **card-claim**，非测得 |
| hint | `correctness_depends_on_hint==False` |
| 灵敏度 | 对 `(T_steady, k_circ)` 与 `(q, L_snp)` 两对最敏感参数出表 |

## 6. model.py contract

- stdlib only；`python3 models/P-0198/M-5/model.py`  
- 无外部数据文件；T_off 钉写在常量区并注释 SOURCE  
- 打印：槽守恒、drain 税、epoch 屏障 / mismatch、分流量类相对 makespan、Snp 1.4× 与 completions、duty 扫描 + rebind-off、压力臂 / hint advisory、灵敏度  
- 退出码 0  
- 不向总监/周报投递未审计数字（流程约束；本文件可含模型输出）
