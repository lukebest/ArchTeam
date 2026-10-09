# Dr. Archi · T1 微架构评审 · P-0198/M-5r1 CRRF-SB

> 评审对象：`M-5r1.md`（ArchTeam PR #85）、`models/`（spec / model / harness / insight / test_sb，**作者模型，UNSIGNED**）、`tier0.md`（PR #89）。
> 平台真值：`lukebest/bufferless-ring-noc` `main@63163ca`（浅克隆，只读）。下文 `brn:` 前缀指该仓路径。
> 外部量级（非 repo，单独标注）：AMBA CHI 的 SNP flit 不带数据字段，量级约 1e2 bit；DAT flit 带 64 B 数据，加 BE 和控制字段后约 6–7e2 bit。
> 我在作者 harness 上跑了几个探针，脚本放在 `/workspace/p0198-m5r1/probe/probe{,2,3,4}.py`。结果只是 **模型数字**：减箱、未签字，不代表硅。

## 结论
**致命缺陷**

M-5 这条线有一个前提从来没人核过：Snp 物理环能装下一个 Dat flit。repo 不建模任何位宽，一个 NetworkFlit 就是一个槽；按 CHI 语义，Snp 不带 64 B 数据，所以 Snp 环在硅里是窄环。于是 ghost Dat 只有两条路，两条都走不通：
- **加线**：这已经不是时间复用。正确的基线变成「Dat 子环 2→3」，它直接支配本卡。
- **拆拍**：k≈6–8。Dat 是 2 条子环，见 `brn:tests/soc_sim/gen_config.py:308`，扣完后收益 ≤~6%，卡上 0.55–0.85× 的区间不可达。

另外，steal-back 只在本地成立。用作者自己的 harness，只把 Dat 量加大（参数和规则都不动），15:1 推理混合列的 Snp makespan 就到了 1.41–8.8×，越过 1.4 杀线。卡没有密度上限，repo 的 i-tag 最快 128 拍才触发，给不出 1.4× 量级的界。

## 五维打分
| 维 | 分 | 一句话理由 |
|---|---|---|
| 可行性 | 1 | Snp 窄环载 Dat 要么加线（等于不是复用），要么 k≈6–8 拆拍；卡和模型都默认 Dat 宽的 Snp。 |
| 新颖性 | 2 | 机制核心是「低优先级类机会式借用另一物理子网空槽 + 本地类优先」。header 权威以后 epoch/bind 在构造上就冗余（见 §5），落回多物理子网负载均衡族。 |
| 预期收益 | 1 | 以 Dat×2 为基线、k≥6 时，环受限情形 T_dat/off 的理论下界 ≈0.94–0.95；就算 k=1，也被「直接加第三条 Dat 子环」支配。 |
| 评估可信度 | 1 | harness 的 `snp_path` 列在 r1 下恒等于 rebind-off（没有 Dat 就没有 ghost）；dest 两环无限 eject；flit=txn；没有 RBRG、NACK、eject 失败；ready_at 记账延后。soc_sim 没有 Snp 源。 |
| 系统可组合性 | 2 | 把 Dat 汇点的进度耦合进 Snp 环和 Snp NI/RBRG 缓冲，破坏 CHI「通道独立」的死锁隔离假设；绑定表 4×4 和 repo 的 1/2/1/2 子环数对不上。 |

## 最强反对意见
**DV200 的 Snp 环物理位宽小于 Dat flit 位宽，所以 ghost Dat 不是「借空槽」，而是「借 k≈6–8 个空槽」或「新增 ≥512 bit/方向/链路导线」。**

可证伪的形式：在 soc_sim 新分支上实现 `ghost_beats_per_dat = ceil(W_dat/W_snp)`，用真实 k，以 rebind-off（Dat×2 子环）为基线。我预测 15:1 推理混合下：
- T_dat/off ≥ 0.93；
- Snp 列在 ghost 密度不封顶时 >1.4。

只有一种情况能推翻这条意见：拿出 DV200 文档或 RTL 证据，证明 Snp 链路宽度 ≥ Dat flit 宽度。repo 里没有这条证据。

## 评估层必须验证的一个假设
**H-GHOST-SERIAL（物理位宽 + 下游饥饿合一）**

