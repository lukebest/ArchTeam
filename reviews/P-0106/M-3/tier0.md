# Tier 0 · P-0106/M-3 · 每 DMC 活 bank 列表译码 LUT

- 机制卡: mechanisms/P-0106/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `slot=H(G) mod n_live`，查 L[slot]。LUT 在测试/修复时写好。哨兵 0x3F 走错误路径。
- 完美预测/无限带宽/零延迟: 无预言器。1R SRAM。
- 关键边界: 不跨 DMC。可逆到活集。不能打到退役 bank。与 M-2 成对可独立评估。
- 硬件开销: 384×48×6b LUT + n_live CSR。列修风格，可扫描。

## 轴二 新颖性
- vs 文献: 列修复 LUT / spare remap 表是 DRAM 工厂默认。卡自己写成「同族结构」。
- vs 本周卡: M-1/M-2 的 SRAM 版。没有新的 live-set 代数。

## 轴三 质量
- 机制完整度: 哨兵、BIST 对照、H 的 6b XOR fold 写清。
- 可证伪性: i≥n_live 应进错误路径；死 bank 不应出现在 L[0,n_live)。
- 增量: 实现变体。

## 理由
可行性通过。新颖性：列修 LUT。不进 Tier 1。
