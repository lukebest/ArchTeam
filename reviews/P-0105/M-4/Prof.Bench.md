# Prof. Bench T1 — P-0105/M-4 SNS

## 结论
有条件通过
库现在强制扫 base 相位 + bit[21,33)，跨 base 不变性可测；huge-page 对齐仍可能把 1D 钉在好相位。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 剪切 + 256B ROM + fold384，1 拍。 |
| 新颖性 | 4 | 负载命题是相位/base，和 P-0103 的因子 3 正交。 |
| 预期收益 | 3 | 坏相位 2MiB 上相对 1D 可从 3 DMC 拉到 384；好相位 / STREAM 上增量小。 |
| 评估可信度 | 3 | base 相位已是 `team-interleave-microbench` 必扫项。生产 huge page 分布仍无。卡内 CV≈0.044 不得当已测。 |
| 系统可组合性 | 3 | 消融（去剪切 / 去 S-box）可组合；OS 对齐不在生成器默认里。 |

## 最强反对意见
合格是 base 不变 + 分轴满射，不是平均 BW。生成器扫 512B 粒度相位，但生产 huge page 把 base 钉在 2MiB 对齐。若钉住的是 1D 好相位，SNS 的跨 base 故事对生产为 0。STREAM 天花板同样能藏坏相位。

## 评估层必须验证的一个假设
`team-interleave-microbench` 的 base 扫描必须拆两套：① 库默认 512B 粒度相位；② 仅 2MiB 对齐。若 ② 上 `G mod 384` 已分轴满射且跨 base 相对差 <5%，SNS 收益不在生产对齐下出现。2MiB 打满 18432 不是合格项。

## 负载特征核对
- 机制依赖：S∈{2MiB,1MiB,512KB,4608B,512B}；base/phase；bit[21,33)；partial-good 1/16。
- 库里：主评测含 base 相位 + bit[21,33)。禁止 decode。H100 校准不能代替 TEAM-SPEC 384 桶 discrepancy。
- 反例：huge-page 对齐；去剪切只留 S-box；STREAM；随机 p-chase；只跑 2 的幂（漏 4608B）。
