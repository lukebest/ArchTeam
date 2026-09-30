# T2 spec · P-0198/M-2 CSR（Rendezvous–Grant 会合–授权脊骨）

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0198 / M-2 |
| Name | CSR — Collective Spine via RBRG (Rendezvous–Grant) |
| Problem | `problems/P-0198.yaml` |
| Mechanism | `mechanisms/P-0198/M-2.md`（PR #53 tip，T1-return-1；**main 可能尚未着陆卡正文**，本 spec 摘自该卡 + T1） |
| T1 | `reviews/P-0198/M-2/tier1_synthesis.md`（PR #61 已合 main；T1-return-1，取代首轮致命退回） |
| Envelope | DV200 `tests/soc_sim`（同源 `github:lukebest/bufferless-ring-noc`） |
| Style | LIMINAL / roofline（CAM 零载荷守恒 + 会合–授权调度；**非**空槽日历，**非**吞吐曲线拟合） |
| Out of scope | cycle 级 CAM/GRANT FSM 状态机（→ T3）；消息级到达神谕；无限带宽「子瞬时齐」；team-384dmc / decode-* / STREAM / team-interleave-microbench |

**禁止编辑** `mechanisms/`、`reviews/`、`problems/`、`FUNNEL.md`。本树只新增 `models/P-0198/M-2/{spec.md,model.py,insight.md}` 并在 `models/README.md` 索引本卡。

**正交（禁止混结论）**：本卡对象是 **集合成员会合 + GRANT flit**。不得把 M-1 CBC 空槽日历方程、M-4 AODI 造洞、或 M-5 CRRF 通道重绑的结论/数字并进本卡过关叙事。

### 信封（口径冻结）

| Quantity | Value | SOURCE |
|----------|--------|--------|
| 拓扑 | 12 top + 2 bottom；CHI Req/Rsp/Snp/Dat 各自独立成环；环间经 RBRG | 问题 YAML / bufferless-ring-noc README |
| highway | 每方向每拍 **1** 槽；无片上 flit 队列 | 问题 YAML；卡 §1 |
| 请求粒 | 512 B（均匀读/写基线；集合扫描同公开设定） | 问题 YAML；卡 §4 |
| outstanding | 读 512 / 写 256（AIC；额外流控关）；集合扫描 outstanding ∈ {256, 512} | 问题 YAML；卡 §4 |
| Dat 拍数 / 512 B | 8（512 B / 64 B flit；**只作拍计数说明**，不导出绝对 ns） | CHI Dat 512b；卡 §0 |
| RBRG CAM | **N_cam = 4** 真并发；每项 39 b 专用（非 TDM 假 8） | 卡 §0 / §2.1 |
| 端点 | 分流量类 makespan、完成事务数、collapsed；**加上** `cam_overflow_fallback`、`collect_timeout_fallback` | 问题 YAML；卡 §4；T1 条件 2 |

### 公开基线钉（harness 输出，非硅）

Makespan（与 M-1 参考同一张表：`docs/srcfc_ca_model/data.json` scheme=`off`，与问题 YAML 一致处优先 YAML）：

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

**0.85** = 问题及格线 / 卡约束条，**不是**测得均值。禁止把各类平均加速或 min/mean≥0.85 叙事过关。

**卡宣称区间（card-claim，非过关、非测得）**：

| 流量类 | card-claim makespan | 置信（卡） |
|--------|---------------------|-----------|
| gather / reduce / allreduce / allgather | **0.45–0.80×** | 中；视 GRANT 窗与回退率 |
| alltoall | **0.60–0.95×** + 显式残差 | 低–中 |
| broadcast | **0.75–0.98×** | 中；基线已未坍 |
| uniform_read / uniform_write | **0.95–1.05×** | 高；近中性 |

若 `cam_overflow_fallback` **或** `collect_timeout_fallback` **主导完成路径** → 上表区间 **失效**，不得自评通过（卡 §4；T1 条件 2/4）。

**无公开硅**：不得做 ±15% vs silicon。占用代数（CAM Dat≡0、拒收滞留≡0）精确；绝对 makespan 仅在具名相对缩放假设（H-REL-SCALE）下由 `T_hat = T_off · r` 得到，并分列标注。

