# Tier 0 · P-0103/M-5 · Base-3 Carry-Save Hash (B3CSH)

- 机制卡: mechanisms/P-0103/M-5.md
- 判决: PASS
- 可行性: PASS
- 新颖性: NOVEL
- 质量: SUBSTANTIAL
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: 24b 切 8 个 3b 块 → trit LUT → Z_3 CSA 树 + GF(2) 11b，只看当前 A。无 FSM、无 stride 锁。1 拍组合树。
- 完美预测/无限带宽/零延迟: 无预言器。不假设双射。
- 关键边界: **不宣称** 18432 上双射。论证是：δ≡0 (mod 3) 只冻结整数 `G mod 3`，不冻结按位切块的 trit 输入。PACK_SEL 禁止 +1、禁止对 N_good 再 mod 3。不跨 DMC。
- 硬件开销: 8 份 8×2 LUT + 深度 4 的 Z_3 CSA + 11×11 接线。可实现。

## 轴二 新颖性
- vs 文献: 二进制 CSA 常见；**在 Z_3 上对地址切块做 carry-save 来打断 3-adic 赋值**，不是 XOR-scheme，也不是再一次 `G mod 9`。与 residual-number / trit hash 有亲缘，但对准的是本信封「v_3(δ)≥1 ⇒ DMC 因子消失」这一条，不是通用 residual map。
- vs 本周卡: M-1/M-2/M-4 仍先算整数 r=G mod 9 再注入。本卡根本不走那条同态。这是独立假说。

## 轴三 质量
- 机制完整度: 非双射声明、统计平衡口径、PACK_SEL 禁区、与 2 幂轴 GF2_11 的分工都写了。
- 可证伪性: S=3·2^k 上 trit 树输入应仍变；若切块全落在冻结 3b 对齐上，应看到退化——卡把这条留给评估，而不是藏起来。
- 深度: 打的是赋值本身，够进 T1 用占用/X_rel 打假说。

## 理由
三轴通过。进入 Tier 1：对 3-adic 根因换了一条可实现的非同态路径，并诚实放弃双射。
