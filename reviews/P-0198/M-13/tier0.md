# Tier 0 · P-0198/M-13 · WSOR Wave-Sunset Occupancy Reclaim

- 机制卡: mechanisms/P-0198/M-13.md（PR #84 head `e6a5e2b`）
- 判决: REJECT
- 可行性: FAIL
- 新颖性: DIFFERENT_APPROACH
- 质量: FLAWED
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc `main@63163ca`

## 卡摘要
flit 头加 4b `wave_id`；dest 按 posted expected-count 计数，收齐后在 Req 上发 SUNSET marker；各节点看到 marker 后把 highway 上 `wave_id` 落在过期窗（落后 1–2 波）的 payload 同拍改 empty。主张：多步 decode 中「上一波已完成但仍在绕的公民」挡下一波，回收后 `T_seq` 下降；单波 `r≈1`。

## 轴一 可行性
- 因果性: 失败，回收对象在信封内为空集。dest `recv≥expected` 的含义是本波每一拍都已 eject。无损 CHI 织物里每拍唯一，eject 即离环；因此「本波已 complete 但仍在环上」的 flit 只能是重复拍或多余拷贝。卡列的四个来源逐一核对：
  1. 晚到重复拍：基线无重复发送路径。CHI Dat 无链路级重传；Req 的 RetryAck/PCrdGrant 重发的是新 Req，不是旧 Dat 残留。
  2. 未杀干净的多播残段：库内 Dat 多播在最后一个目标处已同拍 `valid=false`（`src/TCsHighWay.cpp:397-410`，`m_tgtCs==0` 分支），不存在残段。
  3. RBRG 换路残留：桥接是移交，不复制。
  4. NACK 重注入：基线不存在 NACK；NACK 是 M-5 CRRF 失配路径才引入的，且属 ghost 世代问题。
  所以 `C_t`（波间残留占用）在 tests/soc_sim 上为 0。多步 decode 中真正跨波的占用是上一波**尚未完成**的 flit，那是合法在途数据，WSOR 按规则不碰它（`stale` 只对 complete 后的波）。机制在正确实现下是 no-op。
- 安全性: 反过来，任何一次误回收（模 16 绕回、SUNSET 与 expected 偏斜、expected 软件填错）都是把合法 payload 改成 empty，即在无缓冲环上丢数据。卡给的兜底是 Rsp NACK + 源重注入，但源 NI 在 flit 上环后不保留副本（CHI 无 Dat 重传缓冲），重注入需要新增源端重传缓冲，这正是信封禁止的片上 flit 队列。没有合法 sink。
- 死锁/活锁: SUNSET 在 Req 上有界重试，本身无死锁；但 `false_reclaim` 路径若源无副本，事务永不完成，等价于挂死。
- 完美预测: expected-count 由软件 posted，不是神谕；但它必须精确等于实际拍数，错一拍就是丢包或永不 sunset。

## RTL / 仿真器改动核查
- `wave_id` 头字段、`convert_to_empty`、SUNSET 解码都在库内 highway 层（`src/TCsHighWay.cpp` slot 处理、`include/chi_ring_common.h` NetworkFlit）。属仿真器结构改动，只能开新分支；不触 RTL（仓内无 RTL 源）。卡对此表述正确。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| M-1 CBC | DIFFERENT_APPROACH | 不 tag raw-empty，不按日历 |
| M-5 CRRF drain | DIFFERENT_APPROACH | 不 drain、不 stall |
| 源端流控 | DIFFERENT_APPROACH | 不限 outstanding |
| 环 destination stripping / 失效 flit 清除 | 近亲 | 环上回收失效 slot 是老思路；本卡把失效判定绑到波完成 |
| slotted ring / 最短方向 | 非等价 | — |

新颖性本身不构成淘汰理由，淘汰在可行性。

## 指标核对
主 endpoint `T_seq`。由于回收集合为空，`T_seq` on/off 应相等；若出现差异，只能来自误回收（丢包）或 SUNSET marker 占 Req 的负税。不缩短推理 makespan / 尾。

## 判决理由
可行性 FAIL：在无损 CHI、无重复拍的 tests/soc_sim 信封里，「已完成波的残留占用」不存在；机制正确时是 no-op，出错时丢合法数据且无 CHI 合法 sink（源无副本）。REJECT / FLAWED。

若重提：须先在 cycle 级给出 complete 后仍在环上的 flit 计数 > 0 的证据，并说明其来源；否则无对象。
