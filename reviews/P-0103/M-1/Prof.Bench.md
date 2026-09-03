# Prof. Bench T1 — P-0103/M-1 MRFI

## 结论
有条件通过
Feistel 注入在库强制的 `3|δ` 合成 AP 上代数成立；H100 10 MC 不是 ×3 代理，只跑 2 的幂会漏掉整张卡。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 纯函数，1–2 拍，GOOD_MAP 1R 冲突已点名。 |
| 新颖性 | 4 | 打冻结奇数环，不是又一张 XOR。 |
| 预期收益 | 3 | `S=3·2^k` 上 n_DMC 128→384；2 幂 stride 上相对 XOR mapper 增量应为 0。 |
| 评估可信度 | 3 | 含 3/9 的 stride 已写入 `team-interleave-microbench`。无生产到达；退役率分布未知。 |
| 系统可组合性 | 3 | 100% good 可跳过 SRAM；1/3 图案 XOR 重试再相关仍在。 |

## 最强反对意见
`X_rel=3` 只在 `gcd(δ,384)` 吃掉因子 3 时出现。库现在**会生成**这些步长，但它们仍是 TEAM-SPEC 微基准，不是生产 miss 谱。H100 是 10×512b MC、无 9 轴，×3 stride 在那台上不痛。只跑 2 的幂（GF(2) 友好）会让 MRFI 看起来无增量。STREAM 天花板还能让坏映射过关。

## 评估层必须验证的一个假设
主评测必须含因子 3/9 的 stride，并与「只跑 2 的幂」对照同表。若 2 幂上相对 XOR mapper 的 n_DMC 增益 ≠ 0，机制伤了 2-adic 轴；若含 3 的步长上增益 = 0，Feistel 没离开子群。禁止用 `hbm-stride-h100` 的 ×3 档代替这条。

## 负载特征核对
- 机制依赖：S 含 1536B/3KiB/4608B/1.5MiB；partial-good 0/6/12% + 1/3 图案；8GiB；outstanding 128。
- 库里：`team-interleave-microbench` 主评测（必须含 3 和 9）。`hbm-stride-h100` 只作几何对照。禁止 decode。
- 反例：只跑 2 的幂；STREAM 天花板；随机 p-chase；工作集进 SRAM；1.5MiB 下 `p_wide` 6b 熵；1/3 图案再锁坏 trit。
