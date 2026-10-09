# Tier 0 · P-0221/M-2 · 下游空槽索取（Downstream Vacancy Claim, DVC）

- 机制卡: mechanisms/P-0221/M-2.md（PR #100 head `07c78cd`）
- 题卡: problems/P-0221.yaml（main@1909fb0）
- 作者: Jim Keller
- 判决: REJECT
- 可行性: PASS（有条件：CLAIM 放得进现有 flit 字段；需保留 opcode 与每 CS 解码 = 库内改动、新分支）
- 新颖性: FUNCTIONAL_EQUIVALENT（DQDB/IEEE 802.6 反向总线请求计数；环库 in-ring 源端 FC + i-tag；P-0198 M-19 的多跳推广）
- 质量: INCREMENTAL
- 进入 Tier 1: NO（本轮最接近可推进的一张，见「决策点」）
- 平台核查: bufferless-ring-noc live `main@63163cad`（= 63163ca，无漂移）

## 卡摘要
下游节点 k 在本向连续 inject-fail ≥ K_fail=8 时，在**同通道对向**发一条 CLAIM（claimant、seg、Q=4、wave）。CLAIM 逆流经过的上游 CS 若有路径含 `s_k` 的待注入 flit，则置 skip，让空槽前进；k 用掉 Q 个空槽后段主发 CLAIM_REL 清 skip；超时 `T_claim=2·C_ring` 强制释放。每段至多 1 个活 claim。上界只在 claim 期间宣称：`ρ_transit(s_k, W_claim) ≤ 1 − Q/W_claim`。

## 轴一 可行性
1. 因果方向正确：上游先见空槽、下游饿，是无缓冲环的经典空间不公平（与 P-0198 M-12/M-19 判决一致）。由饥饿方逆流通知、上游**只对穿过 `s_k` 的注入**让空槽，执行点和问题对得上。
2. Sink / 死锁 / 活锁：被跳过的是空槽，过路仍优先，待注入 flit 留在端点 outstanding；每段 1 活 claim + 超时，不形成环上 claim 列车；无死锁。活锁风险在多下游争同一段时（卡已列，`claim_wait_p99`），有超时兜底，属性能问题非正确性问题。
3. 上界性质：**条件上界**（仅 claim 活跃时），且只约束 `s_k` 一段；无 claim 时不宣称任何上界。题面闭合条件是「对逐环段占用密度给出上界」——DVC 给的是「饥饿触发后的局部配额」，闭合度弱于题面要求，T1 会被追问。
4. 卡对先例的关键描述错误：§1、§3 称「i-tag 只能在空槽已到达本口之后抢仲裁」。实际 i-tag 在**过路占用槽**上打 `sender_tagged`（`TCsHighWay.cpp:1095-1110`），占用者弹出后该槽仍是保留槽（`isSlotReservedFlit` `:1151-1158`），所有上游都不能用，绕回打标者（`tryItagProcess` `:894-950`）。即 i-tag 已经是「下游预约一个上游不可见的槽」，DVC 的增量只是**数量 Q>1 + 提前阈值 + 只抑制穿段注入**。
5. 时序拍数需重算：卡用 `C_ring=CS_NUM`；实际一圈 = Σlat（top 42 拍，bottom V 132–152 拍）。最坏闭环 `2·C_ring` 在 top 为 84 拍、bottom V ≈300 拍，已接近 / 超过 i-tag 阈值 128 拍 + 一圈，「K_fail=8 比 i-tag 更早」的优势在长环上被传播延迟吃掉。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
**专项：M-2 的反向 CLAIM 是否占用现有通道位宽？**
结论：**不加宽、不占用现有字段的额外位宽；它占用的是对向同通道的整槽带宽（一个完整 flit 拍）**，并需要一个保留 opcode 与每 CS 的截获解码。
- Dat 侧：CLAIM 是一条完整 DATFLIT（Data 512 b + BE 64 b + 头），只用约 21–25 b 信息（claimant 7–11 + seg 6 + Q 4 + wave 4）。Opcode 需用 DAT 保留编码（IHI0050E.a Table 13-18：0x8–0xA、0xD–0xF Reserved）。不挤占任何正在用的字段，但每条 CLAIM/REL 吃掉对向 Dat 一个槽 × 传播跳数。
- Snp 侧：SNPFLIT 无 Data（Table 13-8）。可放入现有字段：claimant→SrcID（7–11 b），seg 6 + Q 4 → TxnID（12 b，余 2 b），wave 4 → FwdNID 低位（7–11 b）；Opcode 用 SNP 保留编码（Table 13-17：0x0E–0x0F、0x18–0x1F）。卡写的「7–11+6+4 ≤ 12+5+11」漏了 wave 4 b，且把 5 b Opcode 算作载荷——Opcode 必须用作 CLAIM 标识，不能装载荷。按上面的映射重排后**放得下**。
- 代价：Snp CLAIM 与本征 Snp 流量共享对向 Snp 环，Snp 15:1 小包延迟必须单列；双向 KV 下对向 Dat 也忙，CLAIM 发不出（卡 §4 已承认行为退回基线）。
- 卡未考虑的零带宽替代：库内 FC 通路 `m_highWayFcBuf`（`TCsHighWay.cpp:152-155`、`:1423-1527`）是独立于数据槽的反向传播路径，载荷 `NetworkFlowCtrl{m_csId, m_localPort, m_fcValue, m_fcSpreadCnt}`（`include/chi_ring_common.h:618-630`）。若 CLAIM 改走 FC 通路，不占数据槽；但其物理位宽未知（模型里是 `uint32_t`），seg 6 b + Q 4 b 是否放得进硬件 FC 字段须查 DV200 设计文档——T1 必验项。

| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | 每向每 CS 槽 | 1，`TCsHighWay.h:136` | `m_sendFlit` 在 `:135` | ✅（行号 -1） |
| 2 | 子环数 | Dat 2 / Snp 1 | `gen_config.py:308` `sub_channel_cnt req 1 rsp 2 snp 1 dat 2` | ✅ |
| 3 | `C_ring` / 传播上限 | `= CS_NUM`，「≤ C_ring」 | 拍数 = Σlat：top 42，bottom H ≈72–76，V 132/148/152 | ❌ 拍数低估 2–4× |
| 4 | `kBeatBytes` | 64，`Endpoint.h:27` | ✅ | ✅ |
| 5 | DAT Data/BE | 512/64 b | Table 13-9 DW=512 | ✅ |
| 6 | SNP 无 Data | Table 13-8 | ✅ | ✅ |
| 7 | NodeID 宽 | 7–11 b | Table 13-8/13-9 注释 | ✅ |
| 8 | CLAIM 载荷放入 SNPFLIT | 7–11+6+4 ≤ 12+5+11 | 漏 wave；Opcode 不能当载荷；按 SrcID/TxnID/FwdNID 重排可放下 | ⚠️ 算式错，结论成立 |
| 9 | 保留 opcode | 「opcode 自定义」 | E.a：SNP 0x0E–0x0F、0x18–0x1F；DAT 0x8–0xA、0xD–0xF 为 Reserved。注意后续 CHI 版本可能占用 | ⚠️ 可用，需锁版本 |
| 10 | 每段 claim latch | ~20 b，1 活 | 段主 CS 新寄存器：owner 7–11 + q_left 4 + 计时 ≥ ⌈log2(2·lap)⌉（top 7 b，bottom V 9 b）；6 子环 × 2 向 / CS | ⚠️ 计时位宽按 lap 重算 |
| 11 | 每 NIC skip 位图 | ≤64 b | 需按子环 × 方向各一份：≤64 × 6 × 2 b | ⚠️ 少乘子环/方向 |
| 12 | 失败计数 | 8 b / NIC / 向 | 库内已有注入失败计数（`TNetworkInterfaceBase` `m_injectFailCntAll`，FC 与 dyn leaf-tag 都在用） | ✅ 可复用 |
| 13 | i-tag 语义 | 「空槽到达后才抢」 | 过路槽打标 → 弹出后保留 → 上游不可用（`:1095-1110`、`:1151-1158`、`:894-950`） | ❌ |
| 14 | 队列 / 源端副本 | 0 / 无 | ✅ 无缓冲；数据在端点 outstanding | ✅ |

