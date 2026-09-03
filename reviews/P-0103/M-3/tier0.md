# Tier 0 · P-0103/M-3 · SLCT

- 机制卡: mechanisms/P-0103/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 每核独立 STRIDE_FSM，用已经发生的 `G−last_block` 差分。UNLOCK/CAND 走 MRFI；连续 3 个匹配非零 Δ 才 LOCK。失配当拍切回 MRFI，不消费过期 `τ`。明确禁止 t=0 已知 S、禁止全局预测器。
- 完美预测/无限带宽/零延迟: 不是完美预测（warmup=3 请求，3/128≈2% 窗口）。1–2 拍 mapper，不是 0。τ 是平移不是预言未来地址。
- 关键边界（S=3·2^k、partial good、冻结奇数因子、512B/4K）: `key[0]=(3|S)`，仅此时加横截；纯 2 幂 stride 关闭横截以免破坏已均匀的 2-adic。`S=1.5MiB` 时 `p_wide` 64 点不是单点；卡承认 `|Im_F|=1` 时 τ 不能放大像——没有假装 ROM 能从单点变出 384。partial-good 同 M-1 的 XOR 重试，DMC 在 ρ 之后冻结。不改 384/18432。
- 硬件开销 vs 问题约束: 120 份 ~51b FSM + 每核 256×8 LUT（或组合），加一份完整 MRFI。面积仍在 mapper 逻辑量级（~10^{-2} mm² ROM + MRFI）。不增 DMC/bank/die/端口。在信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: Harper & Linebarger IEEE TC 1991 / ISCA'89 *Conflict-Free Vector Access Using a Dynamic Storage Scheme*：把 stride 分解为 2 幂分量与对 2 互素的奇数核，再按这两个参数查一张「旋转类型 + 块旋转量」的存储方案（Budnik–Kuck 行旋转的变体）。本卡 KEY_ENC 的 `ctz(|S|)` + 奇数核 + `3|S` 使能位，再查 `(τ,ρ)` 对 `Z_9` 平移、对 128 组旋转，是同一效果：stride 锁定之后用常数横截/旋转去对齐陪集。DReAM (MEMSYS 2016) 运行时按访问模式重排地址映射，同属「先测模式再换图」。τ 是 `Z_9` 自同构，卡自己写「平移不放大单点像」——与 Harper 旋转「换相位不创造新桶」同构。不是 EXACT_MATCH 的逐公式复制（Harper 面向向量机 2 幂 bank + 编译器已知 stride；本卡是核侧 3-match FSM + 冻结因子 3），但是 FUNCTIONAL_EQUIVALENT。
- vs 本批其他卡: 完整复制 M-1 作为备份，LOCK 后再加 `(τ,ρ)`。是 M-1 的超集/薄增量，不是另一张独立机制。与 P-0105 五张卡（相位不变的 XOR/双线性/双哈希/S-box/2D 仿射）不重复。

## 判决理由
可行性通过（3-match 因果合法，未假定 t=0 已知 S）。淘汰结构化原因：与 Harper 1991 动态存储方案 FUNCTIONAL_EQUIVALENT（stride 分解 2-adic/奇数核 → 查旋转/横截参数）；相对 M-1 只在 LOCK 后加常数平移与 128 组旋转，而 τ 不能把 `|Im_F|<3` 放大成满 `Z_3`。质量 INCREMENTAL，不进 T1。若 T1 需要「大步长 Im_F 变瘦」的对照，应作为 M-1 的消融臂，而不是独立机制卡。
