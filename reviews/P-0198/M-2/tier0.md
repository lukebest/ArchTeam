# Tier 0 · P-0198/M-2 · CSR Rendezvous–Grant（T1-return-1 重跑）

- 机制卡: mechanisms/P-0198/M-2.md
- 修订: T1-return-1
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES
- 原致命点: 全部CLOSED

## 轴一 可行性
- 因果性: RENDZ 头经短 divert 置 `child_bitmap`；位图齐 → GRANT flit 占 Dat 环 1 槽；参与端按**静态集合类 order 表**在授权窗注入。fold 在端点 RF/cache，不在 RBRG。无到达时刻神谕；timeout 是逃逸不是预言。spine-off 消融要求集合 makespan 回基线量级，因果可证伪。
- 完美预测/无限带宽/零延迟: 明确禁止。order 表按 opcode 类静态；N_cam=4 真并发上界写死；溢出/超时强制 RING_P2P 并计数。GRANT 与 payload 共享每方向 1 槽，零和诚实。Classifier/CAM/GRANT 均有 1 拍量级上界，非 0 延迟魔法。
- 约束边界: **禁止** RBRG 内 Dat latch / 多拍 fold / reject-and-orbit 载荷队列——与 bufferless「无片上 flit 队列」对齐。不变式 `occupancy(CAM_i, Dat_beats)==0` 与 `retention_depth==0` 强于原「≤1 Dat 拍」。CAM 满不发明第三槽，头继续在环前进并重分类。代价：4 路并发下高 outstanding 集合易触发 `cam_overflow_fallback`——卡要求该计数进 endpoint，主导完成路径则区间失效，属可评估杀假设而非结构偷缓冲。
- 硬件开销: 4×39 b CAM ≈156 b + 每项专用 timeout/FSM；GRANT 装配与 1 注入仲裁口；2×32b 回退 CSR。面积按 4 路真并发计。明确为零：512b Dat latch、fold RAM、highway FIFO。相对 DV200 RBRG 可接受；不把「小 latch 时分假 8」写回硅片。

## 原致命点核对（编号对应 fatal_points.md · M-2 CSR）
1. **CLOSED** — 卡取消一切 RBRG Dat 载荷存储；断言 `∀i occupancy(CAM_i, Dat_beats)==0`（强于 ≤1），拒收 RENDZ 立即 RING_P2P 且 `RBRG_reject_retention_depth==0`；512 B / outstanding 256|512 / 12 top 列为仿真必绿断言。
2. **CLOSED** — 明文取消「1–2 物理 latch 时分复用 8 CAM」；`N_cam=4`，每项专用 39 b 状态 + 独立 timeout/FSM，面积按 4 路真并发。
3. **CLOSED** — 每项 `timeout` 到期 → FORCE_FALLBACK RING_P2P 计 `collect_timeout_fallback++`；CAM 满/busy → 立即重分类计 `cam_overflow_fallback++`；两计数与 makespan/completions/collapsed 并列 endpoints，禁止静默完整。

## 轴二 新颖性
- vs 文献: 不同于经典 in-network reduce（桥上/路由上折叠寄存器堆）。本卡把会合状态与 payload 路径切开，RBRG 只做 Tag CAM + GRANT，fold 退回端点——相对「网络内归约缓冲」是 DIFFERENT_APPROACH。与 MPI rendezvous / token-ring 授权同族精神，但落在 CHI 四环 + RBRG + 无缓冲单槽信封，且用显式 overflow/timeout endpoint 约束并发，不是 EXACT_MATCH 某公开 RTL。
- vs 本批修订卡（仅 M-2/M-4/M-5）: M-4 造注入洞（对向偏转）；M-5 时间复用 Snp 导线给 ghost Dat。本卡对象是**集合成员会合与授权窗**，状态在 RBRG CAM、环上多 GRANT 公民——与偏转几何、通道重绑正交，非换皮。

## 判决理由
三致命点均 CLOSED；轴一无结构偷队列/第三槽/完美预测。残余风险是 N_cam=4 下回退率可能吃掉集合收益——属评估断言（回退主导 → 不得自评通过），非未闭合结构洞。新颖性相对 in-network reduce 为 DIFFERENT_APPROACH，质量达可送 T1 的诚实脊骨设计。**PASS_T1 / 进入 Tier 1: YES**。
