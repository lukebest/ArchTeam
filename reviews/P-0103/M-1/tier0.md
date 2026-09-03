# Tier 0 · P-0103/M-1 · MRFI

- 机制卡: mechanisms/P-0103/M-1.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: 纯函数 `A → (die,HA,pipe,bank)`。F 只依赖当前 `p_wide=A[24:9]`，反函数 `r=(r'−F(p_wide)) mod 9` 可逆。不读未来请求、不依赖尚未到达的 stride。
- 完美预测/无限带宽/零延迟: 无预测器、无 warmup。100% good 时 1 拍组合；partial-good 时再 1 拍共享 SRAM。明确不是 0 拍。outstanding 128 盖住 1–2 拍 mapper 延迟，论证走占用而非延迟。
- 关键边界（S=3·2^k、partial good、冻结奇数因子、512B/4K）: 粒度 `G=A[63:9]` 对齐 512B。不改 384/18432（含因子 3）。`δ=3·2^{10}` 时 `G[9:0]` 冻、`A[24:19]` 仍以 3 步进，XOR-fold 高 nibble 仍变，F 非常数。`δ≡0 (mod 9)` 时 r 冻，覆盖靠 `F` 满 9 类（ROM 直方图 0..6 各 2 次、7/8 各 1 次，平移不丢剩余类）。GOOD_MAP 384×48b 1R 共享；坏 bank 用 `live5` XOR 最多两次，禁止顺序 `+1`，DMC 不弹跳。1/3 图案可能把 XOR 重试再对齐到坏 trit——卡已标为中等置信，不是忽略边界。
- 硬件开销 vs 问题约束: 只改 interleave。每核 ~10^2–10^3 GE 组合（MOD9 CSA + 16:1 LUT + 模 9 + CRT），×120 约 10^{-2}–10^{-1} mm²。GOOD_MAP 18 kb 共享一份，不复制 120 份。不增端口、不改 384/18432、不加 die。1R 冲突要求模型计入，不是偷加端口。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: Seznec/Lenfant ISCA'93 *Odd memory systems* 与 Gao ISCA'93 CRT 素数存储器是「`bank = addr mod N` + 低位当局部位移」——那正是本问题里塌缩的整数取模，不是本卡。HSRAI (arXiv:2608.00016, 2026) 修剪拓扑的 CRT 路径在 `2^a×q` 上对奇数子域做仿射再加 high-salt，盐来自更高页位，不是把仍在走的 2-adic 宽位经单边 Feistel 注入 `Z_9`。CEASER/CEASE（Qureshi MICRO'18）的 Feistel 用于 cache 集合加密换钥，不针对冻结奇数因子的陪集占用。Intel DRAM XOR decode、Vandierendonck XOR hash、Zhang MICRO'00 permutation page interleave 都在 GF(2) 上混 bank 位，384=3×128 不能靠纯 XOR 表达因子 3。Rau ISCA'91 伪随机交织是 GF(2) 多项式模不可约多项式。本卡的代数对象是 `Z_9×Z_{2048}` 上「2-adic 坐标不变、奇数坐标被 `F(p_wide)` 平移」的单边 Feistel + CRT 解码，针对 `3|δ` 时 `|im|=N/gcd(δ,N)` 的子群塌缩。不是已发表方案的换名。
- vs 本批其他卡: 与 M-4（trit 注入 + bitrev）、M-5（Z_3 CSA 树）同属「打奇数环」家族，但解码与注入函数不同（CRT 逆 vs 数位接线 vs 进位树）。M-3 以本卡为 UNLOCK 备份再加 `(τ,ρ)`，是超集不是重复。与 P-0105/CRXS（GF(2) Latin 矩阵、相位不变）问题与代数对象都不同。

## 判决理由
轴一全部通过：因果合法、无完美预测、覆盖 S=3·2^k 与 partial-good、开销落在「只改 interleave」信封内。新颖性不是 Seznec CRT 取模也不是 Intel XOR 的薄换皮，而是把仍活的 2-adic 熵 Feistel 注入冻结的 `Z_9` 以离开 AP 子群。结构足够支撑一篇顶会论证（占用从 128 拉回 384 的代数路径），送入 T1。1.5MiB 下 `p_wide` 只剩 6b 熵、1/3 图案与 XOR 重试再相关，是评估风险不是 T0 淘汰理由。
