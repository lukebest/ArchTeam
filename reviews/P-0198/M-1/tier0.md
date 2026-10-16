# Tier 0 · P-0198/M-1 · CBC Circulating Bubble Calendar

- 机制卡: mechanisms/P-0198/M-1.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: Bubble FSM + 64×8 日历按 **流量类 epoch**（P2P / 扇入 / 扇出）编程 duty 与相位；节点将 eligible empty 标为 bubble tag 并在环上循环；注入仅进非气泡空槽或按优先级窃取气泡。因果链是「日历强制空槽份额 → 可见注入机会上升 → 扇入相 inject-fail 下降 → makespan 缩短」。消融 calendar-off 须使已坍集合变差（HARD-1），卡内写明。
- 完美预测/无限带宽/零延迟: 日历绑定 **拓扑/集合类 epoch**，明确「非预测到达」「非消息级」。不假设未来消息时刻，不增每方向 highway 槽数，不宣称无限带宽。插入 1–2 拍；气泡一圈延迟=基线链路延迟，非零延迟。
- 关键边界（bufferless 单槽、无 flit 队列、CHI 四环、RBRG、DV200 12+2、点对点+全集集合、有限 outstanding）: 气泡是 **空槽编码 + 1b tag + 4b age**，不增加 flit 缓冲深度；每方向每拍仍 1 槽。CHI 四环各自 Bubble FSM。评估计划钉满 12+2、P2P+全集、有限 outstanding；禁止单环/仅均匀读/完美预测减箱。Age≥15 强制退化为普通空槽，破聚团。RBRG 不承载本机制状态。
- 硬件开销 vs 问题约束: ~0.002–0.005 mm²/top、~1–3 mW；无 flit 队列。开销在 bufferless 信封内。T1 风险（不淘汰）：P2P epoch 若 duty 过密会把均匀读峰值后 goodput 压成另一类坍塌——卡已要求稀疏 1/16–1/8 并测 P2P 中性区间。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: Puente et al. Adaptive Bubble Router（ICPP 2001 / JPDC）与 Flit Bubble Flow Control（Chen & Enright Jerger et al., IEEE TC；「Leaving One Slot Empty」）在 **有缓冲** VCT/wormhole torus 上用「留一空缓冲槽」做死锁避免——依赖队列深度，不是 bufferless highway 上的可窃取标签气泡。Prevention Slot flow control（IET Computers & Digital Techniques）用模 N 轮转 **禁止注入** 制造空槽，目标亦偏死锁/公平，无 bubble tag、无按流量类 epoch 的 steal/keep 优先级、无 age 退化。经典 slotted ring / token ring 有循环空槽，但是固定槽帧语义，不是「日历把 raw empty **制造**为带 age 的气泡对象再按集体/P2P 窃取」。CBC 的可论证对象是：**无缓冲环上把空槽提升为一等几何对象，用类 epoch 日历制造密度并用 steal 规则服务扇入**——相对上述文献 DIFFERENT_APPROACH，非 EXACT_MATCH。
- vs 本批其他卡: 异于 M-3 DPH（永久 CW/CCW 角色分区，无日历）；异于 M-4 AODI（按需对向偏转造 1 拍注入洞，无气泡对象）；异于 M-2 CSR（路径改到 RBRG 树，不改环上空槽几何）；异于 M-5 CRRF（跨通道时间复用物理环，不制造气泡）。CBC 与 AODI/DPH 可正交组合，但本卡独立：制造循环空位 vs 挪走过路 vs 永久分区。无本批 EXACT_MATCH。跨批 P-0101..0106 为 DRAM interleave，域不同，无结构孪生。

## 判决理由
轴一通过：类 epoch 日历 ≠ 消息级预测；气泡为编码非队列；信封与消融写清。新颖性是 bufferless 信封下「可窃取循环气泡 + 日历密度」结构，区别于有缓冲 Bubble FC / Prevention Slot / 令牌环。质量足以支撑顶会论证（扇入 inject-fail → 气泡密度 → makespan，calendar-off 消融，P2P duty 过密反例）。进入 T1。T1 必须分流量类报 makespan/collapsed，并扫 duty 对均匀读峰值后坍塌的副作用。
