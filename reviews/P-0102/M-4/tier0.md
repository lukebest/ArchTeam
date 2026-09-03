# Tier 0 · P-0102/M-4 · 启动可配 bit-mux 抽取

- 机制卡: mechanisms/P-0102/M-4.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 14 个独立 mux，SEL 仅 boot/作业开始写。飞行中常数。
- 完美预测/无限带宽/零延迟: 无运行时探测。固件选错 SEL 就是负对照（OriginalMapper-like）。
- 关键边界: 高位程序覆盖 [21,33)。不把 mux 改成跨 DMC 借 bank。占用 ≤K。
- 硬件开销: 70b SEL + 14×24:1 mux。无 SRAM 表。

## 轴二 新颖性
- vs 文献: BIOS/MRC 可编程 bit-select 是工业默认（Intel DRAM decoder fuse、ARM NIC bit-swizzle）。不是算法贡献。
- vs 本周卡: P-0101/M-5 矩阵、P-0102/M-1 滑动窗是同一配置面。本卡最薄：每输出选一根线。

## 轴三 质量
- 机制完整度: 两套对照程序可直接仿真。
- 可证伪性: 高位程序 vs OriginalMapper-like 在 S=2MiB 应分出占用/BW。
- 增量: 配置口。

## 理由
可行性通过。新颖性：可编程 bit-mux。不进 Tier 1。
