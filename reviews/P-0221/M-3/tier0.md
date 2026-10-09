# Tier 0 · P-0221/M-3 · 注入–越过守恒窗（Inject–Pass Conservation Window, IPCW）

- 机制卡: mechanisms/P-0221/M-3.md（PR #100 head `07c78cd`）
- 题卡: problems/P-0221.yaml（main@1909fb0）
- 作者: Jim Keller
- 判决: REJECT
- 可行性: FAIL（Snp 每包先等 ≥1 圈预约，按设计越过 Snp 15:1 KILL 线；`I_max` 以 CS 数定标而上界按拍数成立，段利用率被压到 18–36%；NACK 回滚无物理路径；绕圈 / U-turn 重复越过破坏守恒）
- 新颖性: FUNCTIONAL_EQUIVALENT（逐链路 in-flight 窗口 = 教科书 credit / window 准入；路径预约 = ATM CAC / Orwell 环试约；P-0198 M-2 CSR 预约族）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc live `main@63163cad`（= 63163ca，无漂移）

## 卡摘要
每段 `inflight[s]` = 已获准、路径含 s、尚未越过 s 的 flit 数，上限 `I_max = ⌊ρ_max·C_ring⌋`（top 15）。源 NIC 在同通道对向发 RESERVE（src、dst、n_beats≤8、txn），沿途每个路径段的段主试 `inflight += n_beats`，超限打 NACK；走满一圈回源得 ACK 才可注入 n_beats 拍。flit 越过 s 时段主本地 −1。提前结束发 RELEASE。卡声称圆周窗 `ρ_transit(s, C_ring) ≤ I_max / C_ring ≤ ρ_max`。

## 轴一 可行性
1. **上界的单位错误，且错误方向是灾难性的。** 证明的关键其实成立：一个被释放的 inflight 名额要再被使用，必须经历「RESERVE 从段主逆流回源 + 数据从源顺流到段主」≈ 一整圈；所以任意一圈长的窗内越过次数 ≤ I_max。但「一圈」是 **Σlat 拍**，不是 CS 数：top 42 拍（`gen_config.py:345` `lats=[2]*21`），bottom V 33/37/38 CS × 4 拍 = 132/148/152 拍（`gen_config.py:449`）。按卡 `I_max=⌊0.75·CS_NUM⌋`：top ρ ≤ 15/42 ≈ 0.36，bottom V(37) ρ ≤ 27/148 ≈ 0.18。机制把每个环段的利用率永久钉在 18–36%，推理 makespan 必然恶化。改按拍数定标（top 31、bottom V ≤114）则计数器 7 b，卡的「≤6 b 因 CS_NUM≤64」也随之失效。
2. **Snp 按设计越过 KILL 线。** 卡把 IPCW 套在 Snp×1 环上，单拍 Snp `n_beats=1`，每条 Snp 注入前必须等 RESERVE 走完一圈（top ≥42 拍）。均匀最短方向路径约 CS/4 ≈ 5 跳 ≈ 10 拍，Snp 路径延迟变为 ≈ (42+10)/10 ≈ 5×，远超 1.4×（H-SNP 阈值）/ 1.5625× 的 KILL 线。卡 §2.5「Snp 稀疏，税小」只算了槽数没算延迟。
3. **预约税按跳加权远大于 1/8。** RESERVE 必须逆流经过路径上所有段主并回源，路程恒为一整圈（C 跳）；数据平均只走 ≈C/4 跳。每 8 拍 Dat 的正向跳负载 ≈ 8·C/4 = 2C，对向 RESERVE 负载 C ⇒ **对向跳负载税 ≈ 50%**（对 Snp：C 对 C/4 = 400%）。双向 KV / all-to-all 下对向本就满载，等价于砍掉三分之一带宽。CSR（P-0198 M-2）正是死于同类预约税（T3 r≈1）。
4. **NACK 回滚无物理路径。** 环单向：RESERVE 在段主 m 处 NACK 时，它已加过账的段主都在它身后。卡说「回程把已成功的加账减回去」，但 RESERVE 只能继续前行回源，减账需另发 RELEASE 再走一圈。期间幻影账挡住别人；两个预约各占一段、互相 NACK 的场景是经典两阶段加锁活锁，只有指数退避的概率保证。
5. **守恒在真实环上不成立。** 弹出失败的 flit 继续绕圈（库内有 e-tag 正是因为弹出失败常见），U-turn（`UturnConnect`）与换环都会让 flit **第二次越过 s**，而 `inflight[s]` 第一次越过时已减。要守恒必须改为「最终弹出时才减」，这又让上界变成「≤ I_max × 圈数」。卡 M-4 自己点名了这一点。
6. 跨环路径：top→RBRG→bottom 的事务在每个环上都要各自预约；RBRG NI 作为注入者需要在输出缓冲（ChangeRing 端口 `outputBufferDepth=15`，`gen_config.py:211-213`）中扣住 flit 等一圈预约——卡未讨论，可能把预约延迟转成 RBRG 反压。
7. Sink / 死锁：NACK 时数据留在端点 outstanding、不在环上，无死锁；问题在活锁、Snp 延迟与带宽税。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
**专项：M-3 每段预约状态的存储与信令从哪里来？**
- **存储**（全部是新寄存器，均在哈希锁定库 `include/`/`src/`，只能新分支）：
  - 段主 CS：每（子环, 方向）一个 `inflight` 计数器。每 CS 6 子环（Req1+Rsp2+Snp1+Dat2）× 2 向 = 12 个。位宽按正确定标（I_max 以拍数计，最大 0.75×152 ≈ 114）需 **7 b**，≈84 b/CS；卡写 6 b。
  - 源 NIC：每（通道, 方向）1 深预约寄存器：txn 12 + n_beats 4 + src/dst 各 7–11 + 状态 ≈ 40–50 b，再加 ACK 后剩余拍数计数。卡写「数十 bit」✅。
  - 路径 ROM（src,dst→段集合）：与 M-1 同，卡未列入本卡开销。
  - RELEASE / 回滚待办状态：卡未列；按第 4 点需要。
