# P-0198 / PR #1 第五轮（gate r4）只读审计 —— option A：非单根集合 + 饥饿闸门

- 仓库：lukebest/bufferless-ring-noc PR #1，分支 `cursor/p0198-llm-noc-baseline-aa90`
- 审计 tip：`bbb7baff76bc559b3acda519bf968b923b3d4123`（`git ls-remote` / `git rev-parse` 一致）
- 作者报告提交：`e1add1baf3a8941cd0b22b8b781ec9d8675cddd6`（README 钉死的 option-A 报告 SHA）
- 本轮相对 tip 242aae4 的新增：801e4d7（HA 中介 ring/hier 集合）、7f400c8（rsv_up_plus_down / root 扫 / top-link-latency）、e1add1b（option-A 结论）、bbb7baf（README 钉 SHA）
- 审计方式：只读。运行在 scratch `/workspace/brn-p198-audit`（分支 pr1r5）与 `/tmp/r5`。对目标仓**无** commit/push/评论；**不改**作者代码。
- 构建：`artifacts/soc_sim/build/d7b0842b693436ee/soc_sim`
- 饥饿线（r2/r3）：S0 单 die×单 ring、物理 CS 序；S1 R−3SE>1.10 且 ≥7/8 种子 R>1；S2 下游≥1.0 且 Δ≥0.5；S3 方向按 TNetwork.cpp:83-106。
- 船长 18:21 option A：非单根集合下若仍饿 → 有条件放大；若不饿 → **不放大并关 P-0221**。本审计的签字即闸门。

## 0. 摘要

- **映射**：ring_* = 真非单根（每步 20 rank 齐注）；hier_allreduce = 分段双根 gather（phase1 仅 2 个 die-root），**不应**标 non_single。
- **复现**：lib×non_single 64/64 完成；与作者表 104 行一致；starve 清单空；最近 aic die2 r0 cc half dn=0.211 R=0.528 ✔。ring-only / hier-only 各自也 0 行过线。
- **单根对照**：仍饿，且饿在 root 所在 die（root=0→die1，root=10→die2）；root=5 时 aic 半环线不过、rsv cw half 过。
- **rsv_up_plus_down**：推断挂接，可作敏感性，不可当平台挂接签字。
- **Lat=1**：309/1920、309/1280 精确复现；奇数圈断言；lap22/24 死、lap42 活 → 作者分类可签。
- **闸门判定：不放大，关 P-0221**（§7）。依赖 H-HA-MEDIATED / chunks=1 等已披露假设。

## 1. 映射是否真非单根？（check A）

依据：`COLLECTIVES.md` 的 H-RING-* / H-HIER-* 假设，以及 `TrafficGen.h` `build_collective`（801e4d7）实现。N=20（2 die × 10 AIC）。

### 1.1 ring_*（真正的非单根）

`ring_rs` / `ring_ag`（`TrafficGen.h` ~332-364）：对 step `s = 0..N-2`：

1. **所有 N 个 rank** 各写 1 个 chunk（发给程序序邻居 `i+1`）；
2. **所有 N 个 rank** 各读 1 个 chunk（收自 `i−1`）。

| 项 | 值 |
|---|---|
| 每 phase 同时注入的 rank 数 | **N=20**（全员） |
| 单 rank 占比 | 1/N = 5% |
| RS/AG 期望事务 | `2·N·(N−1)·chunks`；AR = 其 2 倍 |
| option-A chunks | 1（`H-RING-CHUNK-512`） |
| 漏斗 phase | **无** |

假设标签（作者自标，均属流量建模假设，非平台字段）：

| Id | 选择 | 影响 |
|---|---|---|
| `H-RING-NEIGHBOR-RANK` | 邻居按程序 rank 序，非物理 CS 序；9↔10、19↔0 跨 die | 跨 die 的 ring 边走 3DIO |
| `H-RING-BARRIER-PHASE` | 每半步全局 barrier | 比真正的 per-neighbor credit 更串行 |
| `H-RING-CHUNK-512` | chunks=1 | smoke 缩尺；单根对照仍用 32/4 |
| `H-HA-MEDIATED` | send=写 HA cell，recv=邻读同一 cell | 无 AIC↔AIC P2P；每“跳”变成两次 HA 往返 |

