# Prof. Bench T1 — P-0106/M-5 AffineRebind

## 结论
有条件通过
库规定 n=40 → L=32+本 DMC spare、禁跨 DMC steal，重绑命题可测；退役率分布仍标未知，100% good 是反例。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | repair 固件重绑，运行 2 拍仿射 + kth-one。 |
| 新颖性 | 3 | 译码器是 M-2；新命题是 n_live 因子分解。 |
| 预期收益 | 3 | n=40 上相对仍 mod 48 可拉类数；100% good 增益必须 ≈0。 |
| 评估可信度 | 3 | partial-good 规则已写入主评测（n=40/L=32）。公开退役率分布没有，只扫 T0 规则。 |
| 系统可组合性 | 3 | 不跨 DMC。H100 row remap 是坏行替换，不是 per-DMC bank LUT。 |

## 最强反对意见
3-adic 故事需要「丢掉因子 3」的 mask。库只给 n=40 一条规则，没有生产退役分布。HBM 修的是 row/column/颗粒，不是 `bank_in % 3` 陪集屠杀。均匀随机退役时收益只剩「mod n vs mod 48」，2 幂上选 α 不改变 gcd（T0 已写）。把 1/3 图案当主评测仍是自造症状。

## 评估层必须验证的一个假设
`team-interleave-microbench` 必须三组 mask 同表：LUT 满好（恒等）、n=40 均匀、1/3 残类偏退役（若生成器能做）。满好上相对 M-2 增益 ≈0；收益记在「模数跟随 n」的 gcd 表，不记在「选了哪个 α」。禁止用 H100 row remap 当这条的硅校准。

## 负载特征核对
- 机制依赖：退役 6.25/12.5/25%；均匀 vs 3 残类偏退役；文档 S 含 3。
- 库里：n=40 → L=32+spare，禁跨 DMC。退役率分布 = 未知。行缓冲/DMC 时序/单 bank 峰值 = 未知。
- 反例：100% good；STREAM 天花板；H100 row remap；decode-*；运行中持续退役（卡是一次 fence+drain）。