在 `bufferless-ring-noc` 新分支上做三件事：
1. 新增 `ghost_beats_per_dat=k`，取值 k∈{1, k_real}。k_real 由 DV200 的 W_dat/W_snp 给出，没有出处就取 6。
2. 新增 Snp 流量源。repo 现在没有，见 §KILL。
3. 跑 12+2 全信封、15:1。

可操作断言：k=k_real 时，下面两条**同时**成立：
- `snp_path` 列和推理混合列的 Snp makespan / rebind-off 都 ≤ 1.4；按源节点位置分列的 Snp 注入等待 p99 ≤ 0.4·L_snp(off)。
- 推理 Dat makespan / rebind-off ≤ 0.85。

任一不成立，该臂 KILL。只报 k=1 的结果视为 reduced-bbox，不计。

## 逐条核查（主持指定 1–5）

### 1 物理位宽 —— 结论：OPEN-致命（波及整条 M-5 线）

**repo 事实**
- flit 没有位宽。Snp 和 Dat 是同一个结构 `CHIFlitFields`，只有 src/tgt/txn/addr/opcode 等字段，没有数据载荷字段（`brn:tests/esl_wrapper/compat/chi_common.h:92-118`）；`ChiRingChiFlitSNP/DAT` 只是它的 typedef（`brn:include/chi_ring_common.h:125-133`）。
- NetworkFlit 只挂指针 `Snpflit/Datflit`（`brn:include/chi_ring_common.h:239-300`）。highway 是「single-flit slot register」，跟通道无关（`brn:docs/noc_simulator_faq.html:55`）。
- 结论：**模拟器里任何 flit 占一个槽，不管 Snp 还是 Dat**。ghost Dat 在 soc_sim 里会被静默当成 1 个 Snp 槽，也就是静默假设 Snp 环和 Dat 一样宽。
- Dat 的数据粒度：`kBeatBytes = 64`（`brn:tests/soc_sim/platform/Endpoint.h:27`，注释为 top ai_flit_min_size；`brn:docs/noc_setup.md:166`）。一个 512 B 事务 = 8 个 Dat beat（`brn:tests/soc_sim/platform/TrafficGen.h:52-54`）。
- 子环数：`sub_channel_cnt req 1 rsp 2 snp 1 dat 2`（`brn:tests/soc_sim/gen_config.py:308`；`brn:docs/noc_simulator_faq.html:109`），每个子通道是一个独立的 TNetwork 环（`brn:src/TRing.cpp:49-54`）。**Dat 已经有 2 条物理子环，Snp 只有 1 条。**卡 §1「四条独立双向环」和 spec §3.1 的 `C_dat_ideal = 1 + duty_dat` 都把 Dat 当成 1 条，基线错了一倍。
- Snp 链路或环的物理位宽：**repo 未见**。repo 里唯一的链路宽度是 3DIO 跨 die 的 32 B/cycle（`brn:tests/soc_sim/platform/Mux3dio.h:22-31`，四个通道共用 beat_cycles），以及 `NOC0 Bus Size 128 bytes`（`brn:docs/hardware_setup.md:45`，AI Core 侧总线，不是环通道宽度）。

**硅里怎么工作**（外部量级，非 repo）：Snp flit 约 90–120 bit，Dat flit（64 B）约 680–730 bit，k = ceil(W_dat/W_snp) ≈ 6–8。三条路：