**判定：ring_* 是真正的非单根。** 任何一步都不存在单 rank 汇聚。

### 1.2 hier_allreduce（**不是**非单根）

`TrafficGen.h` ~366-385，6 phase：

| Phase | 谁 | 做什么 |
|---|---|---|
| 0 | 全部 N | 写自己的 cell |
| **1** | **仅 die-root 0 与 N/2** | **各自读本 die 半区的 N/2 个 cell** |
| 2 | 两 die-root | 各写 partial |
| 3 | 两 die-root | 交叉读对方 partial |
| 4 | 两 die-root | 写全局结果 |
| 5 | 其余 N−2 | 从本 die-root 读全局结果 |

| 项 | 值 |
|---|---|
| phase1 同时注入的 rank 数 | **2**（不是 N） |
| phase1 每 die-root 读回 | N/2 = 10 cells（×chunks） |
| 漏斗 | **有：每 die 一个 gather root**（`H-HIER-DIE-SPLIT`） |
| 期望事务 | `N+N+2+2+2+(N−2)` × chunks = 64（chunks=1） |

作者自己在 `COLLECTIVES.md` 写明：“This is **not** a published NCCL tree binary; it is the smallest multi-root mapping”。它是 **双根 / 分段单根**，不是非单根。phase1 的 incast 规模是单根 AR phase1（root 读 N）的一半，但仍是单点汇聚。

**判定：把 hier 放进 `NON_SINGLE` 池（`pool.py:53-55`）不符合船长对“非单根”的字面要求。** 后续饥饿表必须拆开：

- **ring-only**（3 类）：真非单根；
- **hier-only**（1 类）：分段双根；
- **作者 non_single 池**（4 类混合）：复现用，不单独作为“非单根”签字依据。

### 1.3 实测注入计数（单种子，跑完后回填）

计划：对 `ring_allreduce` / `hier_allreduce` / `tp_allreduce` 各取 seed 20260903，按 AIC / dio_top 的 `inject_succ` 与 `summary.traffic` 核对无单 rank incast。

## 2. `rsv_up_plus_down` 挂接裁定（check C）

### 2.1 定义（作者本回合新加，不在 r2 `TOP_3DIO_CANDIDATES` 表）

`gen_config.py:406-419`：

- `0x50–0x52`：**UP** 1×2 @ reserved CS **9/10/20**（`noc_setup.md:90` RBIST/MN/DISP）
- `0x53–0x57`：**DOWN** 1×2 @ AIC CS **0,2,4,6,8**（`:123-124` 的前 5 个）

与审计 r4 的 `rsv_up_plus_down` 探针（3 UP 保留 + 5 DOWN@2,6,13,17,19）**CS 集合不同**：作者把 5 个 DOWN 钉在低号 AIC CS；r4 探针用了另一组。两者都能启动。

### 2.2 文档 / 库是否允许

| 点 | 结论 |
|---|---|
| 保留 CS 上挂 UP | 库允许（无 AIC/COC NI，`TCrossStation.cpp:181` 不炸）；文档 :90 说这些 CS 留给测试/管理，**未授权**挂 3DIO |
| DOWN 与 UP 混用 | 文档 :137 说“全部 UP”；库支持 DOWN（bottom D2U 已用）。混挂是推断 |
| 单独 `reserved_up_1x2` | 只有 3/8 端口 → `TBridge.cpp:502`（作者与 r4 均复现） |
| 是否“文档完整读法” | **否**。是“在库约束下最接近 reserved-UP 字面的可启动拼凑” |

### 2.3 签字可用性

- **可作为敏感性挂接**：证明“换几何是否翻转饥饿线”。
- **不可作为平台真实挂接签字**：文档未给出该混合；保留槽用途被挪用；一半端口仍是 DOWN 推断。
- 闸门主结论应建立在 **aic_down_1x2**（以及真非单根 ring）上；rsv 只作旁证。若主结论依赖 rsv 才成立，则按硬性规则标未核、不能签放大。


