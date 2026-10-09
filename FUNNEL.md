# FUNNEL

周次: 2026-10-05 ~ 2026-10-11（上海）
配额: 新问题 30 → 机制 150 → 过 T0 40 → 过 T1 12 → T2 8 → T3 3
用量: 问题 7/30 · 机制 22/150 · T0 过 1/40 · T1 过 0/12 · T2 过 0/8 · T3 过 0/3

## 2026-10-09 船长给题派出

船长 2026-10-09 10:24 经 Firstmate 给题（bufferless ring NoC 上 LLM 数据搬运与集合通信端到端时间最短的拥塞控制），即已有 P-0198；10:26 拍板 A+B 并行。
A：第二轮机制，Jim Keller 5 张 + 保守架构师 5 张（带上周淘汰约束）；负载基线补推理（decode KV/P2P/权重）与训练（AllReduce/AllGather/ReduceScatter/All-to-All）负载表；cycle 级基线=无拥塞控制/源端流控/M-5 CRRF。
B：Jim 交 M-5 CRRF 修订卡修 15:1 小包延迟；微架构仿真补测现版 CRRF card-claim（以推理为主），交评估审计。不开 T4。
默认约束（船长 10:27 补充）：仍不改 RTL；允许新分支改仿真器结构（不动 main，审计后再谈合入）；负载以推理为主（decode KV/P2P + 推理集合通信），训练降为次要不单独报，主指标以推理为准。汇报只经 Firstmate。
同日船长令：未给题不自发派活；微架构仿真夜间复扫、文献情报每日扫描、问题提炼每日出题均已停。
本周配额用量未变（卡未入 main 不记机制层）。今日 09:00 台账 routine 失败，本条代补。
B 进展（10:40）：M-5 CRRF card-claim 补测（PR #83）经评估审计（PR #86）判部分成立，不签全信封。可引用：gather 0.551 / allgather 0.667 / alltoall 0.719（过 0.85）；allreduce 1.000 不过；decode_kv_p2p 0.824 边缘。全类 0.55–0.85× 与推理相关性不签（负载基线表未到，existing_config）。卡收益收窄为 gather/allgather 型集合，本 bbox。15:1 Snp 仍 KILL。T3 存活，不开 T4。
A/B 在途：Jim M-11..M-15（PR #84）、M-5r1 CRRF-SB 修订卡（PR #85）已交设计验证 T0；保守架构师 5 张、负载基线表未到。
T0 收口（10:45）：第二轮 11 张（Jim M-11..M-15、保守 M-16..M-20、M-5r1）仅 M-5r1 CRRF-SB 过（PASS_T1/INCREMENTAL），已交评审主持 T1。REJECT：M-11 MELB、M-12 HSSL、M-13 WSOR、M-15 TOSE、M-16 RBRG 拼接、M-17 highway 对换、M-19 饥饿气泡中继。KNOWN_CONFIRM：M-14 PSCK、M-18 目的位图组播（=环库已有 Dat 多播）、M-20 最长弧先发（按 M-7 先例）。口径：环库已有功能算先例；Snp 无数据载荷位宽问题列 M-5 线 T1 必验，不判 KILL。基线补充已交负载基线：开库内多播、i-tag 门限扫 8/16/32、发射顺序三臂、UturnConnect。
T1（10:52）：M-5r1 CRRF-SB 共识 FAIL（PR #95），退回 Jim。致命点：Snp flit 无数据字段，ghost Dat 需 k≈6–8 槽或加线；卡上基线少算一条 Dat 子环；无逐节点 ghost 密度上限。drain-off/header-only 数字与全机制一致，epoch/bind 赘余。
审计更正（11:03，PR #96）：原 M-5 CRRF T3 仿真一槽载整笔 512B（k=1）、Dat 只建 1 环、作业未跨 flip。M-5 T3 PASS → 退回重测；card-claim（#86 部分成立）→ 撤回。估算真实条件 gather/allgather/alltoall 约 0.92–0.97，均不过 0.85；15:1 Snp 仍 KILL。
船长拍板（10:57）：CRRF 路线不加线，只在现有线宽内拼槽重试一次（M-5r2，即本次重测），过不了关闭。k 按 CHI 规范字段宽推算，扫 64B/128B beat 与 k 区间，KILL 按最不利 k；Dat ×2 基线；作业跨多次 flip。
设计验证 T0（~11:17）：M-5r2 KILL — 可行性 FAIL，新颖性 FUNCTIONAL_EQUIVALENT，不进 T1（PR #98）。依据：推理 makespan 上界 2/(2+1/k)，k=6 时 0.923，修正 k 时约 0.947，均达不到 0.85 过线；修正后 64B k∈[9,17]（卡上 [6,9] 漏了每 beat Dat 头约 62–66 bit 与每分片重组头约 24–29 bit）；重组 CAM 满后分片两圈超时丢弃=丢数据（作者探针 k=18 时 150 完成 149）；逐节点 ghost 密度上限未闭合。
按船长 10:57 裁定（不加线只重试一次，过不了就关闭），CRRF 路线关闭（10-09）。同类借 Snp 槽运 Dat 的 M-15 TOSE 一并列入关闭清单。不再做只调上限/k/15:1 混合比的重试；唯一剩路是加宽 Snp=第三个 Dat 环，属加线，船长不允许。RTL 未动。已报 Firstmate，第二轮方向等船长拍。
船长 11:20 拍 P-0198 第二轮方向一+方向二并开（2026-10-09 ~11:22 上海）。方向一：负载基线先修 Dat 多播（bufferless-ring-noc PR #1 分支），再全臂推理重跑，审计后给出对推理 makespan 有用的旋钮。方向二：新题 P-0221（上游注入填满下游环段、下游饿死）已规范化入仓（PR #99），派 Jim Keller（P-0221/M-1..M-5）与保守架构师（P-0221/M-6..M-10）。新硬规则：仿真/模型中容量、位宽等物理假设审计必须单独核对。共同约束：不改 RTL、不加线、仿真器结构只在新分支改、以推理为主。问题 6→7/30。
方向一（~11:39 上海）：评估审计签 bufferless-ring-noc PR #1（tip 89f9c88）有条件可用、仅 smoke 级（PR #101）；Dat 多播已修（640/640、1680/1680，根因 3DIO reset_route 清 ctrl）；出处 P1–P9 与 Snp 位宽不表达未签；已派负载基线按清单修并全臂多 seed 推理重跑，加库流控/leaf-tag 对照臂与沿环注入等待梯度。
方向二（~11:39 上海）：P-0221 Jim M-1 STB/M-2 DVC/M-3 IPCW/M-4 SOSG/M-5 PMQR 全 REJECT FUNCTIONAL_EQUIVALENT（PR #100 卡、#102 T0），0 进 T1。主因：库已有环内流控/i-tag/leaf-tag 先例；一圈时间误用站数 21（实际顶层 42 拍、横环 72–76、纵环 132/148/152）；每 flit 加 1 bit 算加线。总监裁定 M-2 维持 REJECT，待基线重核（库三项全开后梯度是否仍在）再定是否重写；P-0221 题卡已补三条约束（PR #103：加 1 bit 算加线、一圈时间按链路延迟之和、库三项全开为基线）。等保守架构师 M-6..M-10。机制 12→17/150。
方向二（~11:52 上海）：P-0221 保守架构师 M-6..M-10 全 REJECT（PR #104 卡、#105 T0）：M-6/M-7/M-8/M-10 FUNCTIONAL_EQUIVALENT，M-9 EXACT_MATCH（=端口 insertAfterRemoval=false）；M-8 ≈ platform --sub-rr；M-10 同构 P-0198 M-3 DPH。P-0221 两批 10 张 0 进 T1。
重要发现：不加 --sub-rr 时 pick_sub 恒为 0（Endpoint.h:180-181），bufferless-ring-noc 基线分支 89f9c88 上 P-0198 全部 11 个基线配置只用 Dat0，第二 Dat 子环/Rsp 子环闲置。已派负载基线加 sub-rr、insertAfterRemoval 对照臂与“库全开”组合基线；P-0221 后续是否继续出卡等库全开后饿死梯度是否仍在。机制 17→22/150。
方向一（~13:47 上海）：评估审计签 bufferless-ring-noc PR #1 @94498c7（PR #106）。可签（smoke 级、相对值）：sub_rr p2p 0.878 / allreduce 0.931 / RS 0.961 / mix_L 0.933，属基线配置修正（启用闲置的第二 Dat 子环），不是机制增益；lib_all_on 相对 sub_rr 无可测增量；dat_mcast p2p 0.938 / mix_S 0.898；issue_longest/shortest 使 moe 变慢 1.149/1.175；其余旋钮在噪声内或 FC 未触发；没有一行 ≤0.85。噪声门限 |1−ratio| > max(3×噪声, 2%)。
「库全开后除 Req 外无饿死」不签：池化口径错，先平均再取比后 Req0 0.81、Req1 0.83，结论反转；底 die 侧未测。P-0221 继续暂停出卡。
已派负载基线：修池化脚本、测底 die 侧、真随机 ≥8 seed、outstanding 扫 16/128/512、拆开 kv 与权值、lib_all_on 消融、给参数找出处。完整 12+2 die 信封已请船长拍板。
(~16:03 上海) 方向一 r2 签字（bufferless-ring-noc PR #1 @f279803，PR #107）：旋钮只有 sub_rr 有证据（p2p 0.966，lib_all_on 0.963）；撤回 #106 所签 AR 0.931/RS 0.961/mix_L 0.933（8 seed 打乱后 0.981/0.985/0.990），降为确定性参考；无旋钮接近 0.85；os128/512 相对 none 的 0.65–0.78 全部来自 sub_rr（基线配置修正，非机制）。饿死判定线（审计定）：单 die 单环物理 CS 序；R−3SE>1.10 且 ≥7/8 seed R>1；下游 ≥1.0 cycle/inject 且下游−上游 ≥0.5。os16 库全开无饿死；os512 饿死成立（top 3DIO Dat ring0 cc 0.264→1.235，R 4.68，8/8 seed，库全开消不掉），但峰在未核的 3DIO 挂接处，只签模型级。
(~16:20 上海) 船长拍：放大门按 os512 判。先小规模对照文档改对 3DIO 挂接位置重测；下游等待仍 ≥1 个槽位时间则放大到 12+2 die，否则不放大、P-0221 关闭。修正结果需审计签字。已派负载基线。P-0221 继续暂停出卡。
(~18:10 上海) 评估审计 gate r3（bufferless-ring-noc PR #1 @242aae4，PR #108）：有条件放大。饿死与挂法无关（所有可启动挂法均饿），链路时延敏感性不改结论；die1 aic_down 下游 2.096 cycle/inject、8/8 seed。根因为集合单根 incast（root 默认 rank0 在 die1 CS0；root 移 die2 饿死跟着搬，移环中 rank5 不过线；对称负载无梯度）。顶层链路时延=1 时 AR/RS 死锁未查。
(~18:21 上海) 船长拍 A：先小规模用环形/分段集合替换单根并扫 root；仍饿则带审计全部条件（root 扫描、等待剖面、两种挂法、查死锁、非单根对照）放大到 12+2；不饿则不放大、P-0221 关闭。死锁一并查。结果需审计签字。已派负载基线。
(~18:27 上海) 船长拍：内存交织 SNS / AffineRebind 停止，不开 T4，记为淘汰（原因：船长决定停止）。

