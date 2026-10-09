# Tier 0 · P-0221/M-1 · 环段令牌桶准入（Segment Token Bucket, STB）

- 机制卡: mechanisms/P-0221/M-1.md（PR #100 head `07c78cd`）
- 题卡: problems/P-0221.yaml（main@1909fb0，引入提交 `5c7c0b7`）
- 作者: Jim Keller
- 判决: REJECT
- 可行性: FAIL（§2.5 段密度上界的证明不成立；Snp 环 1b `hot` 捎带 = 加线）
- 新颖性: FUNCTIONAL_EQUIVALENT（教科书 token bucket / leaky bucket 逐链路限速；环库已有 in-ring 源端流控令牌桶）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc live `main@63163cad900979ab00edff1e0268f87b37b18e3b`（2026-10-09 11:31 CST `git fetch` 后的 tip；与 63163ca 相同，卡所引行号无漂移，见 SUMMARY §1）

## 卡摘要
每个环段 `(channel, sub-ring, direction, CS_i→CS_{i+1})` 设一只共享令牌桶（B=2，每拍 +ρ_max=3/4）。注入方对路径 P 上每段的**本地锁存副本**各减 1，全部 ≥1 才可注入，否则 fail-wait。段主 CS 持有权威桶，通过同通道对向 Dat 子环的「控制 Dat 心跳」（Data 内 128 b 向量，每 W_hb=16 拍一圈）广播；Snp 环只捎 1b `hot`。卡声称 `ρ_transit(s,W) ≤ ρ_max + B/W` 且 `oversub≡0`。