**禁止外卡钉**：H100、team-384dmc、decode-*、STREAM、team-interleave-microbench 不进本卡评测。

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| N_top | 1 | 12 | DV200；卡 §0 |
| N_src | 1 | 12（全集合成员掩码；默认 = N_top） | 卡 §2.1 child_bitmap 12b |
| N_cam | 1 | **4**（真并发，专用项） | 卡 §0 / §2.1 |
| bits_cam_i | b | 39 = 16+12+3+8 | 卡 §2.1 |
| CAM_bits | b | 156 = 4×39 | 卡 §5 |
| state | enum | IDLE=0 / COLLECT=1 / GRANT_PENDING=2 / GRANT_SENT=3 / FORCE_FALLBACK=4 | 卡 §2.1 |
| timeout | cycle | 255（8b；默认可配） | 卡 §2.3 |
| N_beats | beat | 8 / 512 B txn | 卡 §0；见上 |
| S | slot/cycle | 1 per direction×Dat ring | 问题 YAML；卡 §1 |
| occupancy(CAM_i, Dat_beats) | beat | **恒 0** | 卡 §0；T1 条件 1 |
| RBRG_reject_retention_depth | flit | **恒 0** | 卡 §0；T1 条件 1 |
| concurrent_live_cam | 1 | [0, 4] | 卡 §2.1；T1 条件 2 |
| λ_coll | 1/cycle | ≥0 | 集合 txn 到达率；**假设 H-CAM-LOAD** |
| τ_collect | cycle | N_src · T_hdr | 末头到达；**假设 H-COLLECT** |
| T_hdr | cycle | >0 | 头间距；**假设 H-COLLECT** |
| τ_grant_emit | cycle | 1（环槽可用时） | 卡 §2.3 |
| τ_hold | cycle | τ_collect + τ_grant_emit | H-CAM-RELEASE（GRANT_SENT 后释 CAM） |
| a | Erlang | λ_coll · τ_hold | H-CAM-LOAD |
| f_overflow | 1 | B(N_cam, a) ∈ [0,1] | §3.3 |
| p_timeout | 1 | [0,1] | §3.4；H-TIMEOUT-WINDOW |
| f_timeout | 1 | (1−f_overflow)·p_timeout | §3.4 |
| f_grant | 1 | (1−f_overflow)·(1−p_timeout) | §3.4 |
| W_grant | 1 | ≥1（静态 order 表窗内并发上界；默认 1） | 卡 §2.1 静态 order 表 |
| f_fanin | 1 | [0,1] | Amdahl 扇入时间占比；**假设 H-FANIN-BOUND** |
| κ_grant | 1 | ≥0 | GRANT 公民 + 开窗税；**假设 H-GRANT-TAX** |
| tax_orbit | 1 | ≥0 | 仅当 H_inject_gate 被违反 | T1 条件 3；H-ORBIT |
| w_tree, w_res | 1 | w_tree+w_res=1 | alltoall 多树/残差；**假设 H-A2A-SPLIT** |
| T_off | ns | 上表 | 公开基线 |
| T_hat | ns | — | 模型预测（相对缩放，非测得） |
| r | 1 | T_hat/T_off | H-REL-SCALE |
| I_payload | 1 | {0,1} | 端点 payload 注入；H_inject_gate |

Classifier 输出：`{RING_P2P, SPINE_RENDZ}`。普通读写不得进 CAM。FORCE_FALLBACK / overflow → 立即 RING_P2P。

## 3. First-principles equations

本卡 **不是** 空槽再分配。收益叙事是：把「谁齐了」从 Dat 公路的 payload 洪泛里抽到 RBRG Tag CAM，环上只在 GRANT 窗内跑有序集合序列；扇入争用从 Ω(N) 盲目注入降为授权窗口内的有界并发。零和诚实：不增加 highway 槽，不在 RBRG 造 FIFO。

### 3.1 零 Dat 占用与零拒收滞留（精确，无拟合）

任意时刻、任意活跃 CAM 项：

```
occupancy(CAM_i, Dat_beats) == 0
RBRG_reject_retention_depth == 0
concurrent_live_cam <= N_cam == 4
```

RENDZ 只经短 divert 送入 **1-flit header/credit**。payload Dat 拍 **永不**进入 RBRG 存储。拒收 RENDZ 头 = 同拍重分类 RING_P2P，头继续在环前进——**禁止**对 Dat 载荷做 reject-and-orbit。

CAM 状态位（非载荷）：

```
bits_i = 16 + 12 + 3 + 8 = 39
CAM_bits = N_cam * 39 = 156
```