| 方案 | 硅代价 | 对卡的含义 |
|---|---|---|
| (a) 把 Snp 环加宽到 Dat 宽 | 每条链路每方向约 +600 线。top die：2 环 × 21 CS × 2 向 = 84 段（`brn:docs/noc_simulator_faq.html:109`）。Snp NI 的 share/output buffer（例如 AIC snp shareBufferDepth 13 / outputBufferDepth 9，`brn:tests/soc_sim/gen_config.py:140`）和 RBRG Snp 缓冲（outputBufferDepth 15，`brn:docs/noc_setup.md:405`）全部要加到 Dat 宽。 | **不再是时间复用**，而是加了一条 Dat 宽的环。公平对照变成「dat 子环 2→3、Snp 不动」：它不碰 Snp，也不需要 epoch，C_dat=3 优于 CRRF 的 2+0.77。本卡被这个对照支配。 |
| (b) 拆拍：一个 Dat beat = k 个 Snp 槽 | 两种实现：要求连续 k 槽的「列车」，注入概率约按 (1−ρ)^k 衰减，本征 Snp 会被长度 k 的列车阻塞；或者允许不连续，那么每个目的地要按源做重组缓冲（N_src × 64 B），**这是发明出来的缓冲**。另外每个 NI 需要 SerDes。 | 拆拍后每个 Snp 槽只送 1/k 个 Dat：C_dat ≈ 2 + 0.77/k ≈ 2.10–2.13，环受限下 T_dat/off ≥ 0.94–0.95，卡的 0.55–0.85 不可达。为送同样多的 Dat，ρ_wire 要放大 k 倍，直接把 Snp 推过杀线。 |
| (c) 静默假设 Snp 和 Dat 一样宽（卡和模型的现状） | 无 | 在 soc_sim 里它是「真」的，因为 repo 不建模位宽；在硅里是假的。**这正是要求查的「作者在掩盖什么」。** |

**单列结论**：OPEN-致命。卡 §2.1 结构表里没有任何位宽行；§5 硬件开销只写「FSM + 4×4 + 计数器量级」，漏掉了 (a) 的约 5 万根线或 (b) 的 SerDes 加重组缓冲。§2.1 的 4×4 one-hot 绑定表和 repo 的 1/2/1/2 子环（6 条物理子环 / 环索引）也对不上。T0 必验第 7 条把这个问题留给了 T1，T1 判它不成立。

### 2 优先级反转 —— 结论：OPEN-致命（按现卡文本；可救路径见 条件 C2）

**卡的规则**（§2.2）：过路 flit 仍然赢；Snp 只在**本地**空槽上赢 ghost。卡里没有按段或按节点的 ghost 密度上限。duty 15:1 只是 FSM 在「可借 / 不可借」之间翻转的**全局时间比例**，不是每节点能强制的下限。

**作者 harness 上直接复现**（模型数字，非硅；`probe.py`、`probe3.py`）。只改负载规模和 ost（16→64），规则不动，3 个种子：

| 负载（N=12） | rebind-off ms_snp | m5r1-15:1 ms_snp | 比值 | Dat 比值 |
|---|---|---|---|---|
| 作者默认：gather 48 Dat + 6 Snp，ost 16 | 5.7 | 5.7 | 1.000 | 0.569 |
| uniform 1200 Dat + 24 Snp | 10.3 | 14.7 | **1.43** | 0.747 |
| uniform 2400 Dat + 48 Snp | 14.7 | 20.7 | **1.41** | 0.708 |
| gather 1200 Dat + 24 Snp（KV 汇聚型） | 10.3 | 91.0 | **8.8** | 0.626 |
| gather 2400 Dat + 48 Snp | 14.7 | 89.7 | **6.1** | 0.681 |

我用 `probe3.py` 给 Snp 卡住的原因计数：gather 1200 场景里有 323 个节点·拍是因为本地 Snp 槽被**在途 ghost** 占着，被本征 Snp 占的只有 6 个，ost 满的是 0 个。卡住的 Snp 注入等待在 80–85 拍，源节点都在汇点上游（1/3 CCW、7/9 CW），ghost 占用率 0.37–0.55。这就是 T0 说的上游 ghost 饿死下游 Snp，而且出自作者自己的模型。

H-GEO（`E[wait]=ρ/(1−ρ)`，spec §3.3）假设空槽相互独立，但 ghost 是单源连续注入的列车，空槽高度相关。几何等待严重低估尾延迟。