- **信令**（不加线；全部占用同通道对向子环的整槽带宽）：
  - RESERVE / ACK / NACK：同一条 flit 逆流走一整圈；每到一个 CS 段主就地读改写 `inflight`（需每 CS 截获解码）。Dat：整条 DATFLIT + DAT 保留 opcode（E.a Table 13-18 Reserved 0x8–0xA、0xD–0xF），载荷 src/dst/txn/n_beats ≈ 30–38 b 放在 SrcID/TgtID/TxnID 等头字段即可；Snp：无 TgtID，卡用 FwdNID 装 dst ✅，n_beats 恒 1，opcode 用 SNP Reserved 0x0E–0x0F、0x18–0x1F。
  - 越过减账：段主本地事件，**无需信令** ✅。
  - RELEASE / 回滚：再一条逆流 flit、再一圈。
  - 带宽代价：Dat 对向跳负载税 ≈50%，Snp ≈400%（见轴一第 3 点），不是卡写的 1/8。

| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | 每向每 CS 槽 | 1 | `TCsHighWay.h:135` `m_sendFlit` | ✅ |
| 2 | 子环数 | Dat 2 / Snp 1 | `gen_config.py:308` | ✅ |
| 3 | `C_ring` | `= CS_NUM`（top 21），RESERVE 一圈 ≤ C_ring | 一圈 = Σlat：top 42，bottom H ≈72–76，V 132/148/152 | ❌ |
| 4 | `I_max` | ⌊0.75·CS_NUM⌋ = 15（top） | 上界按拍数成立 ⇒ ρ ≤ 15/42 ≈ 0.36（top）、27/148 ≈ 0.18（bottom V） | ❌ 致命定标错误 |
| 5 | `inflight` 位宽 | ≤6 b（CS_NUM≤64） | 正确定标需 7 b | ⚠️ |
| 6 | 512 B ⇒ 8 beats | 512/64 | `Endpoint.h:27` `kBeatBytes=64` | ✅ |
| 7 | DAT Data/BE、SNP 无 Data | Table 13-9 / 13-8 | ✅ | ✅ |
| 8 | Snp 预约用 FwdNID 装 dst | SNPFLIT 无 TgtID | FwdNID 7–11 b 可用 | ✅ |
| 9 | CHI Size 表号 | Table 13-18 | E.a 为 Table 13-20；13-18 是 DAT opcode 表 | ⚠️ 表号 |
| 10 | 预约税 | 每 8 拍 1 条，1/8 | 按跳加权 ≈50%（Dat）/ ≈400%（Snp） | ❌ |
| 11 | 本地预约状态深度 | 1，无 Dat 副本 | ✅ 数据留在端点 outstanding | ✅ |
| 12 | highway 队列 | 0 | ✅；但 RBRG 输出缓冲（15）会被预约等待占住 | ⚠️ 未讨论 |
| 13 | 每拍每段 0/1 越过 | 一对一 | 弹出失败绕圈 / U-turn 会重复越过 | ❌ 守恒破 |

