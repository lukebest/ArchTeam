# Prof. Bench T1 — P-0198/M-2 CSR（T1-return-1）

## 结论
有条件通过
T0-rerun（PR #55）致命点全 CLOSED；Rendezvous–Grant 取消 Dat latch、把 `cam_overflow_fallback` / `collect_timeout_fallback` 与 alltoall 残差升成 endpoints，堵住了「假完整脊骨」叙事；收益仍取决于 4 路 CAM 在全集集合下回退是否主导——回退主导则区间失效。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | `Dat_beats_held≡0` 可断言；溢出/超时立即 RING_P2P；无 reject-and-orbit 滞留。 |
| 新颖性 | 4 | 会合+GRANT 与 CBC 空槽日历切割清楚；非 datapath reduce 栈换皮。 |
| 预期收益 | 3 | gather 系 0.45–0.80× 中置信；alltoall 0.60–0.95× + 残差分列；回退主导则失效。 |
| 评估可信度 | 3 | 两回退计数与 alltoall 残差已钉进评估计划；库仍无 NoC 包，端点仍是 soc_sim 分流量类。 |
| 系统可组合性 | 3 | P2P 留环、集合走 GRANT 窗；N_cam=4 并发诚实，压满即回环。 |

## 最强反对意见
N_cam 从伪装 8 改成诚实 4，溢出在多并发集合 / alltoall 分段 GRANT 下更易触发。若报表把回退路径并进「脊骨成功」均值、或不把 alltoall 残差环争用分桶，仍会把「CAM 未填满的单树 gather」当成全集代表负载——修订已要求分列，评估层不得偷懒。

## 评估层必须验证的一个假设
满 12+2、512 B、outstanding 256|512 下，并发活跃集合或 alltoall 多树压 CAM 时：`cam_overflow_fallback` 与 `collect_timeout_fallback` 必须与 makespan/completions/collapsed **同表分列**；回退流量 makespan **不得**并入 GRANT 成功桶。spine-off 须回到基线坍塌量级。若两回退计数主导完成路径，不得宣称区间成立。断言全程 `occupancy(CAM_i, Dat_beats)==0`。 cycle 模型须与「payload 不进 RBRG、端点持有/GRANT 窗内注入」一致，禁止把环上 orbit 做成隐式深度。

## 负载特征核对
- 机制依赖：集合 opcode→SPINE_RENDZ；payload 永不进桥；GRANT 窗内有序占用环；溢出/超时显式 RING_P2P。
- 库里：无专用 NoC 包。主评测 = 均匀读/写 + broadcast/gather/reduce/allgather/allreduce/alltoall（`tests/soc_sim`）。禁止 decode / DRAM interleave 顶替。
- 反例：仅单活跃 allreduce；隐藏回退计数；alltoall 只报均值；减箱；任何 Dat latch/FIFO 复活。
