# Tier 0 · P-0101/M-1 · 区分位饱和抽取

- 机制卡: mechanisms/P-0101/M-1.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `d=addr[32:21]`、`v=d⊕P·addr[20:9]`、`c=ENC9(addr[16:13])`、`flat=(c·4096+v) mod 18432` 全是当前地址的组合函数。无 FSM、无未来请求、无 stride 输入。P 复位 0，飞行中不改。
- 完美预测/无限带宽/零延迟: 无预测器。XOR 树 ~4 门 + 一次校正减法，目标 1 周期寄存；不是 0 拍、不假设 DRAM 零延迟。outstanding 128 覆盖译码。
- 关键边界（鸽笼 K≤4096 @ 2MiB、partial good、冻结资源、512B/4K）: 卡写明 `S=2^m` 时占用 ≤K，`m=21` 时 12 个区分位满秩 ⇒ `|{flat}|=4096=K`，禁止占用 >K/N=22.2%。`4096` 不整除 `18432`，但连续 4096 点模 18432 仍互异——不宣称打满 18432。粒度 `G=addr>>9`。bank 仍落在本 DMC 48 槽，partial-good 交给后续 live mask，不跨 DMC 借 bank。不改 120/384/18432。
- 硬件开销 vs 问题约束: `<0.5kGE`、0 SRAM、无 CSR 写口。只改 interleave。顺序流上默认 P=0 时 2MiB 窗内 c 只走 9 值（局部 bank 偏少）是评估风险，不是鸽笼违例。

## 轴二 新颖性
- vs 文献: FUNCTIONAL_EQUIVALENT 于高位/bit-field 交织（大步长把行走位接到索引）加上对 `N=9×2048` 的 CRT 式 9-way 打包。Frailong XOR-Schemes（ICPP 1985）、Rau I-Poly（ISCA 1991）、Intel DRAM XOR、Zhang 页交织（MICRO 2000）都是「选地址位（或 XOR）当 bank/channel」。默认 P=0 时 v 就是 `addr[32:21]` 硬线；ENC9 吃冻结位只选陪集，是教科书「奇数因子单独编码」的薄实例，不是新代数对象。Seznec 素数模、Latin square、bit-reversal、HBM hash 也不是本卡，但本卡并不比高位抽取多出一个可命名对象。
- vs 本批其他卡: 与 M-2 同族（区分位进索引、占用坐到 K），差别只是 9-way 用冻结位 vs 区分位、拼装 `·4096` vs `·2048`。与 M-3 不同目标（本卡饱和 bank 陪集基数，不保证 4096 点不挤进 ~86 个 DMC）。与 P-0102/M-1 滑动窗+I-Poly、P-0102/M-4 boot mux 是同一「把支撑对齐自由位」命题的静态 2MiB 切片，非 EXACT_MATCH。与 P-0103 CRT 注入奇数环、P-0105 CRXS 双侧抽头、P-0106 live-mask 无机制重复。

## 判决理由
轴一通过：组合可逆、承认鸽笼、开销在只改交织信封内。淘汰结构化原因：新颖性是高位 bit-field + 9-way 陪集的薄包装（FUNCTIONAL_EQUIVALENT），质量 INCREMENTAL。连续 4096 块模 18432 把 K 个点挤进约 `4096/48≈86` 个 DMC，相对 `G mod N` 的 9 桶是工程改进，不是顶会新对象。FUNCTIONAL_EQUIVALENT 且非 ISCA_WORTHY，不进 T1。
