# Tier 0 · P-0105/M-4 · SNS

- 机制卡: mechanisms/P-0105/M-4.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: `x'=(x+7y) mod 2^12`，再 `SBOX[x'[11:4]] XOR y[7:0]`，只依赖当前地址。ROM 离线装填置换多项式，无运行时学习、无 stride FSM。
- 完美预测/无限带宽/零延迟: 无。剪切加法 + 256×8 ROM + fold384，1 mapper cycle。outstanding 128 覆盖。
- 关键边界（S=2MiB 稀疏子集、base/phase、partial good、512B/4K）: 无剪切时 S=2MiB 的 x 冻结，任何只吃 x 的 S-box 都会 n_DMC=1。奇数剪切让 4096 点的 x' 成全置换，行走进入 S-box 地址与 bank 窗；相位只旋转起点。非线性再打掉「线性像落在 384 的 2 幂剩余类并」这条 M-1 类残留。partial-good 仍是 2.25 KB 位图 + PE，S-box 不参与重映射。评估含 4608 B 与页内 base。粒 512B。
- 硬件开销 vs 问题约束: 256 B ROM + 12 bit 剪切 + 位图。不改 384/18432，无额外流量。信封内。S 必须按整数 `u^5+u^3+u mod 256` 装填（卡已排除 AES GF(256) 多项式，那不是置换）。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 剪切单独看接近 Harper/Jump 偏斜与 Budnik/Kuck 行旋转；S-box 单独看是密码置换多项式。合在一起——先用奇数剪切把 1D 格拧成对角，再用整数环置换多项式毁掉残留线性码，再 fold 到非 2 幂 384——不是标准 DRAM 图。Rau 多项式交织（ISCA 1991）是 GF(2) 上模不可约多项式，仍是 H 矩阵线性 XOR。Intel 内存 scrambling 服务 SSO/保密，不服务占用多重集。QPP 交织是 turbo 码 1D 二次置换，不是 shear+ROM。Kim/Prasanna perfect Latin square（ISCA 1989）打 2D 模板。标 DIFFERENT_APPROACH。S-box 段 discrepancy 是实验性的（无 Weil 界），这正是 T1 该测的，不是 T0 否决点。
- vs 本批其他卡: 与 M-1 XOR Latin、M-2 平面导数、M-3 双哈希概率、M-5 Z_n 互素仿射明确不同代数对象。P-0103 ORCM 的立方在 Z_9 上注入奇数因子，不是 12 bit 剪切+256 项 S。无兄弟重复。

## 判决理由
轴一通过；结构命题「线性像可能被 384 的 2 幂因子成团，剪切保证大步长仍走、S-box 拆线性码」可供顶会论证；非 EXACT_MATCH。进入 T1。T1 必须按卡内 ROM 表与 12 bit 截断建模，并扫 base 看 fold 后占用是否真与相位无关。
