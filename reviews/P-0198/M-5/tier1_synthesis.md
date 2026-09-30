# T1 综合 · P-0198/M-5 CRRF（T1-return-1）

- 裁决：过线，进入 Tier 2 / #eval
- 修订：T1-return-1（机制卡 PR #53；T0 重跑 PR #55）。**取代** 首轮 T1 综合（致命缺陷退回）。
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 3 | 3 | 4 | 4 | 3 |
| 新颖性 | 4 | 3 | 4 | 4 | 4 |
| 预期收益 | 3 | 3 | 3 | 3 | 3 |
| 评估可信度 | 4 | 4 | 3 | 3 | 3 |
| 系统可组合性 | 3 | 3 | 3 | 3 | 3 |

## 一致点

- Epoch Drain + skew 接受集 + `bind_mismatch_redirect` 堵住静默丢包/永久 stall；软件 COLL_EP 主臂已拔。
- 必须报 Snp makespan/completions；duty∈{3:1,7:1,15:1}；Snp≤1.4× 为杀假设；稳态 redirect≈0。
- 时间复用 ≠ 永久第二 Dat 槽。

## 分歧点

- 新颖性：Sys 3 vs Archi/Bench/Sim 4。
- 评估可信度：Archi/Sys 4 vs Bench/Sim 3（指标是否真跑）。

## 单一视角会漏的盲点

- Archi/Sys：本地 sniff ≠ 全局空；`epoch_committed` 须为全员 drain+flip 屏障。
- Sim：原子 flip / 只报 Dat 会藏 mismatch 与 Snp 退化。
- Bench：drain 税与 Snp floor 是否仍让 Dat 净赢；15:1 必扫。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. Epoch Drain/skew cycle 模型；全员 `epoch_committed` 屏障后再允新世代注入（Archi / Sys）。
2. `bind_mismatch_redirect` 稳态 ≈0；有界 mismatch staging，禁止静默丢与永久 stall（Archi / Sim）。
3. duty∈{3:1,7:1,15:1} + rebind-off；Snp makespan/completions 与 1.4× 杀假设同表（Bench / Sim）。
4. 相位仅本地压力计数；runtime hint 至多 advisory（卡 §0 / Sys）。