### 1.3 实测注入（seed 20260903，aic_down，lib_all_on，os512）

| 类 | done/expected | phases | AIC Dat inject_succ（core 维） | 结论 |
|---|---|---|---|---|
| ring_allreduce | 1520/1520 | 76/76 | 每 core 608（die1 上 0–9 完全相等；见下） | **无单 rank 漏斗** |
| ring_reducescatter | 760/760 | 38/38 | 每 core 304 | 同上 |
| ring_allgather | 760/760 | 38/38 | （对称，同 RS） | 同上 |
| hier_allreduce | 64/64 | 6/6 | **core0=48，core1–9=16**（die1）；core0 是 die-root | **确认 per-die 单根 gather** |

ring 的 Dat 注入在各 AIC 间完全均匀，与“每步全员写/读”一致。hier 的 die-root（rank0 / rank10）Dat 注入是非 root 的 3 倍，与 phase1 读半区 + phase2/3/4 根操作一致。

dio_top Dat（ring_allreduce）：die1 侧 raw 0x50–0x57 合计约 6080 量级且分散在 8 口；die2 侧也有注入（跨 die ring 边）。**不存在“单 3DIO 口吃掉全部”的 incast。**

> 注：`core_ring_counts.csv` 无 die 列，两 die 的 local core 号都会写成 0–9 并在合计中撞车。ring 下各 core 仍完全相等 → 两 die 各自内部也均匀。hier 下 core0（= 两 die 的 die-root 之和）=48、其余=16，与双 die-root 漏斗一致。

## 3. Lat=1 死锁（check D）

### 3.1 复现

命令等价于作者 `LAT1_DEADLOCK.md`：`--top-link-latency 1`，`aic_down_1x2`，os512，seed 20260903，`none` 臂，AR 与 RS。

| | AR（作者 / 审计） | RS（作者 / 审计） |
|---|---|---|
| ticks | 80000 / **80000** | 80000 / **80000** |
| phase | 0/4 / **0/4** | 0/2 / **0/2** |
| accepted | 640 / **640** | 640 / **640** |
| done | **309 / 1920** / **309 / 1920** | **309 / 1280** / **309 / 1280** |
| blocked | 7,032,903 / **7,032,903** | 同 / **同** |

hang_cores：所有 rank `phase_cursor==32`（phase0 写各自 32 chunk 已发完）；完成写的 rank 集合与作者一致（2,4,8,9,11,12,18 inflight=0）；其余卡在 inflight/write_q；`awaiting_grant==0`。**与 LAT1_DEADLOCK.md 逐项一致。**

生成配置一圈时延：20×1 + 1×2 = **22**（CS20→0 被 `even_sum` 抬到 2），与作者描述一致。

### 3.2 偶一圈断言 / 能否构造奇数圈

| 实验 | 做法 | 结果 |
|---|---|---|
| 文档字面 21×1 | 生成 lat=1 后再把全部 Link 改回 1（和=21） | **构造期断言** `TRingConfig.cpp:439` `m_oneCycleLatency % 2 == 0` failed（rc -6） |
| 作者路径 lap=22 | `--top-link-latency 1` + even_sum | 构造成功，AR/RS **死锁**（上表） |
| lap=24 / lap=42 | 生成后改 Link 使一圈为 24 或 42（不改库） | 批次进行中（见 §3.3） |

**结论：奇数圈在不改库的前提下无法运行；even-lap 断言是硬约束。** 作者说“even-sum bump 是贡献性的模型假象、死锁是无缓冲 Dat 环资源环” —— 前半已核（没有 bump 就进不了仿真）；后半（资源环机制）与 hang 状态（Dat inject_fail 巨大、Rsp/Dat 停在 309、phase barrier 不前进）一致，**可签字为现象分类**；其微观因果链（leaf-tag 占 5 slot、latency+1 缓冲等）引用了库行号，本审计对照了断言行与 lap=22 事实，**未逐步重做 leaf-tag 计数**，标为“作者机制解释：已核到断言与挂死状态，leaf-tag 算术未独立复算”。

