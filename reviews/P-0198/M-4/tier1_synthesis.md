# T1 综合 · P-0198/M-4 AODI（T1-return-1）

- 裁决：过线，进入 Tier 2 / #eval
- 修订：T1-return-1（机制卡 PR #53；T0 重跑 PR #55）。**取代** 首轮 T1 综合（致命缺陷退回）。
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys **通过** · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 3 | 4 | 4 | 4 | 4 |
| 新颖性 | 2 | 3 | 3 | 3 | 3 |
| 预期收益 | 3 | 3 | 3 | 3 | 3 |
| 评估可信度 | 4 | 4 | 3 | 3 | 3 |
| 系统可组合性 | 3 | 4 | 3 | 3 | 3 |

## 一致点

- 双忙真值表钉死 `inject-hole≡0`；增益窗口改写为不对称占用；alltoall 双忙饱和预期 ≈0。
- Rejoin + 逐包 φ 取代 Σage 假进度；须 deflect-off 与对向 util / 完成数，禁只报 inject-success。
- 新颖性中位 3（偏转家族 FE/INCREMENTAL 近亲仍成立）。

## 分歧点

- 新颖性：Archi 2 vs 其余 3。
- Sys 给「通过」；Archi/Bench/Sim 坚持「有条件」（φ 在首选向满时的活锁、异拍偷槽）。

## 单一视角会漏的盲点

- Archi：首选向长期满时 Rejoin 无抢占 → φ 冻结。
- Sim：swap/Rejoin/异拍 hole 组合可偷第三槽；Σage / inject-success 会洗掉双忙≈0。
- Bench：分桶证明增益只在单侧空闲。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. 双忙周期硬断言 `inject-hole==0`；违例=机制失败（全体）。
2. deflect-off 分列；对向利用率与完成数；分桶 hole（不对称 vs 双忙）（Bench / Sim）。
3. 逐包 φ 有界下降：首选向满时不得活锁；AGE_MAX 后仅合法 Rejoin（Archi / Sim）。
4. alltoall 双忙饱和单独成行，不得用聚合 makespan 宣称 0.50–0.85×（Bench）。
