# T1 · Prof. Sys · P-0198/M-2 · CSR

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 静态类树 + 有界 CAM/latch；COLLECT 绑有限 outstanding，不是无限带宽。 |
| 新颖性 | 3 | 相对 SHARP/FANIN 是信封特化；系统上看仍是「NoC 内集合引擎」家族。 |
| 预期收益 | 4 | 扇入从 Ω(N) 环槽挪到脊骨，直接打集合 makespan；P2P 近中性写得清楚。 |
| 评估可信度 | 4 | spine-off、CAM 溢出回退计数、alltoall 多树残差都可测。 |
| 系统可组合性 | 3 | Classifier+树边表是新控制面；latch 守门写明了，但多租户抢 8 CAM 未闭合。 |

## Bufferless 守门审计（M-2 必答）

1. **Partial-reduce latch**：卡写 512b × ≤8 CAM 项，上界 = 1 flit/活跃 txn，声明非 highway FIFO。**通过条件**：实现与模型必须强制 `occupancy(latch_i) ∈ {0,1 flit}`，禁止把同一 CAM 项背后挂 2+ flit 深的归约窗或子 flit 拼接队列。时分复用「1–2 个物理 latch」可以，但同一时刻仍 ≤1 flit/项。T1 仿真若出现 `depth>1` 或按字节流式累加缓冲，记 **越界**，本卡作废为 buffered reduce。
2. **RING_P2P 回退**：CAM 满 → 显式降级环路径，禁止静默丢弃（HARD-4）。**通过条件**：指标必须含 `cam_overflow_fallback` 计数；回退事务走完整 RING_P2P 完成，不得 NACK 丢弃。若回退被实现成「等 CAM」而无上界，则滑成隐式队列——同样越界。
3. **结论**：纸面守门成立；系统可组合性是否过关取决于评估是否把上述两条做成硬断言，而不是文档愿望。

## 最强反对

CSR 在 RBRG 上放了一台共享集合机：8 CAM + latch 是**整机稀缺资源**，不是 per-tenant。两个并发 allreduce 就能打满 CAM；第三个溢出回退环面——回退瞬间把争用送回单槽环，正是本题要逃离的状态。LLM 运行时若默认「硬件集合总是 SPINE_TREE」，在多租户/多流并发下会周期性掉回 RING_P2P，makespan 方差爆炸。Classifier 靠 opcode ROM：库若用非标准/融合 opcode，或把 reduce 拆成普通写，会静默走错路径。树边表按集合类静态，不看租户放置——12 top 上两作业绑不同 die 子集时，静态树可能把流量送进无关 RBRG。

## 评估层必须验证的一个假设

满 DV200、两道并发 allreduce（或 allreduce+allgather）下：`cam_overflow_fallback` 占比 ≤10%，且回退事务的 makespan 有上界（不得无限等 CAM）；同时 cycle 级断言全程无 `latch_depth>1`。任一失败，本卡在真实运行时并发下不可组合。

## 系统视角

- 软件可见性：端点 Classifier 对应用可透明，但对集合库**半透明**——opcode 必须落在 32×2 ROM 能认的集合类。需要文档化 opcode→{RING_P2P,SPINE_TREE} 表，并禁止库绕过。
- 编程模型：无新用户 API 亦可工作；但要有「注册树边表 / 集合类」的固件或驱动面。NCCL 类拓扑与静态树不一致时，收益归零甚至变差。
- 协议/一致性：归约在 Dat 脊骨上做——必须保证 CHI 事务完成语义与 Rsp 配对不被 latch 打乱；Snp 默认不进脊骨是对的。Partial-reduce 可见中间值不得泄露给错误 txn_id（CAM 隔离）。
- 多芯片：树以 bottom/RBRG 为根，贴合 12+2。跨包/多 socket 无定义；本信封内可组合。
- 多租户：CAM/latch 共享；无租户配额。回退是唯一安全阀，也是性能悬崖。
