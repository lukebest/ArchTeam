# Tier 0 · P-0106/M-4 · HAVM

- 机制卡: mechanisms/P-0106/M-4.md
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `ok=V[ha][pipe*48+bank]` 与 3 态 PASS/REDIRECT/ERROR 只看当前译码目标与 HA 上的 valid mask / spare CSR。无未来请求、无 stride 神谕。因果性本身成立。
- 完美预测/无限带宽/零延迟: 无预测。PASS 路径与译码并行 +0 cycle，不是假设零 DRAM 延迟。ERROR/NAK 走控制，不把 PASS 路径变成 0 拍神谕。
- 关键边界（live-set 可逆、禁止跨 DMC 借 bank、3-adic、512B/4K）: **FAIL（live-set 可逆 + 症状双条件）**。问题要求：不得命中退役 bank **并且** 映射在活集上可逆、合格标准随 `N'` 变（只禁不重映射会把死原像叠到活邻居，额外失衡）。本卡是闸门不是主 interleave：
  - ERROR/poison：死目标不到 DRAM（命中率 0），但那些请求吞吐为 0，没有把地址**重映射到活集**；不是活集上的双射。
  - REDIRECT：所有死原像改写到该 pipe 的 **1 个 spare slot**。卡自证 25% 退役、上游均匀打 48 槽时约 12 个死槽叠进 1 个 spare，热度 ~13×——这正是症状里的 stacking，只是叠到预留活槽而不是「最近邻居」。多对一，**不可逆**。
  - spare 不得跨 DMC/pipe：遵守「不能跨 DMC 借 bank」，但因此没有备用容量可偷，闸门无法恢复并行度。
  - 3-adic / `gcd(δ,N')`：完全不碰模数与仿射，忽略点名的奇数因子交互。
  满好时闸门不降 BW 不能挽救：退役才是本问题。卡自己写 REDIRECT+25% 的 BW 相对压缩方案 `0.3～0.7`、不宣称过 0.85。
- 硬件开销 vs 问题约束: 192×96b=2.25KB flop + 336B spare CSR，CAM-less，面积在信封内。失败不在面积，在机制对症状。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于 **valid-mask 拦截 + poison/NACK / 单 spare 重定向**：Linux `hwpoison` / `memory_failure` / page retirement 把坏页踢出分配器（ERROR 路径）；内存控制器 valid 位与 NoC 非法目的地 NACK；DRAM 单 spare 行/列把多处缺陷 mux 到同一冗余（US6671822 一类 surrogate way——正是 stacking）。CXL memory sparing（bank/row/cacheline sparing）是用备用资源**替换**同 DPA，不是 HA 闸门。Chipkill-Correct ECC（Dell/IBM）在编码层扛颗粒故障，不改 bank 图。不是新路由对象。
- vs 本批其他卡: 与 M-1/M-2/M-3/M-5 的压缩双射明确不同——卡自称安全网不是主方案。跨批无主卡重复（P-0103/P-0105 的位图用于 select-k 压缩，不是 NAK）。无 EXACT_MATCH。

## 判决理由
逻辑约束失败：只 NACK/单 spare 而不把原像均匀压到活集，直接违反 P-0106「必须在 live set 上可逆 + 只禁不重映射会额外失衡」。不是缺仿真数字。质量 FLAWED。轴一 FAIL ⇒ 不进 T1。拒绝原因：症状是死桶命中**与**失衡，闸门只挡前者并在 REDIRECT 下再现 stacking。
