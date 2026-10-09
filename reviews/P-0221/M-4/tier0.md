# Tier 0 · P-0221/M-4 · 环段占用快照门（Segment Occupancy Snapshot Gate, SOSG）

- 机制卡: mechanisms/P-0221/M-4.md（PR #100 head `07c78cd`）
- 题卡: problems/P-0221.yaml（main@1909fb0）
- 作者: Jim Keller
- 判决: REJECT
- 可行性: FAIL（每个对向 flit 捎带 1b `over_piggy` = 每链路加 1 根线；改走现有 FC 通路后即为库内 in-ring FC）
- 新颖性: FUNCTIONAL_EQUIVALENT（ECN / IEEE 802.17 RPR 保守公平模式；环库 in-ring 源端 FC + dynamic leaf-tag 的分级滞回）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc live `main@63163cad`（= 63163ca，无漂移）

## 卡摘要
段主 CS 用 W=16 位移位窗统计本出边**过路**占用（`dst≠next`），`occ > 12/16` 置 `over`、`occ ≤ 8/16` 清（滞回）。`over` 位以 1b 捎带在每个对向 flit 上（ESL `NetworkFlit` 元数据），对向空闲时每 W 拍发心跳。上游 NIC 若待注入路径上有 `over` 的过路段（hop≥2），fail-wait。卡承认是软上界：稳态 `ρ ≤ ρ_max`，瞬态超调 ≤ `T_prop + T_drain ≤ 2·C_ring`。

## 轴一 可行性
1. **「1b ESL 元数据不是新线」不成立。** i-tag / e-tag 字段（`sender_tagged`、`tagger_sender_ID` 等）之所以「免费」，是因为它们在 DV200 硬件 flit 头里本来就有线。给**每个**对向 flit 新增一个随流走的 1b 字段，物理上是每条链路、每方向、每子环 +1 根线。违反题面硬约束「不加线」。只靠心跳（不捎带）则心跳占数据槽，且只在「对向空闲」时发——恰恰在双向满载、最需要它时发不出来。
2. **可行的修法就是库内已有的东西。** 环库有独立的 FC 反向通路（`m_highWayFcBuf`，`TCsHighWay.cpp:152-155`、`:1423-1527`；`NetworkFlowCtrl`，`include/chi_ring_common.h:618`），专门把「某 CS 的拥塞等级」逆流传 `spreadCnt` 跳给上游，上游令牌桶限速（`TCsHighWay.cpp:626`、`:907`）。把 `over` 改走这条通路 = 库内 in-ring FC，只是触发量从「本 NI 注入失败均值」（`genSendFlowCtrl`，`TNetworkInterfaceBase.cpp:842`）换成「本出边过路占用率」，门控从「整 NI 降速」换成「路径含该段才停」。
3. 超调界的拍数要重算：卡 `T_prop ≤ C_ring`、`T_drain ≤ C_ring` 用 CS 数；实际一圈 Σlat：top 42 拍，bottom V 132–152 拍。W=16 的窗远短于传播延迟，`over` 置位后要 ≥42（top）/ ≥150（bottom V）拍上游才停，再 ≥ 一圈才排空：控制环延迟 ≫ 测量窗，开关式 1b 门几乎必然振荡（卡 §4 已列「窗太短抖」，但没意识到是传播延迟 ≫ W 的结构问题）。
4. 一刀切 1b：所有路径含 s 的上游同时停、同时开，配额不分人；饥饿节点自身的「下一跳弹出」被排除在门外是对的，但上游中「本身也饿」的节点同样被停，可能把尾换到别人身上。
5. Sink / 死锁：fail-wait 在端点，无丢包；`overshoot_fail` 只是探针，不是执行。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | 每向每 CS 槽 / 环数 | 1；Dat 2 / Snp 1 | `TCsHighWay.h:135`；`gen_config.py:308` | ✅ |
| 2 | `C_ring` / 超调界 | `≤ 2·C_ring`（CS 数） | 一圈 Σlat：top 42，bottom H ≈72–76，V 132/148/152 拍 ⇒ 超调界 top ≥84、bottom V ≥300 拍 | ❌ 拍数低估 |
| 3 | `over` 捎带 | 1b ESL 元数据，「不是新线」 | 新增随 flit 字段 = 每链路每方向每子环 +1 线 | ❌ 违反「不加线」 |
| 4 | `over` 向量 | ≤64 b | 每 NIC 锁存需按子环 × 方向：≤64 × 6 × 2 b ≈ 768 b/CS | ⚠️ 少乘 |
| 5 | 段主窗 | W=16 b 移位 + 5 b popcount | 新寄存器，12 个（子环×向）/CS，约 250 b/CS；`include/`/`src/` 新分支 | ✅（量级） |
| 6 | 心跳 | 对向空闲时每 W 拍 1 条同通道 flit | 占数据槽；需保留 opcode（DAT 0x8–0xA/0xD–0xF，SNP 0x0E–0x0F/0x18–0x1F，E.a） | ⚠️ |
| 7 | Snp 无 Data | Table 13-8，走元数据 | 宽度上不用 Data ✅；但「元数据」即第 3 项新线 | ❌（同第 3 项） |
| 8 | DAT Data 512 b | 心跳不需 Data | ✅ | ✅ |
| 9 | 过路判定 `dst≠next` | 段主本地可得 | flit 路由信息在 CS 可见 ✅ | ✅ |
| 10 | highway 队列 | 0 | ✅ | ✅ |
| 11 | 绕圈 / U-turn 计入 transit | 测量自然计入 | ✅ 测量法优点成立（M-3 的守恒破口在这里不存在） | ✅ |

