# Tier 0 · P-0198/M-14 · PSCK Pass-by Subscriber Copy + Last-Sub Kill

- 机制卡: mechanisms/P-0198/M-14.md（PR #84 head `e6a5e2b`）
- 判决: KNOWN_CONFIRM
- 可行性: PASS
- 新颖性: EXACT_MATCH
- 质量: INCREMENTAL
- 进入 Tier 1: NO（转为基线：在 tests/soc_sim 打开库内已有 Dat 多播）
- 平台核查: bufferless-ring-noc `main@63163ca`

## 卡摘要
fan-out 类（推理 broadcast / 前缀 KV 分享 / TP broadcast / decode AllGather 扇出半边）源端只注入 1 条 Dat，头带订户 bitmap；路过订户时拷贝进 NIC、清本位、不移出 highway；最后一个订户同拍把槽改 empty；busy-dest 保持 bit 再绕，`LAP_MAX` 后回退 unicast；RBRG 不持拍、不做归约。

## 轴一 可行性
- 因果性: 成立。N 条 unicast → 1 条多播，砍掉 `(N−1)` 次注入串行与 N 条公民的环占用，last-sub 到达时间可以实打实缩短，属完成侧收益。
- Sink / 死锁 / 活锁: 拷贝进 NIC 走正常 eject，busy 时 bit 保留继续走，不丢不缓存；`LAP_MAX` + unicast 回退给出活锁上界。无环上等待链。
- 约束边界: 无队列、无第三槽、RBRG 不持拍，合规。all-to-all 卡已自行排除。
- 信封注意: tests/soc_sim 的 broadcast 是拉取式：root 先写到自己的 HA，再由各 rank 各发一条 Read（`tests/soc_sim/platform/TrafficGen.h:195-198`）。扇出发生在 HA 返回的 N 条读数据上，所以「源只注入一条」要求 HA 侧把同地址读响应合并，而不是 root NIC 发一条多播写。

## RTL / 仿真器改动核查
- 卡称「结构变更几乎必然：dest eject 多半是弹出=拿走」，与代码不符。被评估的 ChiRingFabric 库已实现 PSCK 的全部核心语义：
  - 头带目标位图 `m_tgtCs`，多播标志 `m_isMultiCast`（`include/chi_ring_common.h:301-302`），仅 Dat 支持（`assert ... "just dat support multicast"`）。
  - 路过目标：复制出 `newFlit` 推给 NI，原 flit 清本 CS 位继续前进（`src/TCsHighWay.cpp:352-417`）。
  - 末目标：`m_tgtCs==0` 时同拍 `valid=false` 并释放（`:397-410`），即「末订户斩槽」。
  - RBRG：按环拆分目标集 `clearThisRingTgtCs`（`:369-373`），NI 侧 `getThisRingTgtForMultiCast`（`src/TNetworkInterface.cpp:443-445`），桥不做归约。
  - 入口：`TBridge` 由 `ctrl.m_isCoalesceSucc` 与 `ctrl.m_broadcastTgtList` 激活（`src/TBridge.cpp:527-533`），即读响应合并成功后转多播。
- 因此评估只需要在 `tests/soc_sim/platform/`（HA/Endpoint 侧设置 `m_isCoalesceSucc` 与 `m_broadcastTgtList`）驱动现有路径，不需要动库，更不触 RTL（仓内无 RTL 源）。唯一库内没有的是 `LAP_MAX`→unicast 回退；库对 busy 目标的处理沿用 eject 失败 + e-tag。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| 库内 ChiRingFabric Dat 多播（coalesce → multicast，copy-and-forward，末目标 invalid，RBRG 拆分） | EXACT_MATCH | 结构与语义逐项对应；PSCK 增量只有 `LAP_MAX` 回退与 classifier ROM |
| 教科书环 multicast / destination stripping | FUNCTIONAL_EQUIVALENT | 卡把「绕满圈回源删除」当作教科书版本并以末订户删除区分；末目标删除（destination stripping）本身也是环网络的已知选项 |
| M-2 CSR | DIFFERENT_APPROACH | CSR 是扇入 + RBRG CAM/GRANT；PSCK 是扇出、无桥状态 |
| M-1/M-4/M-5 | 无关 | — |
| M-6/M-7 | 非等价 | 无时隙、不改方向 |

## 指标核对
对推理 broadcast / TP fan-out / decode AllGather 扇出半边，last-sub 完成时间会缩短，方向正确；对纯 P2P KV 中性。问题 SYMPTOM 里 broadcast 本来是唯一未进崩塌区的集合，收益集中在推理扇出尾，而不是解决 gather/reduce/alltoall 的崩塌。

## 判决理由
机制可行且对推理扇出有真实完成侧收益，但它就是被评估库已有的 Dat 多播路径，PSCK 没有新增结构。KNOWN_CONFIRM / EXACT_MATCH，不进 T1。

建议：把「tests/soc_sim 在 broadcast 与 allgather 扇出半边打开库内多播（HA 设置 `m_isCoalesceSucc`/`m_broadcastTgtList`）」作为平台基线修正，单列一行进所有后续卡的 cycle 基线（no-CC + 多播）。平台改动只在 `tests/soc_sim/platform/`，开新分支即可。之后任何以「N 条 unicast」为对照的扇出类收益都应先扣掉这一行。