解析探针（构造为恒真；违例 = 机制失败，不是调参）：

```
flag_dat_held = any(occupancy(CAM_i, Dat_beats) > 0)
flag_retention = (RBRG_reject_retention_depth > 0)
flag_cam_oversub = (concurrent_live_cam > N_cam)
invariant_ok = (not flag_dat_held) and (not flag_retention) and (not flag_cam_oversub)
```

### 3.2 Rendezvous–Grant 日程（相位守恒）

一条 `SPINE_RENDZ` txn 的解析相位（卡 §2.2–2.3）：

1. **COLLECT**：子节点各发 1-flit RENDZ 头；CAM 置 `child_bitmap[src]`，刷新 `timeout`。
2. **GRANT**：位图对齐该类静态成员掩码 → `GRANT_PENDING` → 向 Dat 环注入 1 拍 GRANT flit（txn_id + 序列相位）。GRANT 是既有 1-slot 公路上的公民，**不发明第三槽**。
3. **窗内注入/orbit**：参与端按 **静态集合类** order 表在授权窗内注入或交拍。禁止按到达时刻神谕排程。
4. **端点 fold**：折叠在目的/root NIC 已有 RF/cache 端口，1 拍/运算宽度。**不**建成 highway FIFO，**不**进 RBRG。

CAM 占用时间（**假设 H-CAM-RELEASE**：`GRANT_SENT` 后释放该项；fold 不占 CAM）：

```
τ_collect    = N_src * T_hdr
τ_grant_emit = 1
τ_hold       = τ_collect + τ_grant_emit
```

窗长（环上，不占 CAM）：

```
τ_window = (N_src * N_beats) / W_grant
```

`W_grant=1` 对应卡「静态 order 表串行注入」的诚实上界。`W_grant>1` 是扫描参数，不是硅承诺。

### 3.3 CAM 溢出 = 损失系统（Erlang-B，无队列）

卡：CAM 满/busy → **立即** RING_P2P，`cam_overflow_fallback++`。这是 **M/M/N_cam/N_cam** 损失系统，不是等待队。

```
B(0, a) = 1
B(n, a) = a * B(n-1, a) / (n + a * B(n-1, a))     # n = 1..N_cam
f_overflow = B(N_cam, a)
a = λ_coll * τ_hold
```

确定性对照（C 个同时到达的会合需求）：

```
f_overflow_det = max(0, C - N_cam) / max(C, 1)
```

主列用 Erlang-B；确定性式只作探针。`cam_overflow_fallback` 计入完成路径分母，禁止从完成集剔除。

### 3.4 COLLECT 超时（第一类计数）

每 CAM 项独立 `timeout[7:0]`；到期 → `FORCE_FALLBACK`，释放 CAM，`collect_timeout_fallback++`。禁止静默永等。

**假设 H-TIMEOUT-WINDOW**（迟到份额，非指数拟合）：

```
p_timeout = max(0, 1 - timeout / max(τ_collect, ε))
f_timeout = (1 - f_overflow) * p_timeout
f_grant   = (1 - f_overflow) * (1 - p_timeout)
```

`timeout=255` 且 `τ_collect ≤ 255` ⇒ `p_timeout=0`。头间距被环争用拉长后超时才亮。

完成质量守恒：

```
f_overflow + f_timeout + f_grant == 1
completions ≡ cam_overflow_fallback + collect_timeout_fallback + spine_grant
```

**失效开关（卡 §4；不得改成脚注）**：

```
fallback_dominates = (f_overflow > 0.5) or (f_timeout > 0.5)
card_claim_valid   = not fallback_dominates
```

任一类上 `fallback_dominates` → 该类 card-claim 带作废。禁止把回退完成并进「脊骨成功」均值。

Sys 组合预算（T1 评估层假设，**不是**卡过关线）：两道并发集合下希望 `f_overflow + f_timeout ≤ 0.10`。解析打印 `flag_sys_fb`，不把 ≤10% 签成 pass。

### 3.5 H_inject_gate 与 FORCE_FALLBACK 可观测性（T1 条件 3）

**H_inject_gate（端点门控注入）**：对任意 `SPINE_RENDZ` txn，在该源端点观测到本 txn 的 GRANT flit **之前**：

```
I_payload(txn, t < t_GRANT_obs) == 0
```

