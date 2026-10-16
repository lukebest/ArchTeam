# T2 spec · P-0198/M-1 CBC（环上循环气泡日历）

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0198 / M-1 |
| Name | Circulating Bubble Calendar (CBC) |
| Problem | `problems/P-0198.yaml` |
| Mechanism | `mechanisms/P-0198/M-1.md`（PR #44 tip；main 尚未着陆卡正文，本 spec 摘自该卡 + T1） |
| T1 | `reviews/P-0198/M-1/tier1_synthesis.md`（PR #52 已合 main） |
| Envelope | DV200 `tests/soc_sim`（同源 `github:lukebest/bufferless-ring-noc`） |
| Style | LIMINAL / roofline（空槽守恒 + 注入机会再分配；非吞吐曲线拟合） |
| Out of scope | cycle 级 Bubble FSM 状态机；RBRG 对侧气泡；消息级到达神谕；team-384dmc / decode-* / STREAM 代理 |

**禁止编辑** `mechanisms/`、`reviews/`。本树只新增 `models/P-0198/M-1/{spec.md,model.py,insight.md}`。

### 信封（口径冻结）

| Quantity | Value | SOURCE |
|----------|--------|--------|
| 拓扑 | 12 top + 2 bottom；CHI Req/Rsp/Snp/Dat 各自独立成环；环间经 RBRG | 问题 YAML / bufferless-ring-noc README |
| highway | 每方向每拍 **1** 槽；无片上 flit 队列 | 问题 YAML；卡 §1 |
| 请求粒 | 512 B（均匀读/写基线） | 问题 YAML |
| outstanding | 读 512 / 写 256（AIC；额外流控关） | 问题 YAML；卡 §4 |
| 底环 CS 数（文档例） | 25 CS / FullRing（bottom manyring） | `docs/topology.md`；**解析模型不依赖精确周长做 makespan 绝对值** |
| 端点 | 分流量类 makespan、完成事务数、collapsed；均匀读峰值后 goodput | 问题 YAML；T1 条件 2 |

### 公开基线钉（harness 输出，非硅）

Makespan（`docs/srcfc_ca_model/data.json` scheme=`off`，与问题 YAML 一致处优先 YAML）：

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

均匀读负载曲线钉：offered ~5767 B/ns → goodput ~5761 → 崩至 ~2.8–3.4 TB/s。SOURCE: 问题 YAML。

**0.85** = 问题及格线 / 卡约束条，**不是**测得均值。禁止用各类平均加速或 min/mean≥0.85 叙事过关。

**无公开硅**：不得做 ±15% vs silicon。占用代数（空槽守恒）精确；绝对 makespan 仅在假设 H-INJ-DOM 下由相对比缩放 T_off，并分列标注。

**禁止外卡钉**：H100、team-384dmc、decode-*、team-interleave-microbench 不进本卡评测。

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| N_dir | 1 | 2（CW/CCW） | 卡 / 拓扑 |
| N_chi | 1 | 4（Req/Rsp/Snp/Dat） | 卡 §2 |
| S | slot/cycle | 1 per (node-local view of) direction×ring | 卡 §1 |
| ρ_payload | 1 | [0,1] | 稳态过路载荷占槽率；**UNKNOWN 实测**，扫描参数 |
| ρ_empty | 1 | 1−ρ_payload | 守恒定义 |
| ρ_raw | 1 | [0,ρ_empty] | 无 bubble tag 的空槽 |
| ρ_bubble | 1 | [0,ρ_empty] | 带 bubble tag 的空槽 |
| d | 1 | {0, 1/16, 1/8, 1/4, 1/2} | 卡 §2 日历 duty；高 4b 密度 0–15 → d=k/16 |
| φ | 1 | [0,15] | 低 4b 相位；本解析模型不模拟相位错配动力学（标 假设） |
| W | cycle | 8 | 卡 §2；未见气泡才 EMIT |
| AGE_MAX | 1 | 15 | 卡 §2 |
| f_coll | 1 | [0,1] | 扇入相时间占比；Amdahl；**假设** |
| α_eject | 1 | [0,1] | eject/残留贡献的 raw-empty 到达相对空载；H-CBC-empty-supply |
| I_c, I_p | 1 | {0,1} | 本拍是否有 collective / P2P 注入意愿 |
| p_inj | 1 | [0,1] | 有效注入成功率（单口视角，稳态） |
| T_off | ns | 上表 | 公开基线 |
| T_hat | ns | — | 模型预测 makespan（相对缩放） |
| G_peak | B/ns | ~5761 | 均匀读峰值 goodput；YAML |
| G_coll | B/ns | ~2.8e3–3.4e3 | 坍塌带（YAML 写 TB/s；换算见 model 注释） |

