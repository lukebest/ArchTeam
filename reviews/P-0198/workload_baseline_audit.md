# P-0198 workload baseline 审计（评估审计 · 只读）

- 对象：lukebest/bufferless-ring-noc PR #1，分支 `cursor/p0198-llm-noc-baseline-aa90`
- 最终审计 tip：**`89f9c889955ea68bef61a18768c226e007ab974a`**（base `main@63163ca`）
  - 初审 tip `f0ba6fd`；审计期间作者落地 `a422bb3`（修 multicast）+ `89f9c88`（PHYSICAL_ASSUMPTIONS.md）。以下结论按 `89f9c88`。
- 方法：box 上 scratch clone `/workspace/brn-p198-audit`（未 commit/push），clang 19 编译 soc_sim，复跑 smoke（seed 20260903，2 top die，outstanding 16，80000 cycle；修前另跑 800000 cycle）。原始输出：`/tmp/brn_runs`（修前）、`/tmp/brn_runs2`（修后）。
- 口径：只是 smoke，相对指标，不排序，不涉及硅片结论。与 M-1/M-2/M-4 已淘汰候选无关。

## 判决

**有条件可用**：只能当 smoke 级 workload baseline，供非 CRRF 对照臂（none/srcfc/itag/issue-order/uturn/dat_mcast）做冒烟。
**不能用于 M-5 CRRF 15:1 Snp KILL 判决（退回这一用途）。** 原因见第 1.3 节：一是混合流量顺序注入，二是本 baseline **完全没有 Snp 流量**（所有 run `snp=0`）。

## 1. 四个映射假设

### 1.1 H-P2P-AS-BROADCAST：**有条件接受（只当扇出压力代理）**
- 实现：`TrafficGen.h` broadcast 是 root 写 cell 0，其余 N−1 个 rank 读（`TrafficGen.h:242-245`）。`target_for` 按 cell 取 HA，cell 0 的 32 个 chunk 全部落到**同一个 HA**（`TrafficGen.h:222-225,233-236`）。实测 p2p_act_none 640 txn 全进 bottom0 port 0x200（`ha_counts.csv`）。
- 与单播 p2p 比（16 KB，相邻 stage）：单播约 32 写 + 32 读 = 64 txn；broadcast 是 32 + 19×32 = **640 txn（约 10 倍）**。Dat 弹出点从 1 个变成 19 个，Dat 槽占用约放大 N−1 倍，并多出一个 HA 源端热点。hop：两者都经 HA 中转（H-HA-MEDIATED），所以环上 hop 是 AIC↔3DIO↔HA 路径，不是 AIC↔AIC 相邻距离。broadcast 的平均距离覆盖全部 rank，比相邻 stage 单播更长。
- 偏差：**高估**环负载、eject 数、槽占用和 HA 热点；对 multicast 类机制（dat_mcast）明显有利。
- 只适合看：单源扇出读、HA 源热点下的完成性和相对尾延迟。不适合看：p2p 时延、p2p 带宽、makespan 绝对值、按链路的负载。

### 1.2 H-RS-AS-REDUCE：**有条件接受（标偏差）**
- 实现：reduce 是 N 个 rank 各写 1 个 cell，然后 **root 一个人**读 N 个 cell（`TrafficGen.h:246-248`）。
- RS 的真实形状：每个 rank 读所有 rank 的 1/N 分片。总读字节和 reduce 同量级（N·S），但 eject 分散在 N 个 rank 上。
- 偏差：reduce 把全部 N×32 次读集中到 root 的单个 AIC：**eject 热点 + 单核 outstanding=16 串行**。makespan 被 root 的闭环卡住（偏悲观），环的并行度被低估。对 eject/hotspot 类机制（uturn、itag）有利，对整环带宽类机制不敏感。
- 只适合看：汇聚热点。不适合代表 SP 的 RS 半边。

### 1.3 H-NO-SIMULTANEOUS-MIX：**不接受。15:1 KILL 可用性：否（NO）**
- 实现：mix_15_1 是两次独立 `run_soc`（large chunks=15、small chunks=1，`generate.py:99-110`），没有同时注入。
- 两次独立 run 之间不存在争用，所以既不能证明 Snp 被饿死（KILL），也不能证明 Snp 活下来（survive）。
- 更根本的问题：这里的「15:1」是**同一 allreduce 的 cell chunk 数之比**（大 cell = 15×512 B），所有 CHI txn 仍是 512 B / 8 beat，全部走 Req/Rsp/Dat。它不是 M-5 的 Dat:Snp duty。**TrafficGen 不产生任何 Snp 流量**：所有修前修后 run 都是 `summary.json traffic.snp=0`、`aic_rx_snp=0`；`try_send_snp` 只被 3DIO 转发调用（`Mux3dio.h:145,149`）。
- KILL 判决需要：(a) 同一次 run 里 Dat 和 Snp **并发注入**，比例可设（Dat 负载使 Dat 窗口真正借用 Snp 环）；(b) Snp 和 Dat 共享被 CRRF 改写的物理环（本树 CRRF unavailable，`configs/baseline_crrf.json`）；(c) 分 class 的 Snp 时延（p50/p99），并有 rebind-off 参照，用来算 ≤1.4× 门限；(d) 15:1/7:1/3:1 duty 下同 seed 复跑。本树今天做不到 (b)，(a)(c) 需要 platform 加 Snp 生成器和按 class 统计。
- 另外，catalog 自相矛盾：`catalog.json:126` H-MIX-15-1 的理由写「8192 B 与 512 B」，`catalog.json:256` 的值是 7680。

