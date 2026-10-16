# Tier 0 · P-0198/M-9 · RBRG 跨环门控窗（无大缓冲）

- 机制卡: mechanisms/P-0198/M-9.md
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 「把跨环注入邻环的时刻收成每 `E` 拍里的 `W` 拍，从而把无界污染收成 `O(W/E)` 占空比」在记账上成立，而且 `W=4,E=16` 的 25% 上界是算得出来的。但记账假定桥可以拒绝而不把拒绝变成环上阻塞或丢 flit。单环不经 RBRG 的流量 `f_b≈0`，卡已承认不能用单环冒充收益；跨环集合上，占空比上限同时是吞吐上限，makespan 目标可能变差，卡把轻载回归写进评估是对的，不能挽救实现洞。
- 完美预测/无限带宽/零延迟: 未用对端未来占用来提前 grant，这点合格。窗是静态 CSR，不是无限带宽；相反，机制把桥服务率硬帽在 `W/E`。等窗上界约 `E−W` 拍，不是零延迟。没有报文到达预言。
- 约束边界（bufferless 单槽、无 flit 队列、CHI 四环、RBRG、DV200 12+2、点对点+全集集合、有限 outstanding）: 失败。卡写「窗外到达的跨环请求不进入 skid，只拉 `bp`」，又写「不请求过桥的过路 flit 继续沿本环走」。第三类——已经在源环 highway 槽里、目的是过桥、当前不在窗内或 skid 已满——没有下一跳。`bp` 只能挡住还在 NI staging 的新注入，挡不住已经上环的 flit；DV200 上 top NI 与 RBRG 不是同一个控制点。Bufferless 单槽不能把该 flit 原地冻住而不把上游整环顶死（那就是环上反压，正是无缓冲环要避免的），也不能丢。HiRD 类设计在这个点上的合法动作是偏转再绕环，本卡没有写偏转，也没有 livelock 界。另外，窗结束后 FSM 留在 Hold/Grant 且 skid 保持直到对端接受，这段等待把「1 flit skid」用成了跨多拍的 flit 队列（上界约 32 个，每个可停到 `E−W` 拍），用来吸收对端忙。问题禁止用片上 flit 队列吸收突发；同拍 cut-through 寄存可以辩，跨 Hold 窗驻留不能辩。禁止 4–8 深 FIFO 并没有避开深度 1 的等待队列。四通道与 12+2 的规模估算（skid≤32）本身与信封一致，但一致的规模不能让非法缓冲变合法。
- 硬件开销 vs 问题约束: 控制 `<2 kGE`/桥可以接受。存储侧的 1-flit skid 被写成「只存当前拍切片」，这是对的切片方式，但多拍驻留使它仍是队列。开销数字不是通过理由。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 桥口周期 grant 是端口整形/TDM，不是新跨环结构。Goossens 等 Æthereal（IEEE D&T 2005）的槽表就是「这一拍这个口能不能送」。漏桶/GCRA 一类速率 policer 把发送限制在固定占空比里，本卡 `W/E` 是退化形式。真正对着 bufferless 分层环桥的工作是 Ausavarungnirun 等, "Design and Evaluation of Hierarchical Rings with Deflection Routing," SBAC-PAD 2014（HiRD; arXiv:1602.06005）：环内无缓冲，桥用少量 transfer FIFO，满则 flit 留在环上绕回再试，并用 injection/transfer guarantee 防 livelock。本卡想要 HiRD 的「别让崩塌环灌满邻环」，但拿掉了偏转与前进保证，换成静态窗 + 反压到 NI。功能上仍是桥准入限速，且比 HiRD 少了在无队列约束下能跑通的那一半。
- vs 本批其他卡: 与 M-6 同为 `{8,16}` 周期门，M-6 卖的是 NI 空波，本卡限的是桥 grant，位点不同、族相同。与 M-8 的 `RBEN`/`CPHASE` 几乎是同一扇门：M-8 按集合 `ep` 旋转独热，本卡对所有跨环请求用一个窗长；M-8 还把 Hold 语义指向本卡。本卡更完整，但仍未补上被拒绝 flit 的去向，因此不能算本批里一个独立的新机制。与 M-7 的选向、M-10 的本地年龄仲裁无等价关系。

## 判决理由
可行性 FAIL：在无 flit 队列、每方向每拍单槽的环上，关窗拒绝过桥没有合法落点；用 skid 把 flit 停过整个 Hold 窗，就是用队列吸收对端冲突。占空比公式不能代替这个动作。相对 HiRD 与端口 TDM 也不是新途径。REJECT / FLAWED / 不进 T1。
