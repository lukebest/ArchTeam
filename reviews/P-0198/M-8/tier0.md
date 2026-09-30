# Tier 0 · P-0198/M-8 · CHI 信道亲和与集合相位钉扎

- 机制卡: mechanisms/P-0198/M-8.md
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 只在「两类突发被合法地放到两条都承载得动的环上，且过桥拒绝能在无队列下落地」时才成立。推荐 on 表并没有做到前半句：allreduce/alltoall/broadcast 的 payload 仍都在 Dat，P2P 读在 Req、完成在 Rsp，这就是 CHI 字面映射。同通道里再靠 `ep==phase_now` 把集合波错开，前提是流量真按自由运行的 `CPHASE` 对齐；卡禁止用集合完成预言推相位，于是要么收益依赖测试台把发射时刻钉死（工作负载排程，不是网络因果），要么门只是与波次无关的 1/4 占空比，主动加等待。Amdahl 项 `f_x` 在单类负载上约为 0，卡已承认；并发信封也不能补上下面的实现洞。
- 完美预测/无限带宽/零延迟: 计数器本身不是到达预言，也没有发明带宽。但「软件把 `RBEN` 写成与 `CPHASE` 同步的独热」若要分开 alltoall 与 allreduce 收尾，就是事先知道这两类会重叠并为其指定相位——对动态 LLM 重叠而言，这是报文级相位编排。未当成无限带宽：钉扎把桥 grant 切成相位片。零延迟不成立，关窗必有等相。
- 约束边界（bufferless 单槽、无 flit 队列、CHI 四环、RBRG、DV200 12+2、点对点+全集集合、有限 outstanding）: 两处硬违反。（1）`AFF.ch` 允许任意 TC 改挂到 Req/Rsp/Snp/Dat。信封里四环是 CHI 通道而不是四条同构原始公路：512 B 数据拍在 Dat，Req/Rsp/Snp 是另一类 flit；一致性虽出范围，Snp 仍被要求建模且应接近空。把集合 payload 挪到 Snp/Req 要么格式不合法，要么把模型降成「四条可互换环」，属于 reduced-bbox。推荐表避开了这种挪法，于是信道亲和半张卡在合法配置下没有新隔离域。（2）`rbrug_ok=0` 时「头停在 NI/桥控制级」。源 NI 与 RBRG 不是同一跳：flit 一旦占用 highway 槽，bufferless 单槽没有地方可停。卡写在途过路不受影响，却没有给出「要过桥但窗关着」的第三态——不能进队列（问题禁止）、不能消失、不能假定还在 NI。多源在开窗内注入、关窗时到达，1 个既有 staging 接不住。未实例化更完整桥语义时，这条路径在 12+2、有限 outstanding 的全信封上不闭合。
- 硬件开销 vs 问题约束: CSR 与 16:1 mux `<2.5 kGE` 本身不大。开销不是否决点；否决点是门控在无 flit 队列的环上没有合法的拒绝动作。`O_ch,d∈{0,1}` 的定义没有问题。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 把业务类分到不同物理网络是已有做法，而且本题的四环已经是这种分法。Balfour & Dally, "Design Tradeoffs for Tiled CMP On-Chip Networks," ICS 2006；Michelogiannakis, Balfour, Dally, "Elastic-Buffer Flow Control for On-Chip Networks," HPCA 2009（用重复物理子网而不是 VC 来分 traffic class）。Bolotin, Cidon, Ginosar, Kolodny, "QNoC," JSA 2004 用优先级类别做区分服务，不改通道语义。集合算法本身的相位（例如 ring allreduce 的分步）是 MPI/集合调度，不是新的环微结构。桥上按相位开关 grant 与 Æthereal 端口时隙、以及本批 M-9 的窗，是同一类 TDM 门。本卡是「CHI 默认分通道」加「静态相位独占桥」的拼接。
- vs 本批其他卡: `CPHASE`+`RBEN` 与 M-6 的 `Φ`+`CAL`、M-9 的 `EΦ`+`W` 同族；M-6 错开的是 NI 注入位，M-9 是与类别无关的桥占空比，本卡是按 `ep` 旋转的桥使能。M-10 也消费 TC/Class，但是本地打分，不过桥、不改通道。拼接没有产生独立于 M-6/M-9 的可实现新机制。与 M-7 无关。

## 判决理由
可行性失败，因而 REJECT / FLAWED / 不进 T1。合法 CHI 映射下信道亲和退化为现状；相位钉扎要么是测试台排程，要么是无关占空比，并且在 bufferless 环上没有写出被拒绝 flit 的去向。不能靠「停在既有 staging」把已上环的 flit 收回 NI。新颖性即使忽略实现洞也只是已知的子网隔离加 TDM 桥门。