### 1.4 H-RANK-AIC：**接受（已声明，`catalog.json:99-102`，README:62）**
- rank = 每 top die 10 个 AIC core，smoke 2 die → 20 rank；rank 顺序按 core 索引，root=0（`summary collective_root 0`）。
- 影响：所有集合都经 HA，rank 位置只影响 top die 上 AIC↔3DIO 段。HA 选择由 cell id 决定（`cell % candidates`），与 rank 局部性无关。所以热点由「cell 0 → 单 HA」和「root=rank0」决定，不由 rank 映射决定。12-die 信封下的 TP 世界大小（120）没有来源，属假设，已标。
- `Core_num=24` 与 10 的冲突已披露（README:67，`gen_config.py:44`）。

## 2. 出处（provenance）——未标或标错的数字

大部分数字标了 sourced/推导/假设，质量较好。以下有问题（行号 @89f9c88）：

| # | 数字 | 位置 | 问题 |
|---|---|---|---|
| P1 | tp_allgather `collective_chunks=4` | `generate.py:119`；README:81 | 推导值应为 16384/512=32；4 只有「O(N²) keep tiny」注释，没有 假设 标签，smoke 实际只有 2 KB/rank |
| P2 | moe_alltoall `collective_chunks=1` | `generate.py:123`；README:83 | 推导值 16；无 假设 标签 |
| P3 | kv_decode「smoke 用 16 token」 | README:77，`catalog.json:95` | generate 没有实现；实际是 uniform、`txns_per_pair=1` → 1920 txn（约 3 token），与声明不符 |
| P4 | `cycles 80000` | `generate.py:83`；README:108 | 标了 假设，但没有依据 |
| P5 | `txns_per_pair 1` | `generate.py:85`；README:107 | 只写「smoke 缩尺」，没有 tag（catalog H-SMOKE-BBOX 部分覆盖） |
| P6 | envelope read outstanding 512 | `catalog.json:31-34` | 标 sourced，实为 128×4 推导 |
| P7 | 15:1 大包 7680 vs 8192 | `catalog.json:126` vs `:256` | 理由与值不一致 |
| P8 | itag 扫描点 8/16/32 | `configs/baseline_itag_*.json`，README:39 | 扫描点选择没有出处或 假设 标签（参照 64 有出处） |
| P9 | 0.2 ns/cycle | `generate.py:223` | 硬编码；源在 `Endpoint.h:18`，建议引用常量 |

## 3. dat_mcast 未完成（578/640、1543/1680）

**一句话诊断（修前 f0ba6fd）：platform 层的完成路径丢 beat。不是库死锁/活锁，也不是 cycle 上限太短，也不是 expected 计数错。** HA 把 Dat 打成 multicast（`m_isCoalesceSucc` + tgt/txn 列表），并给组员每人扣 1 beat（`Endpoint.h:725-729`）。但 HA 在 bottom die，目标 AIC 在 top die，bottom TBridge 不会激活 multicast（`TBridge.cpp:402-410,512`：只在目标同 die 时激活）。flit 经 3DIO 时，`Mux3dio.h:129,138` 和 DIO 重注入（`Endpoint.h` try_send_*）调用 `reset_route()`，旧版会 `f.ctrl = {}`，把 multicast 元数据抹掉。到 top die 后它是一个普通单播，只送给组长，组员被扣掉的 beat 永远收不到。

证据（复跑，结果与 PR 表完全一致）：

| run | done/expected | HA tx_dat | AIC rx_dat | 需要 beat | 结束状态 |
|---|---|---|---|---|---|
| p2p_act none 80k | 640/640 | 4864 | 4864 | 4864 | — |
| p2p_act dat_mcast 80k（修前） | 578/640 | 4526 | 4526 | 4864 | `valid_hw 0 valid_ni 0 ha_tracked 0` |
| p2p_act dat_mcast **800k**（修前） | 578/640 | 4526 | 4526 | 4864 | 同上，与 80k 完全相同 |
| tp_allgather dat_mcast 80k / **800k**（修前） | 1543/1680 | 12054 | 12054 | 12800 | 同上 |

