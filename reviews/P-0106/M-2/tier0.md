# Tier 0 · P-0106/M-2 · 同 DMC 奇数步长 / 第 k 活位压缩

- 机制卡: mechanisms/P-0106/M-2.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 仿射后 `mod n_live`，再 1 cycle 并行前缀找第 k 个活 bit。无 48-iter 探针。mask/n_live 在 repair 时写。
- 完美预测/无限带宽/零延迟: 无预言器。禁止译码路径迭代。
- 关键边界: 可逆性来自 Z_{n_live}→活集合双射，不是 +α 探活（多对一）。α 与 n_live 互素，n_live 变则重编程。不跨 DMC。注意到 48=16×3，奇数 α 仍可能与 3 不互素。
- 硬件开销: 每 DMC 48b mask + 6b n_live + 组合 kth-one。无 SRAM 列表。

## 轴二 新颖性
- vs 文献: select-k / parallel prefix popcount 是标准组合（优先编码器、col-repair decode）。仿射再 mod n_live 是 textbook。
- vs 本周卡: 与 M-1 同 mask，译码从「压缩 r0」换成「第 k 活位」。M-3 用 LUT 做同一双射。

## 轴三 质量
- 机制完整度: 禁止 48-iter、禁止 +odd 探活，写对。3-adic 与 n_live 互素点到了。
- 可证伪性: 迭代探活对照应不可逆/超 1 cycle。
- 增量: 译码变体。

## 理由
可行性通过。新颖性：标准 kth-one。不进 Tier 1。
