# Tier 0 · P-0102/M-4 · 启动可配 bit-mux 抽取

- 机制卡: mechanisms/P-0102/M-4.md
- 判决: KNOWN_CONFIRM
- 可行性: PASS
- 新颖性: EXACT_MATCH
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `idx[i]=addr[9+SEL[i]]`，14 个独立 5b mux，源为当前 `addr[32:9]`。SEL 仅 boot/作业开始写，飞行中常数。无 stride 探测器、无未来地址、无 FSM。
- 完美预测/无限带宽/零延迟: 固件按「stride 类别 + 活 bank 几何」**一次性编程**，不是运行时预言每条流的 S。批注「boot-time bit-mux 若编程一次则更可信」——本卡满足该契约。高位程序把 `[21,33)` 全部 12 线永久接进索引，之后不必再猜 S。mux 深度 ~5 级 2:1，可选 1 cycle 寄存。无 0 延迟、无无限 BW。
- 关键边界（[21,33) 饥饿、partial good、冻结硬件、512B/4K）: **高位程序** `SEL={12..23,0,1}` 抽出 `addr[21:32]` 再补 `addr[9:10]`，S=2MiB 上 I=12，占用可达 K。另 2 根低位让相邻 512B 块仍能 2 路分开，不是纯高窗。**OriginalMapper-like** 停在 `[9,24]`，2MiB 只剩 3 自由位、占用 ≤8——这是症状的可复现负对照，不是漏洞。稀疏抽取不必连续 20b 窗。partial-good：明确不跨 DMC 借 bank，活集压缩留给 P-0106。不改 384/18432。粒度 512B。
- 硬件开销 vs 问题约束: 14×32:1 mux ≈1.1kGE + 70b SEL CSR，0 SRAM。BIOS 可编程交织，信封内。比本批 M-5 干净：无运行时遥测、无 drain。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: **EXACT_MATCH** 点名的 Intel DRAM decode / BIOS DRAM map，以及 bit-selecting hash（Vandierendonck DATE 2006 对照 XOR 时的基线：「bit-selecting hash function selects the set index from the address bits」；Givargis DAC 2003 选位）。Intel IMC 的 MAD_INTER_CHANNEL / CHANNEL_HASH / bank bit 选择就是 boot 编程「哪些物理地址位进 channel/rank/bank」（Pessl 等 DRAMA，USENIX Security 2016 逆向的也是这张图）。卡自己写「这不是新算法族，就是保守的『BIOS DRAM map』」。纯 mux（每输出恰好 1 根地址线、无 XOR）甚至弱于工业界常见的 XOR-decode，是选位哈希的子集。
- vs 本批其他卡: 本批 M-1 滑动连续窗是 SEL 被约束为 20 个连续下标的 5 档特例；P-0101/M-1 硬线 `[32:21]` 是高位程序的静态切片；P-0101/M-5 的 XOR 矩阵行是 mux 的超集（一行可 XOR 多源）。与 P-0105/CRXS（固定多抽头 XOR）不同实现、同一目的（让 `[21,33)` 进索引）。与 P-0103/P-0106 无重复。

## 判决理由
轴一通过：一次编程的 bit-mux 合法、高位程序覆盖 `[21,33)`、只改交织，是本批最贴信封的保守修复，也比 M-1 更不依赖运行时知道 S。新颖性是对 Intel/BIOS DRAM map 与 bit-selecting hash 的 **EXACT_MATCH**（作者自陈）。按规则 EXACT_MATCH → KNOWN_CONFIRM，不进 T1。它仍是本问题的正确工程答案：T1 不必再发明选位 mux，只需在评估里把「高位 SEL vs `[9,24]`」当作已知对照。