## 2026-10-09 Jim T1 M-5r1 CRRF-SB

P-0198/M-5r1 CRRF-SB T1 = FAIL（Archi 致命）→ 退回 Jim Keller（T1-return）。票：Dr.Archi 致命缺陷 · Prof.Sys / Prof.Bench / Dr.Sim 有条件通过。不进 T2 / #eval。不记 T1 过线配额。

## 2026-10-08 09:00 台账

今日无派出、无退回、不派建筑师。昨夜已入账：P-0217–P-0220 备案（问题 6/30；cards tip `b78770e`）；其中 P-0218/P-0219/P-0220 来自文献 PR #82（cs.AR 2026-10-08 Trail 2610.08483 / SVRF 2610.07078 / DynaCore 2610.07443，DRAFT OPEN，同源已入仓，不另勾），P-0217 来自 PR #81（Terracotta 2610.06475）。无 P-0221+ 可勾。机制层仍空（0/150）。T0–T3 本周均 0。自 10-07 09:00 以来 main 仅备案入仓（tip `a4dab65`），无新审计/仿真、无新 night 结果。P-0198/M-5 CRRF 与旧 Top P-0105/M-4 SNS、P-0106/M-5 AffineRebind 均等人定 T4（不开 T4）。文献 PR #27–#43+#77–#82 仍 DRAFT OPEN。P-0198 产物 #44–#75 等多份仍 DRAFT OPEN（#76 已合）。拍板仍等人（T4/停 · 扩配额 · 本周备案 P-0215–P-0220 是否派建筑师）。

