# Prof. Bench T1 — P-0103/M-5 B3CSH

## 结论
有条件通过
点名 δ 的活块现在是库内必生成项；论证仍是 8GiB 线性扫描的统计覆盖，随机 gather / STREAM 是反例。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 1 拍 CSA 树，不宣称双射。 |
| 新颖性 | 4 | 不算 `G mod 9`，负载命题与 MRFI/MRDR 有差。 |
| 预期收益 | 3 | 单活块 ⇒ d0 满 Z_3 是组合事实；多块进位相关后只是期望。 |
| 评估可信度 | 3 | 翻转块可在 `team-interleave-microbench` 上打印。11×11 秩未算；无生产 gather。 |
| 系统可组合性 | 3 | select-k 禁止再 mod 3；H100 10 MC 不能复现 9 轴塌缩。 |

## 最强反对意见
活块表是为等差扫描写的。库的反例「随机地址」会掩盖相位/stride 折叠，也掩盖「切块树是否真打掉 3-adic」。C3 只在 1.5MiB 才活。把点名 δ 当唯一主评测、不跑随机与 STREAM，等于自造症状。

## 评估层必须验证的一个假设
`team-interleave-microbench` 必须打印每个 S 下 C0..C7 翻转计数（δ=3→C0，δ=9→C0+C1，δ=24→C1，δ=3072→C3），并加随机 gather 反例。若随机上 `dmc_odd` 与 `G mod 3` 互信息仍高，或 n_DMC 已满，×3 占用只属于 AP。

## 负载特征核对
- 机制依赖：文档 δ 上至少一块 3b 满跑；8GiB 使 A[32] 活。
- 库里：`team-interleave-microbench` 主；`hbm-stride-h100` 对照几何，×3 在 H100 上不是代理。
- 反例：STREAM；随机 p-chase；只跑 2 的幂；工作集进 SRAM；decode-*。
