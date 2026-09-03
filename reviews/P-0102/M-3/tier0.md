# Tier 0 · P-0102/M-3 · 双索引异或合并

- 机制卡: mechanisms/P-0102/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `idx_lo=H_lo(addr[28:9])`、`idx_hi=H_hi(addr[32:21])` 并行，再 `idx=zext(idx_lo)⊕idx_hi`。两矩阵 boot 写、飞行中常数。消融 CSR 只在空闲改。不读 stride、不读未来。
- 完美预测/无限带宽/零延迟: 无预测器，运行时不必知道 S。20 输入 XOR 树 ~5 门 + 1 级合并，建议 1 cycle 寄存。不是 0 拍。
- 关键边界（[21,33) 饥饿、partial good、冻结硬件、512B/4K）: `H_hi` 输入恰为 S=2MiB 的 12 个自由位 `[21,33)`，饥饿路径被吃满。卡诚实写出 lo-only 在 2MiB 上并非 I=0（`[28:21]` 仍 8b，与库 I-Poly `[9,29)` 同缺口），但丢掉 `[32:29]`；merged 占用 →K。S=512B 时 lo 满变。3 个消融开关（USE_LO/HI/BOTH）是评估臂。粒度 512B；9-way 拼装不改 384/18432；无 live-set，不跨 DMC。
- 硬件开销 vs 问题约束: 11×20 + 12×12 配置 364b（可裁 ~200b）+ 两棵 XOR 树 ≈2–3kGE，0 SRAM。只改交织。信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于单张 GF(2) 线性图。`idx=zext(H_lo(ℓ))⊕H_hi(h)` 就是分块 H 矩阵 `[H_lo_pad | H_hi]·[ℓ;h]`，与 Rau H-matrix、Frailong XOR-scheme、Vandierendonck 可重构 XOR、Intel DRAM XOR decode、CRC/多项式索引（Rau ISCA 1991 把地址当 GF(2) 多项式）同一对象。Seznec skewed-associative 的「双哈希」是两路 bank 用两张不同函数，不是把两路索引 XOR 成一个 idx。P-0105/M-3 DHMI 是双 Knuth + 1b mux 选路，也不是 XOR 合并。双窗叙事与 USE_* 消融是实验设计，不是新代数；合并后的满秩条件仍是「H 在自由位上的列秩」。
- vs 本批其他卡: 对本批 M-2（逐位高低折叠）是可编程分块超集，核心仍是「低窗常数时高窗携带集合」。对 P-0105/CRXS（每行强制两侧抽头的一张 15×28 矩阵）功能等价且更弱（只保证 c=21 与顺序流，不保证中间割切）。对 P-0101/M-2、M-5 的 XOR 矩阵同族。与 P-0103/P-0106 无重复。非 EXACT_MATCH（不是逐公式复制经典 2-input 折叠，故不走 KNOWN_CONFIRM）。

## 判决理由
轴一通过：组合双哈希合法、H_hi 覆盖 `[21,33)`、开销在交织内。淘汰结构化原因：GF(2) 上就是一张分块 XOR 矩阵，与 XOR-scheme / CRXS / 本批 M-2 功能等价；「两条完整索引」是同一线性图的叙事切分。质量 INCREMENTAL。FUNCTIONAL_EQUIVALENT 不进 T1。消融表（lo/hi/merged）应挂在任一 XOR 图的评估计划下，不必独立成卡。
