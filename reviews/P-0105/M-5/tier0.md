# Tier 0 · P-0105/M-5 · AB2A

- 机制卡: mechanisms/P-0105/M-5.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `HA=(11x+13y) mod 96`、`bank=(5x+7y) mod 48`、`die/pipe` 各 1 XOR，纯当前地址。坏 bank 不反馈进仿射系数（避免数据相关毁掉平移不变式）。
- 完美预测/无限带宽/零延迟: 无。移位加 + Barrett 折合，1 cycle。无神谕。
- 关键边界（S=2MiB 稀疏子集、base/phase、partial good、512B/4K）: 互素 ⇒ S=2MiB 冻 x 走 y 时 HA/bank 是 Z_n 置换，占用多重集 {42×32, 43×64} 等只旋转标签。补洞：die/pipe 行走抽头改到 y[5]/y[6]（addr[26]/[27]），避开 HA 模数 96=2^5·3 的 2 幂核，否则 die/pipe 成为 HA 的函数、联合 n_DMC 塌成 96。这是拓扑相关的正确修补，不是预言。partial-good 位图 + PE。小步长对偶核问题被「AP 稠密、y 随 8GiB 窗走」带过，属 T1 风险而非 T0 因果失败。
- 硬件开销 vs 问题约束: 两路 12 bit 移位加 + Barrett + 位图。不改 384/18432。信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于线性偏斜族：Budnik/Kuck *Organization and Use of Parallel Memories*（IEEE TC 1971）、Wijshoff/van Leeuwen *On Linear Skewing Schemes*（IEEE TC 1987）、Harper/Jump skewed storage（IEEE TC 1987）。`gcd(a,M)=gcd(b,M)=1` 的二维仿射 `ai+bj mod M` 是冲突免访问的教科书构造。prime-modulo / CRT 银行系统（BSP 等）同属「与模互素则满轴置换」。die/pipe 抽头避开 2 幂核是对本信封 96=32×3 的参数修补，不是新映射类。
- vs 本批其他卡: 与 M-1 同命题不同环；与 M-2/M-3/M-4 不同构。P-0103 MRFI 的 CRT+Feistel 打 Z_9 奇数因子，不是 2D 互素 MAC。无 EXACT_MATCH。

## 判决理由
可行，且对 S=2MiB 有干净的置换不变式，但是线性偏斜 + 互素系数的直接实例，FUNCTIONAL_EQUIVALENT / INCREMENTAL。核抽头修补不够支撑 ISCA 机制卡。不进 T1。
