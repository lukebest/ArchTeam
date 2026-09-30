# T1 · Prof. Sys · P-0198/M-2 · CSR（T1-return-1 · Rendezvous–Grant）

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 无 Dat latch、`N_cam=4` 诚实、溢出/超时显式 RING_P2P；payload 折叠加在端点已有 RF，不在桥上偷 FIFO。 |
| 新颖性 | 3 | Rendezvous–Grant 脊骨是信封特化；系统上看仍是「NoC 内会合状态机」家族，与 SHARP 类切割在「零持拍」。 |
| 预期收益 | 3 | 扇入争用从盲目注入压到 GRANT 窗；但 4 路真并发 + 回退主导时区间自废——收益诚实、上界偏紧。 |
| 评估可信度 | 4 | `Dat_beats_held==0`、`retention_depth==0`、两回退计数、spine-off 消融均可做成硬断言。 |
| 系统可组合性 | 3 | Bufferless 契约纸面闭合；Classifier/order 表/共享 4-CAM 仍是新控制面，多租户与集合库半透明。 |

## Bufferless / 退回项审计（M-2 必答 · T1-return-1）

对照 T0 rerun PR #55：原致命点全部 CLOSED，判决 PASS_T1；本评独立，不复述轴二。

1. **无 Dat latch（强于旧「≤1 flit」）**：修订取消 RBRG 上任何 Dat 载荷 latch/fold；不变式 `∀i occupancy(CAM_i, Dat_beats)==0` 与 `RBRG_reject_retention_depth==0`。RENDZ 仅 1-flit 头/credit。**判定：CLOSED**——纸面不再滑成 flit FIFO；仿真若出现任意 CAM 持拍或 payload reject-and-orbit，记机制失败。
2. **`N_cam=4` 诚实并发**：取消「1–2 物理 latch 时分假 8」。**判定：CLOSED**——并发上限与面积叙事对齐；不得再宣称 8 路。
3. **显式 RING_P2P 回退**：CAM 满 → `cam_overflow_fallback++` 立即重分类；COLLECT 超时 → `FORCE_FALLBACK` + `collect_timeout_fallback++`；禁止静默等死/丢弃；两计数进 endpoints。**判定：CLOSED**——回退路径写进契约；评估须禁止「等 CAM 无上界」。
4. **残余系统风险（非致命）**：payload 在 GRANT 前留在 Dat 环 orbit——合法且无桥内深度，但会抬高环占用；FORCE_FALLBACK 需端点同步改分类，否则半集合仍等 GRANT。

## 最强反对

CSR 把会合状态做成 **整机共享的 4 槽 CAM**：两道并发集合就能打满；第三道立刻回退 RING_P2P，把争用送回本题要逃离的单槽环。LLM 运行时若默认「集合总走 SPINE_RENDZ」，多租户/多流下会周期性掉崖，makespan 方差爆炸。Classifier 靠 opcode→类：库用融合/非标准 opcode 或把 reduce 拆成普通写会静默走错路径。静态 order 表不看租户 die 子集——两作业绑不同 top 时，GRANT 窗序可能对错成员。GRANT flit 本身占 Dat 环 1-slot 公民：与 CBC 气泡、普通 Dat 争槽，系统上多了一类「控制公民」。

## 评估层必须验证的一个假设

满 DV200、两道并发 allreduce（或 allreduce+allgather）下：全程断言 `Dat_beats_held==0` 且 `retention_depth==0`；同时 `cam_overflow_fallback` 与 `collect_timeout_fallback` 合计占完成路径 ≤10%，且 FORCE_FALLBACK 后相关端在有界拍内改走 RING_P2P（无半集合永等 GRANT）。另查 T0 close call：cycle 模型须自洽「payload 留在 Dat 环直到 GRANT」与「端点侧持有 / 窗内注入」——禁止用环上无限 orbit 假装端点缓冲。任一失败，本卡在真实运行时并发下不可组合。

## 系统视角

- 软件可见性：对应用可透明，对集合库**半透明**——opcode 必须落在 Classifier 能认的集合类；需文档化 opcode→{RING_P2P,SPINE_RENDZ}，并禁止库绕过。回退计数 CSR 应对驱动/遥测可见。
- 编程模型：无新用户 API 亦可；但要有固件/驱动面装静态 order 表与成员掩码。NCCL 类拓扑与掩码不一致时收益归零。FORCE_FALLBACK 通知是隐式控制协议，必须进端点状态机。
- 协议/一致性：RBRG 不碰 payload，CHI Dat/Rsp 配对风险低于旧 latch 稿；GRANT 不得被误识别为普通 Dat 拍。Snp/Req 不进脊骨是对的。端点 fold 的中间值不得跨 txn_id 泄露（CAM 隔离仍在会合层）。
- 多芯片：会合钉在 RBRG，贴合 12+2；跨包/多 socket 无定义。多 bottom 若各有 RBRG，成员掩码与 CAM 配额需按桥切分，卡未写。
- 多租户：4 CAM 无租户配额；回退是唯一安全阀也是性能悬崖。与 M-1 CBC 正交（日历 vs 会合），但两者都往 Dat 环塞控制公民——叠加评估必须能单独关掉 CSR。
