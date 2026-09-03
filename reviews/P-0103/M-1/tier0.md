# Tier 0 · P-0103/M-1 · Mixed-Radix Feistel Injector (MRFI)

- 机制卡: mechanisms/P-0103/M-1.md
- 判决: PASS
- 可行性: PASS
- 新颖性: NOVEL
- 质量: SUBSTANTIAL
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: SPLIT/WIDE/F_BOX/FEISTEL/CRT 只看当前 A。GOOD_MAP 1R 共享，重试 ≤2 次且禁止顺序 +1。无 stride 状态。
- 完美预测/无限带宽/零延迟: 无预言器。单边 Feistel，反函数写明。未假设零 t_RC。
- 关键边界: 打的是「奇数剩余被冻结」这一拍：`r=G mod 9` 在 9|δ 时为常数，用仍跳的 2-adic 宽位注入 Z_9。不改 384、不改取模底数。禁止 +1 跳坏 bank。partial-good 走 live-bit XOR 重试，不跨 DMC 借 bank。粒度 G=A[63:9]。
- 硬件开销: 核侧 ×120 组合路径 + 一份 384×48b 位图。在只改 interleave 信封内。

## 轴二 新颖性
- vs 文献: Feistel 本身不是新的（Luby-Rackoff；密码学 Feistel hash）。把它接到 **CRT 切开的 Z_9 奇数环、用宽 2-adic 位当 F、禁止 +1 探活**，是对本信封 3-adic 塌缩的对症结构，不是再写一次 `G mod N` 或 XOR-scheme。文献里的 mixed-radix interleave 通常只做数位重排，不在冻结 trit 上做可逆加法注入。
- vs 本周卡: 给 M-3 当组合备份，与 M-4 的 trit 注入同命题但机制不同（Z_9 加法 vs 两个 mod 3）。比 P-0101 的 ENC9 多了「冻 r + 动 F」这一环。

## 轴三 质量
- 机制完整度: 六块命名、反函数、时序、GOOD_MAP 禁 +1、评估指标（n_DMC、X_rel）对齐问题证伪条件。
- 可证伪性: S=3·2^k 上 n_DMC 应从 ~128 拉向 min(384,K)；若 F 对 p_wide 恒定则应退回塌缩。
- 深度: 环同态诊断 + 可逆单边 Feistel + 明确禁区，够进 T1 做 cycle 级对照。

## 理由
三轴通过。进入 Tier 1：在冻结信封上给 3-adic 塌缩一个可实现、可逆、可证伪的注入，而不是 XOR 重包装。
