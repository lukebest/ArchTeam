# Tier 0 · P-0102/M-2 · 高低位折叠 XOR

- 机制卡: mechanisms/P-0102/M-2.md
- 判决: KNOWN_CONFIRM
- 可行性: PASS
- 新颖性: EXACT_MATCH
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 14 路硬线 XOR，源全部来自当前 `addr[32:9]`。无 FSM、无 stride 输入、无未来请求。同一张图服务 S=512B 与 S=2MiB，飞行中不重配。
- 完美预测/无限带宽/零延迟: 无预测器，**不必知道 S**。2 级 XOR + `%9` 减法，组合纳入 1 cycle；可选寄 1 拍。不是 0 延迟，无无限 BW。
- 关键边界（[21,33) 饥饿、partial good、冻结硬件、512B/4K）: 默认表 `idx[i]=addr[9+i]⊕addr[21+i]`（i=0..11），低窗 `[9,21)` 与高窗 `[21,33)` 一对到底。S=2MiB 时低位冻、高 12b 满变 ⇒ `idx[11:0]` 满变，I=12，占用 →K 不是 1 桶。S=512B 时低位满变、高位缓变，占用接近 N。`idx[12:13]` 两个 XOR3 只是扰码，不承担饥饿修复。粒度 512B；不改 384/18432；无 live-set，bank 仍落 48 槽，partial-good 不跨 DMC。禁止 `core_id`。
- 硬件开销 vs 问题约束: 12×XOR2+2×XOR3 `<50GE`（可配 140b 则 ~1kGE），0 SRAM。纯交织组合。信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: **EXACT_MATCH** 点名的「high-bit XOR fold」以及 Frailong/Jalby/Lenfant *XOR-Schemes*（ICPP 1985）、Rau *Pseudo-randomly interleaved memory*（ISCA 1991）、González 等 XOR-based placement、Vandierendonck/De Bosschere *XOR-Based Hash Functions*（IEEE TC 2005）与 DATE 2006 的 2-input permutation XOR（低 m 位对角 ⊕ 高位选一）、Intel DRAM XOR decode、Zhang 等 permutation page interleave（MICRO 2000）。Seznec *Two-Way Skewed-Associative Caches*（ISCA 1993）的按位 XOR 索引是 cache 侧同一对象。卡自己写「经典折叠：每个索引位至少 XOR 一位 `[9,21)` 和一位 `[21,33)`」——把经典高低位折叠钉在 2MiB 割切上。额外两路 XOR3 与 9-way 拼装是信封打包，不改变对象。INCREMENTAL = 薄换名。
- vs 本批其他卡: P-0105/M-1 CRXS 把「每个割切两侧都有抽头」写成全 c∈[10,21] 的 15×28 矩阵，是本卡在单一割切 c=21 上的严格超集；该批 T0 已判 CRXS 为 XOR-scheme 的 FUNCTIONAL_EQUIVALENT。P-0101/M-1 的 `v=d⊕P·addr[20:9]` 是同一折叠（高 12 ⊕ 可选低 12）。本批 M-3 是把两窗先各自哈希再 XOR，GF(2) 上仍是一张分块 H。非兄弟逐公式复制。与 P-0103 奇数环、P-0106 live-set 无重复。

## 判决理由
轴一通过：硬线高低 XOR 合法、覆盖 `[21,33)`、同一张图服务两种交通、只改交织。新颖性是对经典 high-bit XOR fold / XOR-scheme / Intel DRAM XOR 的 **EXACT_MATCH**（卡内亦自称「经典折叠」）。按规则 EXACT_MATCH → KNOWN_CONFIRM，不进 T1。T1 若需对照臂，用「只接低窗」vs「高低折叠」即可，不必当新机制。
