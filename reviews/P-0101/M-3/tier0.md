# Tier 0 · P-0101/M-3 · 层次正交放置

- 机制卡: mechanisms/P-0101/M-3.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: Stage A `dmc0=ENC3(addr[25:24])·128+addr[32:26]`，Stage B `bank` 来自 `addr[23:21]` 等，均为当前地址组合。可选 SK 仅 boot 写。无 stride 神谕、无飞行中改表。
- 完美预测/无限带宽/零延迟: 无。无 SK 纯组合；有 SK 为 96B 1R + 模加，1 cycle。outstanding 128 覆盖。
- 关键边界: **不**宣称 bank 占用 >K/N。成功标准是 DMC 占用 `min(K,384)/384=1`：`K=4096>384`，铺满 384 个 DMC 不违反鸽笼（鸽笼锁的是 18432 bank）。Stage A 用 9 个区分位喂 `384=128×3`，AP 上这些位满变 ⇒ `|π_DMC|=384`。bank 层每 DMC ~`K/384≈10.67` 点，`10.67/48≈22.2%=K/N`。partial-good：bank clip 到 0..47，不跨 DMC。512B 粒、不改 120/384/18432。
- 硬件开销 vs 问题约束: 组合抽取 `<0.2kGE`；可选 SK 96B flop ≈4.6kGE。只改 interleave。T1 风险（不淘汰）：Stage A 只吃 `addr[32:24]`，`S=512B` 时这些位每 16MiB 才动，顺序流会在单个 DMC 上粘住——必须与大步长一起报，不能用 2MiB 成功掩盖。

## 轴二 新颖性
- vs 文献: 层次 channel/rank/bank 译码本身是 DRAM 标准；XOR-scheme、I-Poly、Intel/HBM hash 把高低位混进同一索引。本卡的可论证对象不是又一张哈希，而是鸽笼下的**目标函数切换**：接受 bank 占用 ≤22.2%，把 min/mean BW 的 roofline 改到「K 点是否盖住 384 DMC」。`384=128×3` 用 7b 接线 + 3-way 满射，而不是 `G mod 384`（`gcd(4096,384)=128` → 3 个 DMC）。这与 Seznec 素数模、Harper 偏斜、Latin square、bit-reversal 都不同构：那些仍在追求桶数或 2D 模板，不陈述「N_DMC 可被 K 盖满、N_bank 不能」。标 DIFFERENT_APPROACH。
- vs 本批其他卡: 相对 M-1/M-2：同一 K 个点，本卡先铺 DMC，避免 `flat` 连续块 `/48` 挤进 ~86 个 DMC（卡内对照 ×3～×4.5）。相对 P-0105/AB2A（Z_n 互素 2D 仿射、INCREMENTAL）和 CRXS（GF(2) 双侧抽头、INCREMENTAL）：那些打 start-address/phase 不变性；本卡打 P-0101 的「空桶不可避免之后 BW 不要塌到 9 个 DMC」。相对 P-0103 奇数因子注入，症状是 `3|δ` 不是 2 幂窗冻结。无 EXACT_MATCH。

## 判决理由
轴一通过：DMC 占用 384/384 与 bank 占用 ≤22.2% 同时成立，不证伪本题。新颖性是鸽笼约束下的分层放置目标，不是 XOR/CRT 换名。结构足够支撑顶会论证（9 DMC vs 384 DMC 的 Little/roofline，以及 M-1 连续块对照）。非 EXACT_MATCH。进入 T1。T1 必须按层计数 die/HA/DMC/bank，并扫 `S=512B` 看高位 DMC 是否粘死。