## 2026-10-08 入仓备案

P-0217 入仓备案：新 DRAM 技术几乎都要改接口加命令、改控制器，N 种技术改 N 次，等标准又锁死已部署系统，叠加组合更难；线索 arXiv:2610.06475 p.1-3（文献 PR #81 Terracotta）；同源 P-0212/P-0215/P-0195 未合并。
P-0218 入仓备案：翻译密集负载上地址翻译仍占约 40–45% 执行时间，不规则跨页转移让空间/淘汰序预取失效，固定小表装不下 delta 对，覆盖率跟不上内存足迹；线索 arXiv:2610.08483 p.1-3；同源 P-0149 未合并。
P-0219 入仓备案：长向量寄存器单个可达数 KB，标量语义指令仍占整宽寄存器，存储/能耗/重命名压力随 VLEN 线性涨而逻辑数据量是常数；线索 arXiv:2610.07078 p.1-3；无同源并入。
P-0220 入仓备案：LLM decode 在脉动阵列上 M=1 复用崩塌、利用率塌到 1/S，连续批处理形状来回切换，两相共置/分设与统一量化都不贴合；线索 arXiv:2610.07443 p.1-3；同源 P-0167/P-0168/P-0144 未合并。
均无解法；不派建筑师。问题 2→6/30。cards tip `b78770e`。

## 2026-10-07 09:00 台账

今日无派出、无退回、不派建筑师。无新规范化问题可勾（最高仍 P-0216，无 P-0217+；cards tip `ce6228b`）。问题仍 2/30；机制层仍空（0/150）。T0–T3 本周均 0。自 10-06 09:00 以来 main 无新合入（tip `b617f87`）、无新审计/仿真、无新 night 结果。新文献 PR #81（cs.AR 2026-10-07 Terracotta 2610.06475）DRAFT OPEN，尚未经问题提炼规范化入仓，不勾。P-0198/M-5 CRRF 与旧 Top P-0105/M-4 SNS、P-0106/M-5 AffineRebind 均等人定 T4（不开 T4）。文献 PR #27–#43+#77–#81 仍 DRAFT OPEN。P-0198 产物 #44–#75 等多份仍 DRAFT OPEN（#76 已合）。拍板仍等人（T4/停 · 扩配额 · 是否派建筑师）。

## 2026-10-06 09:00 台账

今日无派出、无退回、不派建筑师。昨夜已入账：P-0215、P-0216 备案（问题 2/30；cards tip `ce6228b`）；二者来自文献 PR #80（cs.AR 2026-10-06 RAPID 2610.02502 / PEEK 2610.03045，DRAFT OPEN，同源已入仓，不另勾）。无新规范化问题可勾（最高 P-0216，无 P-0217+）。机制层仍空（0/150）。T0–T3 本周均 0。自 10-05 09:00 以来无新合入审计/仿真、无新 night 结果入 main。P-0198/M-5 CRRF 与旧 Top P-0105/M-4 SNS、P-0106/M-5 AffineRebind 均等人定 T4（不开 T4）。文献 PR #27–#43+#77+#78+#79+#80 仍 DRAFT OPEN。P-0198 产物 #44–#75 等多份仍 DRAFT OPEN（#76 已合）。拍板仍等人（T4/停 · 扩配额 · 是否派建筑师）。

## 2026-10-06 入仓备案

P-0215 入仓备案：DRAM 存内计算缺行内相邻比特通路：只能 bitline 内算，逼出比特切片布局，与主机行主序互切必付转置，串行加还是 O(n) 行操作深度；线索 arXiv:2610.02502 p.1-3；同源 P-0195/P-0141/P-0142 未合并。
P-0216 入仓备案：安全关键 OoO 核异构并行检错：不护特权态覆盖率掉到 ASIL-A/B，护了快照胀 5.4×、减速近翻倍，小核特权切换与共享锁争用再拖垮；线索 arXiv:2610.03045 p.1-3；无同源并入。
均无解法；不派建筑师。问题 0→2/30。cards tip `ce6228b`。

## 2026-10-05 09:00 台账

新周开账。今日无派出、无退回、不派建筑师。无新规范化问题可勾（最高仍 P-0214，无 P-0215+；cards tip `eebbf8c`）。机制层仍空。上周收口：问题 20/30、T3 过 1/3（P-0198/M-5 CRRF 存活，M-1/M-2/M-4 T3 淘汰）。P-0198/M-5 CRRF 与旧 Top P-0105/M-4 SNS、P-0106/M-5 AffineRebind 均等人定 T4（不开 T4）。自 10-04 09:00 以来无新合入、无新 PR。文献 PR #27–#43+#77+#78+#79 仍 DRAFT OPEN。P-0198 产物 #44–#75 等多份仍 DRAFT OPEN（#76 已合）。拍板仍等人（T4/停 · 扩配额 · 是否派建筑师）。

