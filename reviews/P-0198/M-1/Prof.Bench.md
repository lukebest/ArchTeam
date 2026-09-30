# Prof. Bench T1 — P-0198/M-1 CBC

## 结论
有条件通过
气泡日历对扇入坍塌类有负载前提；duty 过密会把均匀读峰值后 goodput 压成另一类坍塌，必须分流量类报 makespan/collapsed，禁止用集合均值过线。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 气泡为空槽编码非队列；类 epoch 日历 ≠ 消息级预测；calendar-off 消融可证伪。 |
| 新颖性 | 4 | bufferless 上可窃取循环气泡 + 类 epoch 密度，异于有缓冲 Bubble FC / Prevention Slot。 |
| 预期收益 | 3 | 已坍集合 0.55–0.85× 中置信；P2P 稀疏 duty 下应近中性，过密则读侧反损。 |
| 评估可信度 | 3 | 端点钉在 DV200 `tests/soc_sim` 分流量类；`/workspace/workloads` 无 NoC 集合包，不得用 decode-* 顶替。 |
| 系统可组合性 | 3 | 与 AODI/CSR 层正交可叠；P2P epoch 与集合 epoch 切换若滞后会交叉污染。 |

## 最强反对意见
收益叙事容易缩成「gather/allreduce 不再 collapsed」。问题要求点对点与全集集合（含 alltoall）分报；若只在扇入 epoch 抬 duty、却不扫均匀读峰值后 goodput，会把「制造空槽」的零和副作用藏掉——基线均匀读要约 ~5767 B/ns 后已坍至 ~2.8–3.4 TB/s，过密气泡会加重而非缓解这条曲线。

## 评估层必须验证的一个假设
在满 12+2、CHI 四环、有限 outstanding 下，集合扇入 epoch duty∈{1/4,1/2} 使已坍集合 makespan 下降的同时，P2P epoch duty≤1/8 时均匀读峰值后 goodput **不得**相对基线再掉一个数量级；固定高 duty（无 epoch 切换）对照必须单独成行。若高 duty 下均匀读 collapsed 恶化而集合改善，收益只在集合微基准上成立。calendar-off 须使已坍集合变差才可归因 CBC。

## 负载特征核对
- 机制依赖：扇入相 inject-fail 主导；P2P 近均匀与集合叠在同一 bufferless 织物；日历按拓扑/集合类 epoch 非到达预测。
- 库里：无专用 NoC 包。主评测 = 问题信封：均匀读/写 + broadcast / gather / reduce / allgather / allreduce / alltoall（`tests/soc_sim` 公开设定）。禁止 `decode-*` / `team-interleave-microbench` / STREAM 代理。
- 反例：仅均匀读或仅一类集合；单环/子集 top 减箱；固定高 duty 冒充「日历」；用平均加速或 min/mean≥0.85 宣称全类过关；broadcast（基线未坍）单独当成功故事。
