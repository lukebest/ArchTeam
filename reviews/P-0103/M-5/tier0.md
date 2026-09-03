# Tier 0 · P-0103/M-5 · B3CSH

- 机制卡: mechanisms/P-0103/M-5.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: CHUNK→8×2 LUT→深度 4 的 `Z_3` CSA→`dmc_odd=(d0+d1+d2) mod 3`，与 GF2_11 接线并行。只依赖当前 `A`。无状态。
- 完美预测/无限带宽/零延迟: 无 FSM、无 stride 锁。1 拍树 + 0/1 拍 SRAM/select-k。不是 0。不宣称 18432 上双射。
- 关键边界（S=3·2^k、partial good、冻结奇数因子、512B/4K）: 明确点名翻转块：`δ=3`→C0；`δ=9`→C0+C1（整数 `G mod 9` 冻但 3b 模式不冻）；`δ=24`→C0 冻、C1 满跑；`δ=3072`→C0..C2 冻、C3 活。这正是「3-adic 赋值冻住 `G mod 3`、按位切块不冻」的边界。不改 384/18432。`d2` 几乎不取 2，故不用 d2 当 DMC trit，改用三 digit 之和。partial-good：select-k 用已混合的 k，禁止 `N_good` 再 mod 3、禁止 `+1`。512B：块从 `A[11:9]` 起。A[32] 在 8GiB 作业内活。11×11 `p_mix[i]=G[10−i]⊕G[11+i]` 不声称秩 11——统计覆盖，不是偷换双射。
- 硬件开销 vs 问题约束: 8 个 8:1 LUT + ~8 个 Z_3 CSA + 11 XOR，每核 10^2–10^3 GE。无每核大 ROM。GOOD_MAP 共享。不增端口/资源。在信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: Rau ISCA'91 伪随机交织与 Vandierendonck XOR-hash、Intel DRAM XOR decode 都是 **GF(2)** 线性/多项式模不可约多项式——进位权重是 2 的幂，等价 XOR 树。本卡把地址切成 3b 块、经非 `mod 3` 同态的 8→3 LUT（直方图 3,3,2），再在 `Z_3` 上做带进位权重 ×3 的 CSA。整数同态 `G ↦ G mod 3` 在 `v_3(δ)≥1` 时冻结；按位切块 + LUT 不是该同态，这是相对 Rau/XOR 的结构差，不是换名。Seznec 奇数存储器仍用整数 `mod N`。没有找到「基 3 carry-save 哈希打 DRAM 控制器占用」的 ISCA/MICRO/HPCA 论文。拉丁方/skewing（Budnik–Kuck、perfect Latin squares）是阵列访问的预先倾斜，不是运行时 3-adic 进位树。
- vs 本批其他卡: 与 M-1/M-4 的关键差别是**不算 `G mod 9`**：trit 熵完全来自切块树。M-5 的 GF2_11 只服务 2-adic 轴，不是 P-0105/CRXS 的 15×28 割切鲁棒 Latin 矩阵（CRXS 要打的是 base/phase 不变，不是因子 3 塌缩）。与 M-2 的立方多项式也不同（多项式仍在 Z 上，本卡论证的正是「不要在 Z 里做 mod 9」）。

## 判决理由
轴一通过：组合树因果合法；四个点名 δ 都留下至少一个活 3b 块；partial-good 不把 trit 树的工作 mod 3 抹掉；开销在只改 interleave 信封内。新颖性 DIFFERENT_APPROACH：用 `Z_3` CSA 打 3-adic 赋值本身，而不是把高位哈希加进 `G mod 9`。单活块 ⇒ `d0` 满 `Z_3` 是组合事实，多块进位相关与 11×11 秩是 T1 要打印的翻转计数，不是 T0 淘汰。偏置（送 T1 而非判 FUNCTIONAL_EQUIVALENT）：XOR/Rau 是 GF(2) 对象，不能表达本信封冻结的因子 3；若评测证明树的输出仍与 `G mod 3` 高度相关，再在 T1 杀掉。