**repo 的 i-tag：确实存在，但界不住 1.4×**
- `tryItagProcess`（`brn:src/TCsHighWay.cpp:894-945`）、`wantItag`（`:1000-1037`）、打标（`:1094-1106`）、`isSlotReservedFlit` 含 `sender_tagged`（`:1151-1157`）、已打标 flit eject 后留下 invalid 占位继续绕环（`:524-559`）。
- 语义：注入失败的 NI 等到 `checked_time + 2·thr` 后，给**任意**一个路过的 valid flit 打 i-tag，ghost 也会被打。每个 highway 同时只有一个 tag（`m_haveItag`，policy 0）。被打标的 flit 到目的地 eject 之后，空出的占位绕回来才归打标者用。
- 默认值：`m_itagPolicy = 0`（`brn:src/TPortConfig.cpp:226`），soc_sim 端口 `itagThreshold=64`（`brn:tests/soc_sim/gen_config.py:134`）。也就是**饿满 128 拍才打标**，再加最多 1 圈 42 拍（`brn:docs/noc_simulator_faq.html:109`）。
- 结论：i-tag 给的是**活性**（≥~170 拍才兜底），不是 1.4×。L_snp 只有约 10–21 拍，一旦落到 i-tag 路径就是 >8×。如果被打标的 ghost 在目的地 eject 失败、继续绕圈，占位就迟迟释放不了，i-tag 的界随之消失（见 §3）。
- 卡全文没有提到 i-tag；ghost 是否服从 i-tag 占位、i-tag 是否按类区分（只给本征 Snp 用），卡都没定义。leaf-tag 是按设备类（COC）预留 Dat 环槽（`brn:docs/noc_simulator_faq.html:118-149`），与 Snp 环无关。

**单列结论**：OPEN-致命（按现文本）。「Snp 永远赢」只是本地性质，全局没有界。现卡唯一真正起限流作用的，是 15:1 里那 1/16 的 ghost 不可借窗口（见 §5 消融），它是全局的粗时间窗，不能按节点强制。可救：加按段或按节点的 ghost 密度上限，或者按类区分的 i-tag（只有本征 Snp 能用的占位），并以按节点位置分列的 p99 证明（条件 C2）。

### 3 弹出失败 ghost 绕圈 vs Drain —— 结论：有条件

**repo 事实**
- eject 失败时 flit 留在环上继续绕圈（`brn:src/TCsHighWay.cpp:574-587`，`eject_failed_times++`；`brn:docs/noc_simulator_faq.html` 的 Eject 条目）。
- e-tag：`canSendFlitToLocal` 在第一次失败时尝试 `tryToTag`（`brn:src/TCsHighWay.cpp:681-708`）。`TReserveState::tryToTag` 对每个 NI 的每个输入方向只允许一个 tag（`brn:src/TReserveState.cpp:47-66`），top die 的 `etagReserveCycle 10`（`brn:tests/soc_sim/gen_config.py:342`）。
- 关键在于：e-tag 状态挂在**本环的目标 NI** 上。ghost 走的是 Snp 环，它 eject 到的是 **Snp 环上的 NI**；每个通道/子通道各有自己的 TNetwork/CS/NI（`brn:src/TRing.cpp:49-54`）。所以 **Dat NI 的 e-tag 管不到 ghost**；ghost 和本征 Snp 抢的是同一个 Snp NI 的输出缓冲（snp outputBufferDepth 9，`brn:tests/soc_sim/gen_config.py:140`）。Endpoint 按通道从 Snp 口取 flit，直接记成 Snp 完成（`brn:tests/soc_sim/platform/Endpoint.h:601-609`）。要把 ghost 交给 Dat 消费者，需要新的解复用通路，在硅里还要一条 Snp NI 到 Dat ingress 的 Dat 宽数据通路。卡 §2.2 只写了「eject 到 Dat NI 口」，没有说是哪个口。
- 3DIO 汇点：Dio/Sllc 的 ingress 有深度上限（`brn:tests/soc_sim/platform/Endpoint.h:577-604`），排空靠 Mux 链路 32 B/cycle，即 0.5 beat/拍（`brn:tests/soc_sim/platform/Mux3dio.h:22-31`）。推理 KV/权值搬运正好经过 3DIO，**这个工作负载里 ghost eject 失败会很常见**。

