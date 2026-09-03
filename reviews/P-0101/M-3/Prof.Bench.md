# Prof. Bench T1 — P-0101/M-3 层次正交放置

## 结论
有条件通过
DMC 分层在 `team-interleave-microbench` 的大步长 AP 上可证；合格项是分轴满射不是平均 BW。S=512B 顺序流仍是反例，STREAM 天花板还能把坏映射藏过去。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 组合抽取 + 可选 96B SK，不靠 stride 神谕。 |
| 新颖性 | 3 | 分层目标（先铺 DMC）清楚，负载侧仍是 TEAM-SPEC 合成 AP。 |
| 预期收益 | 3 | S=2MiB 相对 mod-N 可拉开 DMC 占用；S=512B / STREAM 上增量接近 0 甚至更差。 |
| 评估可信度 | 3 | 主评测已立 `team-interleave-microbench`。仍无生产 trace；行缓冲/DMC 时序/单 bank 峰值标未知。 |
| 系统可组合性 | 3 | 只改交织；H100 10 MC 校准不能代替 384 DMC 占用。 |

## 最强反对意见
成功标准若写成「平均 BW」或「2MiB 打满 18432」就错了（库明确不是合格项）。Stage A 吃 `addr[32:24]`，S=512B 顺序流这些位几乎不动，会粘在 1 个 DMC。顺序 STREAM 在 H100 上还能打到 91–94%，映射再差也可能接近天花板。用大步长成功掩盖小步长塌缩，就是单 benchmark 故事。

## 评估层必须验证的一个假设
在 `team-interleave-microbench` 上必须同表上报：S=2MiB 随机 base 的 DMC 分轴满射是否成立，**以及** S=512B 顺序 AP 的 DMC 占用是否塌到 ≪384。若后者塌且前者好，机制只服务大步长扫描；库缺省不把 S≥512KiB 当成生产 LLC-miss 的多数。

## 负载特征核对
- 机制依赖：S∈{512B,512KiB,1MiB,2MiB} 顺序 AP、随机 base、8GiB、K=4096@2MiB；9 个区分位满变。
- 库里：主评测 `team-interleave-microbench`（TEAM-SPEC 生成器）。公开硅 `hbm-stride-h100` 可选，不能代替。禁止 decode-*/mlperf-*。
- 反例（库强制）：顺序 STREAM 天花板；随机 p-chase；只跑 2 的幂；工作集进 L2/SRAM；任何 decode。再加卡内 S=512B 粘 DMC。