- 每个 multicast flit 只到了 1 个目标（HA tx = AIC rx），缺 338 / 746 beat。
- 网络已空（debug_hold），cycle 放大 10 倍结果不变，所以不是死锁/活锁/上限问题。

**修后（a422bb3：`reset_route` 不再清 ctrl，`Endpoint.h:188-191`）复跑**：

| run @89f9c88 | done | HA tx_dat | AIC rx_dat | makespan_ns |
|---|---|---|---|---|
| p2p_act none | 640/640 | 4864 | 4864 | 3249.2（与修前一致） |
| p2p_act dat_mcast | **640/640** | 4512 | 4864 | 3048.0 |
| tp_allgather none | 1680/1680 | 12800 | 12800 | 3589.2（与修前一致） |
| tp_allgather dat_mcast | **1680/1680** | 11331 | 12800 | 3297.2 |

修复有效：beat 守恒，网内复制生效（HA 发出更少、AIC 收齐），none 臂无回归。
遗留：PR body 第 35/66/68/79 行和 README 仍写 dat_mcast 未完成（578/640、1543/1680、「hit cycle cap」），已过时，而且「hit cycle cap」的归因本来就是错的。修后 dat_mcast 的 smoke 行需要重跑并替换。`mcast_spent` 按 txnid 去重（`Endpoint.h` service_replies），不同源 txnid 碰撞时只会延迟，不会丢，属低风险，未进一步验证。

## 4. 结构范围

`git diff --name-only 63163ca..89f9c88`：
- `tests/soc_sim/platform/Endpoint.h`、`tests/soc_sim/platform/TrafficGen.h`（platform，范围内）
- **范围外（tests/soc_sim 下、platform 外）**：`tests/soc_sim/gen_config.py`、`tests/soc_sim/run_soc.py`。这两处只透传已有库开关 `itagThreshold` / `UturnConnect`，PR 已披露。默认值 64 / off 与原行为一致，原 none 臂结果不变。属可接受的越界，需要明确记录。
- `workloads/README.md`、`workloads/p0198-llm-noc/**`（文档、配置、生成器）
- **`include/`、`src/`、RTL：未改动**（diff 无这些路径，`run_soc.py` 的 `verify_originals()` 构建通过）。

## 5. 是否有排序或超出 smoke 的声明

- 没有排序。PR body 和 README 反复写「Do not rank」「smoke-only」。
- 需要注意：PR 表把 makespan / p99 按臂并列，itag_16 990.6 vs none 1060.6 之类的差值很容易被读成排名。单 seed、2 die、`txns_per_pair=1`，差值没有置信区间，不得引用。
- 「15 同时对齐 M-5 Dat:Snp 15:1 扫描粒度」（README:84，`catalog.json:126`）容易让人误以为可以服务 CRRF 15:1，需要改写（见 1.3）。

## 物理假设核对

列：假设 / 值 / 仓内出处 / 是否与平台一致 / 核验状态（「已核」= 本审计打开文件或用运行 readback 确认；「未核」= 不签）。