ROM/日历：64×8；本模型只取当前 epoch 的标量 d，不建 SRAM 时序。

## 3. First-principles equations

### 3.1 空槽守恒（精确，无拟合）

每方向、每 CHI 环、每拍：

```
ρ_payload + ρ_empty = 1
ρ_empty = ρ_raw + ρ_bubble
```

**CONSTRAINT (Archi H-CBC-empty-supply):** CBC **不能**提高 ρ_empty。日历只把 eligible raw-empty 写成 bubble tag：

```
ρ_empty(calendar-on) = ρ_empty(calendar-off)     # 同一载荷过程
```

若某叙述隐含 Δρ_empty>0，判为「制造空槽」因果失败（降级为优先级准入）。解析探针：

```
delta_rho_empty = ρ_empty_on − ρ_empty_off
causal_fail_empty = (delta_rho_empty < 0.05 * max(ρ_empty_off, ε))  # 与 T1「<5%」同形；期望 ≈0
```

（T1 原文是测得 ρ_empty 提升 <5% **且** inject-success <10% ⇒ 失败；解析侧先强制 Δρ_empty≈0，收益只许来自再分配。）

### 3.2 气泡标记（再分配，非 mint）

在 bubble-mandatory epoch、假设 H-EMIT-SAT（扇入相 W 窗常触发）下，稳态把空槽中至多 d 的份额标成气泡：

```
ρ_bubble = min(d, 1) · ρ_empty
ρ_raw    = ρ_empty − ρ_bubble
```

calendar-off / duty=0：`d=0` ⇒ `ρ_bubble=0`，`ρ_raw=ρ_empty`。

age≥AGE_MAX 强制退化：短环上气泡寿命有界。解析上用寿命因子 λ_age∈(0,1] 缩减有效气泡份额（**假设 H-AGE**，默认 1；灵敏度扫描）：

```
ρ_bubble_eff = λ_age · ρ_bubble
ρ_raw_eff    = ρ_empty − ρ_bubble_eff
```

### 3.3 注入 vs 窃取仲裁（卡 §2 优先级）

优先级：collective inject > P2P inject > bubble keep。

单口、稳态、互斥意愿下的有效注入机会（占空槽的条件概率）：

```
# 有 collective 意愿：可吃 raw 与 bubble
p_inj_coll = ρ_raw_eff + ρ_bubble_eff

# 仅 P2P 意愿：可吃 raw；亦可窃取 bubble（优先级高于 keep）
p_inj_p2p  = ρ_raw_eff + ρ_bubble_eff

# 双意愿同拍：collective 独占该空槽机会
p_inj_coll_dual = ρ_raw_eff + ρ_bubble_eff
p_inj_p2p_dual  = 0
```

**看似 P2P 与 collective 单租户同式**：单作业下窃取不改变「谁能用空槽」，只改变空槽的**空间/时间位置**（气泡循环）。解析模型对**单租户**的一阶效应是：

1. 不增加总空槽；
2. 通过气泡把空槽从过路密集区挪到扇入邻域的可窃取位置 —— 用**位置效率** η∈[0,1] 刻画（**假设 H-PLACE**）：

```
p_inj_coll_cbc = ρ_empty · ( (1−d) + d · η )
p_inj_coll_off = ρ_empty · η0
```

取 η0 为无日历时扇入邻域空槽可见率（≤1）。卡叙事对应 η>η0（气泡被送到汇聚邻域）。**CONSTRAINT:** η≤1；η 不能从 ρ_empty 凭空放大到 >1。

固定高 duty 且无 epoch 切换：对均匀读，气泡若 keep 比例上升（无窃取意愿时），载荷可用槽下降：

```
C_eff / C = 1 − ρ_bubble_eff · κ_keep     # κ_keep∈[0,1]：未被窃取而空转的气泡份额；假设
```

峰值后 goodput 代理（非端点替代，只作 HARD-1 副作用探针）：

