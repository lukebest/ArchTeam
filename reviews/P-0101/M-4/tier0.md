# Tier 0 · P-0101/M-4 · 栅栏 epoch 陪集旋转

- 机制卡: mechanisms/P-0101/M-4.md
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性 / 存储语义: RUN 态下 `f'=addr[16:9]⊕EPOCH` 是 `(addr, EPOCH)` 的函数，单请求不读未来。但 EPOCH 在作业内栅栏后递增会**改写同一 PA 的 (dmc,bank)**。DRAM 单元不随映射搬家：跨 epoch 读先前写入的 8GiB 会打到错误 bank。若为保持一致性而在 INC 前搬迁工作集，则是整机 8GiB 额外流量，直接超出「只改 interleave」。二者必居其一。CEASER 式 drain 在 cache 里成立是因为行数据跟着 remap 走；在冻结 DRAM 拓扑上不成立。
- 完美预测/无限带宽/零延迟: 无 stride 神谕。但栅栏把发行门关死，QUIESCE 期间吞吐为 0；收益依赖于「扫描之间插入栅栏」的作业结构。不是 0 延迟。
- 关键边界: 快照占用 ≤K 的陈述诚实，`E=5` 才在时间并集上盖满 N 也不超卖单拍鸽笼。问题不在鸽笼数字，在动态映射与 8GiB 共享作业的持久语义、以及 512B/4K 粒上 PA→bank 必须稳定。
- 硬件开销 vs 问题约束: 8b 机宽 EPOCH 广播、14b 全局 outstanding（或 384×10b inflight）、5 态 drain FSM、**关核发行门**，是同步/控制平面，不是交织函数本身。约束是「只改 interleave、不改拓扑」；全局排空与软件栅栏是额外运行时同步。partial-good 未因旋转跨 48 槽，这一点本身无过。

## 轴二 新颖性
- vs 文献: FUNCTIONAL_EQUIVALENT 于 Harper 动态旋转/横截（与 P-0103/SLCT 同一家族）、偏斜存储随时间换陪集、以及 CEASER/CEASE（Qureshi MICRO'18）的换钥+drain——后两者的数据面在 cache，不能原样搬到 DRAM interleave。page coloring 换色也要求页迁移。不是 EXACT_MATCH 某篇 DRAM 交织论文的逐门复制。
- vs 本批其他卡: 静态索引复用 M-1 的 12b+9-way，增量只是冻结位 ⊕EPOCH。与 P-0103/SLCT（stride 锁定横截，已 INCREMENTAL 淘汰）同「换陪集不放大单点像」。与 P-0102/M-5 窗切换共用 drain，本卡是其协议源。P-0105/P-0106 无 epoch 旋转。无 EXACT_MATCH。

## 判决理由
轴一失败，结构化原因：时间变化的 DRAM 映射若不搬数据则破坏 PA 一致性（因果/正确性），若搬数据则引入 8GiB 级额外流量与全局栅栏，超出 only-interleave。质量 FLAWED。新颖性亦只是动态陪集旋转的换皮。拒绝。不进 T1。单 epoch 内它退回 M-1，没有独立可行机制可评测。
