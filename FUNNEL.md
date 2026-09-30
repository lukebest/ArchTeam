# FUNNEL

周次: 2026-09-28 ~ 2026-10-04（上海）
配额: 新问题 30 → 机制 150 → 过 T0 40 → 过 T1 12 → T2 8 → T3 3
用量: 问题 16/30 · 机制 0/150 · T0 过 0/40 · T1 过 0/12 · T2 过 0/8 · T3 过 0/3

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

## 本周占用（已派、卡未落地）

P-0198：Jim T1 已裁（M-1 CBC T3 REJECT 死，审计 PR #64 / 仿真 PR #62；M-4 AODI T3 REJECT 死，审计 PR #71 / 仿真 PR #70，不开 T4、不把 T2 贴到 T3、仅机制改才重开；M-2 CSR / M-5 CRRF 仍在微架构仿真 T3；卡、模型与仿真未入 main）；保守批已 0→T1（T0：M-7 KNOWN_CONFIRM 冻基线）。机制仍 0/150。

## 本周已入仓备案（未派建筑师）

P-0195、P-0196、P-0197、P-0199、P-0200、P-0201、P-0202、P-0203、P-0204、P-0205、P-0206、P-0207、P-0208、P-0209、P-0210

## 上周备案残留（未派入本周配额）

P-0159、P-0164–P-0194。

## Top（已签 T3；等人定 T4）

- P-0105/M-4 SNS：smoke+night 通过。占用 `rel_err=0`。BW 未签 0.85。
- P-0106/M-5 AffineRebind：smoke+night 通过。占用 `rel_err=0`。BW 未签 0.85。
- 21–29 晚 T3 night 复扫已完成：无数字 delta、未开 PR；占用 rel_err=0 不变；BW 仍不签 0.85；签字不变。

## 拍板仍等人

T4/停 · 扩配额 · 其余备案是否派建筑师。P-0198 已派出。

## T3 淘汰（本周）

| ID | 类别 | 原因 |
|---|---|---|
| P-0198/M-1 CBC | HARD-1 无加速 / 假设不成立 | T3 REJECT 死（审计 PR #64 / 仿真 #62）。HARD-1 fail（无加速）；H-INJ-DOM T3=1.0 vs T2 0.7368/0.5833；dual-tenant fail_T；H-PLACE 不成立；card-claim 未签。不开 T4。不把仿真改回 T2。 |
| P-0198/M-4 AODI | gather/reduce T_mix=1 / 尾回归 | T3 REJECT 死（审计 PR #71 / 仿真 #70；T2 比照 #69；SEED=20260903）。不是 bounce。hole_dual=0 全行；φ→0 age_end=1。gather/reduce T_mix=1.0000（makespan 34=34）；hole_asym=43 抬 p_inj 但不缩短尾；vs T2 0.8448。alltoall 单列 T_mix 1.529 / 1.105 / 1.294（负）。HARD：gather/reduce/broadcast/allreduce 等式 True；P2P/allgather/alltoall False（尾回归）。t2_compare 8/24 flag>30%；card-claim 未签。不开 T4。不把 T2 贴到 T3。仅机制改才重开。与 M-1 CBC 同类：诚实周期未兑现主收益。 |

## T2 淘汰（更早）

P-0103/M-4 CR-MRDR；P-0101/M-3；P-0103/M-1；P-0103/M-5。

## 已知方案确认（T0）

P-0102/M-2、P-0102/M-4 EXACT_MATCH。
P-0198/M-7 KNOWN_CONFIRM（textbook shortest CW/CCW；冻作基线，不进 T1）。