### 3.3 lap 对比（不改库，只改生成配置）

（lap22/24/42 的 AR 跑完后回填：若 lap 增大后死锁消失，则“小偶一圈”是触发条件；若 lap=42 仍死 → 另有原因。）

## 4. 复现非单根饥饿表 + 半环 / 距 root 剖面（check B 前半）

### 4.1 作业范围与完成

审计重跑：`lib_all_on` × {aic_down_1x2, rsv_up_plus_down} × 4 个 RINGISH 类 × 8 种子 = **64** 次（作者 416 的非单根×lib 子集；none 臂与单根对照另计）。

- **64/64** `done == expected_txns`。
- 与作者 `option_a_starvation.csv` 中 `family=non_single ∧ arm=lib_all_on` 的 **104** 行逐键比对（place, roles, die, ring, channel, direction, metric）：下游、R、seeds_R_gt1、starve **全部一致**（相对 1e-3）。

作者声称的 416/416 完成：本审计未重跑 none 臂（216 次），但 lib 非单根子集与单根对照（进行中）已覆盖闸门判定所需。

### 4.2 过线清单

| 池 | 挂接 | starve 行数（S0∧S1∧S2∧S3） |
|---|---|---|
| 作者 non_single（ring+hier） | aic_down / rsv | **0 / 0** |
| **ring-only**（真非单根） | aic_down / rsv | **0 / 0** |
| **hier-only**（分段双根） | aic_down / rsv | **0 / 0** |

### 4.3 最近行（与 README 核对）

| 声明 | 作者 | 审计 |
|---|---|---|
| aic_down，aic die2 r0 dat cc half | dn=0.211，R=0.528 | **0.211143 / 0.528129**，R−3SE=0.233，1/8，starve=False ✔ |
| rsv 最近 Dat 端点 | dn=0.287 | **aic d1r0 cw end = 0.287418** ✔ |

两挂接所有 Dat 行下游均 ≪ 1.0；S1/S2/S3 全不过。

### 4.4 等待 vs 距 root 跳数（die1，ring0，Dat，cc；8 种子均值）

| hop | ring_allreduce | ring_reducescatter | hier_allreduce |
|---|---|---|---|
| 0（root CS） | 0.106 | 0.135 | **0.562** |
| 2 | 0.158 | 0.184 | 0.391 |
| 4 | 0.272 | 0.238 | 0.328 |
| 6 | 0.331 | 0.310 | 0.078 |
| 8 | 0.297 | 0.291 | 0.109 |
| 10 | 0.478 | 0.488 | 0.188 |

- ring：略随 hop 上升，峰值 <0.5，**无饥饿形态**。
- hier：峰值在 hop0（die-root），呈 incast 形状，但绝对值仍 <1.0，不过线。这与 §1.2“分段单根”一致，也说明 **在 chunks=1 的 smoke 缩尺下，双根 gather 不足以跨过 S2**。

## 3.3（补）lap 对比结果

| lap | AR done/expected | phase | 判定 |
|---|---|---|---|
| 21（奇数，强制） | 无法构造 | — | `TRingConfig.cpp:439` 断言 |
| **22**（lat=1 even_sum） | **312/1920**（与官方探针 309 同量级） | 卡在 0 | **死锁** |
| **24** | **462/1920** | 卡在 0 | **仍死锁**（完成数略增） |
| **42**（= 默认 lat=2） | **1920/1920** | 4/4 | **正常完成** |

**作者判断可签：** 死锁不是 TrafficGen 规划 bug；触发条件是“过小的偶一圈 + 无缓冲 Dat 环在 write-blast 下的资源环”。even-sum 把文档 21×1 变成 22，是必要的模型假象；把 lap 拉回默认 42 即消失。leaf-tag 占槽的具体算术未独立复算（未核细节，不影响分类签字）。

## 5. 单根对照仍饿，且饿在 root 所在 die（check B 后半）