**活锁/死锁分析**
- **死锁**：在 Dat 汇点有预分配缓冲（CHI 的读数据缓冲 / DBID 后的写数据缓冲）的前提下，ghost 的消费不依赖 Snp 环，不形成环形等待。ARM_DRAIN 之后没有新 ghost，旧世代的 ghost 数量单调不增，所以 **Drain 有界、无死锁**，但界是 `T_drain_nom + B_backlog / r_sink`，不是卡里的 `T_drain=(k+1)·C_ring+n_pipe`。以 top 环为例：T_drain_nom = 3×42+2 = 128 拍；汇点是 3DIO 时 r_sink ≈ 0.5 beat/拍，界随积压可以到上千拍。
- **RBRG 例外**：如果 ghost 要跨 RBRG（bottom die 的 H/V 环），RBRG 的 Snp NI 缓冲（深度 15）就同时装了本征 Snp 和 ghost Dat。RBRG 现有的反死锁手段是 l1/l2 swap（`brn:docs/noc_setup.md:405`），它按通道设计，从没验证过混类情形。这里**存在跨环环形依赖的可能**，卡没有分析。
- **2b epoch tag 回绕**：接受集 `{local, local−1}`，mod 4（`harness.py` 里 `EPOCH_MOD=4`）。如果一个 ghost 绕圈的时间跨过 ≥3 次翻转，它的 tag 会回绕成「当前」并被误接受。Drain 每次翻转都会等旧 tag 清空，所以只要 Drain 不被超时绕过，就不会回绕；**但卡没有说 Drain 有没有超时**。如果实现上为了活性加了超时，回绕就会变成静默错误。
- 作者 harness 里 eject 永远成功（`harness.py:281-290`：到达 dst 就 complete），所以绕圈、e-tag、Drain 时长都**没有被建模**。

**单列结论**：有条件（C3）。必须同时满足：(i) ghost 禁止跨 RBRG，或者证明 swap 覆盖混类；(ii) 定义 ghost 的 eject 落点和 e-tag 覆盖（Snp NI 级 e-tag 要对 ghost 生效，或者 ghost 只能投向有预分配缓冲的 Dat 汇点，排除 3DIO / RBRG）；(iii) Drain 不加超时，并按 12+2 报告 Drain 时长 p99 和最坏值、ghost 绕圈圈数分布；(iv) 报告 Drain 期间本征 Snp 的尾延迟。

### 4 NACK 重注入数据来源 —— 结论：有条件（按原地持有解释）；若为「源端保留副本」解释则致命

卡 §2.1 写「失配路径：深度 1 holding（非 highway 队列）」，§2.2 写「接受集外 → NACK / 原 Dat 环重注入」。卡**没有说明**载荷从哪里来。两种解释：

| 解释 | 存储 | 判断 |
|---|---|---|
| A. 源端保留副本，等收到 NACK 后重发 | 卡里没有投递确认（无缓冲环本身没有 ACK）。源端必须一直保留到能确认「不会再有 NACK」，而 eject 失败时没有这个界（§3）。最坏按公开 outstanding 算：读源 512 × 512 B = 256 KiB/端口，写源 256 × 512 B = 128 KiB/端口（`brn:tests/soc_sim/platform/TrafficGen.h:49,130`）。另外还要一条新的 NACK/ACK 回程通道。 | **致命**：存储量级不可接受，还多出一条协议通道。 |
| B. 失配点就地持有（RBRG 或目的 NI 把整个 ghost flit 放进 1 深 holding，再转注到 Dat 环） | 每个 RBRG NI 每方向一个 Dat 宽寄存器，约 700 bit。bottom die 有 192 个 ConnectPoint，每个对应一对 RBRG NI（`brn:tests/soc_sim/gen_config.py:36`；`brn:docs/noc_simulator_faq.html:213`）。另外要一条从 Snp RBRG NI 到**同 CS 的 Dat RBRG NI** 的跨通道 Dat 宽通路，并且要选定转注到 2 条 Dat 子环中的哪一条。 | 可行。它不是 highway 队列，和现有的 RBRG 输出缓冲同级（`brn:docs/noc_setup.md:405`），但属于**新增**的 Dat 宽存储加跨通道端口，§5 没有计入。 |

解释 B 的次生问题：
- Dat 环之所以要借 ghost，就是因为已经饱和；holding 要靠过路优先抢到 Dat 槽，最坏得等 i-tag（≥128 拍，§2）。holding 满时，后续失配的 ghost 只能留在 Snp 环上绕圈，并进入 §3 的 Drain 界。
- 如果失配点是**目的 NI**，它把 ghost 转注到 Dat 环、目标还是自己，要付整整一圈。
- 作者 harness 没有失配和 NACK 路径，`bind_mismatch_redirect` 恒为 0，这个口径在模型里没有被检验。

