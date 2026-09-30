# T1 综合 · P-0198/M-2 CSR（RBRG 集合脊骨）

- 裁决：未过线，退回架构师（Jim Keller）
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi **致命缺陷** · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（3/4 过线票，但有致命缺陷 → 否决）
- 分歧最大意见：Dr. Archi（512b latch/CAM 在多 flit COLLECT 下滑向隐式 highway FIFO；1–2 物理 latch 时分复用与 8 槽 CAM 自打脸）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 2 | 4 | 4 | 3 | 3 |
| 新颖性 | 3 | 3 | 4 | 4 | 3 |
| 预期收益 | 2 | 4 | 3 | 4 | 3 |
| 评估可信度 | 2 | 4 | 3 | 2 | 2 |
| 系统可组合性 | 2 | 3 | 3 | 3 | 3 |

## 一致点

- 结构命题是「集合走 RBRG 脊骨、P2P 留环」；须报 CAM→RING_P2P 回退计数与 spine-off 消融。
- alltoall 多树/分段残差不得藏进聚合均值。
- Sys/Bench/Sim 在「纸面守门成立」前提下愿意有条件放行，前提是 latch 深度硬断言。

## 分歧点

- **致命 vs 有条件**：Archi 认为多 flit 512B 信封下 COLLECT 与「每活跃 txn ≤1 flit」结构不可两全，已越过 T0 门禁；其余三人把越界留给评估层硬断言而非当场否决。
- 评估可信度：Archi/Sim 2 vs Sys 4。

## 单一视角会漏的盲点

- Archi：1–2 物理 latch 时分复用无法承载 8 项 COLLECT 折叠态；CAM=8 在 12 top 并发下高频回退与 COLLECT 占槽互喂，FSM 无超时 ⇒ 活锁闭包。
- Sys：occupancy(latch_i)∈{0,1 flit} 与 cam_overflow_fallback 必须做成硬断言，文档愿望不算过关。
- Sim：若不强制 latch 深度审计，好看数字几乎必然来自越界缓冲。

## 退回须回应的核心（摘自 Archi，不改写）

1. 在 cycle 级对 512B 多 flit reduce/allreduce（outstanding∈{256,512}，12 top）证明任意时刻每活跃 CAM 项持有 Dat 拍数 ≤1，且环上不因 RBRG 拒收累积 depth>0 滞留。
2. 取消或重写「1–2 物理 latch 时分复用 8 CAM」表述，使物理状态与 CAM 并发一致。
3. COLLECT 超时/逃逸与 CAM 溢出回退计入端点，禁止静默完整。
