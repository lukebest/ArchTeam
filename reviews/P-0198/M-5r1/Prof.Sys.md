# T1 · Prof. Sys · P-0198/M-5r1 · CRRF-SB（B 线第二轮）

- 卡：PR #85 `mechanisms/P-0198/M-5r1.md`；T0：PR #89（PASS_T1 / DIFFERENT_APPROACH / INCREMENTAL）
- 平台核查：`bufferless-ring-noc` `main@63163ca`（只读；未改 RTL、未改仿真器）
- 独立评审：未读其他三位本轮意见

## 结论

有条件通过（附两条前置条件，不满足即升级为致命缺陷：第 1 项位宽假设、第 2/3 项合起来的协议级循环依赖）

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 3 | 改所有权谓词是对的根因修法；但位宽、NACK 数据来源、ghost 出环口三处在卡上没有可流片定义。 |
| 新颖性 | 2 | 核心退化为「低优先级类机会式借另一物理子网空槽 + 本征类优先」；epoch/bind 若被 header-only 臂证明多余，再降。 |
| 预期收益 | 3 | 15:1 Snp KILL 的根因（排他身份 + 粗 drain 量子）确实被切断；Dat 侧收益在位宽未定前不可信，拆拍时可能整体蒸发。 |
| 评估可信度 | 3 | 杀条件钉得好（两列 ≤1.4、不平均、不抵扣）；但 soc_sim 四通道 flit 同构，不会自动计入位宽差，必须显式建模。 |
| 系统可组合性 | 2 | Snp 与 Dat 共物理环破坏 CHI「通道独立以避协议死锁」的前提；多租户下上游 ghost 可饿下游一致性流量，无配额。 |

## 逐项审计（主持指定 1–5）

### 1. Snp 无数据载荷，Dat 走 Snp 线的物理位宽 —— **未闭合（整条 M-5 线的前置条件）**

- 事实：CHI 的 SNP flit 只带地址/操作码/ID 等控制字段，无数据；DAT flit 带 128/256/512b 数据加 BE/校验等。物理上 Snp 环导线比 Dat 环窄数倍。
- 仿真器会把这件事藏掉：`tests/esl_wrapper/compat/chi_common.h` 里 `CHIReqInfo/CHIRspInfo/CHISnpInfo/CHIDatInfo` 都是同一个 `CHIFlitFields`，一个 Snp 槽在模型里可以装一整个 Dat flit。不显式建模，cycle 结果天然高估 ghost 容量。
- 只有两条路，卡必须选一条并写进 `C_dat_eff`：
  - **加宽 Snp 环到 Dat 宽度**：导线/面积 ≈ 再铺一条 Dat 环。到这一步，「重绑」不如直接说「第五条环」，新颖性与面积叙事都要重写。
  - **ghost 拆成 k 拍**（k = ⌈Dat 宽 / Snp 宽⌉，量级 3–5）：每个 ghost 吃 k 个 Snp 槽，有效增益 ≈ duty_dat/k；目的端要有按 txn 重组的暂存（端点存储，非环上队列，但必须计面积与 outstanding 上限）；拆拍还把 Snp 环占用乘 k，直接加重第 2 项饥饿。
- 判定：**条件**。cycle 臂必须带位宽参数（至少 k∈{1, 3, 4}），k=1 只能标作「加宽环」对照，不能当主列。若 k≥3 时推理 Dat makespan 已不优于源端流控基线，Dat 侧收益宣称作废。

### 2. 优先级反转：上游 ghost 过路优先、饿死下游 Snp、无密度上限；是否依赖 i-tag —— **部分兼容，未闭合**