**单列结论**：有条件（C4）。卡必须明确写成解释 B：NACK 是就地转换，不是发回源端的消息。还要给出 holding 位宽（Dat 宽）、数量和跨通道端口，计入 §5 面积；规定 holding 满时的行为（只能是留环绕圈，不能丢、不能排队）；并报告稳态和翻转窗口内 `bind_mismatch_redirect` 的计数和 holding 占用 p99。如果选的是解释 A，直接升致命。

### 5 对照项 drain-off + header-only —— 结论：有条件（卡和模型都没有这个臂；预测 epoch/bind 在正确性上冗余）

- 卡 §4 的消融只有 `sb-off` 和 `ghost-off`（加源端 FC 和原 M-5），**没有 drain-off + header-only**。harness 的臂只有 4 个（`harness.py:390`），也没有。T0 必验第 5 条要求这个臂，卡没有回应。
- **构造性论证**：卡 §2.2 把 header `channel-id` 定为本征权威，并且「永不把 Dat 载荷按 Snp 语义重解释」。这样 Dat flit 是自描述的，RBRG 或 NI 只看 header 就能正确路由和交付。epoch_tag、接受集、bind 都不再承担任何正确性职责，只剩一个作用：在全局时间上决定「此刻能不能新借」，也就是一个粗粒度的 ghost 占空比阀门。
- 我在作者 harness 里补了 header-only 臂：ghost 永远可借，没有 FSM、Drain、epoch（`probe4.py`，模型数字）：

| 负载 | m5r1-15:1 Snp / Dat | header-only Snp / Dat |
|---|---|---|
| 作者默认 gather 48 + 6 | 1.000 / 0.569 | **1.000 / 0.569（完全相同）** |
| 作者默认规模 uniform 48 + 6 | 1.000 / 0.778 | **1.000 / 0.778（完全相同）** |
| uniform 1200 + 24 | 1.419 / 0.747 | 1.419 / 0.623 |
| gather 1200 + 24 | 8.81 / 0.626 | 22.1 / 0.505 |
| gather 2400 + 48 | 6.11 / 0.681 | 30.4 / 0.505 |

- 解读：在作者的默认负载里，epoch/bind/Drain **一个拍都没贡献**，两个臂数字完全一样。在重 Dat 负载里，epoch 唯一的效果是那 1/16 的不可借窗口在缓解 Snp 饥饿，代价是 Dat 侧变差。换句话说，它是一个**拙劣的密度上限**，不是正确性机制。
- **预测**（soc_sim 新分支）：header-only 加上一个最简单的每节点 ghost 令牌桶或段密度上限，会在 Snp 和 Dat 两列上同时不劣于 on-arm。届时 epoch/bind/Drain 应当删掉，新颖性降到「多物理子网 + 类优先的机会式借槽」（Yoon et al. 多物理网络族），这比 T0 的 INCREMENTAL 还低一档。
- **单列结论**：有条件（C5）。T1 之后必须跑这个臂，并和 on-arm、sb-off、ghost-off、tail-only（M-15）同表报告。如果等价或更优，epoch/bind 作废、重评新颖性。

## KILL 条件核对

**钉住的条件**：15:1 下，Snp makespan / rebind-off ≤ 1.4（且 < 1.5625）。`snp_path` 列和推理混合列**各自**满足，不平均，不用 Dat 收益抵消。主指标是推理 makespan 和尾延迟。RTL 不动，结构改动只能做在 `bufferless-ring-noc` 新分支上。卡 §4 和 §6、T0 §要点三的写法都正确，这条**文字上是钉住的**。

