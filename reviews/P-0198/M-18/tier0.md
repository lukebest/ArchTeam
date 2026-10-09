# Tier 0 · P-0198/M-18 · Dat 环选择组播（目的位图）

- 机制卡: mechanisms/P-0198/M-18.md（PR #87 head `65f1268`，该提交中文件名为 `M-13.md`，按标题映射）
- 作者: 保守架构师
- 判决: KNOWN_CONFIRM
- 可行性: PASS
- 新颖性: EXACT_MATCH
- 质量: INCREMENTAL
- 进入 Tier 1: NO（并入平台基线：打开库内 Dat 多播，与 M-14 同一建议）
- 平台核查: bufferless-ring-noc `main@63163ca`（私有仓，认证访问）

## 卡摘要
Dat 包头带 14b 目的 die 位图 `DMASK`；源按环成员拆成「本环一个组播包 + 至多一个跨环种子」；每个目标 NI 复制进 RX、清本位后继续前送；最后一个目标只弹出不前送，本拍槽变空；RBRG 不复制。只在 Dat 环，Snp 不承载数据。

## 轴一 可行性
- 因果成立：N 路单播 → 每环一次巡游，环上占用条数与集合尾都下降，属完成侧收益。
- Sink / 死锁 / 活锁：复制进 endpoint RX，无织物队列；last 处释放槽。卡没有规定目标 RX 忙时的行为（不清位继续绕？），这一点库内已由 eject 失败 + e-tag 处理。
- 位图粒度：卡以 die 为单位（14b），但 Dat 环成员是环上的 CS/端口，一个 die 有多条环、多个 CS。库内位图是按 CS 的 `m_tgtCs` 加按核心的 `m_broadcastTgtList`，粒度更细。die 级 `RINGMEM` 不能直接对应物理环成员。
- 信封注意：tests/soc_sim 的 broadcast 是拉取式（root 写 HA，各 rank 再读，`TrafficGen.h:195-198`），扇出发生在 HA 返回的读数据上，组播需由 HA 合并同址读响应发出，而不是源 NI 发一条带掩码的写。

## 接口落点核查（bufferless-ring-noc main@63163ca）
| 卡声称的钩子 | 实际位置 | 结论 |
| --- | --- | --- |
| Dat flit 头加 14b `DMASK` | 已有：`NetworkFlit::m_tgtCs`/`m_tgtAllCs`（CS 位图）、`m_isMultiCast`、`m_multiCastGrpNum`，`ChiRingChiFlitDAT::ctrl.m_broadcastTgtList`（`include/chi_ring_common.h:301-302`） | 无需新增 |
| Dat NI 弹出路径加 copy-forward 与 last 空槽 | 已有：`src/TCsHighWay.cpp:352-417`（复制 newFlit 给 NI、清本 CS 位、`m_tgtCs==0` 时同拍 `valid=false`） | 无需新增 |
| 跨环种子、RBRG 不复制 | 库内做法是 RBRG 按环拆目标集（`clearThisRingTgtCs`，`:369-373`；NI 侧 `getThisRingTgtForMultiCast`，`src/TNetworkInterface.cpp:443-445`） | 已有等价物（拆分方式不同） |
| 入口 | `src/TBridge.cpp:527-533`：`ctrl.m_isCoalesceSucc` 置位即转多播 | 平台只需在 HA/Endpoint 设置该标志与目标表 |
| 集合流量发生器改发 1 个带掩码包 | `tests/soc_sim/platform/TrafficGen.h` / `Endpoint.h` | 平台层 |
| `--cc-scheme dat-mcast` | `run_soc.py:329` | 可加开关 |
- RTL：不触 RTL（仓内无 RTL 源）。按库内现有路径评估只需改 `tests/soc_sim/platform/`；卡写的「Dat 头加 DMASK、NI 弹出加 copy-forward」不需要，库里已经有。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| 库内 ChiRingFabric Dat 多播 | EXACT_MATCH | 位图、复制前送、末目标释放、仅 Dat、RBRG 按环拆分，逐项对应 |
| M-14 PSCK（Jim round 2，已 KNOWN_CONFIRM / EXACT_MATCH） | EXACT_MATCH | 两位架构师提交了同一机制；M-18 多了环成员拆分，M-14 多了 `LAP_MAX` 回退，均不构成新机制 |
| 教科书环 multicast / destination stripping | FUNCTIONAL_EQUIVALENT | — |
| M-2 CSR | DIFFERENT_APPROACH | 扇入 vs 扇出 |

## 指标核对
对推理 broadcast / allgather 扇出半边与同步 KV 尾有真实收益，方向正确；纯 KV 步中性。收益属于平台基线修正，不是新机制。

## 判决理由
可行且有效，但与被评估库已有的 Dat 多播逐项相同，也与同批 M-14 相同。KNOWN_CONFIRM / EXACT_MATCH，不进 T1。与 M-14 合并为一条平台基线建议：在 tests/soc_sim 新分支由 HA/Endpoint 设置 `m_isCoalesceSucc`/`m_broadcastTgtList`，为 broadcast 与 allgather 扇出半边打开库内多播，单列「no-CC + 多播」基线行。
