# T1 综合 · P-0198/M-5 CRRF（CHI 通道–环重绑）

- 裁决：未过线，退回架构师（Jim Keller）
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi **致命缺陷** · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（3/4 过线票，但有致命缺陷 → 否决）
- 分歧最大意见：Dr. Archi（SYNC 周长偏斜 + 无 epoch 排空 ⇒ ghost Dat channel-id 破环 / 静默丢包 / stall）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 2 | 3 | 4 | 3 | 3 |
| 新颖性 | 4 | 4 | 4 | 4 | 4 |
| 预期收益 | 2 | 4 | 3 | 3 | 3 |
| 评估可信度 | 2 | 3 | 2 | 2 | 2 |
| 系统可组合性 | 2 | 2 | 3 | 3 | 2 |

## 一致点

- 新颖性四票均为 4：CHI 四环上 Snp 时分为 ghost Dat 是可发表结构叙事。
- 必须报 Snp makespan/完成数；duty∈{3:1,7:1,15:1} 扫描；rebind-off 消融；不得用 Dat 改善偷换正确性时隙。
- 评估可信度普遍偏低（中位 2）：指标易刷。

## 分歧点

- **致命 vs 有条件**：Archi 认为缺排空/偏斜协议已结构性击穿 channel-id；其余把正确性与 Snp killer 写成 T2 条件。
- 系统可组合性：Archi/Sys 2（一致性背压、运行时切 COLL_EP）vs Bench/Sim 3。

## 单一视角会漏的盲点

- Archi：偏斜窗内 NIC 与远端 RBRG epoch 视图分裂 → ghost Dat 注入 vs SNP_EPOCH 拒收。
- Bench/Sim：省略 Snp 指标或把「近 2× Dat 槽」解析上界写成测得 = 偷正确性。
- Sys：Snp 硬 stall 顶进目录/缓存流水，是系统路径而非仅 NoC 局部。

## 退回须回应的核心（摘自 Archi，不改写）

1. 规定 epoch 翻转前对环上周长在途 flit 的排空/栅栏，并 cycle 级建模 SYNC 采样偏斜。
2. 证明 ghost Dat 在 RBRG 的 channel-id 正确性；禁止静默丢包或注入口永久 stall。
3. 强制 Snp 类 makespan/完成数与 duty 扫描；软件/运行时切 COLL_EP 不得伪装成「SYNC≠预测」已洗白相位预言。