## 2026-10-04 09:00 台账

今日无派出、无退回、不派建筑师。无新规范化问题可勾（最高仍 P-0214，无 P-0215+；cards tip `eebbf8c`）。机制层仍空（卡未入 main，0/150）。T3 过仍 1/3。P-0198/M-5 CRRF T3 存活不变；Top SNS/Affine 仍等人 T4。自 10-03 09:00 以来无新合入审计/仿真、无新 night 结果入 main、无新文献 PR。拍板仍等人。

文献 PR #27–#43+#77+#78+#79 仍 DRAFT OPEN。P-0198 产物相关 #44–#75 等多份仍 DRAFT OPEN（卡/模型/仿真未入 main；#76 已合）。

## 2026-10-03 09:00 台账

今日无派出、无退回、不派建筑师。昨夜已入账：P-0213、P-0214 备案（问题 20/30；cards tip `eebbf8c`）。无新规范化问题可勾（最高仍 P-0214，无 P-0215+）。机制层仍空（卡未入 main，0/150）。T3 过仍 1/3。P-0198/M-5 CRRF T3 存活不变；Top SNS/Affine 仍等人 T4。自 10-02 09:00 以来无新合入审计/仿真、无新 night 结果入 main。拍板仍等人。

文献 PR #27–#43+#77+#78+#79 仍 DRAFT OPEN；#79 cs.AR 2026-10-03 ShatterQuant/EdgeDAE（2610.00207/2610.00311）DRAFT OPEN（同源已入仓为 P-0213/P-0214，不另勾）。P-0198 产物相关 #44–#75 等多份仍 DRAFT OPEN（卡/模型/仿真未入 main；#76 已合）。

## 2026-10-02 入仓备案

P-0213 入仓备案：Transformer 块级混合精度在硬件上落不下去（per-tensor 仍主导，非均匀块与固定通路错配）；线索 arXiv:2610.00207 p.1-3；同源 P-0143/P-0182 未合并。
P-0214 入仓备案：边缘 VLA 动作头多步去噪在 GPU 上内存绑定（占参很小却成延迟瓶颈，共享 L2 留不住权重，跨器件同步吃掉异构收益）；线索 arXiv:2610.00311 p.1-3；同源 P-0189/P-0172 未合并。
均无解法；不派建筑师。问题 18→20/30。cards tip `eebbf8c`。

## 2026-10-02 09:00 台账

今日无派出、无退回、不派建筑师。昨夜已入账：P-0212 备案（问题 18/30；cards tip `71bd19c`）。无新规范化问题可勾（最高仍 P-0212，无 P-0213+）。机制层仍空（卡未入 main，0/150）。T3 过仍 1/3。P-0198/M-5 CRRF T3 存活不变；Top SNS/Affine 仍等人 T4。自 10-01 09:00 以来无新合入审计/仿真、无新 night 结果入 main。拍板仍等人。

文献 PR #27–#43+#77+#78 仍 DRAFT OPEN；#78 cs.AR 2026-10-02 NDS（2609.38454）DRAFT OPEN（同源已入仓为 P-0212，不另勾）。P-0198 产物相关 #44–#75 等多份仍 DRAFT OPEN（卡/模型/仿真未入 main；#76 已合）。

## 2026-10-01 入仓备案

P-0212 入仓备案；一句概括「近端简单核已在，透明 offload 被检测/页移/一致性/handoff 与弱 ILP 吃掉带宽收益，已部署二进制跨不过采纳鸿沟」；线索 arXiv:2609.38454 p.1-3；同源 P-0150/P-0195 未合并；无解法；不派建筑师。问题 17→18/30。cards tip `71bd19c`。

## 2026-10-01 09:00 台账

今日无派出、无退回、不派建筑师。昨夜已入账：P-0211 备案（问题 17/30；cards tip `54bd4b9`）；P-0198/M-5 CRRF T3 night 确认通过（审计 PR #76 / 仿真 tip `b0b4cf9` #73）；Top SNS/Affine 30 晚 bit-identical 无 delta。无新规范化问题可勾（最高仍 P-0211，无 P-0212+）。机制层仍空（卡未入 main，0/150）。T3 过仍 1/3。拍板仍等人。

文献 PR #27–#43 仍 DRAFT OPEN；#77 cs.AR 2026-10-01 Zephyr DRAFT OPEN（同源已入仓为 P-0211，不另勾）。P-0198 产物相关 #44–#75 等多份仍 DRAFT OPEN（卡/模型/仿真未入 main）。

## 2026-09-30 入仓备案

P-0211 入仓备案；中文题可一句概括「边缘音频去噪耳机/助听器功耗下 SNN 异构乘加+权重足迹+帧率」；线索 arXiv:2609.37711 p.1-3；同源 P-0155/P-0171/P-0196 未合并；无解法；不派建筑师。问题 16→17/30。cards tip `54bd4b9`。

## 2026-09-30 评估审计 T3 night 确认通过

评估审计 T3 night 确认通过 P-0198/M-5 CRRF（仿真 tip `b0b4cf9` / PR #73；night 审计 PR #76；先日 smoke 审计 PR #75 / tip `da294cb`；SEED=20260903；pytest 25）。仍 T3 PASS / 存活，不是 T4。Snp 15:1 仍 KILL（加严）：snp_path 17.0533 / mixed 32.5873 vs T2 1.5625（不贴作 pass）。flag_gt_30pct=2（仅两行 H-SNP-LAT 15:1）。其它钉 max |rel| 0.113；T_drain 75；f_steady 0.7727；C_dat_eff 1.000/1.488/1.585/1.633；H-COMMIT 0/12；HARD-1 49>27；gather 0.551×3。card-claim 未签；oracle_used=False 108/108；smoke `results/` / #75 未动。不开 T4。M-1 CBC / M-2 CSR / M-4 AODI 仍死。问题仍 16/30。T3 过仍 1/3。