## 接口落点核查（live `main@63163cad`）
| 卡声称 | 实际 | 结论 |
|---|---|---|
| `TCsHighWay.cpp:1041-1117` skip 门；i-tag `:894-950` 不可覆盖 | `sendFlitToWay` `:1041-1118`；i-tag `:894-950`、`:1095-1110` | ✅；哈希锁定库，新分支 |
| 「`tests/soc_sim/platform/` 可发控制事务；highway 识别 opcode 在 `src/`」 | 平台层可构造 flit；但 CLAIM 须在**每个 CS 截获而不弹出**，只能改 `TCsHighWay`（`tryWayToLocal` `:289` 起） | 新分支 |
| 段主 `q_left` 在 `TCsHighWay.h:136` 旁 | `include/` 哈希锁定 | 新分支 |
| RTL | 仓内无 RTL | ✅ |
- 零代码对照：`gen_config.py --fc-profile experiment_srcfc`（库内 in-ring FC 打开到 top Dat 环）；`--itag-policy/--itag-max-tags/itagThreshold` 扫描（`gen_config.py:471-474`、`:134`）。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| **DQDB（IEEE 802.6）分布式队列** | **FUNCTIONAL_EQUIVALENT** | 下游站在反向总线上发 REQ，上游站对每个 REQ 让过一个空槽（RQ/CD 计数器）。DVC = 「饥饿时一次请求 Q 个空槽 + 只有穿段注入者让」——DQDB 的批量版 |
| MetaRing SAT（Cidon–Ofek） | 同类 | SAT 逆流传播，饥饿站扣住 SAT 直到满足，上游配额靠 SAT 续期 |
| 环库 in-ring 源端 FC | FUNCTIONAL_EQUIVALENT | 「注入失败计数 → 反向 `NetworkFlowCtrl` 传 spreadCnt 跳 → 上游限速」（`TNetworkInterfaceBase.cpp:842`、`TCsHighWay.cpp:626`）。差别：库内按 NI 整体限速、不看路径；DVC 只抑制穿过 `s_k` 的注入、以 Q 计数 |
| 环库 i-tag | 同类 | 已是「下游预约一槽、上游不可见」；DVC 是 Q 槽 + 更早阈值 |
| 环库 dynamic leaf-tag | 同类 | 按本地注入失败率分级标记 1/2/3 个过路槽为保留（`TCsHighWay.cpp:745-800`，top Dat 默认开，`gen_config.py:354-362`） |
| **P-0198 M-19 邻节点饥饿气泡中继**（REJECT, FE i-tag） | 同族 | M-19 = 饥饿 → 通知紧邻上游让一槽；DVC = 饥饿 → 通知所有穿段上游各让，合计 Q 槽。多跳化、计数化，执行原语相同 |
| P-0198 M-12 HSSL | 不同 | 方向正确，未重犯 |
| P-0198 M-2 CSR（GRANT） | 不同 | 无扇入会合税 |
- 显式标注（captain 规则）：DVC 不是 token bucket；**是 credit/请求计数类（DQDB）→ FUNCTIONAL_EQUIVALENT**。

## 指标核对
- 作用点在饥饿节点的注入等待，直接对应扇入集合与 KV 的最慢参与者，方向对 makespan。
- 但 i-tag（阈值可扫）与库内 FC 已在同一作用点；在没有与 `experiment_srcfc` / i-tag 低阈值对打前，「Q 槽批量 + 路径选择」的 makespan 增量无从判断。只报 claim 次数或下游 `p_inj` 按淘汰论。

## 判决理由
REJECT（FUNCTIONAL_EQUIVALENT）。机制物理上可落（位宽放得下，代价是对向整槽带宽 + 保留 opcode + 每 CS 解码），因果方向也对；但执行原语是 DQDB 的反向请求让槽，环库已有同一回路（in-ring FC 反向通告 + i-tag 保留槽 + dynamic leaf-tag），P-0198 M-19 已以同理由 REJECT。增量仅为「路径选择性 + 批量 Q」，按「增量必须相对真实代码库」规则，不足以进 T1。

## 决策点（给用户 / 总监）
若希望 P-0221 本轮至少有一张进 T1，DVC 是唯一候选：可改判 PASS_T1 / DIFFERENT_APPROACH-INCREMENTAL，条件为 T1 必验：(1) 与 `--fc-profile experiment_srcfc`、i-tag 阈值 {8,16,32}、dyn leaf-tag 同信封对打，推理 makespan / 最差节点严格更好；(2) CLAIM 走现有 FC 通路的硬件位宽核实，或给出走数据槽的 Snp 15:1 延迟 ≤1.4×；(3) 拍数全部按 Σlat 重算。
