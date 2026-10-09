# Tier 0 汇总 · P-0221（Jim Keller M-1..M-5）

- 题卡: problems/P-0221.yaml（main@1909fb0，引入提交 `5c7c0b7`）
- 机制卡: PR #100 head `07c78cd`（叠在 `cursor/add-p-0221-bd75` 上），mechanisms/P-0221/M-1..M-5.md
- 审查人: 设计验证（Tier 0）
- 日期: 2026-10-09

## 1. 平台 live 核查
- 仓库：`lukebest/bufferless-ring-noc`（私有，gh 认证 clone），2026-10-09 11:31 CST `git fetch`。
- **live tip：`main@63163cad900979ab00edff1e0268f87b37b18e3b`**（提交时间 2026-09-29 17:02 CST）。与卡与 P-0198 T0 所用的 63163ca **是同一提交**，`63163ca..origin/main` 为空，卡所引行号无漂移。
- 非 main 分支提示：`cursor/p0198-llm-noc-baseline-aa90@89f9c88`（2026-10-09 11:27 CST）改了 `tests/soc_sim/platform/Endpoint.h`（`kBeatBytes` 从 :27 移到 :29）、`TrafficGen.h`、`gen_config.py`、`run_soc.py`，并新增 `workloads/p0198-llm-noc/PHYSICAL_ASSUMPTIONS.md`（物理参数审计表）。未改 `src/`/`include/`。若 T1 在该分支上跑，平台行号需按它重新对齐。
- 卡所引行号逐条：

| 卡引用 | live 实际 | 结论 |
|---|---|---|
| `src/TCsHighWay.cpp:1041-1117` 注入 | `sendFlitToWay` `:1041-1118` | ✅ |
| `:894-950` i-tag | `tryItagProcess` `:894-950` | ✅ |
| `:1094-1103` i-tag 打标 | `:1095-1110` | ✅（小偏移） |
| `:289-351` 弹出臂 | `tryWayToLocal` 起 `:289`（全函数至 `:597`）；转发臂不在此区间 | ⚠️ |
| `include/TCsHighWay.h:136` 槽 | `m_sendFlit` 在 `:135` | ⚠️ 差 1 行 |
| `src/TMultiRing.cpp:223-231` 子环数 | 是 `sub_channel_cnt` 解析器；值在 `gen_config.py:308`（`req 1 rsp 2 snp 1 dat 2`） | ✅ |
| `tests/soc_sim/platform/Endpoint.h:27` `kBeatBytes=64` | ✅（main） | ✅ |
| `tests/esl_wrapper/compat/chi_common.h:92-118` `CHIFlitFields` | ✅ | ✅ |
| `CongestionCtrl.h` / `--cc-scheme` | 存在：`soc_main.cpp:80`、`soc.cpp:590-640` `bind_control()`；但它是**每 die NI 组、按窗口**的速率律（srcfc/drr/aimd/hat/ecn/tagwin，`CongestionCtrl.h:280-330`），注释明确不改 NI 令牌（`:113-116`） | ⚠️ 五张卡的逐拍逐路径门都不能落在这里，必须进 `TCsHighWay`（哈希锁定库 → 新分支） |
| `gen_config.py:529` 64 B vs 128 B | `:529` 字符串 "beat 64 (top) vs 128 (bottom); using 64" | ✅ |

## 2. 判决表
| 卡 | 机制 | 判决 | 新颖性 | 一句话理由 |
|---|---|---|---|---|
| M-1 | STB 环段令牌桶准入 | REJECT | FUNCTIONAL_EQUIVALENT（token bucket；库内 in-ring FC 令牌桶） | 上界靠「注入当拍扣权威令牌」，实际只扣陈旧本地锁存，N 个上游并行超订，默认参数下上界退化为 1；Snp 1b 捎带是新线 |
| M-2 | DVC 下游空槽索取 | REJECT | FUNCTIONAL_EQUIVALENT（DQDB 反向请求；库内 in-ring FC + i-tag；P-0198 M-19 多跳化） | 物理可落、方向对，但执行原语即 DQDB / 库内 FC + i-tag，增量仅「路径选择 + 批量 Q」；本轮最接近 T1 的一张 |
| M-3 | IPCW 注入–越过守恒窗 | REJECT | FUNCTIONAL_EQUIVALENT（credit / window；ATM CAC 路径预约；CSR 族） | `I_max` 按 CS 数定标而上界按拍数成立，段利用率被钉在 18–36%；Snp 每包先等一圈预约，按设计 ≈5× 越过 KILL 线；对向按跳税 ≈50% |
| M-4 | SOSG 环段占用快照门 | REJECT | FUNCTIONAL_EQUIVALENT（ECN / RPR 保守模式；库内 in-ring FC + dyn leaf-tag） | 每个对向 flit 捎 1b = 加线；改走现有 FC 通路即库内 in-ring FC 换触发量 |
| M-5 | PMQR 路径配额再平衡 | REJECT | FUNCTIONAL_EQUIVALENT（GSF 帧配额 / max-min 显式速率） | 每段每 16 拍一条 REBAL：对向控制负载 top ≈131%、bottom V ≈231%；合成单条 3.5–11 kb ≫ 512 b；配额龄 ≫ 窗长，Σq=B_s 不被执行 |

