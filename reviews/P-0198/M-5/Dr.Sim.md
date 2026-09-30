# Dr. Sim · T1 · P-0198/M-5 · CRRF Channel–Ring Rebind

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0198/M-5.md（PR #53 修订卡，Epoch Drain + bind_mismatch + 压力驱动）
- T0: reviews/P-0198/M-5/tier0.md（PR #55 T1-return-1 重跑；判决 PASS_T1 = 纸面致命点 CLOSED，**不是** T1 方法学通过）
- 日期: 2026-09-30
- revision: T1-return-1

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | ARM_DRAIN→DRAIN→FLIP+`epoch_committed` 与失配 NACK 路径已写全，可按拍建；不是第二永久 Dat 端口，税和 duty floor 都在纸面上。 |
| 新颖性 | 4 | 评估对象是 CHI 四环 + RBRG 上带 drain 屏障的 ghost Dat 时间复用，不是 VC 重分配口号，也不是 M-2 会合或 M-4 造洞。 |
| 预期收益 | 3 | 理想有效 ≤1+duty_dat 再扣 drain/SYNC/pipe；15:1 过敏与 Snp ≤1.4× 杀假设随时能把 Dat 甜区打穿。 |
| 评估可信度 | 3 | 计数器与 duty 扫描可操作；T0 残余是跨 die 本地 sniff ≠ 全局瞬时空——若仿真把 flip 做成原子栅栏，`bind_mismatch_redirect` 会被人为打成 0。 |
| 系统可组合性 | 3 | 重绑改的是 Snp 物理环身份，CSR 的 GRANT 与 AODI 的端口表都会换底；必须靠 rebind-off 隔离归因，禁止混开后只报 Dat 均值。 |

## 最强反对意见

Epoch Drain 的本地 sniff / marker 双回**不是**全局瞬时清空。偏斜窗口里不同 die 的 4×4 绑定可以不一致；T0 close-call 已点明正确性靠 `epoch_committed` + 接受集 + mismatch redirect 兜底，而不是靠「drain 结束=全环干净」的解析假设。评估若把 flip 建成原子屏障、用软件 `COLL_EP` / runtime hint 在 Snp 空闲时再切相位、或只报 Dat 集合 makespan 而把 Snp completions 藏起来，鬼影 channel-id 与 Snp 饿死都不会进报表。`bind_mismatch_redirect` 稳态目标 0 一旦靠建模简化得到，就不是测得的正确性。duty 只跑 7:1 甜区 = 减箱；15:1 伤 Snp 必须暴露。SYNC 对齐 epoch ≠ 流量预测，谁用 SYNC「预知」集合相位谁在走私神谕。

## 评估层必须验证的一个假设

必须 **cycle 级** 建模 `ARM_DRAIN → DRAIN → FLIP + epoch_committed` 以及 SYNC 采样偏斜窗口（接收方接受 `flit.epoch_tag ∈ {local_epoch, local_epoch−1}`；**禁止**把 Dat 按 Snp 语义重解释）。接受集外失配必须走 NACK / 原 Dat 环重注入，计数 `bind_mismatch_redirect`：稳态目标 **==0**，非零必须解释；禁止静默丢、禁止永久 inject stall。同一 harness 强制 rebind-off（经典 1:1）消融 + duty 扫描 **{3:1, 7:1, 15:1}**；Snp makespan **与** Snp completions 均为 mandatory endpoints。杀假设：Snp makespan ≤1.4× rebind-off，超出 = 机制失败。Rebind 主臂仅本地 Dat util EMA / Snp pending；软件 `COLL_EP` 或 runtime hint **不得**作为正确性或过关驱动。

## 必须 cycle 级建模、不能解析近似

1. 每 die Rebind FSM 五态 IDLE / ARM_DRAIN / DRAIN / FLIP / STEADY 按拍推进；ARM_DRAIN 起停止对「即将被重绑环」的**新**注入，在途 flit 继续，禁止解析成瞬间空环。
2. DRAIN：≥1–2 环周（DRAIN marker 返回两次 **或** highway sniff 确认无 `epoch_tag==old`）；跨 die 不得假设本地 sniff = 全局清空，必须让晚节点靠后续 committed/redirect 收敛。
3. FLIP 仅在本地 DRAIN 完成后更新 4×4 one-hot（+1–2 拍 bind pipe）；`epoch_committed` 随 SYNC 绕全环后才允许新世代注入——晚节点提前按新绑定注入 = 断言失败。
4. SYNC 采样偏斜必须打进 cycle 模型（上界 ≤ 环周链路延迟）；偏斜窗内接受集 `{local, local−1}`；窗外或集外不得「运气译码」。
5. Ghost Dat 在 Snp 物理环上前进时 header channel-id 仍为 Dat + 匹配 `epoch_tag`；RBRG 按**绑定表 + epoch** 译码，禁止当 Snp 嗅探处理。
6. 接受集外 → 显式 NACK / 原 Dat 环 re-inject，`bind_mismatch_redirect++`；稳态目标 0；该路径完成时间计入当事事务，不得从分母剔除，不得静默丢。
7. 相位臂：仅本地 Dat util EMA 与有界 Snp pending 触发 duty/epoch；无 hint 时仍必须安全 drain/flip/steady。出现以 `COLL_EP` 或 runtime 类提示为正确性开关的 harness → 过关无效。
8. SYNC/DRAIN marker 走 Req 环：只对齐 epoch、传播屏障；禁止把 SYNC 当作流量预测或集合相位神谕。
9. 消融 rebind-off：Dat 侧应变差，Snp 侧作对照基线。Snp makespan **和** Snp completions 每 duty 点必报；Snp makespan >1.4× rebind-off → 杀假设成立，机制失败或必须重调 duty 后重跑，不得只改叙事。
10. duty ∈ {3:1, 7:1, 15:1} 全扫；禁止只投稿 7:1。SNP_EPOCH duty floor（例 min 1/8）必须在 DAT_EPOCH 期间给出有界 Snp 注入机会，永久 inject stall = fail。
11. 有效容量记账：≤1+duty_dat − drain 死时间 − SYNC 槽 − bind pipe；宣称「近乎双 Dat 无税」的数字作废。Dat 重集合 / 均匀读饱和与均匀写/对称负载分列，0.85 是 bar 不是 mean。
12. 包络：DV200 12+2、CHI 四环、512 B、公开 outstanding、HARD-2 destination spread；满跑点对点 + 全集集合。单环、只开 Dat、只报 Dat 均值、完美预测 = reduced-bbox ≠ full envelope。
