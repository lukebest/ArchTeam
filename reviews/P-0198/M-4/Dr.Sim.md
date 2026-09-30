# Dr. Sim · T1 · P-0198/M-4 · AODI

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0198/M-4.md
- T0: reviews/P-0198/M-4/tier0.md
- 日期: 2026-09-30

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 同通道 CW↔CCW 2×2 + age 4b + AGE_MAX + 1 拍 inject-hole，深度 0，能严格 cycle 建。 |
| 新颖性 | 3 | 相对 BLESS 族是环对向注入洞特化；可发表差在对象，不是全新偏转理论。 |
| 预期收益 | 3 | 扇入相 0.50–0.85× 有几何空间；双方向皆忙（alltoall）时洞失效，区间上沿脆弱。 |
| 评估可信度 | 3 | deflect-off 写了，但对向拥塞迁移、age 分布与跨通道禁令若只报聚合 makespan，杀手会被平均洗掉。 |
| 系统可组合性 | 4 | 无日历、无永久方向绑定；与 CBC/CSR 正交，但组合须各自 off 消融，禁混功。 |

## 最强反对意见

首选方向注入成功率上升、聚合 makespan 下降的同时，对向环利用率与对向完成延迟可能被迁拥堵垮——若 harness 只报「注入失败↓ + 总 makespan」，AODI 会看起来有效，而机制只是把争用搬到对面。

## 评估层必须验证的一个假设

在 **禁止跨 CHI 通道偏转**（仅 Dat-CW↔Dat-CCW 等同通道方向对）且 AGE_MAX 默认 8 生效的条件下：deflect-off 使已坍塌集合类注入失败计数上升且分类 makespan 变差；同时 **对向方向** 利用率、对向相关完成延迟/事务数必须分列上报——若对向指标恶化超过首选方向收益，不得把聚合 makespan 改善单归因于 AODI 为「净赢」。

## 必须 cycle 级建模、不能解析近似

1. 每节点 × CHI 四通道方向对的 2×2 deflect crossbar：deflect_enable、两入两出；深度 0；同拍或 +1 拍打拍——禁止解析成「等效第三槽」。
2. Age 头字段 4b：每次被偏转 age++；AGE_MAX 比较器（默认可配 8）；age≥MAX 禁止再偏转、必须直通；须直方图 age 分布与活锁探针（全局 age 和是否有界消耗）。
3. Inject-hole latch 1b：有效窗 **恰 1 周期**，与偏转拍对齐；禁止把 hole 当成可持续空槽预约。
4. 优先级：仅当本地有 pending 注入且首选方向被过路占用时使能偏转；过路直通 vs 偏转 vs 注入三路仲裁同拍可观测。
5. 断言：零跨通道偏转（Req/Rsp/Snp/Dat 互不横跨）；违例 run 作废。
6. 消融 deflect-off（纯 fail-wait）：注入失败↑、集合 makespan 恶化才可归因；与满 AODI 对照。
7. 诊断分列（非过关代理）：注入失败计数、偏转次数、对向利用率、对向完成延迟；**禁止**只用注入成功率或平均 hop 代理端到端 makespan。
8. 流量分列：均匀读/写 + broadcast/gather/reduce/allgather/allreduce/alltoall；alltoall 与双忙相单独成列，不得并进扇入均值。
9. 均匀读峰值后 goodput：须报是否仍坍至 2.8–3.4 TB/s 量级；偏转扰动写向时均匀写 makespan 分列。
10. 基线：DV200 12+2、512B、outstanding 512/256、额外 FC 关；满包络；Warm-up 至 age 分布稳态后再采；禁止把「绕行 ≥1 跳」的解析下界当成测得额外代价。
