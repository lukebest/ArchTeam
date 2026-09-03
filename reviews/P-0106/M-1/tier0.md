# Tier 0 · P-0106/M-1 · 每 DMC 48-bit live mask + popcount 压缩

- 机制卡: mechanisms/P-0106/M-1.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 上游算出 dmc 与 r0 后，本 DMC 的 48b mask 做前缀 popcount 压缩。mask 是静态 fusedown。无跨请求状态。
- 完美预测/无限带宽/零延迟: 无预言器。不假设 18432 全好。
- 关键边界: **不跨 DMC 借 bank**。死 bank 命中率 =0，活集上可逆。s_crit 改按每 DMC n_live 算。无 core_id。退役率 6.25/12.5/25% 是问题给定点。
- 硬件开销: 384×48b=2.25KB mask，可接受。不改拓扑个数。

## 轴二 新颖性
- vs 文献: valid-mask + popcount 压缩到 live set 是工厂列修 / disabled-target 的标准（库 implementation-and-validation 已要求 valid mask）。不是新映射。
- vs 本周卡: 给所有上游 mapper 垫一层。M-2/M-3 是同一压缩的不同译码。

## 轴三 质量
- 机制完整度: 粒度选对（每 DMC 48 槽，不是全局 18432 remap）。评估应用 XOR fold 上游。
- 可证伪性: 随机退役后命中死桶应为 0；跨 DMC 的对照应被禁。
- 增量: 库已要求的结构写成卡。

## 理由
可行性通过，且对准「不能跨 DMC」。新颖性：标准 live mask。不进 Tier 1。
