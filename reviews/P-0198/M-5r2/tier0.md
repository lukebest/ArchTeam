# Tier 0 · P-0198/M-5r2 · CRRF-SS k 槽缝合（不加线）

- 机制卡: mechanisms/P-0198/M-5r2.md（PR #97 head `d190264`）
- 修订: CRRF 线船长唯一一次重试（不加线、不改 RTL，只许在既有 Snp 环宽度内缝合）
- 对照: M-5（PR #53）、M-5r1（PR #85；T0 PR #89 PASS_T1；T1 `reviews/P-0198/M-5r1/tier1_synthesis.md` FAIL）
- 判决: KILL
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO
- CRRF 线: 建议关闭
- 平台核查: bufferless-ring-noc `main@63163ca`（私有仓，认证只读）；CHI 规范核对用 ARM IHI 0050E.a（E.b 正文未取得，见要点一）
- 未读 T1 persona 正文；只读 tier1_synthesis.md

## 卡摘要
删掉 M-5/M-5r1 的 epoch、bind、Drain、FLIP，只剩 header-only 路径：当本拍两条 Dat 子环都注入失败、本地无 Snp pending、本节点在途 ghost 未超帽（`G_node ≤ k` 个 fragment，含 orbit）时，把一个 Dat beat 拆成 k 个 fragment 注入 Snp 物理环既有宽度；目的端重组 CAM（`N_src` 项 × D bit）收齐后进 1 深 Dat 宽 holding，再转入 Dat 消费者；CAM/holding 满则 fragment 留环；超时 `T_partial` 丢已收 fragment（`partial_drop`），不留源端副本；ghost 不得发 i-tag。作者自判「过不了」，按船长规则接受关闭。

## 要点一：k 的推导是否成立

### 能核实的部分（IHI 0050E.a 正文已核）
- Table 13-8 Snoop flit：QoS 4、SrcID 7–11、TxnID 12、FwdNID 7–11、FwdTxnID 12、Opcode 5、Addr SAW=41–49、NS/DoNotGoToSD/RetToSrc/TraceTag 各 1、MPAM 0 或 11；Total `S = 51+SAW+M … 59+SAW+M`。卡的 W_snp：92（7/41/0）、104（11/45/0）、119（11/49/11）三点算术正确。无 TgtID、无 Data/BE，正确。
- Table 13-4：`SNPFLITV` 是独立管脚，不在 SNPFLIT 内。卡从 W_snp 再扣 valid 1 b 是保守方向，可接受。
- Table 13-9 Data flit：DW ∈ {128, 256, 512}；Total `D = 221–233 / 370–382 / 668–680 + Y + DC + P`。卡引用正确。
- Size 编码：E.a 中是 **Table 13-20**（另 Table 2-15），`0b110`=64 B、`0b111` Reserved。卡写「Table 13-18」，在 E.a 里 13-18 是 DAT opcode 表；E.b 是否重新编号无法核实，**标为未核**。另：Size 是事务字节数，不是数据总线宽度；128 B beat 不合法的正确依据是 Table 13-9 的 DW 上限 512 b，结论不变。
- 公开 overview 的「SNP 88 b」：未在 E.a 正文中找到，**标为未核**；它比 Table 13-8 下限 92 b 还窄，作保守针可以。
- Issue F 勘误把 Table 13-8 MPAM 从 11 改 12（ARM CHI Issue F Errata 可查到原文），+1 b 不改变 k。

### 推导中的两处错误（都偏乐观）
1. **漏了 Dat 头字段。** 卡的 `D = Data + BE + H_frag`，64 B 时 D=608。但一个 Dat beat 要在接收端还原成合法 DAT flit，除 Data/BE 外还必须携带 Opcode 4、RespErr 2、Resp 3、FwdState/DataPull/DataSource 4、CBusy 3、DBID 12、CCID 2、DataID 2、TagOp 2、Tag 16、TU 4、TraceTag 1、HomeNID 7–11（QoS、TgtID 可由 fragment 头的 dest/QoS 位代替，SrcID/TxnID 计入重组键）。这部分约 62–66 b。规范 DW=512 的 DATFLIT 是 668–680 b，卡只算了 608 b（其中 32 b 还是重组头），实际要搬的 Dat 内容少算了约 60 b。
2. **重组头只算了一次。** 卡说「每个 fragment 自带重组头（计入 D，不偷 U）」，却把 `H_frag=32` 只加一次进 D。若每片都要带 (src, TxnID, frag_id, last) 才能在 CAM 中命中，那么每片可用载荷是 `U − H_frag`，不是 U。
- 修正估算（64 B，DW=512）：每 beat 需搬 ≈ 512 + 64 + 62–66 ≈ 638–642 b；每片头 src 7–11 + TxnID 12 + frag_id 4–5 + last 1 ≈ 24–29 b。
  - U=103：每片载荷 ≈ 74–79 b → k ≈ 9。
  - U=68：每片载荷 ≈ 39–44 b → k ≈ 15–17。
  - 64 B 合法区间约 **k ∈ [9, 17]**，而不是卡上的 [6, 9]。128 B 灵敏度相应升到约 [17, 32]。
