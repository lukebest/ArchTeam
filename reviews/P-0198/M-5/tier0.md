# Tier 0 · P-0198/M-5 · CRRF Channel–Ring Rebind（T1-return-1 重跑）

- 机制卡: mechanisms/P-0198/M-5.md
- 修订: T1-return-1
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES
- 原致命点: 全部CLOSED

## 轴一 可行性
- 因果性: 本地 Dat util EMA + Snp pending 驱动 duty/epoch；ARM_DRAIN → DRAIN（marker 双回或 sniff 清旧 `epoch_tag`）→ FLIP（更新 4×4 one-hot）→ `epoch_committed` 全环后才允许新世代注入。SYNC/DRAIN 走 Req 环，**对齐≠预测**。runtime hint 至多 advisory，正确性不依赖。rebind-off 消融与 Snp ≤1.4× 杀假设提供证伪。
- 完美预测/无限带宽/零延迟: 删除软件/运行时 COLL_EP 主臂。有效容量诚实 ≤1+duty_dat − drain 死时间 − SYNC 槽 − bind pipe 1–2 拍；禁止「近乎双 Dat 无税」。无无限带宽；stall 由 SNP_EPOCH duty floor 有界。
- 约束边界: 每物理环每方向每拍仍 1 槽——时间复用 ≠ 永久第二 Dat 端口。Skew 窗接受 `epoch_tag ∈ {local, local−1}`；接受集外 → NACK/原 Dat 环重注入，`bind_mismatch_redirect++`，禁止静默丢与永久 inject stall。Ghost Dat 头保留 Dat channel-id，RBRG 按绑定表+epoch 译码，禁止当 Snp 嗅探。跨 die 在途用 committed+redirect 兜底，使本地 sniff 非全局瞬时空的缺口变为可计数路径而非语义污染。
- 硬件开销: 每 die Rebind FSM + 周长/marker；flit `epoch_tag` 2b；NIC/RBRG 各 4×4 one-hot + 1–2 拍 pipe；压力 EMA/Snp pending；失配 NACK/re-inject + CSR。无第二永久 Dat 端口、无大 flit 队列。Drain/SYNC 税必须进模型——卡已写入预期区间。

## 原致命点核对（编号对应 fatal_points.md · M-5 CRRF）
1. **CLOSED** — 完整 Epoch Drain Protocol（ARM_DRAIN/DRAIN/FLIP/`epoch_committed`）；flip 前本地 drain；SYNC 只对齐 epoch；skew 接受集写明；cycle 模型强制打 SYNC 采样偏斜。
2. **CLOSED** — Ghost Dat 携原 Dat channel-id + `epoch_tag`；RBRG 按绑定+epoch 译码；失配走 NACK/原 Dat 环重注入并计 `bind_mismatch_redirect`；禁止静默丢包与永久 inject stall；duty floor 界 Snp stall。
3. **CLOSED** — 强制 Snp makespan/completions 与 duty∈{3:1,7:1,15:1}；Snp ≤1.4× rebind-off 为杀假设；Rebind FSM **仅**本地压力计数；COLL_EP/runtime hint 不得做正确性主臂；SYNC≠预测。

## 轴二 新颖性
- vs 文献: 物理通道时间复用/弹性绑定在 VC 重分配、部分 photonics/flexray 工作中有近亲，但钉在 CHI Req/Rsp/Snp/Dat 四独立双向环 + RBRG + **强制 drain 屏障与 ghost channel-id 正确性** 的完整协议，对本 DV200 信封是 DIFFERENT_APPROACH，非某公开「Snp 环借给 Dat」EXACT_MATCH。
- vs 本批修订卡（仅 M-2/M-4/M-5）: M-2 管集合会合授权；M-4 管同通道对向注入洞。CRRF 改的是**通道–环绑定世代**与 ghost Dat 承载——切面正交。

## 判决理由
三致命点均 CLOSED；相位预言主臂已拔掉，drain+skew+redirect 闭合鬼影 channel-id 洞。轴一 PASS：零和与税写进机制，Snp 退化有硬杀假设。残余「drain 税是否吃掉集合收益 / duty 过敏伤 Snp」属扫描可证伪，非 OPEN 结构洞。新颖性 DIFFERENT_APPROACH，质量 ISCA_WORTHY。**PASS_T1 / 进入 Tier 1: YES**。
