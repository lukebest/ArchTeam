# Tier 0 · P-0101/M-5 · stride-class 可配 XOR 矩阵

- 机制卡: mechanisms/P-0101/M-5.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 每请求只读当前 class 的 14×24 mask。m CSR 作业开始写；飞行中只读。无 stride 探测器（v1 明确排除）。
- 完美预测/无限带宽/零延迟: 不探测未来 S。错 class 写成优雅降级/负对照，不假设固件总写对。
- 关键边界: 匹配 class 上占用坐 ~K，禁止 >K。m=21 秩≤12 → ≤4096。不跨 DMC。无 core_id。
- 硬件开销: ~20kGE / 336B 配置，仍是译码侧，不改 DMC/bank 数。

## 轴二 新颖性
- vs 文献: 按 stride/page size 换 XOR 矩阵是可编程 DRAM map / BIOS interleave 的默认能力（Intel XOR decode 可配；Rau 的 programmable interleave）。8 档 14×24 不是新族。
- vs 本周卡: 把 M-1/M-2 的硬线窗做成表。P-0102/M-1 滑动窗、M-4 bit-mux 是同一「换支撑」命题。

## 轴三 质量
- 机制完整度: 四档语义、错 class 负例、写表时机违例都写了。
- 可证伪性: 匹配 class 占用 ~K；高 S+低窗应回到 9～256。
- 增量: 配置化，不是新不变量。

## 理由
可行性通过。新颖性：可编程 XOR 矩阵。不进 Tier 1。
