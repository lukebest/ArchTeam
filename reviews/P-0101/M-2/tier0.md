# Tier 0 · P-0101/M-2 · 2-adic 与 9-way 分离 XOR 置换

- 机制卡: mechanisms/P-0101/M-2.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `u=M·addr[32:21]`、`c=ROM(h)` 只看当前地址。无 FSM、不读未来 stride。`flat=c·2048+u` 无第二次 `mod N`，组合可逆（秩 11 的 M + 满射 16→9）。
- 完美预测/无限带宽/零延迟: 无预测器。XOR 树 + 64b ROM，至多 1 周期寄存。未假设零 t_RC / 无限 DMC 口。
- 关键边界（K≤4096 @ 2MiB、partial good、冻结奇数因子、512B/4K）: 目标是逼近 K 不是超过 K。卡诚实写出静态 12b 窗在 S=512KiB 只到 4096≪K=16384。9-way 用区分位切片，不把奇数因子交给一次 `G mod N`。bank 仍落本 DMC 48 槽。粒度从 addr[9] 起。
- 硬件开销 vs 问题约束: ~0.4kGE + 64b ROM，boot 熔丝，无大 SRAM。只改 interleave。

## 轴二 新颖性
- vs 文献: CRT 切开 `Z_{18432}≅Z_{2048}×Z_9` 后对 2-adic 段做满秩 XOR、对 9 段做小 ROM，是 XOR-scheme + 混合进制拆分的标准拼装（Rau 1991；混合进制 interleave 见 Harper / 教科书 CRT 映射）。不是新的置换族。
- vs 本周卡: 与 M-1 同根（区分位进索引）。差别是 9-way 吃区分位而不是冻结位，以及 `flat=c·2048+u` 对齐 N 的因子。P-0101/M-5、P-0103/M-1 的 CRT 切开是同一骨架。负对照「h 改冻结位 → 占用 2048」说明增量只在切片选择。

## 轴三 质量
- 机制完整度: 秩 11 断言、gcd 对照表、负对照都有。S=512KiB 缺口写明。
- 可证伪性: 占用应从 9 拉到 ~K（2MiB）；h 冻结时应掉到 2048。
- 增量: 相对 M-1 是陪集来源换边，不是新机制。

## 理由
可行性通过。新颖性：CRT+XOR 的已知拆法。不进 Tier 1。