- 结论：k 的推导**不成立**（两处少算），但两处都让 k 偏小、对机制有利。修正后 k 更大，结论只会更差，不改变本判决方向。若船长补 `chi_interface` 给出真实环上 flit 宽度（环级 flit 还有路由/tag 位，规范的 SNPFLIT 不一定等于物理环宽），须按修正式重算。

## 要点二：基线 Dat = 2 子环、Snp = 1 环
- 核实成立。top：`tests/soc_sim/gen_config.py:308` 生成 `sub_channel_cnt req 1 rsp 2 snp 1 dat 2`，`ring_cnt 2`；bottom：`docs/bottom_manyring.csv:1` 同为 `req 1 rsp 2 snp 1 dat 2`，`ring_cnt 28`。解析在 `src/TMultiRing.cpp:223-231`。每个物理环位置上 Dat 有 2 条子环、Snp 1 条，比例 2:1 在 top 与 bottom 一致。
- 每 CS 每方向一个 `NetworkFlit*` 槽（`include/TCsHighWay.h:136` `m_sendFlit`）属实。
- 平台四通道共用同一 flit 结构、不建模位宽（`tests/esl_wrapper/compat/chi_common.h:92-118` 的 `CHIFlitFields`；soc_sim 同源），即任何 flit 占 1 槽 = 隐含 k=1。卡把 k=1 标 `FAKE_WIDTH` 并禁止作主列，正确。
- 由此环受限上界 `T_dat/T_off ≥ 2/(2+1/k)` 成立（且假设 Snp 环全空、帽不生效，是乐观上界）。合法 64 B 最好情形 k=9（修正后）→ ≥0.947；即使取卡自己的乐观 k=6 → ≥0.923。**推理 makespan 在任何合法 k 下都到不了 0.85 pass bar**，这一点不依赖作者的未签字探针。

## 要点三：去掉 epoch/bind 后「一笔事务跨多次 flip」是否不再适用
- 原问题（事务跨 flip，旧世代 ghost 与新绑定失配、需 `epoch_tag` 接受集与 redirect）确实不再适用：没有 flip、没有世代状态，header 的 channel disc 是唯一身份。卡的 `header-only ≡ drain-off ≡ stitch` 是构造性恒等，符合 T1 Archi 的消融发现。
- 但同类问题换了位置：一拍 Dat 现在**跨 k 个 Snp 槽、跨多个周期**，一个 512 B 事务（8 beat）在 k=9–17 时跨 72–136 个 fragment。片间不要求连续，靠目的 CAM 重组，于是出现「部分 beat」状态：CAM 满时后续片留环绕圈，超时 `T_partial`（两圈）后丢已收片（`partial_drop`）。卡说「源靠 CHI 事务层重试」：CHI 对已发出的 Dat 没有链路层或事务层重传（RetryAck/PCrdGrant 只用于 Req 在被接受前），丢 Dat beat 即协议错误。作者自己的减箱在 k=18 已出现 1 个 `partial_drop`（149/150 完成）。
- 结论：「跨 flip」问题消失，但被「跨 fragment 的部分重组 + 超时丢数据」取代，后者是正确性问题，比原问题更严重。

## 要点四：上轮 T1 致命点是否闭合
| T1 点 | 卡的处理 | 判定 |
| --- | --- | --- |
| Snp 线宽载 Dat | 选拆拍：在既有 Snp 宽度内缝合 k 片，计入 `C_dat_eff` 与面积，禁 k=1 主列 | 形式上闭合；但 k 少算（要点一），实际收益比卡写的更小 |
| 每节点 ghost 密度帽 / i-tag | `G_node ≤ k` 片（含 orbit），ghost 禁发 i-tag、须让出保留槽 | 帽存在，但只按节点、不按段：12 个上游节点各 k 片仍可塞满下游段。作者减箱 `cap-off` 与 `stitch` 数字完全相同，帽不起作用，推理混合 Snp 4.0–6.9×（未签字）。**未闭合** |
| NACK 重注入的数据来源 | 数据随片在 Snp 槽内绕环；缝合器 1 深寄存器在 k 片离开后释放；holding 满则留环；无源端副本 | 「源端副本」的致命点闭合；但超时 `partial_drop` 把留环的片丢掉，而源无副本、CHI 无重传 → 丢数据。**换成了新的致命点** |
| Sys：跨通道循环依赖 | 本征 Snp 弹出不进 Dat 入口；帽；有 Snp pending 时空槽归 Snp | 只在本地成立；CAM/holding 满时 ghost 片留环直到超时，环靠丢数据打破。**未合法闭合** |
| drain-off / header-only | 本卡即 header-only，恒等 | 闭合（epoch/bind 已删） |