## 接口落点核查（live `main@63163cad`）
| 卡声称 | 实际 | 结论 |
|---|---|---|
| `TCsHighWay.cpp:1041-1117` 无 ACK 不注入 | `sendFlitToWay` `:1041-1118` | ✅；新分支 |
| `:289-351` `tryWayToLocal` 与转发臂越过减账 | `tryWayToLocal` 起于 `:289`（全函数到 `:597`）；`:289-351` 只是弹出前段，转发臂另在 highway 传输阶段 | ⚠️ 落点不全 |
| RESERVE/RELEASE 状态机在 `Endpoint.h` + highway 解码 | 源端 FSM 可放平台层；逐 CS 截获与 `inflight` 只能在 `TCsHighWay` | 新分支 |
| RTL | 仓内无 RTL | ✅ |

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| **教科书 credit / window 流控（逐链路 in-flight 窗口）** | **FUNCTIONAL_EQUIVALENT** | 「每链路最多 I_max 个已承诺未通过的单元，通过即归还」就是 hop 级 credit 窗口；把窗口按路径上所有链路同时预扣 = 端到端路径准入 |
| ATM CAC / RSVP 路径预约 | FUNCTIONAL_EQUIVALENT | 沿路径逐跳预扣、任一跳失败即拒并回滚 |
| Orwell 环 / DQDB | 同类 | 环上试约 / 反向请求 |
| P-0198 M-2 CSR（Rendezvous–Grant） | 同族 | 都是注入前一轮控制往返；CSR 死于预约税 r≈1，IPCW 的按跳税同样量级（≈50%） |
| 环库 in-ring FC / i-tag | 不同 | 库内无逐段计数；但同解「下游饥饿」 |
| P-0221 M-1 / M-5 | 同族 | 段级合计上界的另两种记账 |
- 显式标注（captain 规则）：**credit / window → FUNCTIONAL_EQUIVALENT**，理由同上。

## 指标核对
- 主指标：每事务至少多一圈（top 42 拍、bottom V ~150 拍）预约等待，跨环路径每环各一圈；decode KV/P2P 为时延敏感小事务，makespan 直接变长。卡 §4 自己写了「若 ACK 等待主导尾，卡死」——按上面的量级，T0 即可判定。
- Snp 15:1：按设计 ≈5×，KILL。

## 判决理由
REJECT。守恒窗的核心论证在「一圈」按拍数计时成立，但卡以 CS 数定 `I_max`，把每段利用率钉在 18–36%；即便修正定标，Snp 每包等一圈预约按设计越过 KILL 线，对向按跳加权的预约税 ≈50% 重演 CSR；NACK 回滚无物理路径，绕圈 / U-turn 破坏守恒。机制本体是教科书逐链路 credit 窗口 + 路径预约，FUNCTIONAL_EQUIVALENT。

## 若作者重提须先回答
1. `I_max`、窗长、计数位宽全部按 Σlat 拍数重做，并给出利用率上限对 makespan 的影响。
2. Snp 豁免或给出 Snp 15:1 ≤1.4× 的路径。
3. 预约税按跳加权计算并与 CSR T3 结果对照；回滚路径与活锁上界。
4. 弹出失败 / U-turn / 换环下的守恒定义。
