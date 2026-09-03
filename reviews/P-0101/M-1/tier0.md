# Tier 0 · P-0101/M-1 · 区分位饱和抽取

- 机制卡: mechanisms/P-0101/M-1.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `d=addr[32:21]`、可选 `P·addr[20:9]`、`c=ENC9(addr[16:13])` 都只看当前地址。无 FSM、无跨请求状态、不读未来 stride。`flat=(c·4096+v) mod 18432` 是组合可逆抽取（固定 c 时 4096 点互异），不是反馈环。
- 完美预测/无限带宽/零延迟: 无预测器。XOR 树 + 一次校正减法，目标 1 周期寄存；128 outstanding 可藏。未假设零 t_RC / 无限 DMC 口。
- 关键边界（K≤4096 @ 2MiB、partial good、冻结奇数因子、512B/4K）: 卡明确占用 ≤K，禁止报 >K；S=2MiB 时 12 个区分位满秩 ⇒ 快照基数 =4096，不宣称打满 18432。N=18432=9×2048 用 9-way 陪集编码，不把奇数因子藏进一次 `G mod N`。粒度从 `addr[9]` 起；4K 页内 `addr[11:0]` 不进主索引。partial-good：索引仍落本 DMC 48 槽、不跨 DMC 借 bank，live-set 交给后续 mask（P-0106），不是假定 18432 全好才能成立。仿射 `G mod N` 在 S=2MiB 塌到 9，本图把冻结位只当陪集选择，区分位当主索引——与鸽笼一致。
- 硬件开销 vs 问题约束: <0.5kGE、0 SRAM、无 CSR 写口，纯交织译码。在「只改 interleave」信封内。

## 轴二 新颖性
- vs 文献: FUNCTIONAL_EQUIVALENT 于把「仍在变的高地址位」接进 bank/channel hash：Frailong/Jalby/Lenfant *XOR-Schemes*（ICPP 1985）、Rau *Pseudo-randomly interleaved memory*（ISCA 1991）、Zhang 等 permutation page interleave（MICRO 2000）、Intel DRAM XOR decode、Vandierendonck XOR hash（IEEE TC 2005）。默认 P=0 更接近「高位直接抽取」而不是满 XOR-scheme；可选 12×12 P 就是 XOR 矩阵。9-way ENC 是把 N=9×2048 的奇数因子从一次 `G mod N` 里拆出来，不是新的哈希族。
- vs 本周卡: 与 P-0101/M-2（2-adic/9-way 分离）、M-5（可配 XOR 矩阵）、P-0102/M-2（高低位折叠 XOR）、P-0105/M-1（CRXS 两侧支撑）同属「区分位进 XOR/抽取」。M-1 的冻结 ENC9 是最薄实例：高 12b 当主索引、低 4b 选陪集。不是独立机制。

## 轴三 质量
- 机制完整度: 位宽、拼装、`/48` 定点、拓扑切开都写清；评估计划有仿射/低位负对照。诚实声明占用上界 =K。
- 可证伪性: 满秩 12b 抽取在 S=2MiB 上占用应坐到 K，可直接数桶。失败模式（P 不满秩、`/48` 校正误差）已点名。
- 增量: 相对教科书 XOR-scheme / 高位抽取，只多了一个 16→9 陪集编码，没有新的不变量。

## 理由
可行性通过：因果、无预言器、遵守 K 界与不跨 DMC。新颖性淘汰：已知 XOR/直接译码的薄重包装。质量 INCREMENTAL，不进 Tier 1。