```
G_hat = G_peak · (C_eff / C)
flag_p2p_collapse = (G_hat <= G_coll_hi)   # 再掉进 2.8–3.4 TB/s 带
```

### 3.4 注入失败主导的相对 makespan（假设 H-INJ-DOM）

对 T1/卡标明 **collapsed / inject-fail 主导** 的集合类，采用 Little 前置：

```
T ∝ 1 / p_inj          # 同 N_txn、同服务体
T_hat / T_off = p_inj_off / p_inj_cbc
```

其中：

```
p_inj_off = ρ_empty · η0
p_inj_cbc = ρ_empty · ( (1−d) + d · η )
```

**Amdahl 上界**（卡 §3；f_coll 假设）：

```
S_inj = p_inj_cbc / p_inj_off
speedup_amdahl = 1 / (1 − f_coll + f_coll / S_inj)
T_hat_amdahl = T_off / speedup_amdahl
```

卡宣称已坍集合 **0.55–0.85×** 仅当 S_inj 与 f_coll 落入使 T_hat/T_off 落在该区间；否则记入 insight「魔法缺口」。

对 **broadcast（基线未坍）** 与 **均匀读/写**：不以 H-INJ-DOM 强行缩 makespan；报告近中性带（卡：broadcast 0.90–1.05×；均匀 0.95–1.10×）为**卡区间对照列**，模型主列打印 p_inj 与 C_eff，不把卡区间当作测得。

### 3.5 双租户（Sys T1 条件）

租户 A：扇入高 duty d_A∈{1/4,1/2}；租户 B：均匀读。

```
p_inj_B_dual = ρ_raw_eff = ρ_empty · (1 − min(d_A,1)·λ_age)   # A 的 collective 吃掉 bubble
T_B_hat / T_B_solo ≈ p_inj_B_solo / p_inj_B_dual
```

Sys 条件：B makespan 恶化 <10% 且 goodput 不进坍塌带。解析探针：

```
flag_sys_fail = (T_B_hat / T_B_solo >= 1.10) or flag_p2p_collapse_B
```

### 3.6 消融臂（必须分列，禁止平均）

| Arm | d | 含义 |
|-----|---|------|
| calendar-off | 0 | HARD-1：已坍集合应变差（相对满 CBC） |
| duty=0 | 0 | 同 off（解析一阶） |
| duty 固定高 | 1/2 | 无 epoch 切换；P2P 副作用单列 |
| CBC-P2P | 1/16 或 1/8 | P2P epoch |
| CBC-coll | 1/4 或 1/2 | 扇入 epoch |

**禁止**把 P2P 与扇入 duty 平均成一个「CBC 加速比」。

## 4. What must stay cycle-level（Dr.Sim；本解析禁止替代）

下列不得用「平均空槽率」冒充测得 makespan（本 spec 只给守恒与相对界）：

1. Bubble FSM（IDLE/WATCH/EMIT/HOLD）×节点×方向×四环  
2. 64×8 日历查表时序与相位对齐  
3. tag/age 逐跳与气泡聚团长度分布  
4. 同拍窃取仲裁的分列计数（steal / raw-inject / fail）  
5. Warm-up ≥ 一圈环后再采  
6. epoch 边界不得由 harness 神谕注入  

## 5. Calibration / PASS lines for this analytical artifact

| Check | Rule |
|-------|------|
| 守恒 | 对所有扫描点 `ρ_payload+ρ_empty==1` 且 `ρ_raw+ρ_bubble==ρ_empty` |
| 不 mint | `delta_rho_empty==0`（同 ρ_payload 过程） |
| 分列 | 每流量类、每 duty 臂单独一行；无均值过关 |
| H-INJ-DOM 适用范围 | 仅 collapsed 集合类打印 T_hat；其余打印 n/a 或中性对照 |
| 卡区间 | 0.55–0.85× 等标为 **card-claim**，非测得 |
| 灵敏度 | 对 (η/η0, d) 与 (ρ_empty, f_coll) 两对最敏感参数出表 |

## 6. model.py contract

- stdlib only；`python3 models/P-0198/M-1/model.py`  
- 无外部数据文件；T_off 与 G 钉写在常量区并注释 SOURCE  
- 打印：守恒检查、空供给探针、分流量类相对 makespan（H-INJ-DOM）、P2P goodput 副作用、双租户、消融、灵敏度  
- 不向总监/周报投递未审计数字（流程约束；本文件可含模型输出）
