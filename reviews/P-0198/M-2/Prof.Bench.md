# Prof. Bench T1 — P-0198/M-2 CSR

## 结论
有条件通过
脊骨把扇入挪出环面，前提是 CAM 不溢出且 alltoall 多树残差仍可报；溢出静默回退或只测 gather/allreduce 会把收益做成单形态故事。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | 静态类树 ≠ 完美预测；≤8×1-flit latch 声明非 highway 队列；满 CAM 显式 RING_P2P 回退。 |
| 新颖性 | 4 | bufferless CHI+RBRG 双路径（环 P2P / 脊骨集合），非机柜 SHARP 门级复制。 |
| 预期收益 | 3 | gather/allreduce 等 0.40–0.75× 中置信；alltoall 0.55–0.90× 低–中，多树残差争用。 |
| 评估可信度 | 3 | 必须报 CAM 溢出回退计数；库无 NoC 包，端点仍是 soc_sim 分流量类 makespan/collapsed。 |
| 系统可组合性 | 3 | P2P 留环、集合走脊骨，解耦形态；与 CBC/CRRF 可互补，但并发集合压满 CAM 时退化为环面。 |

## 最强反对意见
8-entry CAM 在多并发集合或 alltoall 分段多树下会溢出。若评估不把回退路径计入完成数/makespan，或只跑单活跃集合的 gather/reduce，脊骨看起来「永远通畅」——那是 CAM 未填满的微基准，不是 12 源 + 全集集合的代表负载。alltoall 残差若仍挤在环上，问题要求的「全集」端点会漏报。

## 评估层必须验证的一个假设
在满 DV200 与有限 outstanding 下，并发活跃集合 txn >8（或 alltoall 多树同时压 CAM）时，RING_P2P 回退计数 >0，且回退流量的 makespan/collapsed **必须单独成行**，不得并入「脊骨成功」均值。spine-off 须恢复集合坍塌。若 CAM 永不溢且只测单树 gather，增益不可外推到 alltoall。审计 latch 未扩成多 flit highway FIFO。

## 负载特征核对
- 机制依赖：集合 opcode→SPINE_TREE；P2P→RING_P2P；扇入争用从环槽挪到有界 CAM/树边；alltoall 拆多树深度假设可证伪。
- 库里：无专用包。主评测 = 均匀读/写 + 全集集合（含 alltoall）。禁止 decode / DRAM interleave 包顶替。
- 反例：仅单活跃 allreduce；忽略 CAM 溢出；用平均加速过线；减箱（单环、子集 top、仅均匀读）；假完整（未申报静默丢弃）。