| 假设 | 值 | 仓内出处 | 是否与平台一致 | 核验 |
|---|---|---|---|---|
| 每 channel 子环数 req/rsp/snp/dat | 1/2/1/2 | `gen_config.py:342`；`soc.cpp:39 kSubs` | 一致：运行 readback `first_die_subs [1,2,1,2]`（`soc.cpp:1140`），输出含 `*Dat_sub0/sub1`、`*Snp_sub0`。注意 `summary.sub_channel_cnt` 是硬编码字符串（`soc.cpp:1134`），不能当证据 | 已核 |
| **Dat=2 子环、Snp=1 环**（M-5 前提） | Dat 2、Snp 1（每条物理环上） | 同上；`docs/noc_setup.md:41,84` | 一致 | 已核 |
| top 物理环数 | 2（ring_cnt 2, Hring 2） | `gen_config.py:343-344` | readback `first_die_ring_cnt 2` | 已核 |
| bottom 环数 | 28 | `docs/bottom_manyring.csv` | log `constructed bot0 rings=28` | 已核 |
| top CS/环 | 21 | `gen_config.py:19` | 推断（PHYSICAL_ASSUMPTIONS 标 inference） | 已核（值）/出处为推断 |
| Dat beat 宽度 | 64 B | `Endpoint.h:29`；`docs/noc_setup.md:166` | top 一致；bottom 文档 128 B（`noc_setup.md:307`）未采用（`gen_config.py:593`） | 已核（top）；bottom 宽度未核，不签 |
| Snp flit 宽度 | **模型无表示** | 无 | 环模型是每 flit 占一个 slot，不分 channel 位宽，Snp 与 Dat beat 在槽层面同质。CRRF「Dat 借 Snp 环」要求的 Snp 槽位宽 ≥ Dat beat **在本树不可表达** | **未核，不签** |
| CHI txn | 512 B = 8 beat | `docs/hardware_setup.md:57`；`TrafficGen.h` | summary `beats_per_txn 8` | 已核 |
| 3DIO 链路宽 | 32 B/cycle（64 B beat = 2 cycle） | `Mux3dio.h:22,29,53-54`（引 topology.md §4.1 "typically 32B"） | 一致 | 已核（代码）；文档措辞「typically」，未核 |
| Mux rx/tx buffer / pipe / afifo lat / depth | 5 / 20 / 6 / 15 | `Mux3dio.h:20-26`；`run_soc.py:224-229` | summary.mux 一致 | 已核 |
| HA RX 深度 req/rsp/snp/dat | 10/13/10/13 | `Endpoint.h:132-136`（hardware_setup 2.6） | 一致 | 已核（代码），文档行未逐行核 |
| HA TX 深度 | 17/16/16/20 | `Endpoint.h:148-151` | 一致 | 已核（代码） |
| AIC RX credit | 4 | `Endpoint.h:28 kTerminalRx`（无文档） | 代码常量 | 无文档，**未核** |
| 3DIO 端点 buffer | 5 | `Endpoint.h:27` | 一致 | 已核 |
| HA trackers | 512 | `Endpoint.h:26`；`docs/hardware_setup.md:163` | 一致 | 已核 |
| outstanding 信封 rd/wr | 512/256（128×4、64×4） | `TrafficGen.h:145-148`；`hardware_setup.md:60-61` | 一致；catalog 标 sourced 应为 推导 | 已核 |
| outstanding smoke | 16 | `catalog.json:41-44` 引 M-5 README | 外部仓出处，本仓无法核 | **未核** |
| AIC / HA 带宽 | 600 / 134 B/ns | `Endpoint.h:24-25` | 一致 | 已核（代码），文档未逐行核 |
| HBM 时延 | 0 | `gen_config.py:49` | 推断，无文档 | 假设，不签 |
| 端口 buffer（AIC/COC/HA/3DIO share/output depth） | 见 PHYSICAL_ASSUMPTIONS.md §8 | `gen_config.py:130-222` | 抽查 `gen_config.py:138-141` 一致 | 抽查已核，其余未逐项核 |
| 每节点 inject/eject 口 | AIC 1x1 UP（even+odd 两口）；3DIO 1x2 DOWN | `gen_config.py:346-369` | 推断（top 3DIO 挂 AIC CS 是为规避空指针，`gen_config.py:43`） | 已核（值），物理真实性未核 |
| 链路时延/权重 | top 2；bottom 3/4 等 | `gen_config.py:46,476-497` | 多为推断 | 推断，**未核** |

小结：Dat=2、Snp=1 是 baseline 实际运行的配置（readback 已核）。但 **Snp 的 flit 位宽在模型里不存在**，baseline 也**没有 Snp 流量**。所以凡是涉及 Snp 容量或 Dat-on-Snp 的物理论断，本 baseline 都不签。

## 修复清单

1. **[阻断 CRRF 用途]** 在 platform 加 Snp 流量生成（HA→AIC 或 AIC→HA Snp），支持在同一 run 内按比例和 Dat 并发注入，并输出分 class 时延（Snp p50/p99）。在此之前，README/catalog 必须明确「不可用于 M-5 15:1 KILL」，并删掉「对齐 M-5 Dat:Snp 15:1」的表述。
2. mix_15_1 改名或改注释为「allreduce cell chunk 15:1」，不是包长比，也不是 Dat:Snp 比；修 `catalog.json:126` 的 8192/7680 矛盾。
3. 重跑 dat_mcast smoke 行（@89f9c88），替换 PR body / README 中 578/640、1543/1680 和「hit cycle cap」。把根因写成「3DIO 重注入清 ctrl，丢 beat」。
4. 补标签：P1/P2（chunks 4/1 → 假设 + 理由，或改回推导值）、P3（kv_decode 16 token 声明与实现不符）、P4/P5/P8、P6（sourced→推导）。
5. H-P2P-AS-BROADCAST、H-RS-AS-REDUCE：在 README 写明偏差方向（broadcast 约 10× 放大 + 单 HA 热点；reduce 是 root eject 热点 + 单核串行）。p2p_act / tp_reducescatter 的结果禁止用于 p2p/RS 时延结论。
6. PHYSICAL_ASSUMPTIONS.md 补一行「Snp/Dat flit 位宽：模型不表达（每 flit 一个 slot）」，以及「baseline Snp 流量 = 0」。
7. `gen_config.py` / `run_soc.py` 越出 platform 的改动保留，但在 PR 范围声明中列为「platform 外、仅透传库开关、默认值不变」。
