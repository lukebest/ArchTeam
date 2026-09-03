# Tier 0 · P-0101/M-3 · 层次正交放置

- 机制卡: mechanisms/P-0101/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: Stage A/B 只看当前地址；可选 SK 表 boot 写、译码 1R。无跨请求状态。
- 完美预测/无限带宽/零延迟: 无 stride 预言。SK 关闭则纯组合；打开则 1 cycle 读。未假设无限 DMC 口。
- 关键边界: 成功标准写成 DMC 占用 ≈1.0，明确「不是 bank 占用 >K/N」。S=2MiB 时 K=4096≥384，分层放置不证伪鸽笼。ENC3 用区分位，不把因子 3 交给 `G mod 384`。不跨 DMC 借 bank。
- 硬件开销: 组合 <0.2kGE；可选 96B SK flop file。仍在只改 interleave 信封内。

## 轴二 新颖性
- vs 文献: 「先铺 channel/DMC、再铺 bank」是多级 interleave 的默认工程（Intel/JEDEC channel-rank-bank XOR；Zhang permutation page interleave 的分层）。7b 抽取 + ENC3 + 可选斜表 = 高位抽取加 3-way，不是新图。
- vs 本周卡: 相对 M-1 只是把同一区分位优先接到 DMC 而不是 flat。P-0105/M-5 轴均衡仿射、P-0103 的 DMC 奇数因子注入是同一「别把 DOF 倒进一条轴」命题的不同包装。

## 轴三 质量
- 机制完整度: 四层占用探针、与 M-1 对照、失败标准写对（禁止用 bank>K/N 当成功）。
- 可证伪性: S=2MiB 上 n_DMC 应 ≈384；HA 份额有 1.5× 上限。
- 增量: 接线优先级，不是新不变量。

## 理由
可行性通过，问题对齐（DMC 先撞墙）写得清楚。新颖性仍是分层 XOR/抽取。不进 Tier 1。
