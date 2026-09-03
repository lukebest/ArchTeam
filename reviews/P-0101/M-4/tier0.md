# Tier 0 · P-0101/M-4 · 栅栏 epoch 陪集旋转

- 机制卡: mechanisms/P-0101/M-4.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: RUN 路径只看当前地址与当前 EPOCH。EPOCH 只在 `global_outstanding==0` 后加一，仿真器拒绝飞行中改 map。不按请求、不按 core 换陪集。
- 完美预测/无限带宽/零延迟: 无 stride 预言。栅栏是控制面；drain 代价写成 O(T_tail)，不假设零延迟排空。
- 关键边界: 单 epoch 占用仍 ≤K，并集 ≤min(N,E·K)。不宣称单拍打破鸽笼。不跨 DMC。EPOCH 机宽一份，不进 core_id。
- 硬件开销: CSR+计数+5 态 FSM <0.5kGE；可选 480B inflight。只改 interleave/控制面，不改拓扑。

## 轴二 新颖性
- vs 文献: 排空后换 hash/陪集是已知 remap（page coloring 换色、DRAM mapping 热更新、checkpoint 后 re-interleave）。XOR 进冻结位再 ENC9 与 M-1 同图。
- vs 本周卡: 译码复用 M-1；P-0102/M-5 用同一 drain 切窗。本卡是控制包装，不是新抽取。

## 轴三 质量
- 机制完整度: 5 态表、硬约束、T_drain/T_scan 指标都有。诚实：单次扫描收益 0～5%。
- 可证伪性: 并集占用随 E 增长；DMC 已满时旋转收益应为 0。
- 增量: 不改变单快照 K 界，质量停在时间平均摊热点。

## 理由
可行性通过（drain-before-write）。新颖性：已知栅栏 remap。不进 Tier 1。
