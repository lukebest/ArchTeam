# Prof. Bench T1 — P-0105/M-4 SNS

## 结论
有条件通过
跨 base 不变性只在「固定 S 的 AP + 均匀扫 base」上有定义；生产 huge page 把相位钉死，1D 坏相位可能很少出现。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 剪切 + 256B ROM + fold384，1 拍。ROM 必须按整数多项式装填。 |
| 新颖性 | 4 | 负载命题是相位/base，不是因子 3，和 P-0103 正交。 |
| 预期收益 | 3 | 相对 1D 在「坏相位 2MiB」上占用从 3 DMC 拉到 384；好相位 / 随机上增量小。 |
| 评估可信度 | 2 | 卡内已写 maxload=11、CV≈0.044，像预先跑过合成器。库无 base 分布。 |
| 系统可组合性 | 3 | 消融（去剪切 / 去 S-box）可组合；OS 对齐不在模型里。 |

## 最强反对意见
人钉的症状是 same-phase vs wrong-phase。负载库没有 start-address 分布。Linux/HBM 分配大量 2MiB huge page 时，base 不是均匀扫 `0..4K-512`，而是 2MiB 对齐——相位被 OS 钉在同一类。若钉住的恰好是 1D 的好相位，SNS 的跨 base 故事对生产为 0；卡内「扫 8 个 base」是实验室设计，不是到达过程。

## 评估层必须验证的一个假设
主评测必须拆两套 base：① 卡内均匀扫 `0..4K-512`；② 仅 2MiB 对齐（模拟 huge page）。若 ② 上 `G mod 384` 的 n_DMC 已 ≥300 且跨 base 相对差 <5%，则 SNS 的收益不在生产对齐下出现，只能当压力测试。

## 负载特征核对
- 机制依赖：S∈{2MiB, 1MiB, 512KB, 4608B, 512B}；base/phase；4096 点窗；partial-good 1/16 bank。
- 库里有没有：无 base 分布、无 2MiB 相位、无 4608B。decode-long-context 的 12k ISL 不是 DRAM AP 相位。
- 反例：huge-page 对齐 base；去剪切只留 S-box（S=2MiB 应塌）；S=512B 顺序（剪切对偶应仍走，必须测，不能只报 2MiB）；均匀随机。
