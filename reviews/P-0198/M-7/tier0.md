# Tier 0 · P-0198/M-7 · CW/CCW 最短争用弧方向选择

- 机制卡: mechanisms/P-0198/M-7.md
- 判决: KNOWN_CONFIRM
- 可行性: PASS
- 新颖性: EXACT_MATCH
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 主规则因果成立，但名字大于机制。`hop_cw=(D−S) mod N` 与 `hop_ccw=N−hop_cw` 取较短者，把单 flit 沿途槽·拍从最多 `N−1` 收到 `⌊N/2⌋`。少占的槽还给沿途残差注入，扇入时有可能缩短根前弧上的 straggler。这就是最短路，不是沿弧实测争用：卡写 `exposure≈hops_dir`，并未读取弧上占用。打平用的本地/1 拍邻居空槽只覆盖偶数 `N` 的对径，卡自己要求主收益必须来自 hop 比较，且 A3 相对 A1 不可分则不得把传感写成原因。固定 CW 若与 hop-only 不可分，收益为零——这条自我约束正确。
- 完美预测/无限带宽/零延迟: 未触犯。禁止全局占用向量、多跳窥探和「选当前最空的整段弧」。邻居线锁 1 cycle，不准等更远节点。同拍占用则注入失败，禁止同拍改向双口投机。集合根 `dst_id` 来自流量发生器或 opcode 旁路，是工作负载已知目的，不是对空槽到达的预测。不增加槽数。
- 约束边界（bufferless 单槽、无 flit 队列、CHI 四环、RBRG、DV200 12+2、点对点+全集集合、有限 outstanding）: 守住。方向在注入点选定，过路仍绝对优先；失败停在既有 staging，不建队列。`N≤16` 与 12 top + RBRG 附着余量同信封，四通道可复制。评估点名扇入（gather/reduce/allreduce）、多对多、扇出 broadcast 与读写两侧，禁止用平均 hop 代替 makespan，禁止未声明 `p_mix`。单环/只均匀读被标成 reduced-bbox。
- 硬件开销 vs 问题约束: 匹配。5b 加减或 64b LUT、4b 比较、1b `DIR`、可选 2×1b 邻居线，`<4 kGE`、SRAM 0。不增加缓冲与槽。邻居线是实现细节，不是第二套占用指标。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 主规则与双向环最短方向选择逐字相同：顺时针距离 `(D−S) mod N`，逆时针取补，选短的一侧，直径 `⌊N/2⌋`。这是环拓扑的定义性路由，不是新算法；Dally & Towles, *Principles and Practices of Interconnection Networks*（2004）与 Duato, Yalamanchili, Ni, *Interconnection Networks: An Engineering Approach* 把双向环的最短路当基本路由。对径打平任选一侧也是该规则的一部分。真正按争用改方向的工作反而会故意走长弧以平衡负载，例如 counter-rotating ring 上的 load-balanced routing（Wan 等, "Load-balanced routing in counter rotated SONET rings"；以及按预期需求加权选方向的 US 5546542）。本卡明文不要历史、不要全局占用，因此没有进入那条更强、也更易滑向预测的线。1 拍邻域空槽打平是最小自适应里「等长时看本地空闲通道」的标准特例，覆盖面卡自己写成 `<5%`。把该规则叫成「最短争用弧」是重新命名，机制仍是 hop 最短路。
- vs 本批其他卡: M-6/M-8/M-9 管的是何时许可注入或过桥，M-10 管的是同一节点多个 header 谁拿走空槽；本卡只决定这一 flit 走 CW 还是 CCW，比较器输入是目的编号不是相位、类别或年龄。与另外四张无功能等价。它是这批里唯一的方向政策，但是已知政策。

## 判决理由
可行性通过，且规格完整到可以当基线冻结：无预言、无队列、消融把「传感」和「最短路」拆开。新颖性是精确匹配，不是近似。确认其价值仅在于：后续不得再把双向环最短方向当成未解机制；对径 1 拍传感不构成新途径。不值得作为研究提案进 Tier 1。KNOWN_CONFIRM / INCREMENTAL / 不进 T1。若平台默认已是最短方向，则连经验增量都没有，消融 A0 必须先记录默认策略——卡已这么写，确认时保持该条件。
