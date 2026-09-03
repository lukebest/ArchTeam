# Tier 0 · P-0105/M-3 · DHMI

- 机制卡: mechanisms/P-0105/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 两路 Knuth 乘移哈希 + `pick=addr[14]⊕addr[21]⊕addr[27]` 的 2:1 mux，纯当前地址；明确禁止负载表 two-choice。无 stride 锁。
- 完美预测/无限带宽/零延迟: 无。2 cycle 截断乘；128 outstanding 覆盖。未假设完美工作集神谕。
- 关键边界（S=2MiB 稀疏子集、base/phase、partial good、512B/4K）: pick 在 c∈[15,21] 跨相位/行走两侧，把 4096 点劈进两张独立 9 bit 图。fold384 的 2:1 写成恒定 covering。partial-good 只用 2.25 KB 位图，不建 384 项负载 SRAM。论证是概率 balls-and-bins（最坏相位 maxload ~24–26），不是代数零；存在两路同时坏格的非零测度，但不像 M-2 那样把 n_DMC 钉死成 3。512B 粒、4K 页扫在评估计划里。
- 硬件开销 vs 问题约束: 3×32×16 截断乘 + 位图，不改 384/18432，无额外数据流量。信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于 Knuth 乘移 / Dietzfelbinger multiply-shift 通用哈希（1997）再折到非 2 幂桶，加上「两张独立哈希、用地址位选通」这一静态双图混合。不是 Mitzenmacher power-of-two-choices（无负载比较）。Seznec 双路 skewed-associative（ISCA 1993）与 IPS（ISCA 1992）也是多哈希分流，但对象是 cache way / 向量模块而不是「坏格不同时发生」的 DRAM 相位。HBM/GPU channel hash、Intel DRAM XOR 是单张线性/哈希图。把两条 multiply-shift 用 1 bit mux 拼起来，是已知哈希构件的薄组合，不是新映射族。
- vs 本批其他卡: 与 M-1 线性、M-2 双线性、M-4 S-box、M-5 互素仿射不同构。P-0103 无双 Knuth mux。无 EXACT_MATCH。

## 判决理由
可行，但是对 multiply-shift + 双哈希选通的增量拼装，FUNCTIONAL_EQUIVALENT / INCREMENTAL。概率尾巴仍可能留下相位相关 maxload（卡自称跨 base maxload 相对差 ~8%），也不是 ISCA 级结构命题。不进 T1。