## 轴一 可行性
1. **上界证明的第 2–3 步不成立。** 证明假设「每次过路注入消耗 1 个权威 `bucket[s]`」，但规则 §2.3-2 里注入方减的是**自己的锁存副本**，权威桶在段主 CS，注入方当拍无法与远端权威值比较（卡规则 6「注入用 latch-1 与权威比」在物理上做不到：权威值要过 ≥ 半圈才到）。段主只能在 flit **经过时**才知道被消耗，此时注入已经发生。于是：每个上游注入者在一个心跳刷新周期内可以各自花光锁存值（≤B）。N_up 个上游合计每刷新周期可注入 N_up·B 个过路 flit。取卡默认 B=2、W_hb=16、N_up=10：10·2/16 = 1.25 > 1，即上界退化为 `ρ ≤ 1`（无约束）。`oversub≡0` 没有任何执行机制，只是一个探针；按卡 §2.5-7 自己的规则，本上界作废。
2. **分布式共享令牌桶的已知结论**：在无共识/无令牌实体传递的情况下，多个异地消费者共享一个按时间补充的桶，只能靠（a）把桶静态切分给各消费者（= 逐节点配额，题面判为不闭合），或（b）令牌实体本身沿环流动（= 预留槽 / i-tag / SAT 类）。卡两者都不是。
3. **心跳税算错。** 卡用 `C_ring = CS_NUM = 21` 当一圈拍数。实际一圈 = Σ link latency：top 21×2 = 42 拍（`gen_config.py:345` `lats=[2]*TOP_CS`，`:255` 注释 "ring sum is sum(latencies)"），bottom H ≈72–76，bottom V 132/148/152（`gen_config.py:430-449`）。W_hb=16 < 一圈 42 ⇒ 每个子环方向需同时有 ⌈42/16⌉=3 条心跳在环上，锁存龄最坏 ≈ lap + W_hb ≈ 58 拍（top），bottom V > 150 拍。陈旧度直接放大第 1 点的超订。
4. Sink / 死锁：fail-wait 仍落在端点 outstanding，无丢包、无环上队列，无死锁。问题在「上界」不在「活性」。
5. 指标：即使上界成立，也只是**压低过路密度**；下游等待从「无空槽」变成「几何等待剩余空槽」的论证对推理 makespan 的影响要靠 cycle 证明，卡全部数字为 UNSIGNED 假设。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际（代码 / 规范） | 判定 |
|---|---|---|---|---|
| 1 | 每向每 CS 槽数 | 1，`TCsHighWay.h:136` | `std::vector<NetworkFlit*> m_sendFlit` 在 `include/TCsHighWay.h:135`（差 1 行）；每方向一个仲裁槽 | ✅（行号 -1） |
| 2 | 环周 `C_ring` | `= CS_NUM`，top 21 拍 | CS 数 top 21 ✅（`gen_config.py:19`）；**一圈拍数/在途槽容量 = Σlat**：top 42，bottom H ≈72–76，bottom V 132/148/152 | ❌ 拍数与 CS 数混用 |
| 3 | 子环数 Req/Rsp/Snp/Dat | 1/2/1/2，`TMultiRing.cpp:223-231` | 值来自 `sub_channel_cnt req 1 rsp 2 snp 1 dat 2`（`gen_config.py:308`、`docs/noc_setup.md:41`）；所引行是解析器 `src/TMultiRing.cpp:223-231` | ✅ |
| 4 | `CS_NUM ≤ 64` | — | `m_tgtCs` 为 `uint64_t`（`include/chi_ring_common.h:275`）；实际最大 38 | ✅ |
| 5 | `kBeatBytes` | 64，`Endpoint.h:27` | `tests/soc_sim/platform/Endpoint.h:27` ✅（侧分支 89f9c88 上移到 :29，非 main） | ✅ |
| 6 | DAT Data / BE 宽 | 512 b / 64 b | CHI Table 13-9，DW=512 时 BE=64 | ✅ |
| 7 | 心跳向量放进 DAT Data | 64 段 × 2 b = 128 b ≤ 512 b | 宽度够；但每条心跳占一整个 DAT 槽（~670 b 级 flit 运 128 b），且需要一个 DAT 保留 opcode（E.a Table 13-18：0x8–0xA、0xD–0xF 为 Reserved） | ✅ 宽度；⚠️ 需保留 opcode + 每 CS 解码（库内改动） |
| 8 | 心跳税 | 1/W_hb 个对向槽 | W_hb=16 < lap 42 ⇒ 每子环方向 3 条并发心跳，约 3/42 ≈ 7% 对向在途容量；bottom V 更高 | ⚠️ 低估 |
| 9 | Snp 环 1b `hot` 捎带 | 「ESL `NetworkFlit` 元数据，与 i-tag/e-tag 同类，不是新导线」 | i-tag/e-tag 字段在硬件 flit 头里**本来就有线**；新增一个随每个 flit 走的 1b 字段 = 每条链路每方向 +1 根线 | ❌ 违反「不加线」 |
| 10 | Snp 无 Data | Table 13-8 | ✅ 卡未借 Snp 运 Dat | ✅ |
| 11 | REQ Addr / RSVDC | REQ Addr「SAW+3 ≈ 44–52」；RSVDC ≤32 b | CHI：REQ Addr = RAW 44–52，SNP Addr = SAW 41–49；RSVDC Y∈{0,4,8,12,16,24,32} | ✅ 数值；⚠️ 标签写错 |
| 12 | CHI Size 64 B | Table 13-18 `0b110` | 我方 IHI0050E.a 中 Size 编码在 Table 13-20（及 2-15），13-18 是 DAT opcode 表；E.b 表号需复核 | ⚠️ 表号 |
| 13 | i-tag 语义 | 「只在空槽到达后赢仲裁，不阻止上游吃光」 | `sendFlitToWay` `:1095-1110` 在**过路占用槽**上打 `sender_tagged`；该 flit 弹出后槽保持保留（`isSlotReservedFlit` `:1151-1158`），上游一律不可用，回到打标者 `tryItagProcess` `:894-950` 使用 | ❌ 卡对先例的描述错误 |
| 14 | i-tag 阈值 / 活标数 | 64×2=128，每 highway 1 | `wantItag` `:1000-1007`（policy 0：`thr*2`）；`itagThreshold=64`（`gen_config.py:134`） | ✅ |
| 15 | e-tag | 1 reserved，`etagReserveCycle 10` | `gen_config.py:342`；`include/TReserveState.h` | ✅ |
| 16 | 桶 B / ρ_max / W_hb | 2 / 3/4 / 16 | 卡假设，UNSIGNED | — |
| 17 | highway 队列 / 心跳缓冲 | 0 / 0 | 无缓冲环 ✅；但每 NIC 需存「路径上所有段」锁存：≤64 段 × 2 b × 6 子环 × 2 向 ≈ 1.5 kb/CS（卡未列） | ⚠️ 漏列存储 |

