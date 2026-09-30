# Prof. Bench T1 — P-0198/M-4 AODI

## 结论
有条件通过
对向偏转造 1 拍注入洞，在双方向皆忙（尤其 alltoall）时可能只是拥塞迁移；必须分报对向利用率与全集集合 makespan，忌只报注入成功率。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 同通道 CW↔CCW、无队列、AGE_MAX 有界；deflect-off 可证伪；禁跨 CHI 通道。 |
| 新颖性 | 3 | 相对 BLESS 家族为环对向注入洞特化（T0：强 INCREMENTAL）；结构差够进 T1。 |
| 预期收益 | 3 | 已坍集合 0.50–0.85× 中置信；alltoall 0.70–1.00× 低–中，双忙时洞失效。 |
| 评估可信度 | 3 | 端点仍是分流量类 makespan/collapsed；注入失败/偏转次数仅诊断。库无 NoC 包。 |
| 系统可组合性 | 3 | 与 CBC 正交（洞 vs 气泡）；多源同时偏转会把热点推到对向环。 |

## 最强反对意见
基线坍塌集合与均匀读峰值都来自「过路密度高 → 注入稀缺」。AODI 把挡路 flit 推到对向：当对向同样饱和（alltoall、双向均匀写高峰），注入洞变短或立刻被对向回流填回，makespan 改善只出现在「对向空闲」的单向扇入微基准上——那不是问题要求的全集代表负载。

## 评估层必须验证的一个假设
在满 12+2 下，对 alltoall 与已坍扇入类分别报告：首选方向注入失败率、对向方向利用率、完成事务数、makespan/collapsed。若 alltoall 上 makespan 相对基线 ≥0.95× 且对向利用率升至与首选同级，而 gather 单向上改善显著，则收益依赖「对向空闲」反例负载，不得用 gather 代理全集。deflect-off 须使集合 makespan 变差；age 分布须显示无活锁（AGE_MAX 触顶率可测）。

## 负载特征核对
- 机制依赖：首选方向被过路挡住 + 对向可接受；age < AGE_MAX；inject-hole 恰 1 拍。
- 库里：无专用包。主评测 = 均匀读/写 + broadcast/gather/reduce/allgather/allreduce/**alltoall**。禁止 decode 顶替。
- 反例：仅单向扇入；只报注入成功率不报 makespan；减箱；双方向皆忙场景缺失；跨通道偏转（应断言禁止）。