PASS_T1：0 / 5。KILL：0（M-3 的 Snp 分析已越过 KILL 线，但以 REJECT 记，见 M-3 §轴一 2）。

## 3. 物理假设核查（captain 新硬规则）汇总
五份 tier0.md 均有「物理假设逐项核查」专节，逐项给出 卡声称 / 实际 / 判定。跨卡共性问题：

1. **环周拍数 ≠ CS 数（五张卡全中）。** 卡一律 `C_ring = CS_NUM`（top 21）。CS 数正确（`gen_config.py:19`），但一圈拍数 / 每方向在途槽容量 = Σ link latency：top 21×2 = **42 拍**（`gen_config.py:345`；`:255` 注释 "ring sum is sum(latencies)"），bottom H ≈72–76，bottom V 33/37/38 CS × 4 = **132/148/152 拍**（`gen_config.py:430-449`）。所有传播延迟、心跳 / 预约 / REBAL 税、超调界都被低估 2–4×；M-3 因此把段利用率钉在 18–36%。
2. **「ESL 元数据 1b 不是新线」不成立（M-1 Snp `hot`、M-4 `over_piggy`、M-5 Snp 备选）。** i-tag / e-tag 字段免费是因为硬件 flit 头本来就有；新增随 flit 走的字段 = 每链路每方向每子环 +1 根线，违反「不加线」。
3. **控制 flit 均需保留 opcode + 每 CS 截获解码。** CHI E.a：SNP Reserved 0x0E–0x0F、0x18–0x1F（Table 13-17）；DAT Reserved 0x8–0xA、0xD–0xF（Table 13-18）。可用，但需锁定 CHI 版本；截获逻辑在 `TCsHighWay`（新分支）。
4. **环数 / 宽度引用本身正确**：Dat 2 子环、Snp 1 环（`gen_config.py:308`）；DAT Data 512 b / BE 64 b @DW=512（Table 13-9）；SNP 无 Data（Table 13-8）；`kBeatBytes=64`；`CS_NUM≤64`（`m_tgtCs` uint64）。五张卡都没有借 Snp 运 Dat。小错：REQ Addr 标签（应为 RAW 44–52，SNP Addr SAW 41–49）；CHI Size 表号（E.a 为 Table 13-20，13-18 是 DAT opcode）。
5. **对 i-tag 的描述错误（M-1、M-2）。** 卡称 i-tag「只在空槽到达后赢仲裁、不阻止上游吃光」。实际 i-tag 在过路占用槽上打标（`TCsHighWay.cpp:1095-1110`），占用者弹出后该槽保持保留（`isSlotReservedFlit` `:1151-1158`），上游一律不可用，回到打标者使用（`:894-950`）。

专项问题答复：
- **M-2 反向 CLAIM 是否占用现有通道位宽？** 不加宽，也不额外占用现有字段的位宽；它占用的是**同通道对向子环的整槽带宽**。Dat：一条完整 DATFLIT 只运 ~21–25 b 信息 + DAT 保留 opcode。Snp：按 SrcID←claimant、TxnID←seg+Q、FwdNID←wave 重排后放得进 SNPFLIT（卡的算式漏了 wave 且把 Opcode 当载荷，但结论成立）+ SNP 保留 opcode。代价是对向 Snp/Dat 槽与每 CS 解码；库内独立 FC 通路（`m_highWayFcBuf`）是不占数据槽的替代，但其硬件位宽待核。
- **M-3 每段预约状态的存储与信令从哪来？** 存储：段主 CS 每（子环, 方向）一个 `inflight` 计数器（每 CS 12 个；正确定标需 7 b，≈84 b/CS），源 NIC 每（通道, 方向）1 深预约寄存器（≈40–50 b），外加路径 ROM 与 RELEASE 待办——全部是 `include/`/`src/` 中的新寄存器（新分支）。信令：RESERVE/ACK/NACK/RELEASE 均为同通道对向子环上的整槽 flit，RESERVE 恒走一整圈；越过减账是段主本地事件、无需信令；NACK 回滚需要再一圈 RELEASE（卡写的「回程减回」不存在）。按跳加权的对向税 ≈50%（Dat）/ ≈400%（Snp）。

