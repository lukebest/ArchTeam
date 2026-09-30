# Dr. Sim · T1 · P-0198/M-2 · CSR

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0198/M-2.md
- T0: reviews/P-0198/M-2/tier0.md
- 日期: 2026-09-30

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 3 | 8-CAM + 1-flit latch + 显式 RING_P2P 回退可建，但 latch 极易在实现里滑成多 flit FIFO，边界脆弱。 |
| 新颖性 | 4 | 评估对象是 bufferless CHI+RBRG 上「集合走脊骨 / P2P 留环」双路径，不是再贴一张通用 SHARP。 |
| 预期收益 | 4 | 扇入从 Ω(N) 环争用挪到树深 O(log 12) 时集合 makespan 区间 0.40–0.75× 有物理空间；alltoall 残差另列。 |
| 评估可信度 | 2 | 若不强制 latch 深度审计、CAM 溢出回退计数与 spine-off，好看数字几乎必然来自越界缓冲或静默完整。 |
| 系统可组合性 | 3 | P2P 近中性可共存；但 RBRG 集中状态与 CBC/AODI 叠用时 attribution 易糊，须独立 spine-off。 |

## 最强反对意见

评估若把 512b Partial-reduce latch 实现成（或默许）每 txn 多拍堆积的 flit FIFO / 端点无限排队进 RBRG，脊骨 makespan 会大幅好看，而机制已滑出 bufferless「每活跃 CAM 项 ≤1 flit」信封——数字归因 CSR，失败模式却是「latch 滑成 FIFO」。

## 评估层必须验证的一个假设

在 **每活跃 CAM 项物理暂存 ≤1×512b、禁止 highway/端点把 latch 扩成深度>1 的 flit 队列** 的硬约束下：spine-off（集合强制回环）使 gather/reduce/allreduce/allgather **恢复 collapsed=true 且 makespan 显著变差**；同时必须逐 run 报告 CAM 溢出→RING_P2P 回退次数（>0 时不得宣称「脊骨完整服务」），回退路径完成数计入分母，禁止静默丢弃。

## 必须 cycle 级建模、不能解析近似

1. Endpoint Classifier 32×2 ROM：opcode→{RING_P2P, SPINE_TREE}；1 组合/1 拍；普通读写不得误入脊骨。
2. RBRG Tag CAM：8 项 ×（txn_id 假设 16b + child bitmap ≤12b + 态 2b）；每拍匹配/分配；**满 CAM 新集合 txn 显式回退 RING_P2P**，溢出计数强制进指标表。
3. Partial-reduce latch：每活跃项 **恰 1 flit 宽 512b**；审计探针 `latch_depth_max`、`flits_buffered_per_txn`——任一 >1 即判定机制越界，该 run 作废，不得当 CSR 结果。
4. FSM 四态 IDLE/COLLECT/REDUCE/DISPATCH × 每活跃 CAM 槽；COLLECT 等待绑定有限 outstanding 子到达，禁止无限带宽「子瞬时齐」。
5. 静态树边表：broadcast/fan-out 根、gather/reduce 汇、allreduce=reduce+broadcast spine；树深与经 ≤2 bottom 的跳数 **实测分列**，禁止把 O(log N) 解析上界写成测得跳数。
6. alltoall / allgather 多树或分段脊骨：残差环争用与 CAM 并发冲突 **单独成列**，不得并进 allreduce 均值。
7. 消融 spine-off：集合全回环 → 应重现基线坍塌；P2P-only 路径 makespan 应 ≈ 基线（±噪声）；两消融缺一不可归因。
8. CHI 四环交互：集合载荷主压 Dat；Req/Rsp 完成路径；Snp 不强制进脊骨——分通道占用探针，禁用「总 goodput」洗 Dat 扇入。
9. 基线与包络：DV200 12+2、512B、outstanding 512/256、额外 FC 关；满跑均匀读/写 + 全集集合；单环/子集/仅均匀读/完美预测减箱不足。
10. Warm-up：丢弃 CAM/树建立前瞬态；稳态后采分流量类 makespan、完成事务数、collapsed、CAM 溢出回退计数；禁止解析 Amdahl 扇入式直接当测得加速。
