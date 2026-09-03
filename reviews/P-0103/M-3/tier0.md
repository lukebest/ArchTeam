# Tier 0 · P-0103/M-3 · Stride-Locked Coset Transversal (SLCT)

- 机制卡: mechanisms/P-0103/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 每核 FSM 只比较过去的 last_block 与当前 G，3 次匹配才 LOCK。未锁定走 M-1 组合备份。τ/ρ 在 LOCK 后是当前 S 的函数，不读未来请求。
- 完美预测/无限带宽/零延迟: 禁止全局预测器、禁止完美 stride 预言。S 在 t=0 未知。LOCK 用的是已观察步长，不是 oracle。
- 关键边界: 横截 τ 本身是常数，不放大单点像。覆盖来自把塌缩陪集对齐到完全剩余系。GOOD_MAP 同 M-1。不跨 DMC。
- 硬件开销: ×120 FSM + 256×8b ROM + 一份 M-1 路径。仍在 interleave/控制信封内。

## 轴二 新颖性
- vs 文献: stride-aware remapping / lock-on-stride 后加偏移是已知（stream detector + coloring；指令预取里的 stride lock）。TAU_RHO_ROM 是查表横截，不是新代数。
- vs 本周卡: 底图完整复制 M-1。LOCK 只加常数平移/旋转。P-0101/M-4、P-0102/M-5 同属「观察后改陪集」。

## 轴三 质量
- 机制完整度: UNLOCK/CAND/LOCK、禁止退回整数取模、每核一份，写清楚。
- 可证伪性: 对稳定 S=3·2^k 应在 LOCK 后抬 n_DMC；乱序/变 stride 应停在 M-1。
- 增量: 包装 M-1，质量停在探测器。

## 理由
可行性通过（过去匹配，非完美预测）。新颖性：stride lock + 查表横截。不进 Tier 1。
