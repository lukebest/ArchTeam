# Tier 0 · P-0106/M-5 · 修复时重绑定 XOR/仿射参数

- 机制卡: mechanisms/P-0106/M-5.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 每 DMC 三元组 (α,β,n_live) 在 repair 时写。运行时 `mod n_live` + kth-one（M-1 风格）。飞行中不改三元组。
- 完美预测/无限带宽/零延迟: 无预言器。无 stride 探测器。
- 关键边界: 对准「丢掉奇数因子会改 gcd(S_g, n_live)」——满好 mod 48 在退役后仍按 48 的 3-adic 走是真问题。不跨 DMC。α 与 n_live 互素。无 core_id。
- 硬件开销: 每 DMC 仿射三元组 + 复用 mask 译码。

## 轴二 新颖性
- vs 文献: 按 live n 重绑仿射/XOR 是 repair-aware map 的默认（reprogram interleave after fail）。例子 n=40=8×5 换 mod 40 是初等。
- vs 本周卡: 参数层叠在 M-1/M-2 上。P-0101/M-5 是按 stride class 换矩阵，本卡按 n_live 换 (α,β)。同「重绑系数」。

## 轴三 质量
- 机制完整度: 3-adic 例子具体。独立于 M-3 SRAM。
- 可证伪性: 仍 mod 48 再跳死槽的对照应保留 3 碰撞类；重绑后类数随 n_live 变。
- 增量: repair 时写 CSR。

## 理由
可行性通过，诊断对。新颖性：按 n 重绑仿射。不进 Tier 1。