同时全程 §3.1 不变式。若 GRANT 前环上已出现该 txn 的 payload 拍 → 按「提前 orbit」判机制失败，**不得**把收益记在 CSR（Archi）。

本解析锁定的驻留模型（Dr.Sim：必须锁一种，禁止混用）：

- COLLECT / GRANT_PENDING：payload **在端点持有**（已有 RF/cache），不进桥、不提前 orbit。
- GRANT 窗：按 order 表注入；GRANT flit 的 Dat 槽占用计入 `κ_grant`。
- 卡文「payload 留在 Dat 环直到 GRANT」在本模型中读成：**桥不持拍**；环上出现该 txn 的 payload 只发生在 GRANT 之后。COLLECT 期环上只有 RENDZ 头与既有无关公民。

若把门控关掉（探针 `H_inject_gate=false`）：

```
tax_orbit = f_fanin * (1 - W_grant / N_src)
```

该项把 §3.6 的扇入收益对消——解析上再现「提前 orbit ⇒ spine-on 环占用 ≥ spine-off」。

**FORCE_FALLBACK 通知（H-FF-NOTIFY）**：超时必须在有界拍内让相关端改分类 RING_P2P（显式回退 flit **或** 源/桥双端同源 timeout）。解析探针：

```
flag_orphan = (f_timeout > 0) and (not H_FF_NOTIFY)
```

`flag_orphan` → 半集合仍等 GRANT；card-claim 作废。默认假设 H-FF-NOTIFY=true，并把它标成 **具名假设/探针**，不是已测路径。

### 3.6 相对 makespan（H-FANIN-BOUND + H-REL-SCALE）

仅对卡标明 **collapsed** 且扇入争用主导的类启用：`{gather, reduce, allgather, allreduce}`。

基线：12 源盲目注入单槽 Dat ⇒ 扇入相并发 Ω(N_src)。脊骨：授权窗并发 ≤ `W_grant`。

```
r_sched = (1 - f_fanin) + f_fanin * (W_grant / N_src)
r_ok    = r_sched + κ_grant + tax_orbit
r_fb    = 1.0
r       = f_grant * r_ok + (f_overflow + f_timeout) * r_fb
T_hat   = T_off * r
```

这是 **扇入并发上界的 Amdahl 分解**，不是 M-1 的 `T ∝ 1/p_inj` 空槽式。`r_fb=1`：回退路径回到 RING_P2P，makespan 回到基线量级。

**CONSTRAINT：** `W_grant / N_src ≤ 1`；不得靠把 `W_grant` 放到 >N_src 来「制造」加速。`κ_grant≥0`（GRANT 公民税，不能为负来补贴）。

broadcast（基线未坍）与均匀读/写：**不算** H-FANIN-BOUND 绝对值。主列打印分类去向、CAM 需求、GRANT 溢出税；`T_hat` 标 `n/a`。card-claim 只作对照列。

### 3.7 alltoall 多树 / 残差（禁止并进均值）

卡：拆多棵小树 / 分段 GRANT；残差环争用 **单独报告**。

```
N_seg  = ceil(N_src / tree_arity)          # 默认 arity=4 → 3 段
a_a2a  = a_base * N_seg_factor             # 分段抬高 CAM 到达；H-A2A-LOAD
w_tree + w_res = 1
r_tree = (同 §3.6，但用 a_a2a)
r_res  = 1.0                               # 残差仍走 RING_P2P 量级
```

打印 `r_tree`、`r_res`、`w_res` 分列。混合物 `w_tree*r_tree + w_res*r_res` 只作伴生行，**不是**过关数字，也不得与 gather 系平均。

### 3.8 消融 spine-off（HARD 因果探针）

强制全集 `RING_P2P`（CAM 不分配，无 GRANT）：

```
f_grant_off = 0
r_off = 1.0
T_hat_off = T_off
```

已坍集合的 collapsed 叙事回到公开扫描（true）。均匀读/写仍近中性。

**HARD：** `T_hat_off` 必须回到基线量级；若 spine-on 相对 spine-off **没有**变好，不得把收益记在 CSR。解析探针：

```
attr_ok = (T_hat_on < T_hat_off) and (not fallback_dominates)
```

### 3.9 分类器（一拍组合）

```
class(opcode) = SPINE_RENDZ  if opcode ∈ {gather, reduce, allgather, allreduce, alltoall, broadcast}
              = RING_P2P     if opcode ∈ {uniform_read, uniform_write}
              = RING_P2P     if overflow or FORCE_FALLBACK
```

