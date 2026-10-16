# Tier 0 · P-0198/M-10 · 环上年龄/集合进度优先仲裁（注入侧）

- 机制卡: mechanisms/P-0198/M-10.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 局部成立。过路优先不变；只在 `slot_occupied=0` 且本 NI 该方向有多个 ready header 时，`Score=Age+K·Class` 把气泡从 RR 改分给集合类（复位 `K=4` 时 `all*` 相对 P2P 静态 +12），Age 饱和到 15 后长期饿着的 P2P 可以反超刚到的 `all*`，避免活锁。这提高的是 straggler 在本节点的注入份额，不改变环的 `μ=1`，也不降低 offered outstanding。单候选时比较树退化，`f_a=0`，卡禁止用该情形写收益，正确。它管不到别的节点上的过路占用，所以不能单独解释均匀读崩塌或跨环传播。
- 完美预测/无限带宽/零延迟: 未触犯。年龄只数本节点注入失败拍，分数不出 NI，无邻域占用、无全局准入。不增加槽。仲裁 1 拍，过路路径不进比较树。集合类来自发生器标签或 opcode 表，不是对屏障剩余时间的在线预测。
- 约束边界（bufferless 单槽、无 flit 队列、CHI 四环、RBRG、DV200 12+2、点对点+全集集合、有限 outstanding）: 通过，带一条必须守住的边界。4 深 staging 被限定为 header-only、位于 NI、不出环；数据拍仍走既有 Dat 路径，不在织物里排队。这是在端点已有 outstanding（读 512/写 256）里选至多 4 个已就绪头，不是用队列把突发吸进环。若实现把这 4 槽扩成数据 FIFO 或放到 highway 上，则违反信封——卡文本没有这么做。每通道每方向单独仲裁，与四环一致；不碰 RBRG。评估要求 P2P 与 `all*` 并发才能露出多候选，均匀读/写 makespan 变差超过 8% 判失败，0.85 按类而不是按平均。这些都对准 endpoint。
- 硬件开销 vs 问题约束: 可接受。14×4×2×4×4b 年龄寄存器约 1.8 kbit，比较树 `<8 kGE`，无 SRAM、无跨节点分数总线。不增加 highway 槽。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 功能等价于「本地 oldest-first + 静态优先级，并用年龄防止低优先级饿死」。Abts & Weisser, "Age-Based Packet Arbitration in Large-Radix k-ary n-cubes," SC 2007：以年龄决定谁赢，本卡把年龄改成局部注入失败计数，范围更小，不是另一种仲裁。Bolotin 等 QNoC（JSA 2004）已按 traffic class 做优先级。Das, Mutlu, Moscibroda, Das, "Application-Aware Prioritization Mechanisms for On-Chip Networks," MICRO 2009 直接对比了 LocalRR、LocalAge 与应用 rank，并用 batch 封顶饥饿；本卡的 `Age+K·Class` 就是 LocalAge 与静态类权重的线性相加，正是该文当作朴素基线的组合，而不是他们后面的 stall-time criticality。Lee 等, "Probabilistic Distance-Based Arbitration," MICRO 2010 同样在仲裁权重里做区分服务。把 Class 编成 broadcast/reduce/all* 只是给已知打分函数贴了 LLM 标签，没有新的比较结构、没有跨节点年龄、也没有 slack。
- vs 本批其他卡: M-6 在许可相位外即使槽空也不注入；本卡只要槽空且有 ready 就注入，二者一个非 work-conserving、一个 work-conserving，不能互换。M-8 用 TC 选通道和桥相位，本卡用 Class 只做节点内排序，卡也写了不依赖 M-8。M-7 选方向，M-9 限桥，都不决定同一 NI 内谁赢气泡。本卡是这批里唯一的注入侧打分器，但打分器本身是已知的。

## 判决理由
可行性通过：仲裁在注入侧、过路优先、无预言、header 槽不出环，P2P 回归有硬界。新颖性不够：`Score=Age+K·Class` 是本地年龄仲裁加重静态 QoS 权重，SC 2007 / QNoC / MICRO 2009 已经覆盖同一功能，对本题只是把类别表换成集合名。结构增量没有强到值得 Tier 1。REJECT / INCREMENTAL / 不进 T1。