## 2026-09-30 评估审计 T3 PASS

评估审计 T3 PASS P-0198/M-5 CRRF（仿真 tip `da294cb` / PR #73；审计 PR #75；T2 比照模型/签字 PR #63；SEED=20260903；pytest 25；未入 main）。存活，不是 T4。T_drain 75 vs 77；f_steady gather7:1 0.709 vs 0.8666；C_dat_eff 1.000/1.4185/1.5072/1.5515（无 >30% flag）。H-COMMIT 0/12；gather T/off 0.5833×3；HARD-1 24>14 True。Snp 15:1 KILL：snp_path 11.6667 / mixed 23.2222 vs T2 1.5625（flag 2/16，不把 T2 贴到 T3）；mixed 窗 3:1/7:1 亦 KILL；completions 未丢。oracle_used=False；card-claim 未签（0.583 不是 card-claim 签字）。合入 FUNNEL 作 T3 存活；不开 T4。M-1 CBC / M-2 CSR / M-4 AODI 仍死。问题仍 16/30。T3 过 0→1。

## 2026-09-30 评估审计 T3 REJECT

评估审计 T3 REJECT P-0198/M-2 CSR（仿真 PR #72；审计 PR #74；T2 比照审计 PR #68；SEED=20260903；pytest 24；未入 main）。不是 bounce。CAM Dat/retention≡0；N_cam=4；invariant_ok。spine-off HARD：gather/reduce 192 ≯ 194 → False（无优于基线）。gather/reduce r=1.0104 vs T2 0.5386（|rel| 0.876）；allreduce 1.466；alltoall op ~1.335。gate-off ≈1.0469≈T2 1.0362；high-ost f_ov=0.375 vs T2 INVALID 0.5746（诚实 delta）。30/96 flag>30%；card-claim 未签。不开 T4。不把 T2 贴到 T3。仅机制改才重开。与 M-1 CBC / M-4 AODI 同类：诚实周期未兑现主收益。M-2 死。M-5 CRRF 仍在微架构仿真 T3。问题仍 16/30。不记 T3 过线配额。

## 2026-09-30 评估审计 T3 REJECT

评估审计 T3 REJECT P-0198/M-4 AODI（仿真 PR #70；审计 PR #71；T2 比照审计 PR #69；SEED=20260903；未入 main）。不是 bounce。hole_dual=0 全行；φ→0 age_end=1。gather/reduce T_mix=1.0000（makespan 34=34）；hole_asym=43 抬 p_inj 但不缩短尾；vs T2 0.8448。alltoall 单列 T_mix 1.529 / 1.105 / 1.294（负）。HARD：gather/reduce/broadcast/allreduce 等式 True；P2P/allgather/alltoall False（尾回归）。t2_compare 8/24 flag>30%；card-claim 未签。不开 T4。不把 T2 贴到 T3。仅机制改才重开。与 M-1 CBC 同类：诚实周期未兑现主收益。M-4 死。M-2 CSR / M-5 CRRF 仍在微架构仿真 T3。问题仍 16/30。不记 T3 过线配额。

## 2026-09-30 评估审计 PR 批

评估审计 PASS P-0198/M-2 CSR T2（模型 PR #66；审计 PR #68）、M-4 AODI T2（模型 PR #65；审计 PR #69）、M-5 CRRF T2（模型 PR #63；审计 PR #67）；卡与模型未入 main。签字：M-2 CAM Dat_beats≡0 / high-ost a=8 INVALID；M-4 dual-busy hole≡0 / alltoall gain≈0；M-5 15:1 Snp KILL 1.5625>1.4。card-claim 未签。交 微架构仿真 T3。M-1 CBC T3 REJECT 死（审计 PR #64；仿真 #62）。问题仍 16/30。不记 T2 过线配额。

## 2026-09-30 扩展入仓

P-0198/M-2/M-4/M-5 扩展九卡：P-0202 M-2纵、P-0203 M-2横、P-0204 M-2基础、P-0205 M-4纵、P-0206 M-4横、P-0207 M-4基础、P-0208 M-5纵、P-0209 M-5横、P-0210 M-5基础；互不合并、不并入 P-0198；不派建筑师。cards tip `4179c7a`。

## 2026-09-30 评估审计 T3 REJECT

评估审计 T3 REJECT P-0198/M-1 CBC（仿真 PR #62；审计 PR #64；未入 main）。HARD-1 fail（无加速）；H-INJ-DOM T3=1.0 vs T2 0.7368/0.5833；dual-tenant fail_T；H-PLACE 不成立；card-claim 未签。不开 T4。不把仿真改回 T2。M-1 死。M-2/M-4/M-5 当时仍在分析模型 T2。问题仍 7/30。不记 T3 过线配额。

## 2026-09-30 微架构仿真 T3 → 评估审计

微架构仿真交付 P-0198/M-1 CBC T3 于 `sims/P-0198/M-1/`（PR #62；未入 main），交 评估审计 vs T2 #56。未签字数字不进台账。问题仍 7/30。不记 T3 过线配额。

## 2026-09-30 Jim T1-return-1

P-0198 T1-return-1 共识（PR #61）：PASS M-2 CSR、M-4 AODI、M-5 CRRF → 分析模型 T2 + 问题扩展（M-2/M-5 4/4 有条件，M-4 Sys 通过 + 3 有条件，无致命）。M-1 CBC 仍在微架构仿真 T3。卡未入 main，机制层用量不记，问题仍 7/30。不记 T1/T2 过线配额。

## 2026-09-30 评估审计 T2 PASS → 微架构仿真 T3

评估审计 PASS P-0198/M-1 CBC T2（模型 PR #54；审计 PR #56 / bc-fe019356；卡与模型未入 main）。签字：sum_ok；H-INJ-DOM 0.7368/0.5833；HARD-1 537.2>313.4；dual-tenant fail_T。card-claim 未签。交 微架构仿真 T3。问题仍 7/30。不记 T2 过线配额。

