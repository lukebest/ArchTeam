# Tier 0 SUMMARY · P-0198 round 2（M-11..M-15）

门卫：设计验证。机制卡来源：PR #84 head `e6a5e2b`（`mechanisms/P-0198/M-11.md`..`M-15.md`）；题面 `problems/P-0198.yaml`。平台核查：bufferless-ring-noc `main@63163ca`。未读 T1 persona 评审正文。

| id | name | 判决 | 可行性 | 新颖性 | 质量 | one-line reason |
| --- | --- | --- | --- | --- | --- | --- |
| P-0198/M-11 | MELB Missed-Eject Local Bounce | REJECT | PASS | FUNCTIONAL_EQUIVALENT | INCREMENTAL | 被评估库已有 eject 失败 U-turn（`UturnConnect`/`tryUTurn`，≤3 次）+ e-tag；MELB 只是把 U-turn 点放到 dest 邻居 |
| P-0198/M-12 | HSSL Hop-Slack Staggered Launch | REJECT | FAIL | FUNCTIONAL_EQUIVALENT | FLAWED | 过路优先下远源在上游，近源挡不到远源；根因方向反了，且只是注入侧静态偏移 |
| P-0198/M-13 | WSOR Wave-Sunset Occupancy Reclaim | REJECT | FAIL | DIFFERENT_APPROACH | FLAWED | 无损 CHI 下「已完成波仍在环上」为空集；误回收即丢合法数据且源无副本 |
| P-0198/M-14 | PSCK Pass-by Subscriber Copy + Last-Sub Kill | KNOWN_CONFIRM | PASS | EXACT_MATCH | INCREMENTAL | 库内已有 Dat 多播（coalesce→multicast、copy-forward、末目标 invalid、RBRG 拆分）；应作为平台基线打开 |
| P-0198/M-15 | TOSE Tail-Only Snp Express | REJECT | FAIL | FUNCTIONAL_EQUIVALENT | FLAWED | 唯一尾拍标记不可实现（过多/过晚/需回写在途 flit）；仲裁即 M-5r1 加尾拍过滤 |

T1 集合：无。
REJECT：M-11、M-12、M-13、M-15。KNOWN_CONFIRM：M-14。
同日 line B 修订卡 M-5r1 单独评审：`reviews/P-0198/M-5r1/tier0.md`（另行 PR）。

## RTL / 仿真器改动核查
- bufferless-ring-noc 仓内无 RTL 源（无 .v/.sv）。`include/`+`src/` 是导入的哈希锁定 ChiRingFabric ESL 库（`provenance/esl-2026-09-15.json`），按 RTL 行为建模；`tests/soc_sim/` 是 DV200 平台。本批无卡要求改 RTL。
- 需要动库（= 仿真器结构改动，只能开新分支、默认关闭、进新 manifest）：M-11（eject 失败分支与 U-turn 在 `src/TCsHighWay.cpp`，卡称「只加 tests/soc_sim 模型」不准确）、M-13、M-15。
- 只需 `tests/soc_sim/platform/`：M-12（NI 首拍门）、M-14（HA/Endpoint 设置 `m_isCoalesceSucc`/`m_broadcastTgtList` 驱动库内已有多播；卡称「结构变更几乎必然」与代码不符）。

## 平台基线建议（非 T1 任务）
1. 在 tests/soc_sim 新分支为 broadcast / allgather 扇出半边打开库内 Dat 多播，作为所有扇出类卡的 cycle 基线行（no-CC + 多播）。
2. 在 DV200 配置打开 `UturnConnect` 并报 `eject_failed_times` 分布，零代码回答「dest-miss 税是否主导推理尾」；同时为 M-5 线「dest-eject 主导」的 T3 归因提供直接计数。

## Close calls（请门卫确认）
1. **M-11 / M-14 以「被评估库已有特性」做 dedupe**：本判把库内实现视同已知机制（M-11 FUNCTIONAL_EQUIVALENT，M-14 EXACT_MATCH）。若门卫认为 dedupe 只对文献/教科书与 M-1..M-10，M-11 可改 PASS_T1 / DIFFERENT_APPROACH / INCREMENTAL（T1 必验见其 tier0），M-14 仍应因与库实现逐项相同而 KNOWN_CONFIRM。
2. **M-12 跨环情形**：近源位于 RBRG 汇入点上游时确有「近挡远」，但键应是汇入点位置而非 hop 数；改键后与 M-9/M-2 同族。按主情形判 FAIL。
3. **M-15 物理位宽**：Dat flit 走 Snp 导线的位宽问题对整个 M-5 线成立，round 1 T0 未提；本批在 M-15 与 M-5r1 中列为 T1 必验，不单独作为 M-15 淘汰理由。
