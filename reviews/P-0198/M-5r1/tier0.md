# Tier 0 · P-0198/M-5r1 · CRRF-SB Channel–Ring Rebind + Snp Native Steal-Back

- 机制卡: mechanisms/P-0198/M-5r1.md（PR #85 head）
- 修订: M-5 CRRF line B（修 15:1 Snp 小包延迟）
- 对照: mechanisms/P-0198/M-5.md（PR #53）；reviews/P-0198/M-5/tier0.md（PR #55，T1-return-1 重跑 PASS_T1）
- 判决: PASS_T1
- 可行性: PASS（附 T1 必验条件）
- 新颖性: DIFFERENT_APPROACH
- 质量: INCREMENTAL
- 进入 Tier 1: YES
- 平台核查: bufferless-ring-noc `main@63163ca`

## 卡摘要
M-5 中绑定表是 Snp 物理环的排他身份：DAT_EPOCH 期间本征 Snp 不得上该环，只能等下一个 SNP_EPOCH，每次翻转付 Epoch Drain。M-5r1 把绑定表降级为「ghost Dat 是否可借空槽」的资格位：`channel-id=Snp` 的 flit 任何时刻都是 Snp 环合法公民，不看 epoch、不走 Drain；ghost Dat 只在本拍 Snp 环槽空、本地无 Snp pending、FSM=STEADY 且世代已 committed 时注入；同拍 Snp 与 ghost 争空槽，Snp 赢；在途 ghost 仍享过路优先。ARM_DRAIN/DRAIN/FLIP/`epoch_committed` 保留，但只约束 ghost 世代切换。

更正派单描述：卡没有删除 Drain 与 FLIP，是把它们的职责收窄到 ghost 世代（卡 §2.3）。被删除的是「Snp 注入必须等 SNP_EPOCH / 经 Drain 准入」这条谓词。

## 要点一：机制改动还是调参
- 是机制改动。M-5 的 Snp 等待是 `O(T_drain + 排他窗)`，原因是身份排他，不随 duty 消失；卡引用的 T3 证据（`snp_path` 无 Dat 混合时仍 17.05×、3:1 混合仍 27.51×）说明调 duty 救不了。M-5r1 改的是所有权谓词（本征 Snp 不受 epoch 门控）与仲裁规则（空槽同拍 Snp 优先），duty 只剩「借多少」的偏置。改 7:1/3:1 不是修订，卡自己也这样写，成立。
- 是否重开 T1 原致命点（编号按 PR #55 tier0）：
  1. Epoch Drain + SYNC skew：未重开。Drain、`epoch_committed`、接受集 `{local, local−1}` 对 ghost 世代原样保留；本征 Snp 本来不携带 `epoch_tag`，不受 skew 影响。新增的风险是 Drain 期间 Snp 环上同时有本征 Snp 与旧世代 ghost，sniff/marker 必须只清 ghost，卡 §2.3 已写明。
  2. Ghost channel-id @ RBRG / `bind_mismatch_redirect`：未重开，反而收紧：RBRG 以 header channel-id 为权威，`channel-id=Snp` 无条件按 Snp 桥接，消除「bind=Dat 时本征 Snp 被误译」的路径；失配只针对 ghost。残留问题：失配 NACK + 原 Dat 环重注入要求源 NI 在 ghost 上环后仍保留副本，卡未说明副本在哪里；稳态目标 0，但 T1 须给出 NACK 时的数据来源，否则就是丢包。
  3. FSM 只看本地压力：未变，仍是本地 Dat EMA + Snp pending，hint 仅 advisory。
- 机制退化风险：既然本征 Snp 按 header 译码、不看 bind，ghost Dat 也可以只按 header（`channel-id=Dat`）译码。若 T1 发现 `bind`+epoch 对正确性不再必要（header-only 译码的 drain-off 臂与 on-arm 等价），M-5r1 就退化为「Dat 机会式借用 Snp 环空槽、Snp 优先」，epoch/drain 只剩开销，新颖性也会降到多物理子网负载均衡一级。这是 T1 必须跑的臂。