普通读写的 CAM 到达率 λ=0 ⇒ `f_overflow=f_timeout=0`。

## 4. Named hypotheses

| ID | 含义 | 风险 |
|----|------|------|
| H-CAM-DAT0 | 不变式：CAM 永不持 Dat 拍 | 违例 = 机制失败（复活 latch/FIFO） |
| H-RETENTION0 | 拒收零滞留 | 违例 = 环面隐式队列 |
| H_inject_gate | GRANT 前端点 payload 注入≡0 | 关掉则提前 orbit，扇入零和回来 |
| H-FF-NOTIFY | FORCE_FALLBACK 端点可见 | 假则半集合永等 GRANT |
| H-CAM-LOAD | a=λ·τ_hold | outstanding 256/512 下 a 可把 overflow 推过主导线 |
| H-CAM-RELEASE | GRANT_SENT 后释 CAM | 若窗内仍占 CAM，a 更大 |
| H-COLLECT | τ_collect=N_src·T_hdr | 头被环堵则超时亮 |
| H-TIMEOUT-WINDOW | 迟到份额 | 不是指数拟合 |
| H-FANIN-BOUND | 已坍类 makespan 由 Ω(N) 扇入主导 | 非坍塌类禁用 |
| H-GRANT-TAX | κ_grant≥0 | GRANT 公民与 P2P 抢 Dat 槽 |
| H-ORBIT | 仅 gate 关闭时的对消税 | 不得当默认收益来源 |
| H-A2A-SPLIT / H-A2A-LOAD | 树/残差分列；分段抬 a | 残差可吞掉树收益 |
| H-REL-SCALE | T_hat=T_off·r | 绝对 ns 不是硅 |
| H-SPINE-OFF | 消融回基线 | 无差异则不可归因 |

## 5. What must stay cycle-level（Dr.Sim；本解析禁止替代）

下列不得用「平均扇入比 / 平均 Erlang」冒充测得 makespan（本 spec 只给守恒与相对界）：

1. 每拍每活跃 CAM 的 `Dat_beats_held` 探针（必须恒 0）
2. 拒收同拍重分类 vs 任何 payload reject-and-orbit
3. 4 项专用 FSM × 独立 timeout 递减；`concurrent_live_cam ≤ 4`
4. Classifier 与 FORCE_FALLBACK 通知路径的有界拍
5. GRANT 发射与静态 order 表窗（禁止到达神谕、禁止无限带宽齐子）
6. 端点 fold 的 RF/cache 端口争用（禁止零延迟归约）
7. alltoall 分段 GRANT 的残差分桶/分位数
8. Warm-up 与满 12+2 / 四环 / 512 B / ost 256\|512 包络

## 6. Calibration / PASS lines for this analytical artifact

| Check | Rule |
|-------|------|
| Dat≡0 / 滞留≡0 | 所有扫描点不变式成立 |
| 完成守恒 | `f_overflow+f_timeout+f_grant==1` |
| 分列 | 每流量类单独一行；无均值过关；alltoall 残差分列 |
| H-FANIN-BOUND 适用范围 | 仅 gather/reduce/allgather/allreduce 打印 T_hat；其余 n/a 或中性对照 |
| 回退主导 | 任一类 `f_overflow>0.5` 或 `f_timeout>0.5` → 该类 card-claim 标 INVALID |
| 卡区间 | 0.45–0.80× 等标为 **card-claim**，非测得，不签 pass |
| H_inject_gate | 默认 on；off 臂必须使已坍类 r 回到 ~1 量级 |
| spine-off | 已坍类 T_hat_off/T_off=1；on 优于 off 才可归因 |
| 灵敏度 | 对 (a, N_cam) 与 (f_fanin, W_grant) 两对最敏感参数出表 |

## 7. model.py contract

- stdlib only；`python3 models/P-0198/M-2/model.py` 必须 exit 0
- 无外部数据文件；T_off 钉写在常量区并注释 SOURCE（与 M-1 参考同一张表）
- 打印：不变式、完成守恒、分流量类表、回退主导探针、H_inject_gate / FORCE_FALLBACK 探针、alltoall 残差、spine-off 消融、灵敏度
- 不向总监/周报投递未审计数字（流程约束；本文件可含模型输出）
