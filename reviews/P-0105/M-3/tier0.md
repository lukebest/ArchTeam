# Tier 0 · P-0105/M-3 · 双哈希选通（DHMI）

- 机制卡: mechanisms/P-0105/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 两个 Knuth multiply-shift + 1 bit mux，只看当前 G。无全局负载表。
- 完美预测/无限带宽/零延迟: 不是 two-choice 动态负载（卡自己排除）。无预言器。
- 关键边界: 选通 bit 要割切鲁棒，否则 mux 本身随相位翻。占用 ≤K。不跨 DMC。
- 硬件开销: 两次乘法哈希 + mux，只改 interleave。

## 轴二 新颖性
- vs 文献: 双独立哈希再选通是 tabulation / double hashing / two-choice 的无状态退化。Knuth multiply-shift 是教科书。
- vs 本周卡: P-0102/M-3 双索引 XOR 合并；本卡改 mux。P-0105/M-1 已保证单图相位不变，双图是冗余包装。

## 轴三 质量
- 机制完整度: 排除全局表避免了 T0 状态杀手。坏相位「几乎不可能同时」是概率话，没有最坏 base 证明。
- 可证伪性: 需要扫 base 找双坏相位；卡没有给出必不存在的不变量。
- 增量: 两张已知图 + 1 bit。

## 理由
可行性通过。新颖性：双哈希 mux。不进 Tier 1。
