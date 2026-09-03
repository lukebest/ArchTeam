# Tier 0 · P-0101/M-5 · stride-class 可配 XOR 矩阵

- 机制卡: mechanisms/P-0101/M-5.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 选中 class 后 `idx=T[class]·G[23:0]` 是当前地址的组合 XOR。`m` CSR 在作业开始写，飞行中只读；换表须空闲或复用栅栏。不读未来请求。
- 完美预测/无限带宽/零延迟: **监视项：stride-class 神谕。** v1 明确不做硬件步长探测器，只接受软件/BIOS 写 `m`。这是 boot/作业描述级配置（与 Intel BIOS DRAM map、P-0102 mux 同类），不是请求路径上「永远猜中下一个 S」的负载型预测器。收益在匹配 class 上成立，写错则退回低窗饥饿——卡要求负对照，不把神谕藏进关键路径。评测夹具不得把 `S` 每拍喂给 CSR。无 0 拍、无无限 BW。混步长作业不在 v1 范围，属能力边界不是因果违例。
- 关键边界: 各档秩拉到 `min(14,33-m)`，`m=21/20/19` 占用上界 4096/8192/16384=K，不宣称 >K。`S=512B` 时 K>N，上界改 N。粒度 `addr>>9`。不改 384/18432。partial-good 仍 48 槽内。
- 硬件开销 vs 问题约束: 8×14×24=2688b flop + XOR 阵列 ~20kGE，译码 1R 语义（8:1 行选择，不是每请求读整表）。只改 interleave。飞行中写表禁止。

## 轴二 新颖性
- vs 文献: FUNCTIONAL_EQUIVALENT 于可编程 XOR-scheme / I-Poly 系数表（Rau ISCA 1991、Frailong 1985、Intel DRAM XOR fuse、Vandierendonck XOR hash）。8 档按 `v2(S)` 换矩阵是「为每种 stride 选支撑」的 profile-guided 配置，不是新哈希族。单张对每个割切两侧都有抽头的矩阵（P-0105/CRXS、HSRAI affine）在**不知道 m** 时已经覆盖同一组 2 幂割切，本卡被该静态构造支配。
- vs 本批其他卡: M-1/M-2 是本卡 `m=21` 档的硬线特例。与 P-0102/M-1 滑动窗（软件 `m*`）、P-0102/M-4 14×bit-mux 功能等价（bit-select 是每行一个 1 的 XOR 矩阵）。P-0103 奇数环、P-0106 live-set 无重复。无 EXACT_MATCH。

## 判决理由
轴一通过：拒绝把作业启动 CSR 判成请求路径完美预测；鸽笼数字诚实。淘汰结构化原因：可编程 XOR 矩阵按 stride class 换表是已知交织配置的薄层（FUNCTIONAL_EQUIVALENT），质量 INCREMENTAL，且被「一张双侧支撑矩阵」支配。不进 T1。
