# Tier 0 · P-0105/M-2 · BPPB

- 机制卡: mechanisms/P-0105/M-2.md
- 判决: REJECT
- 可行性: FAIL
- 新颖性: DIFFERENT_APPROACH
- 质量: FLAWED
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `DMC=(7x+11y+5·(xy mod 2^12)) mod 384` 只看当前地址的 2 MiB 内外坐标，无未来预测、无跨请求状态。因果性本身成立。
- 完美预测/无限带宽/零延迟: 无。12×12 乘 + 移位加，2 mapper cycle，outstanding 128 可藏。
- 关键边界（S=2MiB 稀疏子集、base/phase、partial good、512B/4K）: **FAIL**。问题要求占用多重集不随 base 变（n_DMC 变化 <10%，min/mean BW 相对差 <5%）。本卡自己给出残留类：`x=1` 时斜率 `B+Cx=16`，`gcd(16,384)=16`，`n_DMC=24`；`x≡17 (mod 128)` 时 `11+5x≡0 (mod 128)`，`n_DMC | 3`。S=2MiB 的 4096 点在这些相位上塌回 24 或 3 个 DMC——这正是 `G mod 384` 的 wrong-phase 症状，不是待测数值噪声。机制把「base 滑动稀疏子集」重新变成「base 选择循环长度」，未满足点名的 phase 边界。partial-good 位图与 512B/4K 处理合格，但过不了主边界。
- 硬件开销 vs 问题约束: 乘法器 + 2.25 KB 位图在信封内；失败不在面积，在映射代数。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 相对 DRAM XOR hash / 整数取模 / 加性 skew（Harper/Jump skewed storage，IEEE TC 1987；Budnik/Kuck 线性偏斜，IEEE TC 1971）是 DIFFERENT_APPROACH：把平面函数导数 `Δf=AΔx+CΔx·y` 做到 Z/384Z 交织。相关但不等价：LTE QPP 交织 `f1 i + f2 i^2` 是 1D 置换多项式（通信，不是 DRAM bank 图）；Lee 非线性偏斜（IEEE TC 1991）与 Kim/Prasanna Latin square（ISCA 1989）打的是 2D 阵列模板冲突，不是 1D AP 的相位不变。无 EXACT_MATCH。
- vs 本批其他卡: 卡内已声明与 M-1 XOR Latin、M-3 双哈希、M-4 剪切+S-box、M-5 Z_n 互素仿射不同构。P-0103 无 xy 双线性项。无兄弟重复。

## 判决理由
逻辑约束失败：平面项在复合模 384=2^7·3 上不能消去 gcd 残留类，占用随 base 在 {3,24,384} 间跳，直接违反 P-0105 的 start-address/phase 不变性。不是缺仿真数字。质量 FLAWED，不进 T1。