## 2026-09-30 Jim T1-return-1 T0 → T1

设计验证 T1-return-1 T0（PR #55 评审 / PR #53 卡未入 main，机制层用量不记，问题仍 7/30）：PASS_T1 全过 M-2 CSR、M-4 AODI、M-5 CRRF（T1 致命已 CLOSED）→ 评审主持重开 T1（不含 M-1）。M-1 CBC 仍在评估审计（PR #54）。不记 T0/T1 过线配额。

## 2026-09-30 分析模型 T2 → 评估审计

分析模型交付 P-0198/M-1 CBC T2 于 `models/P-0198/M-1/`（PR #54；未入 main），交 评估审计。未签字数字不进台账。问题仍 7/30。不记 T2 过线配额。

## 2026-09-30 Jim T1-return → T0

Jim Keller 按 T1 致命退回重交 M-2/M-4/M-5（PR #53；卡未入 main，机制层用量不记，问题仍 7/30），交 设计验证 重跑 Tier 0。M-1 CBC 仍在分析模型 T2。

## 2026-09-30 扩展入仓

P-0198/M-1 CBC 扩展三卡：P-0199 扇入硬上界、P-0200 单发送权1/N、P-0201 共织物+epoch；互不合并、不并入 P-0198；不派建筑师。cards tip `e2da82a`。

## 2026-09-30 Jim T1

P-0198 T1 共识（PR #52）：PASS M-1 CBC → 分析模型 T2 + 问题扩展（4/4 有条件，无致命）。REJECT 致命 M-2 CSR（latch→FIFO）、M-4 AODI（无洞）、M-5 CRRF（SYNC drain）。保守批已 0→T1。卡未入 main，机制层用量不记，问题仍 4/30。不记 T1/T2 过线配额。

## 2026-09-30 保守 T0

保守架构师 P-0198 T0（PR #45 卡与评审未入 main，机制层用量不记，问题仍 4/30）：0 张进 #review / 0→T1。REJECT M-6（FUNCTIONAL_EQUIVALENT slotted-ring/TDM）、M-8 FAIL、M-9 FAIL、M-10 FUNCTIONAL_EQUIVALENT。KNOWN_CONFIRM M-7（textbook shortest CW/CCW）— 冻作基线，不进 T1。Jim T1 仍为 M-1/M-2/M-4/M-5。

## 2026-09-30 Jim T0

Jim Keller P-0198 T0（PR #44 卡与评审未入 main，机制层用量不记，问题仍 4/30）：PASS_T1 M-1 CBC、M-2 CSR、M-4 AODI、M-5 CRRF → 交评审主持。REJECT M-3 DPH（FUNCTIONAL_EQUIVALENT）。

## 2026-09-30 派出

人确认派建筑师。P-0198 无缓冲环 NoC 上 LLM 点对点/集合通信 makespan（tests/soc_sim）。占用：保守架构师 + Jim Keller（各 5 卡）。

Jim Keller 已交 M-1..M-5（CBC/CSR/DPH/AODI/CRRF）于 PR #44，交 设计验证 做 Tier 0；T0 见上。
保守架构师已交 M-6..M-10（TDMA 注入窗 / CW-CCW 方向 / CHI 亲和 / RBRG 门控 / 年龄优先仲裁）于 PR #45，交 设计验证 做 Tier 0；T0 见上。卡与评审未入 main，机制层仍 0；问题用量不变 4/30。

## 2026-09-30 人题入仓

P-0198 无缓冲环 NoC 上 LLM 点对点/集合通信 makespan（tests/soc_sim，同源 P-0001/P-0176 未并入）；人点题探索；暂未派建筑师（等人确认）。cards tip `b46bb8d`。

## 2026-09-30 入仓

勾选并入仓（总监代推）：P-0196、P-0197。tip `d391d4f`。**不派建筑师。** 第 1 张同源 P-0178 未并入；第 2 张无同源合并。
1. P-0196 尖峰视觉 Transformer 边缘 MHSA 参数访存与片上拥堵（同源 P-0178 未并入）
2. P-0197 解释器 threaded 分发间接分支足迹巨大（无同源合并）

## 2026-09-30 09:00 台账

今日无派出、无退回、不派建筑师。凌晨已入仓 P-0196、P-0197（见上；非本次新勾选）；无新规范化问题可勾（最高仍 P-0197，无 P-0198+）。机制层仍空。拍板仍等人。

29 晚 T3 night 复扫（bc-4501c6b8）：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

文献 PR #27–#43 仍 DRAFT OPEN（新增 #43 MorphAtt / InterpLookahead）。

## 2026-09-29 入仓

勾选并入仓（总监代推）：P-0195。tip `31f4082`。**不派建筑师。** 无同源合并。
1. P-0195 DRAM 内 bit-serial 体计算竖排操作数与系统水平布局冲突（格式转换性能降约 3.9×）

## 2026-09-29 09:00 台账

今日无派出、无退回、不派建筑师。凌晨已入仓 P-0195（见上）；无新规范化问题可勾（最高仍 P-0195，无 P-0196+）。机制层仍空。拍板仍等人。

28 晚 T3 night 复扫（bc-a3eafdc3）：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

文献 PR #27–#42 仍 DRAFT OPEN。

## 2026-09-28 09:00 台账

新周开账。今日无派出、无退回、不派建筑师。无新规范化问题可勾（最高仍 P-0194，无 P-0195+）。机制层仍空。拍板仍等人。

27 晚 T3 night 复扫（bc-58714daa）：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

文献 PR #27–#41 仍 DRAFT OPEN。

## 2026-09-27 09:00 台账

今日无派出、无退回、不派建筑师。自昨日台账以来无新入仓（最高仍 P-0194）。机制层仍空。拍板仍等人。

26 晚 T3 night 复扫（bc-b3424a14）：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

文献 PR #27–#41 仍 DRAFT OPEN。

## 2026-09-26 09:00 台账

