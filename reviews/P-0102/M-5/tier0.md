# Tier 0 · P-0102/M-5 · DMC 占用监视触发窗切换

- 机制卡: mechanisms/P-0102/M-5.md
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 计数的是已经发生的 DMC issue，采样边界才比 `max/mean`，置 NEED_SWITCH 后走 P-0101/M-4 同类 drain，`outstanding=0` 才翻 SWITCH。不读未来 S，FLIP_ONCE 防抖。索引只看当前 SWITCH 选中的 A/B 窗。因果链本身合法。
- 完美预测/无限带宽/零延迟: **不是**零延迟占用神谕。384×16b 饱和计数是发行直方图，Q 默认 65536 issue 才出快照，比较在采样态多周期、不在 issue 组合路径。代理 `proxy_bw=active_dmc/384` 也不是真带宽、不是无限 BW。这一项本身可接受（局部、有延迟）。失败不在「完美预测 S」——本卡正是为了避免猜 S。
- 关键边界（[21,33) 饥饿、partial good、冻结硬件、512B/4K）: B 窗 `m*=21` 含 `[21,33)`，切换后占用可回 K，饥饿路径被点名。partial-good 未建模（计数的是 DMC issue，死 bank 会扭曲 max/mean）。512B 顺序流可能 `max/mean>8` 误切——卡要求报假阳性，承认中低置信。粒度 512B。不改 384/18432 个数。
- **硬件开销 vs 「只改 interleave」（失败点）**: 问题约束是冻结信封、只改 interleave。本卡负载面是 384×16b flop（~37kGE / 768B）+ 18b 全局 issue 计数 + max/sum 归约树 + 5 态 drain + 机宽发行门。索引函数本身只是 M-1 的 A/B 两档 `m*`；多出来的是一条**运行时遥测 + 闭环控制面**。`giss` 按「全局 DMC issue」累加，采样要扫齐 384 计数，这是全局归约，不是组合交织。Axis 1 明文：overhead outside only-interleave → FAIL。与 P-0101/M-4 同一条：drain/发行门不是交织。次要：FLIP_ONCE 使闭环退化成一次性切到高窗，长作业若切完后 stride 再变无法收回；相对「boot 就写 M-4 高位程序 / 硬线 M-2」没有新映射能力。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于动态重映射/热点检测换图，不是新对象。Harper & Linebarger 动态存储方案（IEEE TC 1991）按测得 stride 换方案；DReAM（MEMSYS 2016）运行时按访问模式重排地址映射；DATE 2006 可重构 XOR-index 按应用换哈希（离线/开机，非占用闭环）。「统计 channel/bank 不平衡 → 换交织参数」是工业自适应 channel hash 的常见控制回路。CEASER-S（Qureshi MICRO 2019）按冲突换 cache 集合密钥，对象不是 DRAM 位窗。本卡特化成「DMC max/mean>8 → drain → 切 I-Poly 窗」，公式与阈值新，对象不新。非 EXACT_MATCH（不是逐寄存器复制某篇占用监视器）。
- vs 本批其他卡: 译码路径完整复制本批 M-1（A/B 滑动窗）；drain 完整复制 P-0101/M-4。是 M-1 的一次性控制包装，同 P-0103/SLCT 相对 MRFI 的关系。P-0103/SLCT 用每核 stride FSM（局部、3-match），本卡用 384 路占用（更重）。与 P-0105 五张静态图、P-0106 live-set 无重复。无兄弟 EXACT_MATCH。

## 判决理由
轴一失败：占用侧是带 Q 延迟的局部直方图（神谕条款未杀——监视在旁路、Q=64K、非 0 拍），但 384 计数器 + 全局归约 + drain 闭环超出「只改 interleave」信封。即使放宽开销，闭环在 FLIP_ONCE 下退化成「检测到饥饿则加载 M-1 高窗」，相对 M-1/M-4 是薄包装（质量 FLAWED）。新颖性对动态重映射文献 FUNCTIONAL_EQUIVALENT。不进 T1。