审计重跑：`lib_all_on` × {aic_down, rsv} × {AR, RS} × roots {0,5,10} × 8 种子 = **96** 次，全部 `done==expected`。
（作者单根池还含 `tp_allgather`；AG 无 root-read incast，会稀释池化下游。审计用 AR+RS 是更干净的“会饿的类”。）

| 挂接 | root | 饿的 die | 代表行（dio_top Dat half） | 另一 die |
|---|---|---|---|---|
| aic_down | 0 | **die1** | d1r0 cc dn=6.14，R−3SE=2.74，8/8 | 0 行 |
| aic_down | 10 | **die2** | d2r0 cc dn=6.64，R−3SE=3.03，8/8 | 0 行 |
| aic_down | 5 | **无**（半环线） | — | — |
| rsv | 0 | **die1** | d1r0 cc dn=7.06，R−3SE=3.03，8/8 | 0 行 |
| rsv | 10 | **die2** | d2r0 cc dn=8.36，R−3SE=4.29，8/8 | 0 行 |
| rsv | 5 | **die1** | d1r1 **cw** half dn=4.82，R−3SE=1.23，7/8 | 0 行 |

与作者 `option_a_starvation.csv` 单根 starve 清单**同构**：饿的都是 root 所在 die；root=5 时 aic_down 半环线不过、rsv 的 cw half 过。绝对值因池内类集合不同（审计无 AG）偏高，不翻转“饿在 root die / 非环内禀”的定性。

**结论：先前 os512 饥饿是单根 incast，不是 lib_all_on 清不掉的环内禀位置不公。** 与 r4 的 root 搬迁实验一致。

## 6. 物理假设核对（check E）

| 假设 | 值 | 仓内出处 | 是否与平台一致 | 已核/未核 |
|---|---|---|---|---|
| 饥饿线 S0–S3 | 见文首 | r2/r3 审计约定 | 非平台字段 | 约定 |
| CC/CW 方向 | cw→高 CS；cc→低 CS | TNetwork.cpp:83-106 | 库内一致 | 已核 |
| top 3DIO 候选 aic_down_1x2 | DOWN 1×2 @ AIC CS | gen_config；文档无此挂法 | 推断 | **未核**；非单根下不过线，敏感性旁证 |
| top 3DIO 候选 rsv_up_plus_down | 0x50-52 UP@9/10/20 + 0x53-57 DOWN@AIC 0,2,4,6,8 | gen_config:406-419；TOP_3DIO_CANDIDATES 本回合新增 | 文档未授权保留槽挂 3DIO；UP/DOWN 混挂推断 | **未核**；可作敏感性，**不可当平台挂接签字**（§2） |
| `H-RING-NEIGHBOR-RANK` | 邻居=程序 rank±1，非物理 CS；9↔10 跨 die | COLLECTIVES.md；TrafficGen.h | 流量假设 | **未核**（建模选择） |
| `H-RING-BARRIER-PHASE` | 每半步全局 barrier | 同上 | 比 per-neighbor credit 更串行 | **未核** |
| `H-RING-CHUNK-512` | chunks=1 | 同上；单根对照 chunks=32 | smoke 缩尺 | **未核**；放大后需加 chunk |
| `H-HA-MEDIATED` | send/recv 经 HA cell，无 AIC↔AIC P2P | TrafficGen；COLLECTIVES.md | 与真实 NCCL 环不同 | **未核** |
| `H-HIER-DIE-SPLIT` | die-root=0 与 N/2 | TrafficGen hier | 分段双根，**不是非单根** | 实现已核；归类错误见 §1.2 |
| 一圈偶数且 <200 | TRingConfig.cpp:439 | 库断言 | 库约束 | **已核**（奇数圈无法构造） |
| lat=1 → lap=22 | even_sum 把 CS20→0 从 1 抬到 2 | gen_config even_sum；noc_setup.md:103 允许 1–3 | 文档 21×1 不可运行 | **已核**；死锁在 22/24，42 消失（§3） |
| 无缓冲 highway = 1 slot/CS + latency+1 | TCsHighWay.cpp:70-71 | 库 | — | 行号已核；与死锁分类一致 |
| 静态 leaf-tag 占槽 | sta_leaf_tag_cc/cw 各 5 | TNetwork.cpp:166-172；gen_config | — | **未核算术**（作者称 22 圈上占 5；未独立复算） |
| top 链路时延默认 2 | gen_config；区间 1–3 | noc_setup.md:103 | 常数值无出处 | 默认已核；lat=1 死锁已核 |
| bottom H/V 时延 | 3 / 4 | 同 r3/r4 | 局部有文档 | **未核**（本轮未扫；非单根结论不依赖） |
| collective root 默认 0 | run_soc --collective-root | — | 流量假设 | 已核为单根饥饿根因 |