## 要点二：空槽抢占的饥饿 / 死锁 / 活锁
- Snp 饥饿（优先级反转）：存在，卡没有闭合。steal-back 只在**本地**空槽上让 Snp 赢；在途 ghost 享过路优先。上游节点在本地无 Snp pending 时可以持续注入 ghost，这些 ghost 填满经过下游节点的 Snp 环槽，下游有 Snp pending 也拿不到空槽。这是无缓冲环经典的上游饿死下游，只是饿的对象换成了本征 Snp，ghost 是低优先级类，却在途中压住高优先级类。「Snp 永远赢」只对本地空槽成立，不是全局性质。
  - 有界性：卡里没有 ghost 密度上界（duty 偏置只控制借用倾向，不按段计数）。库内有 i-tag（注入饥饿后保留槽，`src/TCsHighWay.cpp:894` `tryItagProcess`）；若 Snp 环 i-tag 生效、且 ghost 必须服从 i-tag 保留槽，则下游 Snp 等待有界。卡未声明这一点。T1 必验：ghost 是否服从 Snp 环 i-tag/保留槽；Snp 注入等待最坏值与 p99 分布（按节点位置分列）。
- Ghost Dat 的 sink：ghost 在 dest 从 Snp 物理环 eject 到 Dat NI 口，与 Dat 环到达者争同一 eject 口。eject 失败时 ghost 在 **Snp 环**上绕圈，每圈占 Snp 槽，直接加重上一条饥饿；库内 e-tag（`dest_port_tagged`，`src/TCsHighWay.cpp:686-701`）是否跨物理环对 ghost 生效，卡未定义。T1 必验：ghost eject 失败率、ghost 在 Snp 环上的圈数分布、Dat NI 口 e-tag 对 ghost 的覆盖。
- Drain 完成性（活锁）：DRAIN 要求旧世代 ghost 清空；若 ghost 因 dest 忙在 Snp 环上 orbit，Drain 等待无界。M-5 已有同一问题，M-5r1 没有恶化它，但本征 Snp 现在与 orbit ghost 共环，Drain 期的 Snp 尾直接受影响。T1 必验：Drain 时长分布与最坏值。
- 死锁：无环上缓冲依赖链（ghost 不停驻、Snp 不排队），RBRG 1 深 hold 满时只能让 ghost 留环 orbit 或走 NACK；只要 NACK 的数据来源成立（见要点一第 2 条），无循环等待。T0 判断：无死锁结构，但有两处活锁/饥饿需 cycle 证伪（下游 Snp 饥饿、ghost orbit 阻塞 Drain）。

## 要点三：数字与杀条件
- 卡与 `models/P-0198/M-5r1/insight.md` 中 `m5-15:1` 的 7.8×→`m5r1-15:1` 1.0×（snp_path），以及 19.0×→1.0×（mixed），是 UNSIGNED、减箱（N=12、n=3、SEED=20260903）的分析/harness 探针。本评审只把它们视为假设，不作 card-claim，不进周报。
- **显式杀条件（T1/cycle 级）**：H-SNP-LAT-SB：DV200 12+2 全信封 tests/soc_sim 新分支，15:1 臂 `T_snp / T_snp(rebind-off)` ≤ 1.4（且须 < T2 代数阈值 1.5625）。cycle 级 > 1.4 ⇒ 该臂失败；`snp_path` 与推理混合（KV/P2P+Snp）两列都须报，任一列 > 1.4 即该臂 KILL，不得用 Dat 侧 0.55–0.85× 抵消，不得平均。H-SNP-CAP（Snp 饱和对照）允许 > 1.4，但必须单列，且该情形下 Dat 甜区声明作废。
- HARD-1 保持：rebind-off 的推理 Dat makespan 必须严格差于 SB 最佳 on-arm；只涨 `p_inj`/注入次数不计分。

