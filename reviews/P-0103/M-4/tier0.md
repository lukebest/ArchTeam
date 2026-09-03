# Tier 0 · P-0103/M-4 · Mixed-Radix Digit Reversal (MRDR)

- 机制卡: mechanisms/P-0103/M-4.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 接线置换 + 两个 2b 模 3 加，只看当前 G 与 p_wide。无预测器。1 拍。
- 完美预测/无限带宽/零延迟: 无 FSM。XOR 重试只打 bank-in-DMC，DMC 保持。
- 关键边界: 卡正确指出「只做数位反转不够」——冻着的 trit 翻到高位仍然冻。注入 H0/H1 来自不相交地址位。禁止 +1、禁止跨控制器弹跳。
- 硬件开销: 接线 + 两个模 3 加，极轻。

## 轴二 新颖性
- vs 文献: bit-reversal interleave 是教科书（FFT 式、Harper mixed-radix digit reversal）。trit 上加 XOR 折叠是 M-1 F_BOX 的拆分版。
- vs 本周卡: 「反转之前注入」与 M-1 Feistel、M-5 trit 树同命题。本卡是最薄的接线版。

## 轴三 质量
- 机制完整度: 两件事缺一不可写清楚；评估应对「只反转不注入」做负对照。
- 可证伪性: 关掉 H0/H1 在 3|δ 上应仍失因子 3。
- 增量: 已知数位反转 + 小折叠。

## 理由
可行性通过。新颖性：bitrev + 小 XOR 注入。不进 Tier 1。