- 卡的「Snp 赢」只在本地空槽成立。上游节点本地无 Snp pending 时可连续注入 ghost，这些 ghost 以过路身份压过下游节点，下游 Snp 拿不到空槽。卡上没有 ghost 段密度上限。
- 库内 i-tag 的实际行为（`src/TCsHighWay.cpp`）：NI 注入失败超阈值后给过路 flit 打 `sender_tagged`；该 flit 出环后留下 `valid=false` 的占位槽，`isHighwayEmpty()` 判 `m_sendFlit!=nullptr` 为非空，其他站点不能注入，直到回到打标站（`tryItagProcess`）。**只要 ghost 注入走同一条本地上环判定，ghost 天然服从 i-tag 预留槽**——这是兼容的。
- 但依赖 i-tag 不能闭合本项，原因三条：
  1. 默认阈值 `itagThreshold=100` 拍、固定策略、`itagMaxTags=1`/站（`src/TPortConfig.cpp`）。i-tag 是饥饿兜底，不是优先级：Snp 最坏等待 ≈ 100 拍 + 被标 flit 出环时间 + 一圈。对稀疏、延迟敏感的推理 Snp，这个量级本身就可能把 makespan 推过 1.4×。
  2. 被打标的 flit 如果恰好是 ghost，且 ghost 在目的端出环失败（第 3 项），预留槽永远不回来，i-tag 界失效。
  3. 反向风险：ghost 的源 NI 在 Snp 环上注入失败同样会累计、同样会发 i-tag。若不禁止，ghost 可以在 Snp 环上给自己预留槽，与本征 Snp 抢预留——优先级被反向固化。
- 判定：**条件**。必须写死：(a) ghost 注入走原生上环判定，服从 `isSlotReservedFlit`；(b) **ghost 不得在 Snp 环上发起 i-tag**；(c) Snp 环 i-tag 在 15:1 臂中开启并扫阈值（如 16/32/100）；(d) 另加不依赖 i-tag 的 ghost 密度上限（例：每站每向 ghost 令牌 / 每段在途 ghost 上限），因为 i-tag 只保证「终会注入」，不保证尾延迟。按节点位置分列 Snp 注入等待最坏值与 p99。

### 3. 弹出失败的 ghost 在 Snp 环绕圈，Drain 是否无限期卡住 —— **会，卡未闭合**

- DRAIN 要求旧世代 ghost 清空。ghost 在目的端从 Snp 物理环出到 Dat 侧入口；入口忙则留环绕圈（flit 有 `looped_times` 字段可计数）。没有出环保证时，Drain 等待无上界。
- 库内 e-tag（`canSendFlitToLocal` → `TReserveState::tryToTag` / `checkSlotReserved`）能保证「绕一圈后有预留位」，但它挂在**目标 NI 的本端口、本方向**上。ghost 到达的是 Snp 环的站点，接收的却是 Dat 语义：卡没有定义 ghost 出环挂在哪个 NI、用哪个 `TReserveState`。如果 ghost 共用 Dat NI 的入口预留，它和 Dat 环到达者抢同一份 e-tag；如果单开，就是新加的端点暂存。
- 判定：**条件**。必须：(a) 定义 ghost 出环口与其 e-tag 归属，保证任一 ghost 至多 1–2 圈内出环；(b) Drain 加看门狗计数并报最坏值、`looped_times` 分布；(c) 给出 Drain 上界公式（含 e-tag 后应为常数个环周）。做不到时，Drain 是一个依赖 Dat 入口进度的全局屏障，与第 2 项、下文协议死锁直接耦合。

### 4. 被 NACK 的 ghost 重注入时数据从哪里来 —— **卡的写法不成立，需改成「原地转道」**

- 无缓冲信封里源端不留副本：CHI 读数据由 HN/SN 发出后不保留，写数据由 RN 发出后也不保留。512/256 outstanding 下若要源端保留副本，等于给每个在途 Dat 加一份重传缓冲，远超卡上「深度 1 holding」的面积叙事。
- 唯一与 bufferless 自洽的读法：**NACK 不是回源重发，而是失配 ghost 本身在当前节点从 Snp 环转到 Dat 环（原地转道）**，flit 自身就是数据来源。这要求失配发生点有 Snp→Dat 的跨环口和 1 深暂存；暂存占满时该 ghost 只能继续绕圈。
- 判定：**条件**。卡须把「NACK / 原 Dat 环重注入」改写为原地转道，明确禁止源端重传；1 深暂存满时的行为写成「留环 + 计数」，并纳入第 3 项的出环保证。`bind_mismatch_redirect` 稳态 0 仍是目标，但瞬态也必须零丢失。

### 5. 对照项：关 drain、只按 header 解码 —— **必须跑；系统侧预期 epoch/bind 大概率可删**

