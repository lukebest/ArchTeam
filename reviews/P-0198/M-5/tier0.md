# Tier 0 · P-0198/M-5 · CRRF Channel–Ring Rebind Fabric

- 机制卡: mechanisms/P-0198/M-5.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: Rebind FSM 在 COLL_EP 将 Snp 环硬件按 epoch 时间复用为 ghost Dat（例 Dat:Snp≈7:1）；Req 环 SYNC flit 对齐各节点 2b epoch；NIC/RBRG 4×4 one-hot 绑定；Snp **仅 SNP_EPOCH 注入**，DAT_EPOCH 对 Snp 口 stall（无队列）。因果链「Dat 饱和而 Snp 闲 → 时分把闲置物理环划给 Dat 形态 → Dat 有效槽上升 → 集合/读坍 makespan 改善」，代价是 Snp stall。rebind-off 须使 Dat 侧恶化；duty 可证伪。
- 完美预测/无限带宽/零延迟: SYNC **只对齐 epoch 计数**，不知未来消息——卡明确「SYNC ≠ 预测」。不增加单环每拍槽数；第二 Dat 高速来自复用已有 Snp 导线。FSM 由软件/运行时类提示或本地计数阈值切 P2P/COLL_EP，非消息级到达神谕。流水 1–2 拍。
- 约束边界: 零和仍是每物理环每方向每拍 1 槽；无 flit 队列。Req/Rsp 本假设下不重绑，降低一致性风险。HARD-2：绑定 channel↔ring epoch，不冻结地址高位；ghost/主 Dat 目的分布须在 512B 窗下展示未坍成单槽。Killer：Snp makespan 在 7:1 下可能 1.0–1.4×——必须报告，不得刷掉。DV200 满包络。
- 硬件开销 vs 问题约束: ~0.005–0.015 mm²/top、~3–10 mW；面积在交叉与绑定控制。符合「不加 buffer、重绑已有环」。T1 风险：CHI 通道语义/一致性在 ghost Dat 上的正确性；SYNC 占 Req 偶发槽；epoch 对齐误差 ≤ 环周延迟须 cycle 级建模。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 静态 TDM NoC（如 S4NoC，statically scheduled TDM）与动态 TDM 虚电路把时隙分给连接，通常 **预留槽**，闲置浪费除非调度器重算。VC/子通道带宽窃取、物理通道 remapping（如 TeraNoC 类 request/response 通道重映射）在 mesh/多通道上再平衡。CHI 本身 Req/Rsp/Snp/Dat 为独立通道语义，工业实现多为静态 1:1。CRRF 的对象是：**在 bufferless CHI 四独立环上，用 Req-SYNC 对齐的 epoch 把空闲 Snp 环硬件时分为 ghost Dat，Snp 无队列只在 SNP_EPOCH 注入**——不是通用 TDM 调度器复述，也不是 VC 信用再分配。标 DIFFERENT_APPROACH；非 EXACT_MATCH。
- vs 本批其他卡: 异于 M-2 CSR（CSR 改集合路径到 RBRG 树并做 reduce；CRRF 留环面、偷 Snp 时隙给 Dat）。异于 M-1/M-4（造空位/注入洞，不跨通道重绑）。异于 M-3（方向角色，不改通道–环绑定）。CBC/AODI/DPH 在通道内；CRRF 跨通道——正交层。无 EXACT_MATCH。跨批 DRAM 无孪生。

## 判决理由
轴一通过：SYNC/epoch 粗相位 ≠ 完美预测；无 flit 队列；Snp killer 与 duty 可证伪写清。新颖性：CHI 四环信封下的 Channel–Ring 时分重绑是可发表结构（Dat 瓶颈 Amdahl + 闲置 Snp 零和再分配）。质量 ISCA_WORTHY。进入 T1。T1 必须强制 Snp 类 makespan/完成数、duty∈{3:1,7:1,15:1} 扫描、rebind-off 消融，并证明 ghost Dat 未触发 HARD-2 目的坍缩。
