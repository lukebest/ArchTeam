# Tier 0 · P-0105/M-4 · 剪切加 S-box 等距（SNS）

- 机制卡: mechanisms/P-0105/M-4.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 奇数剪切 + 8b S-box，只看当前 x/y。无状态。
- 完美预测/无限带宽/零延迟: 无预言器。S-box 组合或 256×8 ROM。
- 关键边界: 目标是 4096 点像在 384 上属同一 discrepancy 类、与 base 无关。不宣称单轴吃下 4096 DOF。不跨 DMC。
- 硬件开销: 剪切加法 + 8b 置换，可实现。

## 轴二 新颖性
- vs 文献: shear + S-box 是 SPN / 非线性 interleave 的标准两步（AES 风格扩散；permutation polynomial + sbox hash）。不是新构造。
- vs 本周卡: 第三条路（相对 M-1 线性、M-2 双线性），但仍是「拧格子再非线性」的已知配方。

## 轴三 质量
- 机制完整度: 动机清楚（线性码成团、双线性 gcd 洞）。S-box 具体表与 discrepancy 界未给可检查的不变量。
- 可证伪性: 需要 discrepancy / 占用随 base 的扫描，卡没有闭式。
- 增量: 工程拼装。

## 理由
可行性通过。新颖性：shear+S-box。不进 Tier 1。
