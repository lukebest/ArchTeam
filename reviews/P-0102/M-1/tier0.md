# Tier 0 · P-0102/M-1 · 滑动支撑窗

- 机制卡: mechanisms/P-0102/M-1.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `start=min(m*,13)` 与 20 宽 mux 只看当前地址与静态 CSR。改 m* 要求空闲/drain，飞行中视为常数。
- 完美预测/无限带宽/零延迟: v1 不探测 stride，靠软件写 m*。不假设写对。
- 关键边界: 占用仍 ≤K，不宣称打满 N。m*=21 时窗 [13,33) 含全部 [21,33)。不跨 DMC。I-Poly 系数沿用库，本卡只换支撑。
- 硬件开销: 5b CSR + 20×(5:1) mux，0 SRAM。只改 interleave 前线。

## 轴二 新颖性
- vs 文献: 滑动/可编程抽取窗是 bit-mux interleave 与 I-Poly 前的 barrel（Harper 低/高位选择；工业 BIOS DRAM map）。不改多项式族。
- vs 本周卡: P-0101/M-5、P-0102/M-4 是同一「换支撑」；本卡特化成 I-Poly 前的 5 档 mux。

## 轴三 质量
- 机制完整度: 信息量对照表（固定窗 vs 滑动窗）清楚。越出 bit33 的禁区写明。
- 可证伪性: S=2MiB 固定窗 ≤256 区分值，滑动窗应到 K。
- 增量: mux 前置，不是新哈希。

## 理由
可行性通过。新颖性：可编程窗。不进 Tier 1。