## 接口落点核查（live `main@63163cad`）
| 卡声称 | 实际 | 结论 |
|---|---|---|
| 段主窗在 `TCsHighWay.cpp:1041-1117` 旁；弹出臂 `:289-351` 标 transit=0 | `sendFlitToWay` `:1041-1118`；`tryWayToLocal` 起 `:289` | ✅；新分支 |
| `NetworkFlit` 加 1b `over_piggy`（`include/` 新分支） | `include/chi_ring_common.h` 哈希锁定 | 新分支；且即第 3 项加线 |
| NIC 门在 `tests/soc_sim/platform/CongestionCtrl.h` / `Endpoint.h` | `CongestionCtrl` 是每 die NI 组窗口速率律（`CongestionCtrl.h:280-330`），不改 NI 令牌（`:113-116`），不做逐拍逐路径门 | ⚠️ 门必须进 `TCsHighWay`（新分支） |
| RTL | 仓内无 RTL | ✅ |
- 零代码对照：`gen_config.py --fc-profile experiment_srcfc`（库内 in-ring FC 开到 top Dat）；dynamic leaf-tag 已在 top Dat 默认打开（`gen_config.py:355-362`，窗 100、阈 80/90/95、标 1/2/3 —— 与 SOSG 的「窗 + 分级滞回」同构）。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| **ECN / 拥塞位反压** | **FUNCTIONAL_EQUIVALENT** | 在拥塞点测占用、置 1b、逆流通知、源端停发——教科书 ECN/BECN 形态 |
| IEEE 802.17 RPR 保守模式 | FUNCTIONAL_EQUIVALENT | 站点测本链路利用率，超阈值向上游通告，上游对穿该链路流量限速 |
| 环库 in-ring 源端 FC | FUNCTIONAL_EQUIVALENT | 同一回路；差别仅为触发量（占用率 vs 注入失败）与门控粒度（路径 vs 整 NI） |
| 环库 dynamic leaf-tag | 同类 | 滑窗 + 分级滞回的本地拥塞测量（`TCsHighWay.cpp:745-800`） |
| P-0198 M-19 | 同族 | 饥饿通知上游让路 |
| P-0221 M-1/M-2/M-3/M-5 | 同族 | 卡已切开记账方式，但同属段级反压 |
- 显式标注（captain 规则）：不是 token bucket / credit / window；是 **ECN 类反压 → FUNCTIONAL_EQUIVALENT**。

## 指标核对
- 题面主指标 makespan；SOSG 只在 `over` 置位期间释放下游空槽，传播延迟 ≫ 窗时开关振荡，集合一步可能被一次超调钉死（卡 §4 自认）。「测量好看但尾不动」风险高。

## 判决理由
REJECT。1b 捎带在物理上是新线，违反「不加线」；去掉捎带、改走库内现有 FC 通路后，机制就是环库 in-ring 源端 FC（或 RPR 保守公平 / ECN）换了一个触发量，FUNCTIONAL_EQUIVALENT。超调界按 CS 数算，实际拍数大 2–4×。

## 若作者重提须先回答
1. `over` 走哪条已有物理通路（FC 通路的硬件位宽？），不得新增 flit 字段。
2. 与 `--fc-profile experiment_srcfc` + dynamic leaf-tag 同信封对打的 makespan 增量。
3. 以 Σlat 拍数重算控制环延迟，给出不振荡的 W / 滞回条件。
