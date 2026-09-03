# Prof. Bench T1 — P-0101/M-3 层次正交放置

## 结论
有条件通过
DMC 分层放置在文档 AP 上可证，但收益钉死在 ≥512KiB 步长；库里没有这类 DRAM stride，S=512B 顺序流是现成反例。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 组合抽取 + 可选 96B SK，不靠 stride 神谕。 |
| 新颖性 | 3 | 分层目标（先铺 DMC）清楚，但负载侧仍是标准 AP 扫描。 |
| 预期收益 | 3 | S=2MiB 相对 mod-N 可到数十倍 DMC 占用；S=512B / 随机到达上接近 0。 |
| 评估可信度 | 2 | 负载库全是 LLM serving；无 512B–2MiB DRAM stride、无 base 分布。STREAM 91–94% 是 H100 硬件针，不是步长谱。 |
| 系统可组合性 | 3 | 只改交织，能叠；但和缓存过滤后的 miss 流是否仍呈 2MiB AP 未验证。 |

## 最强反对意见
成功标准写的是 S=2MiB 时 DMC 占用 ≈1.0。Stage A 吃 `addr[32:24]`，S=512B 顺序流这些位几乎不动，会粘在 1 个 DMC 上（T0 已点名）。512B 顺序填充才是 STREAM / 缓存行写回的常见形态；2MiB 步长扫描不是。用大步长成功掩盖小步长塌缩，就是「收益只在一个 benchmark 上出现」。

## 评估层必须验证的一个假设
在 S=512B 顺序 AP（随机 base）上，本卡的 DMC 占用是否仍 ≥0.5；若 <9/384，则必须同时给出「生产 LLC-miss 中 S≥512KiB 的比例」——库里该比例当前是未知，缺省视为 0。

## 负载特征核对
- 机制依赖：S∈{512B, 512KiB, 1MiB, 2MiB} 的顺序 AP、随机 base、8GiB 窗、K=4096@2MiB。成功靠 9 个区分位在 AP 上满变。
- 库里有没有：无。`/workspace/workloads` 只有 decode-chat / long-context / reasoning / MLPerf / prefill。无 stride、无相位、无 DMC 占用探针可校准的 trace。
- 反例：S=512B 顺序；均匀随机（mod-N 已满 384，分层无增量）；缓存命中后根本到不了 DRAM 的 2MiB 扫描。不要拿 decode 包顶上。
