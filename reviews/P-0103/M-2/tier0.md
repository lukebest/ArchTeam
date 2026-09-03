# Tier 0 · P-0103/M-2 · Odd-Ring Cubic MAC (ORCM)

- 机制卡: mechanisms/P-0103/M-2.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: INCREMENTAL
- 质量: THIN
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 立方 MAC 只看当前 A。2 拍流水，无 stride 状态。同一 A 同一映射。
- 完美预测/无限带宽/零延迟: 无预言器。SQ/CUBE 用组合 CSA，禁止时序乘循环。
- 关键边界: 卡自己写明立方 **不能**单独盖满 3 个 DMC trit：n_DMC ≈256=128×2，X_rel 从 3 降到 1.5 不是 1。partial-good 禁止对 N_good 再 mod 3。不跨 DMC。
- 硬件开销: 组合部分积，不实例化 120 份 4kb ROM。可实现。

## 轴二 新颖性
- vs 文献: 多项式哈希 / 幂次 MAC 进 interleave 有先例（permutation polynomial、power hash）。Z_9 上 x^2+x^3 的像缺一个 trit 类是域算术事实，不是新观察。
- vs 本周卡: 与 M-1 同 CRT 骨架，只把 F 换成立方。卡写「若要 384 不是 256，必须加一次非 g 的 trit 注入（本卡不加）」——增量停在半截。

## 轴三 质量
- 机制完整度: Δ 表与边界诚实，这是优点。
- 可证伪性: 主指标被改成「占用集上的 min/mean」，全局 128 个空 DMC 的 min=0 被避开。问题要的是 n_DMC=min(384,K)，本卡规格达不到。
- 深度: 已知洞写进成功标准，T1 没有新假说可验。

## 理由
可行性通过（因果、诚实边界）。新颖性/质量不够：以「盖不满 Z_3」为规格，不能过 T0。不进 Tier 1。