**作者模型能不能诚实地评估这条杀线？不能。**
1. **`snp_path` 列是恒等式**。该模式只生成 Snp（`harness.py:375-376`），r1 下没有 Dat 就没有 ghost，m5r1 和 rebind-off 逐拍相同，所以 1.000 是**构造出来的**，不是测出来的。insight 里的「7.8→1.0」只说明 M-5 的排他窗口被去掉了，对优先级反转一个字都没测。
2. **推理混合列**：6 个 Snp 对 48 个 gather Dat，ost=16，N=12，3 个种子。比值是种子均值之比（`harness.py:400-412`），没有 p99 尾。负载稍微加重就越线（§2 表：1.41–8.8×）。
3. **eject 无限**：到达 dst 就完成（`harness.py:281-290`），Dat 环和 Snp 环可以在同一拍同时向同一个 dst 交付。Dat 收益（0.569）主要来自**目的端 eject 带宽翻倍**这个伪影。insight.md:26 承认 M-5 的 0.583 是 dest-eject 伪影，但 r1 的 0.569 出自同一机制，却没有标注。
4. **flit=txn**：没有 8 beat，没有位宽 k，没有 RBRG、12+2、NACK、失配、eject 失败。
5. **记账**：`ready_at` 在对齐之后、第一次尝试注入时才写入（`harness.py:205-206, 240-241, 309-315`），首个翻转波之前的等待被排除在 makespan 外。同时 Snp 和 Dat 共用每节点的 ost（`harness.py:200, 230`）。
6. **代数模型**：`C_ring=25`、`L_snp=12.5`（`model.py:83-89`），和 repo 的 top 环一圈 42 拍（`brn:docs/noc_simulator_faq.html:109`；链路延迟 2，见 `brn:tests/soc_sim/gen_config.py:345`）不符。`alpha_occ=0.55` 是自由参数。`C_dat_ideal=1+duty` 把 Dat 当成 1 条环。
7. **soc_sim 没有 Snp 源**：repo 里 Snp 只由 Mux3dio 转发（`brn:tests/soc_sim/platform/Mux3dio.h:108,113,145,149`），HA 和 TrafficGen 都不产生 Snp，TrafficGen 只计 `completed_snp`（`brn:tests/soc_sim/platform/TrafficGen.h:497-499`）。所以 `snp_path` 列和「推理混合的 Snp 成分」都要在新分支上**新建流量类**，而这个流量类的密度、位置分布本身就决定 KILL 结果，必须在跑之前钉死（条件 C6）。推理负载分支 `cursor/p0198-llm-noc-baseline-aa90`（T0 提到）我没有克隆，内容 repo 未核。
8. **杀线敏感度**：1.4× 意味着 E[wait] ≤ 0.4·L_snp。top 环最短路径平均约 5 跳 × 2 拍 ≈ 10.5 拍（取 C/4），按卡的取法 C/2 是 21 拍，所以允许的平均注入等待只有约 4–8 拍。在独立假设下，这对应 ghost 在下游的占用率 ρ_wire ≤ 0.81–0.89；列车相关性会把这个门槛进一步压低。i-tag 兜底的 128 拍和这个量级差两个数量级。

**判断**：卡没有可信证据通过这条杀线。按 §1 的位宽，k_real 下只会更差；按 §2 的复现，作者模型本身就会越线。

## 微架构要点
- **面积/功耗自洽性**：§5 写「FSM + 4×4 + 计数器量级」，和机制本身不自洽。漏掉的有：(a) 加宽方案约 600 bit × 84 段/top die 的环线，加上 Snp NI 与 RBRG 缓冲加宽；或 (b) 每 NI 的 SerDes 加重组缓冲；还有 Snp NI 到 Dat ingress 的 Dat 宽解复用通路（每个设备端口），以及 RBRG 的 Dat 宽 holding 和跨通道端口。环线翻转功耗：ghost 用 Snp 线送 Dat，每个 Dat beat 的能耗至少等于 Dat 环；拆拍时还要乘以 k 倍控制位开销。
- **端口**：每个 CS 每个方向的注入仲裁只在两个 NI（UP/DOWN）之间轮转（`brn:src/TCsHighWay.cpp:598-620`；`brn:docs/noc_simulator_faq.html` 的 Inject 条目）。ghost 注入要求 Snp 环 CS 上的 Snp NI 能拿到 Dat 队列的数据。要么 Snp NI 加一个 Dat 宽输入口，要么 Dat NI 物理上也挂到 Snp 环 CS（每 CS 第三个本地口），卡 §2.1 都没写。
- **时序拍**：steal-back 门控只是在既有「槽空」判断上多与一个 `Snp pending`，组合逻辑一两级，能放进 2.5 GHz（0.4 ns，`brn:tests/soc_sim/platform/Endpoint.h:17`）的同拍，这一项**可以接受**。但 RBRG 那里「bind + epoch_tag + 接受集」译码，加上「holding 满 → 留环」的决策，和 eject 在同一拍，卡标的是「1–2 拍 pipe」，没有核实 RBRG 的 outLatency=4（`brn:docs/noc_setup.md:405`）能不能容纳。
- **绑定表尺寸**：卡写 4×4 one-hot。repo 每个环索引有 1/2/1/2 共 6 条物理子环，top die 还有 ring_cnt 2（`brn:tests/soc_sim/gen_config.py:308-310`）。ghost 借 1 条 Snp 环时，选哪条 Dat 子环作为「原 Dat 环」重注入，卡未定义。
- **与信封的拟合**：「无片上 flit 队列」只对 highway 成立（`brn:docs/noc_simulator_faq.html:55`），NI 和 RBRG 都有缓冲（`brn:tests/soc_sim/gen_config.py:138-141`；`brn:docs/noc_setup.md:405`）。卡用「非 highway 队列」为 holding 辩护说得通，但不能说「没有新增存储」。RTL 不动的要求：repo 没有 RTL（T0 已核），所有钩子都是 ESL 库内的结构改动，必须放在新分支、默认关闭。卡 §7 写「本环境读不到该仓（GitHub 404）」与事实不符：repo 公开，可以克隆。
- **CHI 通道独立性**：CHI 用独立通道把 Snp 的进度和 Dat 的汇点解耦。ghost 让 Snp 环槽、Snp NI 输出缓冲、RBRG Snp 缓冲的进度依赖 Dat 汇点（3DIO 只有 0.5 beat/拍）。这是可组合性风险，任何依赖「Snp 必达」的一致性或栅栏机制都会被拖进 Dat 拥塞域。
- **未发明但被误用的关系**：spec §3.3 的 `ρ_wire = duty·f·(1−p_steal)·α_occ` 把 ghost 占用写成全局均值，而饥饿只出现在汇点上游的局部段，均值掩盖了局部（§2 复现中局部占用 0.37–0.55，等待却超过 80 拍）。