今日无派出、无退回、不派建筑师。凌晨已入仓 P-0194（见下）。机制层仍空。拍板仍等人。

25 晚 T3 night 复扫（bc-f6a78d69）：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

文献 PR #27–#41 仍 DRAFT OPEN。

## 2026-09-26 入仓

勾选并入仓（总监代推）：P-0194。tip `6103546`。**不派建筑师。** 同源 P-0173 未并入。
1. P-0194 边缘 FPGA 学习型图像压缩延迟不可由 MAC 数预测

## 周五 17:00 周报收口（2026-09-25）

- 本周机制层空转：未派建筑师；T0–T3 无新案、无新签字淘汰。
- Top 两张 T3 签字不变（SNS smoke+night；Affine smoke+night）。占用 rel_err=0 可写；BW 仍不签 0.85。
- 本周晚间 T3 night 复扫（21–24 晚）：均无数字 delta、未开 PR。
- 拍板项交人：两张 Top **T4 或停止**；是否扩配额；是否派建筑师 dig 本周备案。
- 文献 PR #27–#40 仍 DRAFT OPEN（docs only）。
- 未签字数字不进周报绝对值。约束沿用 09-04 六条（本周无新增）。

## 2026-09-25 09:00 台账

今日无派出、无退回、不派建筑师。凌晨已入仓 P-0192、P-0193（见下）。机制层仍空。拍板仍等人。

24 晚 T3 night 复扫（bc-759a481b）：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

文献 PR #27–#40 仍 DRAFT OPEN。

## 2026-09-25 入仓

勾选并入仓（总监代推）：P-0192、P-0193。tip `cca1615`。**不派建筑师。** 第 1 张同源 P-0190/P-0187/P-0180，第 2 张同源 P-0189/P-0169，均明确不并入。
1. P-0192 长 prefix KV 缓存外扩到 SSD/CXL：块接口经主机 DRAM 中转与 LLC 争用使 TTFT 慢约 1.8–3×，引擎与设备互不知下一步（同源不并入）
2. P-0193 连续视觉传感到处理串行交接钉死单帧 P99，XR <50 ms / 自动驾驶 <100 ms 在 Slack/Balanced/Overload 三区各有瓶颈（同源不并入）

## 2026-09-24 09:00 台账

今日无派出、无退回、不派建筑师。凌晨已入仓 P-0190、P-0191（见下）。机制层仍空。拍板仍等人。

23 晚 T3 night 复扫：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

## 2026-09-24 入仓

勾选并入仓（总监代推）：P-0190、P-0191。tip `69c2c86`。**不派建筑师。** 第 1 张同源已备案 HBF/agentic KV 卡（P-0187/P-0180/P-0152），明确不并入。
1. P-0190 Agentic 暂停会话冷 KV 先溢出 HBM，热集仅约 3% 容量却扛约 98% 读流量，恢复时重算或慢互连回迁伤 TBT（同源不并入）
2. P-0191 近阈脉动阵列为最慢 MAC 钉死全局时钟，约 80% 操作单周期完成却浪费正 slack，尾部约 15–20% 定周期

## 2026-09-23 09:00 台账

今日无派出、无退回、不派建筑师。凌晨已入仓 P-0186–P-0189（见下）。机制层仍空。拍板仍等人。

22 晚 T3 night 复扫：无数字 delta、未开 PR；Top 签字不变（占用 rel_err=0；BW 仍不签 0.85）。

## 2026-09-23 入仓

勾选并入仓（总监代推）：P-0186–P-0189。tip `544e286dba46bcdd01be5c7e963c6d18789fd60f`。**不派建筑师。** 第 2 张同源已备案 HBF 卡（P-0180/P-0152），不并入。
1. P-0186 弱内存 RC 排序过度强制：drain 退休停顿与投机 load squash 压制合法执行
2. P-0187 百万 token KV 在高带宽闪存上稠密全历史注意力压垮每 GPU 吞吐与平面并行（同源 HBF 已备案，不并入）
3. P-0188 边缘投机解码 draft/verify/prefill 跨算强区间，扩 tile 反把验证推回内存界
4. P-0189 VLA 两相位共跑被 CTA 分发队头阻塞，action chunk 速率腰斩难达约 50 Hz

## 2026-09-22 09:00 台账

今日无派出、无退回、不派建筑师。凌晨已入仓 P-0184、P-0185（见下）。机制层仍空。拍板仍等人。

## 2026-09-22 入仓

勾选并入仓（总监代推）：P-0184、P-0185。tip `dde7abf9aa919937d51f19e016f09aedcbebef83`。**不派建筑师。** 第 1 张同源已备案边缘 MoE 卡，不并入。
1. P-0184 STA 上 MoE 解码专家权值 DMA 钉死端到端与计算空转
2. P-0185 WAN 多路径下 BDP 位图打穿 FPGA NIC 片上状态并拉长流完成时间

## 上周 09-28~10-04 占用（已派、卡未落地）

P-0198：Jim T1 已裁（M-1 CBC T3 REJECT 死，审计 PR #64；M-2 CSR T3 REJECT 死，审计 PR #74 / 仿真 PR #72；M-4 AODI T3 REJECT 死，审计 PR #71 / 仿真 PR #70；M-5 CRRF T3 PASS / 存活，night 确认通过 审计 PR #76 / 仿真 tip `b0b4cf9` #73（smoke #75 / `da294cb`），等人定 T4、不开 T4；卡、模型与仿真未入 main）；保守批已 0→T1（T0：M-7 KNOWN_CONFIRM 冻基线）。机制仍 0/150。

## 本周已入仓备案（未派建筑师）

- P-0215（DRAM 存内计算缺行内相邻比特通路…）
- P-0216（安全关键 OoO 核异构并行检错…）
- P-0217（新 DRAM 技术改接口/控制器 N 次…）
- P-0218（翻译密集负载地址翻译占 40–45%…）
- P-0219（长向量寄存器标量语义占整宽…）
- P-0220（LLM decode 脉动阵列 M=1 复用崩塌…）

