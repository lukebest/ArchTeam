# Tier 0 · P-0102/M-1 · 滑动支撑窗

- 机制卡: mechanisms/P-0102/M-1.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 每请求 `X[i]=addr[9+off+i]`，`off=min(m*,13)-9`，再送入现成 I-Poly。`m*` 是 5b CSR，只在空闲或 drain 后由软件写「主导 stride 的 2-adic 阶」，飞行中视为常数。映射是当前地址的组合函数，不读未来请求、不做每拍 S 探测。
- 完美预测/无限带宽/零延迟: **不是**逐请求预言 S。`m*` 与 P-0101/M-5、Intel MAD 同一契约：作业/BIOS 配置，不是负载路径上的神谕。饥饿修复甚至不依赖运行时改 `m*`——钳位 `start=min(m*,13)` 把 `m*=21` 钉在窗 `[13,33)`，静态写一次即含全部 `[21,33)`。滑动只是顺序流还想吃 `[9,13)` 时的档位优化。混合步长单窗失效是覆盖缺口，不是因果作弊。20×(5:1) mux ~3 级 2:1，目标纳入原 I-Poly 的 1 cycle；不够则 X 上 +1 寄存。无 0-cycle、无无限 BW。
- 关键边界（[21,33) 饥饿、partial good、冻结硬件、512B/4K）: `m*=21` 时窗 `[13,33)` 含 12 个自由位，I=12，占用上界 K=4096 不是 1 桶。`start≤13` 禁止滑出 bit33。固定对照 `[9,29)` 在 2MiB 上只交 8b、丢掉 `[29,33)`——卡正打本题症状。粒度 `G=addr>>9`；4K 页不进 map。不引入 live-set，bank 仍落本 DMC 48 槽，partial-good 交给级联 mask（P-0106），不是假定 18432 全好。不改 120/384/18432。
- 硬件开销 vs 问题约束: ~0.16kGE mux + 5b CSR，0 SRAM。只换 I-Poly 的 20 根输入线。改 `m*` 的 fence 是控制面、与 P-0101/M-4 同类，不在每请求关键路径上另造端口。只改 interleave，信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于可重构 bit-select：Vandierendonck/De Bosschere DATE 2006 *Application-Specific Reconfigurable XOR-Indexing*（按应用选哪些地址位进索引）、Givargis DAC 2003 按 profile 选 cache index 位、Intel MAD/BIOS DRAM map 的可编程抽位。I-Poly 本身是 Rau ISCA 1991 *Pseudo-randomly interleaved memory* 与 González/Topham 多项式取模索引；本卡明确「不改多项式族，只在前面加滑动窗」——新对象只是 5 档连续窗 mux。`start=min(m,33-w)` 让支撑跟踪 `[m,33)` 是已知选位策略在 2MiB 割切上的特化，不是新代数。不是 bit-reversal，也不是 CRC index。
- vs 本批其他卡: 与 P-0101/M-5（按 stride class 换 14×24 XOR 矩阵）同一家族：固件写 `m`，支撑对准自由位。M-5 更一般（任意 XOR 行）；本卡是连续 20b 窗的 5 档子集。与 P-0101/M-1 硬线 `addr[32:21]`、本批 M-4 高位程序在 `m*=21` 上功能重叠。与本批 M-2/M-3（固定双侧 XOR、无需 `m*`）不同实现、同一目的。与 P-0105/CRXS（固定矩阵、每个割切两侧抽头、无需 `m*`）不同构但同属「让高位进索引」。与 P-0103 奇数环、P-0106 live-set 无重复。非 EXACT_MATCH。

## 判决理由
轴一通过：作业级写 `m*` 不是完美预测，2MiB 窗含 `[21,33)`，开销落在只改交织。淘汰结构化原因：质量是对可重构 bit-select / BIOS 抽位 / P-0101/M-5 的薄特化（连续窗 + 原 I-Poly），INCREMENTAL，FUNCTIONAL_EQUIVALENT 不进 T1。若评估需要「固定 `[9,29)` vs 滑到 `[13,33)`」的对照，应作为库 I-Poly 的消融臂，而不是独立机制。
