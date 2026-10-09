# Tier 0 · P-0198/M-15 · TOSE Tail-Only Snp Express

- 机制卡: mechanisms/P-0198/M-15.md（PR #84 head `e6a5e2b`）
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc `main@63163ca`

## 卡摘要
每 dest 每波至多一拍 `tail_critical` Dat，在 Snp 物理环本拍为空且本地无 Snp pending 时，从 Dat NIC 旁路注入 Snp 物理环；头仍标 `chi=Dat`，dest/RBRG 按 channel-id 译码；Snp 绝对优先；无 epoch/SYNC/drain/duty；RBRG 失配 1 深 hold 后回 Dat 环。

## 轴一 可行性
- 尾拍标记: 失败。卡要求 H-UNIQUE-TAIL「任意 dest、任意 wave 在途 `tail_critical` ≤1」，给的武装规则做不到：
  1. 源侧规则「本波最后一拍置位」：每个源只知道自己的最后一拍。gather / KV 拉取有 N 个源，就有 N 个 `tail_critical`，违反唯一性；而且哪一个是全波最后到达，在注入时不可知。
  2. dest 侧规则「`expected−recv==1` 时 Rsp 回 ARM_TAIL，源给下一拍置位」：dest 只差一拍时，那一拍已经在途或在源 NI 已注入（outstanding 已发），ARM_TAIL 走 Rsp 绕一段才到源，到达时没有「下一拍」可标。
  3. 「同时武装 >1：后到的清先到的」：要清的是已经上环、在别的节点途中的 flit 头位，无缓冲环上没有回写在途 flit 的通路，需要全局知识。
  因此要么标记过多（每源一拍，唯一性假设失效），要么标记过晚（无对象），要么依赖神谕。
- 收益上限: 被标记的那一拍只在源 NI 注入等待时受益；一旦上 Dat 环，过路优先，途中不再等待。所以 TOSE 的收益是**一拍的注入等待**，属注入侧。若 dest eject 主导（M-5 T3 gather 打平的归因），express 拍到达 dest 后仍要和 Dat 环到达者争同一个 Dat eject 口，不增 eject 带宽。
- Sink / 死锁 / 活锁: express 在 Snp 环 eject 失败会在 Snp 环上 orbit，每圈占 Snp 槽；卡没有规定 express 的 e-tag（Dat NI 的目的口保留跨物理环是否生效）。RBRG 1 深 hold 满时「回 Dat 环重试」要求 flit 能离开 Snp 环，而无缓冲环上 flit 不能原地停，hold 满时 flit 只能继续在 Snp 环 orbit；有界性未给出。
- Snp 伤害: 过路 express 挡下游 Snp 注入（卡自认「唯一可能伤 Snp 的点」），密度界依赖唯一性，唯一性已不成立。
- 物理位宽（T1 也应查）: Dat 环与 Snp 环的 flit 位宽不同（CHI 规范里 SNP flit 没有 Data 字段，DAT flit 带 128–512b 数据；平台 docs 未给各环物理位宽，库按 flit 计槽，不建模位宽）。Dat flit 走 Snp 导线，需要把 Snp 环拓宽到 Dat 宽度或拆拍。这个问题 M-5 线同样存在，round 1 T0 未提。

## RTL / 仿真器改动核查
- 改动点（NIC Dat→Snp 旁路、dest/RBRG 按 channel-id 译码、1 深 hold）都在库内：`src/TNetworkInterface*.cpp`、`src/TCsHighWay.cpp`、`src/TBridge.cpp`、`src/TNetworkInterfaceRbrg.cpp`。属仿真器结构改动，只能开新分支；卡表述正确，不触 RTL（仓内无 RTL 源）。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| M-5 CRRF | 同线 | Dat 走 Snp 物理环、channel-id 保持、RBRG 按 id 译码、失配 hold；TOSE 去掉 epoch 并限到尾拍 |
| M-5r1 CRRF-SB（PR #85，line B 修订） | FUNCTIONAL_EQUIVALENT | M-5r1 = ghost Dat 只借 Snp 空槽 + 本地 Snp pending 时本征 Snp 优先，正是 TOSE 的仲裁规则。TOSE ≈ M-5r1 加一个「只允许尾拍」过滤器，可作 M-5r1 的一个消融臂 |
| 多物理子网负载均衡（Yoon et al., multiple physical networks vs VCs） | 近亲 | 闲置子网借用 |
| M-6/M-7 | 非等价 | 无 duty 表、不改方向 |

## 指标核对
尾拍识别不可实现，收益只有一拍注入等待，且在 dest-eject 主导区为零；不能证明缩短推理 makespan / 尾。

## 判决理由
可行性 FAIL：唯一尾拍标记要么过多、要么过晚、要么需要回写在途 flit；express 在 Snp 环上 eject 失败的 orbit 与 hold 满时的去向无界。新颖性 FUNCTIONAL_EQUIVALENT：仲裁规则与同期 M-5r1 相同，「仅尾拍」是过滤器，不是独立机制。REJECT。

建议：把「仅标记每源最后一拍的 ghost 资格」作为 M-5r1 T1 的消融臂（`tail-only`），用它测 M-5r1 的 ghost 收益是否集中在尾拍。