## RTL / 仿真器改动核查
- 卡 §7 写「本环境读不到该仓（GitHub 404）」：本次核查时 https://github.com/lukebest/bufferless-ring-noc 为公开仓，`main@63163ca` 可正常 clone；另有分支 `cursor/p0198-llm-noc-baseline-aa90`（推理负载）。
- 仓内无 RTL 源（无 .v/.sv）。`include/`、`src/` 是导入的哈希锁定 ChiRingFabric ESL 库（`provenance/esl-2026-09-15.json`），`tests/soc_sim/` 是平台。基线没有通道–环绑定层：每个 CHI 通道在 `m_networkList[channel][sub_channel]` 上有自己的环（参见 `src/TCsHighWay.cpp:341` 对 `m_networkList[Dat_CHANNEL]` 的访问），NI 注入（`src/TNetworkInterface*.cpp`）、highway 仲裁（`src/TCsHighWay.cpp` `tryLocalToWay`/`tryWayToLocal`）、RBRG 译码（`src/TBridge.cpp`、`src/TNetworkInterfaceRbrg.cpp`）都在库内。
- 卡 §7 的 5 个钩子（NIC 注入仲裁、绑定资格位、RBRG 按 header 转发、Drain 门控、遥测）全部落在库内，属仿真器结构改动，只能在 bufferless-ring-noc 新分支实现，须默认关闭并进新的 provenance manifest；不改 RTL。卡的说法（「不得改 RTL」「若无绑定层应新增」）成立。
- PR #85 在 ArchTeam 只新增 `mechanisms/P-0198/M-5r1.md` 与 `models/P-0198/M-5r1/*`，未改 M-5.md / reviews/。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| M-5 CRRF | 修订，DIFFERENT_APPROACH | 所有权谓词从排他身份改为宾客资格 + 本征优先；不是调参 |
| M-6 TDMA / slotted ring | 非等价 | 无固定时隙留给 Snp |
| M-10 age/class arbitration | 非等价 | 优先级按本征通道权，不按年龄；但「类优先」本身是 QoS 常规，新意在跨通道借环而非优先级 |
| M-15 TOSE（同期） | M-15 是本卡的子集 | TOSE = 本卡仲裁 + 仅尾拍过滤；建议作 T1 消融臂 |
| 多物理子网负载均衡（Yoon et al. 多物理网络 vs VC） | 近亲 | 若 epoch/bind 被证明多余，本卡退化到此族 |

质量从 M-5 的 ISCA_WORTHY 下调为 INCREMENTAL：修订后机制核心是「低优先级类机会式借用另一通道空槽」，新意依赖 epoch/bind 是否仍有正确性作用。

## T1 必验点
1. H-SNP-LAT-SB 杀条件：15:1 `snp_path` 与推理混合两列 cycle 级 ≤ 1.4（< 1.5625），超出即该臂 KILL。
2. 下游 Snp 饥饿：按节点位置分列 Snp 注入等待最坏值/p99；ghost 是否服从 Snp 环 i-tag/保留槽；若不服从，须加 ghost 段密度上限。
3. Ghost eject 失败：失败率、Snp 环 orbit 圈数、e-tag 对 ghost 的覆盖；Drain 时长最坏值。
4. NACK/重注入的数据来源（源 NI 副本）与 `bind_mismatch_redirect` 稳态 0。
5. `header-only 译码 / drain-off` 臂：若与 on-arm 等价，epoch/bind 应删除并重评新颖性。
6. `tail-only` 臂（M-15 思路）与 `ghost-off`、`sb-off` 消融同表。
7. 物理位宽：Dat flit 走 Snp 导线需要 Snp 环拓宽到 Dat 宽度或拆拍；这是 M-5 线共有的未审问题，T1 须给出位宽与拆拍假设，并把拆拍成本计入 `C_dat_eff`。
8. 推理 makespan/尾为主列（decode KV/P2P + 推理集合），训练只作附注；rebind-off、源端流控、原 M-5（15:1 保留）同表分列，不平均。

## 判决理由
是真实的机制修订：去掉了 Snp 注入的排他身份与 Drain 准入，直接针对 T3 的 15:1 Snp KILL 根因；原三条 T1 致命点没有重开，RBRG 侧更紧。空槽抢占规则无死锁结构，但「Snp 优先」只在本地成立，上游 ghost 可饿下游 Snp，ghost orbit 可拖住 Drain，二者都需要 cycle 证伪，并已写成 T1 必验与杀条件。PASS_T1 / DIFFERENT_APPROACH / INCREMENTAL。