- M-5r1 已让本征 Snp 只按 header `channel-id` 译码。若 ghost 也只按 `channel-id=Dat` 译码，接收侧不再需要全局世代一致；ghost「是否允许」退化为每站本地使能位，无需屏障。
- epoch/bind 唯一可能仍有正确性作用的地方：**跨 die / 跨 RBRG**。各 die 的 Rebind FSM 独立，ghost 过 RBRG 进入另一 die 的 Snp 环时，对方可能处于不准 ghost 的状态，此时需要世代或转道规则。header-only 臂必须包含跨 die ghost 流量，否则对照不公平。
- 判定：**条件**。header-only / drain-off 臂与 on-arm 同表；若 makespan 与尾等价（含跨 die），删 epoch/bind，新颖性降到「多物理子网机会式负载均衡」一级。系统上这反而是加分：去掉全局屏障，组合性变好。

## 最强反对

**共用物理环把 CHI 的通道独立性拆了，可能引入协议级循环依赖。** CHI 把 Snp 与 Dat 分通道，正是为了让 Snp 的前进不依赖 Dat 的前进。M-5r1 下可以出现：Dat 入口满（等事务完成）→ 事务等 Snp 响应 → Snp 注入不上环，因为 Snp 环被绕圈的 ghost 占着 → ghost 出不了环，因为 Dat 入口满。本征优先只在本地空槽上成立，打破不了这个环。叠加第 1 项拆拍（占用 ×k）后更易触发。修法必须是结构性的：给本征 Snp 一个不依赖 Dat 入口进度的保底（例如每段保留不被 ghost 占用的槽比例，或 ghost 出环口与 Dat 入口解耦），而不是靠 i-tag 阈值。

## 评估层必须验证的一个假设

在满 DV200 12+2、15:1、**k≥3 拆拍**、Snp 环 i-tag 开启且禁止 ghost 发 i-tag 的设定下，`snp_path` 与推理混合两列 Snp makespan 均 ≤1.4×（<1.5625）且 p99 不劣于 rebind-off 的 1.4×；同时 Drain 最坏时长有常数个环周的上界、ghost `looped_times` 最大值有界、无协议死锁看门狗触发。任一列 >1.4、Drain 无界或死锁看门狗触发，即判 KILL；不得平均，不得用 Dat 收益抵扣。卡上 7.8→1.0、19.0→1.0 只作假设。

## 系统视角

- **软件可见性**：对 OS/运行时透明是优点；但 Snp 尾抖动由硬件内部的 ghost 密度决定，软件无旋钮。需要暴露 `steal_back`、`ghost_gated`、Snp 注入等待 p99、Drain 最坏值、`looped_times` 作为性能计数器。
- **编程模型**：无新 API。hint 维持 advisory 是对的。
- **协议 / 一致性**：本征 Snp 按 header 权威译码，比 M-5 更干净；风险在上面的跨通道循环依赖与位宽。必须与 CHI 通道无死锁论证对齐，至少给出依赖图。
- **i-tag / e-tag 兼容**：ghost 服从 i-tag 预留槽可通过复用原生上环判定得到；ghost 不得发 i-tag；e-tag 归属须定义。三条写进卡后才算兼容。
- **多核**：推理 decode 下 Snp 稀疏但贴尾；多核同时 decode 时 Snp 由目录嗅探突发，steal-back 税集中在突发窗。H-SNP-CAP 单列是对的，但需加「多核同步 Snp 突发」场景，而非只有饱和对照。
- **多租户**：ghost 资格按站点本地压力触发，无租户配额。租户 A 的 Dat 重负载可在上游注入 ghost，饿死租户 B 在下游的一致性流量。需要 per-source 或 per-tenant 的 ghost 上限，评估按源分列 Snp 尾。
- **多芯片**：跨 RBRG 的 ghost 是 epoch/bind 唯一可能保留正确性作用的地方，也是第 5 项对照必须覆盖的地方。

## 仿真范围提醒

RTL 不改。上述位宽参数、ghost 禁发 i-tag、ghost 出环 e-tag、Drain 看门狗、协议死锁看门狗全部属于仿真器结构改动，只能在 `bufferless-ring-noc` 新分支上做，默认关闭，并进新的 provenance manifest。