## 7. 闸门判定（check F）

**判定：不放大，关 P-0221。**

依据船长 18:21 option A：非单根集合 + lib_all_on + os512 下，若仍饿 → 有条件放大；若不饿 → 不放大并关单。

### 理由

1. **真非单根（ring_*）在两条挂接下 0 行过饥饿线**（§4.2），64/64 完成；与作者表 104 行 lib×non_single 数值一致。
2. **作者把 hier 误标进 non_single**（§1.2），但 hier-only 同样 0 行过线（chunks=1 smoke）；不翻转“不过线”的结论。
3. **单根对照仍饿且饿在 root die**（§5），证明 r3/r4 的 os512 饥饿是单根 incast，不是环内禀；option A 换成非单根后该机制消失，与“不放大”一致。
4. **挂接未核**（aic_down / rsv 皆推断），但两种几何下非单根均不过线；按硬性规则，未核挂接不支撑“放大”，**可以支撑“不放大”**（敏感性显示挂接不制造饥饿）。
5. Lat=1 死锁与环模型/偶一圈约束有关，**不是** TrafficGen 规划 bug；不构成“机制清不掉的饥饿线”，与闸门正交。

### 本判定所依赖的、仍属未核的建模假设（硬性规则披露）

| 假设 | 若翻转会怎样 |
|---|---|
| `H-HA-MEDIATED`（无 AIC↔AIC P2P，每跳变 HA 往返） | 真实 P2P 环可能改变注入几何；需重跑 |
| `H-RING-CHUNK-512`（chunks=1） | 加大 chunk / 接近信封后 hier 的双根 gather 或 ring 流量可能过线 |
| `H-RING-BARRIER-PHASE`（全局 barrier） | 更异步的 credit 环可能改变拥塞形态 |
| `H-RING-NEIGHBOR-RANK`（程序序邻居） | 改成物理 CS 邻居后跨 die 边消失，剖面会变 |

这些假设下的 **实现态** option A 不过线 → 签不放大。若船长要求“在真实 NCCL 环 / 大 chunk / AIC↔AIC P2P 下仍不过线”才关单，则当前证据不足，应改判 **其他条件**（先补映射再关）。

### 什么会翻转判定

- **改回「仍放大」**：在 chunks 加大或去掉 HA-mediated 之后，ring_* 某一 die×ring 过 S0–S3；或船长认定 hier 的双根 gather 必须当非单根且在信封规模过线。
- **改成「其他条件」**：要求先有平台真实 3DIO 挂接、或先有 AIC↔AIC P2P 的环实现，再关 P-0221。
- **保持「不放大关 P-0221」**：维持 option A 字面（非单根 + 现实现 + smoke/os512），接受 H-RING-* / H-HA-MEDIATED 为已声明假设。

## 8. 产物路径

- tip / 构建：`bbb7baf` / `artifacts/soc_sim/build/d7b0842b693436ee`
- 非单根：`/tmp/r5/ns`（64）、`an_ns.py`、`ns_rows.json`
- 单根：`/tmp/r5/sr`（96）
- Lat=1：`/tmp/r5/lat1`；奇数圈断言 `/tmp/r5/oddlap`；lap 对比 `/tmp/r5/lap{22,24,42}_ar`
- 静态注入：`/tmp/r5/inject_plan.py`
- 本文件未提交；目标仓无 commit/push/评论。