## 接口落点核查（live `main@63163cad`，与 63163ca 无差异）
| 卡声称的落点 | 实际 | 结论 |
|---|---|---|
| `src/TCsHighWay.cpp:1041-1117` 注入谓词 | `sendFlitToWay` 位于 `:1041-1118` | ✅ 位置对；哈希锁定库，**新分支** |
| i-tag 路径 `:894-950`、`:1094-1103` | `tryItagProcess` `:894-950` ✅；打标块 `:1095-1110` | ✅（小偏移） |
| `tests/soc_sim/platform/CongestionCtrl.h` / `--cc-scheme` | 存在：`soc_main.cpp:80` 解析 `--cc-scheme`，`soc.cpp:590-640` `bind_control()`。但 `CongestionCtrl` 是**每 die NI 组、按窗口**的速率律（srcfc/drr/aimd/hat/ecn/tagwin，`CongestionCtrl.h:280-330`），并在 `:113-116` 注明不改 NI 令牌；不做逐拍逐槽、逐路径段的判定 | ⚠️ 只能挂开关和探针，谓词必须进 `TCsHighWay`（新分支） |
| 段主 `bucket` / `NetworkFlit` 新字段 | `include/` 哈希锁定 | 新分支；`NetworkFlit` 新字段即第 9 项「加线」 |
| RTL | 仓内无 RTL | ✅ 不触 RTL |
- **零代码对照（卡未列）**：环库已有 in-ring 源端流控——下游 NI 按注入失败均值生成 FC 等级（`TNetworkInterfaceBase.cpp:842` `genSendFlowCtrl`），以 `NetworkFlowCtrl` 沿**反方向**传播 `spreadCnt` 跳（独立 FC 通路 `m_highWayFcBuf`，`TCsHighWay.cpp:152-155`、`:1423-1527`），上游 NI 用令牌桶限速（`TNetworkInterfaceBase.cpp:1141` `updateTokenBucket`；注入门 `TCsHighWay.cpp:626`、i-tag 门 `:907`）。`gen_config.py --fc-profile experiment_srcfc` 即在 top Dat 环打开（`:364-365`、`:486-494`）。P-0221 基线「关闭额外流控」= 这条关着。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| 教科书 token bucket / leaky bucket（逐链路速率整形） | **FUNCTIONAL_EQUIVALENT** | 按资源（链路）设桶、按时间补充、消费即扣——就是逐链路 token bucket 准入；「多个源共享一个链路桶」是其多源版本，无新执行原语 |
| 环库 in-ring 源端 FC（令牌桶） | FUNCTIONAL_EQUIVALENT | 同为「下游拥塞信息逆流 → 上游令牌桶门控注入」；差别仅为 STB 按段建桶、库内按 NI 建桶且不分路径 |
| IEEE 802.17 RPR 公平算法 | 同类 | 拥塞链路向上游通告 fair rate，上游对**经过该链路**的流量限速——即「按段共享上界」的教科书形态 |
| MetaRing SAT | 不同 | 卡自述差异成立（SAT 是整环配额），但不构成新意 |
| P-0198 M-1 CBC / M-4 AODI / M-12 HSSL | 不同 | 卡已切开 |
| P-0221 M-3 / M-5 | 同族 | 守恒账 / 配额分割是同一「段级合计上界」的另两种记账 |
- 显式标注（captain 规则）：**token bucket → FUNCTIONAL_EQUIVALENT**，理由同上。

## 指标核对
- 主指标是推理 makespan / 最差节点。卡的因果链「压 ρ_transit → 下游空槽到达率 ≥1−ρ_max → 尾下降」在上界不成立时断在第一环。
- 即便执行成立，`ρ_max<1` 是**全时**节流：无饥饿时也在丢吞吐，扇入集合之外的类（broadcast、均匀读）可能变差；卡 §6 已承认需分列。

## 判决理由
REJECT。核心上界 `ρ ≤ ρ_max + B/W` 依赖「注入当拍扣权威令牌」，而机制只扣本地陈旧锁存，N 个上游可并行超订，默认参数下上界退化为 1，题面闭合条件（逐环段密度上界）不满足；Snp 侧 1b 捎带是新线。去掉这两处后剩下的是教科书 token bucket 加环库已有的 in-ring 源端 FC 令牌桶，属 FUNCTIONAL_EQUIVALENT。

## 若作者重提须先回答
1. 令牌由谁、在哪一拍被权威扣除？给出不依赖陈旧锁存的超订上界（含 N_up、lap=Σlat、W_hb）。
2. 与 `--fc-profile experiment_srcfc`（库内 Dat in-ring FC）同信封对打，证明按段建桶带来 makespan 增量。
3. 用拍数 lap = Σlat（top 42，bottom V ≤152）重算所有时序与税。
