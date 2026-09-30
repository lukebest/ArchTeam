# T1 综合 · P-0198/M-2 CSR（T1-return-1 · Rendezvous–Grant）

- 裁决：过线，进入 Tier 2 / #eval
- 修订：T1-return-1（机制卡 PR #53；T0 重跑 PR #55）。**取代** 首轮 T1 综合（致命缺陷退回）。
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 3 | 4 | 4 | 4 | 4 |
| 新颖性 | 4 | 3 | 4 | 4 | 4 |
| 预期收益 | 2 | 3 | 3 | 3 | 3 |
| 评估可信度 | 2 | 4 | 3 | 3 | 3 |
| 系统可组合性 | 3 | 3 | 3 | 3 | 3 |

## 一致点

- 原致命三点（RBRG Dat latch / 假 8 槽 TDM / 无超时逃逸）在修订卡上结构性拆除：`Dat_beats_held==0`、`N_cam=4` 专用、`cam_overflow_fallback` / `collect_timeout_fallback` 进 endpoints。
- 脊骨改为 Rendezvous–Grant，payload 不进桥；须 spine-off 与回退计数，禁止假完整。
- alltoall 残差与回退主导须分列；回退主导则收益区间失效。

## 分歧点

- 预期收益：Archi 2 vs 其余 3（环上 orbit 到 GRANT 的占用税）。
- 评估可信度：Archi 2 vs Sys 4（inject_gate / FORCE_FALLBACK 通知路径是否钉死）。

## 单一视角会漏的盲点

- Archi/Sim：payload「在环到 GRANT」vs 端点持有 vs 授权窗内注入须锁同一 cycle 模型（H_inject_gate）。
- Sys：FORCE_FALLBACK 需端点同步改分类，否则半集合仍等 GRANT。
- Bench：4 路 CAM 下回退若主导，makespan 区间作废。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. 硬断言 `occupancy(CAM_i, Dat_beats)==0` 与 `RBRG_reject_retention_depth==0`（Archi / Sim）。
2. `cam_overflow_fallback` 与 `collect_timeout_fallback` 作 endpoints；spine-off 消融；N_cam=4 真并发（Bench / Sim）。
3. H_inject_gate：GRANT 前禁止/门控端点注入与 orbit 语义一致；FORCE_FALLBACK 通知路径可观测（Archi / Sys）。
4. alltoall 多树/残差与回退主导场景分列，不得埋进均值（Bench）。