## 未签字探针的权重
作者数字（15:1 推理混合 Snp 4.0–6.9×，推理 makespan r=0.966–1.017；k=14/16 变差到 1.144/1.297）按规则只作假设。但本判决不依赖它们：
- Dat 侧不过线由代数上界 `2/(2+1/k)` 决定（要点二），与探针无关。
- Snp 侧方向与上界一致：要让 Dat 有任何收益，就必须让 ghost 占 Snp 空槽；每拍 Dat 占 k 个 Snp 槽，Snp 本征流量被下游段的 ghost 列车挡住。把帽收紧到能保 ≤1.4，Dat 侧更接近 1。两条杀线不能同时满足。
- 探针只是印证：最坏 k 下 Snp 6.889 > 1.4（KILL 线），Dat r≈1（淘汰规则 2）。

## RTL / 仿真器改动核查
- PR #97 只新增 `mechanisms/P-0198/M-5r2.md` 与 `models/P-0198/M-5r2/*`，不碰 bufferless-ring-noc，不改 M-5.md / M-5r1.md / reviews/。仓内无 RTL 源（无 .v/.sv），**不触 RTL**。
- 卡 §7 的改动点核对（行号属实）：Snp 环注入 `src/TCsHighWay.cpp:1041-1117` `sendFlitToWay`；i-tag `:894-950`；弹出 `tryWayToLocal` 起于 `:289`；Snp 完成计数 `tests/soc_sim/platform/Endpoint.h:601-609`（`completed_snp_`）；`kBeatBytes=64` 在 `Endpoint.h:27`；64 vs 128 B 冲突记录在 `gen_config.py` assumptions（约 `:527`）。
- 落点：channel disc、k 缝合器、`G_node` 帽、ghost 跳过 i-tag、重组 CAM、1 深 holding、同 CS 转道口全部在哈希锁定库（`include/`、`src/`），属仿真器结构改动，只能开新分支；本征 Snp 发生器在平台 `tests/soc_sim/platform/TrafficGen.h`（默认确实不发 Snp）。卡对此表述正确。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| M-5 / M-5r1 | 同线，去掉了唯一的差异结构 | epoch/bind/Drain 删除后，CRRF 的「通道–环重绑」身份不复存在 |
| 多物理子网负载均衡（Yoon et al. 多物理网络 vs VC）、窄子网串行化（如 Catnap 多窄子网） | FUNCTIONAL_EQUIVALENT | 剩下的是「Dat 溢出到空闲窄子网并按子网宽度串行化、目的端重组」 |
| M-15 TOSE | 同族 | 同为 Dat 借 Snp 空槽，M-15 只限尾拍 |
| slotted ring / TDM / 最短方向 | 非等价 | — |

## 判决理由
KILL。
1. 推理 makespan 不可能过线：合法 64 B 下环受限上界 `2/(2+1/k)` ≥ 0.92（卡的乐观 k）/ ≥ 0.947（修正 k），远离 0.85 pass bar，再扣密度帽与 Snp 优先只会更接近 1。按淘汰规则 2（推理 makespan 不缩短即淘汰），不依赖未签字数字即可判定。
2. Snp 杀线与 Dat 收益互斥：帽是唯一杠杆，收紧保 Snp 则 Dat≈1，放松则 Snp 被下游 ghost 列车挡住；作者探针（6.889×）与此方向一致。
3. 正确性：超时 `partial_drop` 在无源端副本、CHI 无 Dat 重传的前提下即丢数据；跨通道循环依赖靠丢数据打破，不合法。
4. k 推导少算 Dat 头字段且重组头只计一次，修正后 k 更大，进一步压低上界。
5. 新颖性：去掉 epoch/bind 后剩余机制等价于多物理子网溢出 + 窄子网串行化。

**CRRF 线关闭建议**：同意关闭。M-5（排他 epoch）死于 Snp 17×；M-5r1（宾客资格）死于位宽与密度帽；M-5r2（不加线的拆拍）在不加线约束下收益上界 <6%，且引入丢数据路径。剩下的唯一出路是加宽 Snp 环到 Dat 宽（= 加线，船长已禁止），而那等价于「Dat 2→3 环」，不再是 CRRF。不建议以调帽、调 k、调 15:1 成分再开第三次重试。
