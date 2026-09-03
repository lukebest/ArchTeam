# Tier 0 · P-0105/M-1 · CRXS

- 机制卡: mechanisms/P-0105/M-1.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 15×28 GF(2) 矩阵是当前 `phys_addr[36:9]` 的纯组合 XOR，无 stride/未来 base 输入，无状态机。
- 完美预测/无限带宽/零延迟: 无。1 mapper cycle；128 outstanding 覆盖；未假设零 DRAM 延迟。
- 关键边界（S=2MiB 稀疏子集、base/phase、partial good、512B/4K）: 对每个割切 c∈[10,21] 要求每行在 <c 与 ≥c 都有抽头；S=2MiB 行走子空间行秩 11，4096 点像 2048。fold96/fold48 写成恒定 2:1 covering，不随相位改标签集合的基数。2.25 KB 位图 + 48:6 PE 覆盖 partial-good，不改 384/18432。粒度 `G=addr>>9`，评估含页内 base 与 4608 B 非 2 幂。
- 硬件开销 vs 问题约束: ~70 XOR2 + 比较减法 + 位图，只改交织。无运行时重映射流量、无额外控制器。信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于 Frailong/Jalby/Lenfant *XOR-Schemes*（ICPP 1985）、Zhang 等 permutation-based page interleaving（MICRO 2000）、Rau *Pseudo-randomly interleaved memory* 的 XOR/多项式交织（ISCA 1991）、Intel DRAM XOR decode、Vandierendonck/De Bosschere *XOR-Based Hash Functions*（IEEE TC 2005）、以及 HSRAI 的 GF(2) affine stride-resistant 交织（arXiv:2608.00016）。「冻结相位 P、行走 W，`out=A·P XOR B·W`，B 每行非零 ⇒ 占用多重集与 P 无关」是 XOR-scheme 对仿射子空间满射的标准推论；「每个割切两侧都有支撑」是把高低位混进 bank/channel hash 的设计规则写成全 c 约束，不是新代数对象。
- vs 本批其他卡: 与 M-5 AB2A 同命题（两侧支撑 ⇒ 平移不变），一个在 GF(2)、一个在 Z_n，不同构。与 M-2/M-3/M-4 的双线性、双哈希、剪切+S-box 不同。与 P-0103 的 B3CSH/MRDR XOR 折叠不同目标（3-adic 陪集 vs 2^c 相位）。无兄弟 EXACT_MATCH。

## 判决理由
轴一通过，但新颖性是对已知 XOR-scheme / DRAM XOR hash 的薄重包装，质量 INCREMENTAL。FUNCTIONAL_EQUIVALENT 不进 T1。拒绝原因：与 Frailong 1985、Zhang MICRO 2000、Intel DRAM XOR、Rau ISCA 1991 功能等价，而非 P-0105 上的新结构。
