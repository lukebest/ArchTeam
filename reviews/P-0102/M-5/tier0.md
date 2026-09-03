# Tier 0 · P-0102/M-5 · DMC 占用监视触发窗切换

- 机制卡: mechanisms/P-0102/M-5.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 计数器旁路 issue 路径；比较在采样边界。切换复用 P-0101/M-4 drain，QUIESCE 后才翻 SWITCH。FLIP_ONCE 防抖振。
- 完美预测/无限带宽/零延迟: 不预测未来 stride，只看已发生的 DMC 发行分布。不假设零 drain。
- 关键边界: 不进每请求关键路径。不跨 DMC 借 bank。A/B 窗仍是 M-1 类抽取，占用 ≤K。
- 硬件开销: 384×16b 计数 ≈768B flop，加上 drain FSM。偏大但仍是监视/控制，不改拓扑。

## 轴二 新颖性
- vs 文献: 占用监视后 remap 是已知闭环（热 bank 迁移、Awasthi 等 DRAM mapping；page recoloring）。本卡阈值 max/mean>8 是工程启发式。
- vs 本周卡: 译码复用 M-1 滑动窗，控制复用 P-0101/M-4。是包装不是新图。

## 轴三 质量
- 机制完整度: 采样、比较树、FLIP_ONCE、drain 时序都点名。比较不在 issue 组合路径。
- 可证伪性: 人为造成单 DMC 热点应触发一次切换；第二次应被锁住。
- 增量: 控制面，质量停在启发式阈值。

## 理由
可行性通过（drain-before-switch）。新颖性：已知监视+remap。不进 Tier 1。
