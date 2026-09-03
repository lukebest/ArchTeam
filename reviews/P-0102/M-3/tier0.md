# Tier 0 · P-0102/M-3 · 双索引异或合并

- 机制卡: mechanisms/P-0102/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 两路 XOR hash 并行后合并，只看当前地址。矩阵 boot 写。
- 完美预测/无限带宽/零延迟: 无预测器。1 cycle 寄存合并结果。
- 关键边界: 大步长 idx_lo 常数、idx_hi 携带集合；顺序相反。占用 ≤K。不跨 DMC。
- 硬件开销: 364b 配置（可裁到 ~200b），0 SRAM。

## 轴二 新颖性
- vs 文献: 双哈希再 XOR 合并是 XOR-scheme 的分块形式，也是 dual-index hashing / two polynomial XOR（Vandierendonck；Knuth multiply-shift 的双独立再混）。不是 two-choice 负载均衡（卡自己排除了全局表）。
- vs 本周卡: 与 M-2 逐位折叠、P-0105/M-3 DHMI（双 Knuth + mux）同族。本卡是「两条完整索引 XOR」而不是逐位配对或选通。

## 轴三 质量
- 机制完整度: H_lo/H_hi 复位单位阵、拼装、位宽裁剪选项写清。
- 可证伪性: 关掉 H_hi 应在 S=2MiB 塌缩；关掉 H_lo 应在顺序流变差。
- 增量: 双路包装。

## 理由
可行性通过。新颖性：双索引 XOR。不进 Tier 1。
