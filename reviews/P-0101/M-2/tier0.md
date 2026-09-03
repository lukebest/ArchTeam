# Tier 0 · P-0101/M-2 · 2-adic 与 9-way 分离 XOR 置换

- 机制卡: mechanisms/P-0101/M-2.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `u=M·d`（`d=addr[32:21]`）、`c=ROM(h)`、`flat=c·2048+u` 均为当前地址组合函数。M 与 ROM 只在 boot/熔丝写；飞行中不改。无 stride 输入。
- 完美预测/无限带宽/零延迟: 无预测器。XOR 树 ~4 门 + ROM 可寄 1 拍。不是 0 拍。
- 关键边界: 明确占用上界仍是 K，目标逼近 K 不是超过 K。`rank(M)=11` 且 h 含 ≥1 个独立区分位时 `|{(u,c)}|→4096`。诚实缺口：静态 12b 窗在 `S=512KiB` 只到 4096≪K=16384。负对照「h 改冻结位 ⇒ 占用掉到 2048」可证伪。无第二次 `mod 18432`，避免 `gcd(2^{m-9},2^{11}·9)` 塌到 9。粒度 512B；bank∈[0,47]；不改 384/18432。partial-good 不跨 DMC。
- 硬件开销 vs 问题约束: 132b 矩阵 + 64b ROM，~0.4kGE，0 大 SRAM。只改 interleave。注意：即便 c 取满 9 值，每个 c 的像仍落在长度为 2048 的 flat 块（~43 个 DMC）内，DMC 占用是否到 384 取决于 M 的整数域散射，卡只保证 bank 占用 2048～4096。

## 轴二 新颖性
- vs 文献: FUNCTIONAL_EQUIVALENT 于 Seznec/Gao CRT 切开 `Z_{2^a}×Z_q`，再在 2-adic 段做 XOR 置换（Intel DRAM XOR、Rau I-Poly、Frailong XOR-scheme）。教科书 CRT(`G mod 2048`,`G mod 9`) 在 `S_g=2^{12}` 时前者冻死、占用只剩 9——本卡把 2-adic 源改成区分位 XOR，这是「高位进 XOR 哈希」的标准修法，不是新环上的新运算。素数模、偏斜阵列、Latin square、bit-reversal 均非本卡。
- vs 本批其他卡: 与 M-1 同命题（区分位饱和 K），拼装底从 4096 换成 2048、9-way 改为区分切片。与 P-0103/MRFI 同用 `Z_{2048}×Z_9`，但 MRFI 把仍活 2-adic 注入冻结的 `Z_9` 打 `3|δ`；本卡打的是 2 幂步长低位冻结，注入方向相反，非 EXACT_MATCH。与 P-0105/CRXS 单张双侧 XOR 矩阵相比，本卡是 CRT 打包的高位 XOR，功能更窄（钉在 2MiB 窗）。P-0106 是 live-set，无重复。

## 判决理由
轴一通过：组合、承认鸽笼、相对 `G mod N` 的 9→4096 代数成立。淘汰结构化原因：CRT 切开 + 2-adic XOR 是已知交织家族的拓扑特化（FUNCTIONAL_EQUIVALENT），质量 INCREMENTAL。关键胜利 9→4096 与 M-1 同类，且 flat=`c·2048+u` 仍把点关在 9 个 2048-块里，不自动给出 M-3 的 DMC 铺满。不进 T1。