## 条件
（结论为**致命缺陷**。C1 不满足即维持致命；只有 C1 被推翻，才可能整体降为「有条件通过」，并且 C2–C6 全部必须满足，任一不满足即升致命。）

1. **C1 位宽**：给出 DV200 的 Snp 环与 Dat 环链路位宽出处（文档或 RTL 参数）。如果 W_snp < W_dat，卡必须二选一并改写：(a) 承认加线，把对照改为「dat 子环 3」，并证明在 Snp 尾和 Dat makespan 上同时优于它；(b) 拆拍，在 soc_sim 新分支实现 `ghost_beats_per_dat=k_real`，把 C_dat 基线改为 Dat×2，重算 card-claim 区间。不允许再用 1+duty。
2. **C2 下游饥饿**：加入可按节点强制的 ghost 密度上限（段令牌或按类 i-tag：只有本征 Snp 能用的占位），并说明 ghost 服从现有 i-tag 占位（`brn:src/TCsHighWay.cpp:1041-1110`）。在 12+2、15:1、gather 型 KV 负载下，按源节点位置分列报告 Snp 注入等待的 p99 和最坏值；两列 Snp makespan 都 ≤ 1.4。
3. **C3 Drain 有界**：ghost 不跨 RBRG，或者给出混类 swap 的无死锁证明；定义 ghost 的 eject 落点和 e-tag 覆盖；Drain 不设超时（防止 2b tag 回绕）；报告 Drain 时长 p99/最坏值、ghost 绕圈圈数分布，以及 Drain 期间的 Snp 尾。
4. **C4 NACK 数据来源**：写明是就地持有（解释 B），给出 Dat 宽 holding 的数量、位宽、跨通道端口和面积，以及 holding 满时只留环；报告 `bind_mismatch_redirect` 和 holding 占用。选源端副本即致命。
5. **C5 对照项**：drain-off + header-only（加简单密度上限）臂和 on-arm、sb-off、ghost-off、tail-only 同表。若等价或更优，删掉 epoch/bind 并重评新颖性。
6. **C6 评估口径**：在新分支上新建 Snp 流量类之前，先钉死它的密度、源分布、与 Dat 的相关性（推理 decode 的目录嗅探模型）。harness 的 `snp_path` 恒等列不得作为证据。eject 端口按 repo 实际建模，不得让双环无限 eject。报告用 p99，不用种子均值比；作者模型的所有数字（7.8→1.0、19.0→1.0、0.569）不得进卡的 claim。
