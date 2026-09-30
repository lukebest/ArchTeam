# Tier 0 · P-0198/M-2 · CSR Collective Spine via RBRG

- 机制卡: mechanisms/P-0198/M-2.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: Classifier 将集合 opcode 标 SPINE_TREE、普通读写标 RING_P2P；集合 flit 短跳入本地 RBRG，经 8-entry Tag CAM 收集 child bitmap，齐后在有界 512b latch 上 REDUCE，再沿静态树边 DISPATCH。因果链是「扇入从单槽环面挪到 RBRG 脊骨边 → 环上同时争槽源数下降 → 集合 makespan 下降；P2P 仍走环」。spine-off 须恢复坍塌（HARD-1）；CAM 满显式回退 RING_P2P，禁止静默丢弃（HARD-4）。
- 完美预测/无限带宽/零延迟: 树边表按 **集合类静态**；「SYNC/到达时刻不进入调度」。COLLECT 等待绑定有限 outstanding 子到达，非无限带宽。机制 1–3 拍 + 基线链路延迟。
- 约束边界: **512b latch ×≤8 CAM 项** 是 RBRG 上的归约暂存寄存器，容量上界明确；卡声明「非 highway flit 队列、不把环改成 buffered NoC」。 gatekeeper 接受该边界：**不是**过路 flit 的深度队列，而是桥接处有界 reduce 状态；若实现把 latch 扩成多 flit highway FIFO 则越界——T1 须按「每活跃 txn ≤1 flit 宽」审计。DV200 12+2、CHI 四环、P2P+全集、有限 outstanding 在评估计划内。alltoall 拆多树/分段脊骨，深度假设可证伪。
- 硬件开销 vs 问题约束: ~0.01–0.03 mm²/RBRG、~5–15 mW。相对 SoC 可接受；不增每方向 highway 槽。T1 风险：CAM=8 在并发集合下溢出率；溢出回退须计入指标，不得靠「假完整」刷分。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: Mellanox SHARP / Streaming Aggregation（SwitchIB-2 / Quantum；Graham et al. SHArP workshop；后续 SAT 评估）在 **机柜 InfiniBand 交换机** 上做树归约/广播，非片上 bufferless CHI 环。FANOUT/FANIN（Krishna et al., MICRO 2011）在 mesh 上做单周期多播分叉与多到一聚合。MultiTree（ISCA 2021）做分布式 DL 多生成树与调度共设计。近期 collective-capable NoC（如 FlooNoC 类）在 AXI 织物上挂聚合。CSR **不是**上述任一的门级复制：结构命题是「在 **无缓冲 CHI 四环 + RBRG 桥** 信封下，把集合重映射到 RBRG reduce/mcast 脊骨、P2P 留环，并用 8-CAM + 1-flit latch + 显式 RING_P2P 回退守住 bufferless 语义」。相对「硬件集合树」家族是领域特化，但相对本信封是路径集合变更对象，标 DIFFERENT_APPROACH（**非** EXACT_MATCH；与 SHARP 近亲，见 Close call）。
- vs 本批其他卡: 异于 M-1/M-4（环上造空位/注入洞，不改集合路径集合）；异于 M-3（方向角色，仍在环面）；异于 M-5（把闲 Snp 环时分给 Dat，仍是环容量再分配，不是树归约引擎）。CSR 专打集合 Amdahl；CRRF 专打 Dat/Snp 不对称利用率——可互补，非重复。无 EXACT_MATCH。跨批 DRAM interleave 无孪生。

## 判决理由
轴一通过：静态类树 ≠ 完美预测；有界 latch 在「非 highway 队列」声明下可接受；回退与消融写清。新颖性足够：bufferless 环上双路径（环 P2P / RBRG 集合脊骨）是本题信封下的可发表结构，而非又一张通用 SHARP 复述。进入 T1。T1 必须：（1）审计 latch/CAM 是否滑成 flit 队列；（2）报 CAM 溢出回退计数；（3）alltoall 多树残差与 spine-off 消融。

Close call: 若把「凡硬件集合树」一律打 FUNCTIONAL_EQUIVALENT，可改判 REJECT / INCREMENTAL；本判决因 **路径重映射 + bufferless 守门 + RBRG 位点** 的结构差给予 PASS_T1。