## 4. RTL / 落点
- 仓内无 RTL，五张卡均不触 RTL。
- 五张卡的执行点（逐拍、逐路径的注入门、段主状态、控制 flit 截获）全部在哈希锁定的 `src/TCsHighWay.cpp` / `include/`，属**仿真器结构改动，只能开 bufferless-ring-noc 新分支**。卡把门挂到 `tests/soc_sim/platform/CongestionCtrl.h` 的写法不对：那一层只做每 die NI 组的窗口速率律，不能做逐拍逐槽判定。
- 卡均因 404 未读 live 仓，漏掉了三项**已在库内、与 P-0221 直接同题**的先例（按「环库已有功能算先例」规则全部计入）：
  1. **in-ring 源端流控**：下游 NI 注入失败均值 → FC 等级（`TNetworkInterfaceBase.cpp:842`）→ `NetworkFlowCtrl` 沿反方向传 `spreadCnt` 跳（独立通路 `m_highWayFcBuf`，`TCsHighWay.cpp:152-155`、`:1423-1527`）→ 上游 NI 令牌桶限速（`TNetworkInterfaceBase.cpp:1141`，注入门 `TCsHighWay.cpp:626`、`:907`）。**零代码开关**：`gen_config.py --flow-control on`（top Req）或 `--fc-profile experiment_srcfc`（另开 top Dat，`:364-365`、`:486-494`）。P-0221 基线「关闭额外流控」= 这条关着。
  2. **i-tag 保留槽**（见 §3 第 5 点），阈值 / 策略可扫（`gen_config.py:134`、`:471-474`）。
  3. **dynamic leaf-tag**：本地注入失败率滑窗分级（窗 100、阈 80/90/95）标记 1/2/3 个过路槽为保留（`TCsHighWay.cpp:745-800`），top Dat 默认开（`gen_config.py:355-362`）。
- 本轮补记：P-0198 M-19（邻节点饥饿气泡中继）的 T0 只引了 i-tag；in-ring 源端 FC 同样是它的先例。M-19 判决不变（REJECT, FUNCTIONAL_EQUIVALENT）。

## 5. 教科书等价显式标注（captain 规则）
| 卡 | 教科书对象 | 标注 |
|---|---|---|
| M-1 | token bucket / leaky bucket；RPR fair rate | FUNCTIONAL_EQUIVALENT |
| M-2 | DQDB（IEEE 802.6）反向请求计数；MetaRing SAT | FUNCTIONAL_EQUIVALENT（credit / 请求计数类） |
| M-3 | 逐链路 credit / window；ATM CAC / RSVP 路径预约；Orwell 试约 | FUNCTIONAL_EQUIVALENT |
| M-4 | ECN / BECN；RPR 保守公平模式 | FUNCTIONAL_EQUIVALENT（不是 token/credit/window，是 ECN 类反压） |
| M-5 | GSF 帧配额；max-min 显式速率（ATM ABR） | FUNCTIONAL_EQUIVALENT |

## 6. 卡间交叉去重
- M-1..M-5 是同一问题的五种记账方式：时间补充桶（M-1）、饥饿请求（M-2）、在途守恒（M-3）、测量反压（M-4）、配额分割（M-5）。都没有越出「段级反压 / 准入」这一教科书族，也都与库内 in-ring FC 同回路。
- 与 P-0198：未重提 CBC / CSR / AODI / CRRF / HSSL / WSOR / PSCK / TOSE（卡自检属实）；M-3 的预约往返与 CSR 同族，税的量级相同。M-2 是 P-0198 M-19 的多跳计数化。

## 7. 给用户 / 总监的决策点
1. **是否给 M-2（DVC）开 T1 通道。** 五张全 REJECT 是按现行规则（库内先例 + 教科书等价）的结论。DVC 是唯一物理可落、方向正确、且相对库内 FC 有可度量差异（只抑制穿过饥饿段的注入、按 Q 计数）的卡。若希望本题有一张进 T1，建议有条件改判 PASS_T1（INCREMENTAL），T1 必验：与 `--fc-profile experiment_srcfc`、i-tag 阈值 {8,16,32}、dynamic leaf-tag 同信封对打，推理 makespan / 最差节点严格更好；CLAIM 走现有 FC 通路的硬件位宽，或走数据槽时 Snp 15:1 ≤1.4×；全部时序按 Σlat 拍数重算。
2. **P-0221 题面本身的基线。** 题面 SYMPTOM 基于「关闭额外流控」。库内 in-ring FC、i-tag、dynamic leaf-tag 三者都直接针对「上游填满、下游饿死」。建议在下一轮出卡前，先用零代码开关跑一次：`--fc-profile experiment_srcfc` + i-tag 阈值扫描 + leaf-tag 开关，看沿环注入等待梯度与最差节点是否仍成立。若库内机制已消除梯度，题面应按其「待证伪」条款收窄；若仍成立，新卡的增量必须以这三者为对照基线。
3. **题面淘汰约束补一条**：控制面 / 捎带「ESL 元数据 1b」视为加线，除非指明复用的现有物理字段或现有 FC 通路；环周一律按 Σlat 拍数计。
4. **平台分支**：`cursor/p0198-llm-noc-baseline-aa90` 今天 11:27 CST 有新提交（平台层，含 `PHYSICAL_ASSUMPTIONS.md`）。T1 若在其上跑，平台行号以该分支为准。
