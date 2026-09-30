# Dr. Sim · T1 · P-0198/M-1 · CBC

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0198/M-1.md
- T0: reviews/P-0198/M-1/tier0.md
- 日期: 2026-09-30

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | Bubble FSM×方向×四环 + 64×8 日历 + 1b tag/4b age + 窃取仲裁，结构边界清楚，能 cycle 建。 |
| 新颖性 | 4 | 评估对象是 bufferless 上「可窃取循环气泡 + 类 epoch 日历密度」，不是有缓冲留一空槽。 |
| 预期收益 | 3 | 0.55–0.85× 是扇入 inject-fail 主导时的区间；日历与拓扑类不对齐或 P2P duty 过密时区间上沿可失效。 |
| 评估可信度 | 3 | calendar-off / duty 扫写了，但 epoch 边界若由 harness 神谕注入，或只报注入成功率，数字会虚胖。 |
| 系统可组合性 | 4 | 不增 highway 槽、无 flit 队列；与 AODI/CSR 正交，但组合须分开消融，禁混归因。 |

## 最强反对意见

若评估把「集合类 epoch」做成对流量相位的完美对齐标签（到达时刻神谕），再报日历高 duty 下的集合 makespan，数字会看起来像 CBC 制造了空槽，实际是 harness 替机制选对了相位——calendar-off 若仍带着同一神谕相位，消融也洗不干净。

## 评估层必须验证的一个假设

在 **无消息级到达神谕**、仅按卡内静态拓扑类/软件 epoch 提示切换日历的条件下：calendar-off 相对 CBC，已坍塌集合类（gather/reduce/allreduce/allgather/alltoall）的分类 makespan **严格变差**且 collapsed 更易为 true；同时均匀读峰值后 goodput **不得**因 duty∈{1/16,1/8,1/4,1/2} 扫到高档而坍回 2.8–3.4 TB/s 量级。

## 必须 cycle 级建模、不能解析近似

1. Bubble FSM（IDLE/WATCH/EMIT/HOLD）× 每节点 × 每方向 × CHI 四环（Req/Rsp/Snp/Dat）；状态转移与环拍对齐，禁止用「平均空槽率」解析替代。
2. 64 行×8 bit 日历：高 4b duty 密度、低 4b 相位；查表→duty 判决 1 组合或 1 拍 SRAM，禁止把预期收益 Amdahl 式直接写成测得 makespan。
3. Bubble tag 1b + age 4b：每跳 age++；age≥15 强制退化为可注入空槽；须探针气泡聚团（同方向连续 bubble 长度分布）。
4. 注入 vs 气泡窃取仲裁：优先级 collective inject > P2P inject > bubble keep；同拍组合；须分列「窃取成功 / 非气泡空槽注入 / 注入失败」计数，禁止只用单环注入成功率代理 makespan。
5. W=8 未见气泡才强制造泡的窗口；P2P epoch duty∈{1/16,1/8} 与扇入 epoch∈{1/4,1/2} **分列**，禁止平均成一个「CBC 加速比」。
6. 消融：calendar-off；固定 duty=0；固定高 duty——三者与满 CBC 对照；仅当 off/0 使坍塌集合变差才可归因。
7. 基线：DV200 `tests/soc_sim` 12+2、512B、读 outstanding 512 / 写 256、额外流控关；满包络跑均匀读/写 + broadcast/gather/reduce/allgather/allreduce/alltoall；reduced-bbox（单环、子集 top、仅均匀读）单独不足。
8. Warm-up：气泡需至少一圈环传播才进入稳态；丢弃前 K 圈（K≥环周跳数）后再采 makespan/goodput；禁止冷启动首圈空槽当收益。
9. 端点分列：每流量类 makespan、完成事务数、collapsed；均匀读峰值后 goodput；**禁止**用各类平均加速或 min/mean≥0.85 均值叙述过关；0.85 若出现仅为约束条，不是测得均值。
