# Tier 0 · P-0102/M-2 · 高低位折叠 XOR

- 机制卡: mechanisms/P-0102/M-2.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: EXACT_MATCH
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 14 个 XOR 门硬线，只看 addr[32:9]。无状态。
- 完美预测/无限带宽/零延迟: 无预测器。纯组合，可选 1 周期寄存。
- 关键边界: 每个 idx 位至少 XOR 一位 [9,21) 与一位 [21,33)，S=2MiB 与 S=512B 两侧都有熵。占用 ≤K。不跨 DMC。无 core_id。
- 硬件开销: 14 个 2–3 输入 XOR + 拼装，远小于信封。

## 轴二 新颖性
- vs 文献: EXACT_MATCH 于 XOR-scheme 的定义性约束——每个输出在割切两侧都有支撑（Frailong/Jalby/Lenfant 1985；Rau 1991「each bit of the index is an XOR of bits from different bit positions」）。默认配对 addr[9+i]⊕addr[21+i] 是教科书图。
- vs 本周卡: P-0105/M-1 CRXS 把同一约束写成 15×28 矩阵。本卡是更薄的 14 门实例。

## 轴三 质量
- 机制完整度: 配对表、拼装、评估对照都够用。
- 可证伪性: 拆掉高侧或低侧应分别在大/小步长塌缩。
- 增量: 无新不变量。

## 理由
可行性通过。新颖性：XOR-scheme 原文级匹配。不进 Tier 1。