## 上周备案残留（未派入本周配额）

P-0159、P-0164–P-0214。

## Top（已签 T3；SNS/Affine 已淘汰）

- P-0105/M-4 SNS：淘汰（船长 10-09 18:27 决定停止，不开 T4）。smoke+night 通过。占用 `rel_err=0`。BW 未签 0.85。30 晚 vs main tip `c5f5b74` bit-identical；无数字 delta、未开 PR。
- P-0106/M-5 AffineRebind：淘汰（船长 10-09 18:27 决定停止，不开 T4）。smoke+night 通过。占用 `rel_err=0`。BW 未签 0.85。30 晚 vs main tip `c5f5b74` bit-identical；无数字 delta、未开 PR。
- P-0198/M-5 CRRF 路线已关闭（10-09，M-5r2 T0 KILL）：T3 smoke+night 通过（审计 #75/#76，仿真 #73 tip b0b4cf9）；card-claim 撤回；Snp 15:1 KILL。
- 21–30 晚 T3 night 复扫：21–29 无数字 delta、未开 PR；30 晚相对 main tip `c5f5b74` bit-identical、无数字 delta、未开 PR；占用 rel_err=0 不变；BW 仍不签 0.85；签字不变。

## 拍板仍等人

扩配额 · 其余备案是否派建筑师。P-0198 已派出。P-0198/M-5 CRRF 路线已关闭（10-09，M-5r2 T0 KILL），不再等人定 T4。SNS/AffineRebind 已淘汰（船长 10-09 18:27 决定停止，不开 T4），不再等人定 T4。
2026-10-09：P-0198 已拍 A+B 并行；CRRF 路线已关闭。SNS/AffineRebind 已淘汰。
放大门：已拍 A（10-09 18:21，先非单根对照）。

## T3 存活 / 通过（上周 09-28~10-04）

| ID | 类别 | 结果 |
|---|---|---|
| P-0198/M-5 CRRF | T3 PASS / 存活 | 评估审计通过（smoke 审计 PR #75 / 仿真 tip `da294cb` #73；night 确认通过 审计 PR #76 / tip `b0b4cf9`；T2 比照 #63；SEED=20260903；pytest 25）。T_drain 75 vs 77；f_steady gather7:1 0.709 vs 0.8666；C_dat_eff 1.000/1.4185/1.5072/1.5515（无 >30% flag）。H-COMMIT 0/12；gather T/off 0.5833×3；HARD-1 24>14 True。Snp 15:1 KILL：snp_path 11.6667 / mixed 23.2222 vs T2 1.5625（flag 2/16，不贴 T2）；mixed 3:1/7:1 亦 KILL；completions 未丢。oracle_used=False；card-claim 未签（勿把 0.583 当 card-claim 签字）。Night：Snp 15:1 仍 KILL（加严 17.0533 / 32.5873 vs T2 1.5625，不贴作 pass）；card-claim 未签；smoke/#75 未动。不开 T4。等人定 T4。 |

## T3 淘汰（上周 09-28~10-04）

| ID | 类别 | 原因 |
|---|---|---|
| P-0198/M-1 CBC | HARD-1 无加速 / 假设不成立 | T3 REJECT 死（审计 PR #64 / 仿真 #62）。HARD-1 fail（无加速）；H-INJ-DOM T3=1.0 vs T2 0.7368/0.5833；dual-tenant fail_T；H-PLACE 不成立；card-claim 未签。不开 T4。不把仿真改回 T2。 |
| P-0198/M-4 AODI | gather/reduce T_mix=1 / 尾回归 | T3 REJECT 死（审计 PR #71 / 仿真 #70；T2 比照 #69；SEED=20260903）。不是 bounce。hole_dual=0 全行；φ→0 age_end=1。gather/reduce T_mix=1.0000（makespan 34=34）；hole_asym=43 抬 p_inj 但不缩短尾；vs T2 0.8448。alltoall 单列 T_mix 1.529 / 1.105 / 1.294（负）。HARD：gather/reduce/broadcast/allreduce 等式 True；P2P/allgather/alltoall False（尾回归）。t2_compare 8/24 flag>30%；card-claim 未签。不开 T4。不把 T2 贴到 T3。仅机制改才重开。与 M-1 CBC 同类：诚实周期未兑现主收益。 |
| P-0198/M-2 CSR | spine-off HARD 无优于基线 / gather-reduce 无加速 | T3 REJECT 死（审计 PR #74 / 仿真 #72；T2 比照 #68；SEED=20260903；pytest 24）。不是 bounce。CAM Dat/retention≡0；N_cam=4；invariant_ok。spine-off HARD：gather/reduce 192 ≯ 194 → False（无优于基线）。gather/reduce r=1.0104 vs T2 0.5386（|rel| 0.876）；allreduce 1.466；alltoall op ~1.335。gate-off ≈1.0469≈T2 1.0362；high-ost f_ov=0.375 vs T2 INVALID 0.5746（诚实 delta）。30/96 flag>30%；card-claim 未签。不开 T4。不把 T2 贴到 T3。仅机制改才重开。与 M-1 CBC / M-4 AODI 同类：诚实周期未兑现主收益。 |
| P-0105/M-4 SNS | 淘汰（船长 10-09 18:27 决定停止，不开 T4） | 船长决定停止（T3 存活，带宽 0.85 未签，不开硬件级验证） |
| P-0106/M-5 AffineRebind | 淘汰（船长 10-09 18:27 决定停止，不开 T4） | 船长决定停止（T3 存活，带宽 0.85 未签，不开硬件级验证） |

## T2 淘汰（更早）

P-0103/M-4 CR-MRDR；P-0101/M-3；P-0103/M-1；P-0103/M-5。

## 已知方案确认（T0）

P-0102/M-2、P-0102/M-4 EXACT_MATCH。
P-0198/M-7 KNOWN_CONFIRM（textbook shortest CW/CCW；冻作基线，不进 T1）。
