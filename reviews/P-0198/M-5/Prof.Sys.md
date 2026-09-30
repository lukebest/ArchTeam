# T1 · Prof. Sys · P-0198/M-5 · CRRF（T1-return-1）

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 3 | Drain+skew+失配重定向堵住鬼影；仍依赖全环 SYNC/`epoch_committed`，实现与 skew 模型重。 |
| 新颖性 | 3 | 通道–环时间复用已知思路；系统贡献在杀软件预言 + 强制屏障协议。 |
| 预期收益 | 3 | Dat 侧可赢，但 drain/SYNC 税 + Snp≤1.4× 杀假设把窗口收窄；duty 过敏必须暴露。 |
| 评估可信度 | 4 | rebind-off、Snp makespan、duty∈{3:1,7:1,15:1}、`bind_mismatch_redirect`、skew cycle 模型都可强制。 |
| 系统可组合性 | 3 | 正确性不再绑 COLL_EP；但 flip 是织物级屏障，多租户/一致性税仍在。 |

## 退回项审计（T1-return-1）

对照 T0 rerun PR #55：原致命点全部 CLOSED，判决 PASS_T1；close call 强调跨 die 本地 sniff 非全局瞬时清空——正确性靠 committed+skew+redirect。

1. **Epoch Drain / Barrier + skew**：ARM_DRAIN→DRAIN→FLIP+`epoch_committed`；skew 接受 `epoch_tag ∈ {local, local−1}`；cycle 模型必打 skew。**判定：CLOSED**——纸面闭合翻转窗口。
2. **Ghost Dat @ RBRG**：保留 channel-id + epoch_tag；按绑定表译码；失配 → NACK/原 Dat 环重注入，`bind_mismatch_redirect++`；禁静默丢、禁永久 inject stall。**判定：CLOSED**。
3. **杀相位预言**：主臂改为本地 Dat util EMA / Snp pending；runtime hint 至多 advisory；强制 Snp makespan/completions + duty 扫描。**判定：CLOSED**——软件暗示不再是正确性依赖。

## 最强反对

CRRF 的 flip 仍是 **整机织物事件**：DRAIN + `epoch_committed` 绕环期间，所有依赖「即将重绑物理环」的新注入停住——多租户下租户 A 的 Dat 压力可以触发全局 drain，租户 B 的 Snp/旁路流量吃屏障税，且没有 per-tenant 拒绝 flip 的旋钮。Snp 在 DAT_EPOCH 被时间复用：即使有 duty floor 与 ≤1.4× 杀假设，一致性流量（目录嗅探）与数据搬运抢同一物理环的**时间片**，OS/运行时看不见 epoch，只能看见偶发长尾。失配重定向正确但不免费——稳态 `bind_mismatch_redirect` 非零意味着 skew/绑定发散，会把重注入送回本已饱和的 Dat 环。多 bottom / 多 RBRG 时 epoch 对齐域未钉死：一 die 本地压力触发、全织物 SYNC，域过大则税爆，域过小则 ghost Dat 译码不一致。

## 评估层必须验证的一个假设

满 DV200、无 runtime hint、duty 扫描含 15:1：Snp makespan ≤1.4× rebind-off，且稳态 `bind_mismatch_redirect==0`（T0 close call：跨 die 在途靠 redirect 兜底，稳态必须真能 ≈0）；同时 Dat 重集合 makespan 相对 rebind-off 仍改善（扣 drain/SYNC 税后）。任一失败——尤其无 hint 就不能安全 flip，或 15:1 下 Snp 越界而只报 7:1 甜区——本卡在真实多租户/一致性负载下不可组合。

## 系统视角

- 软件可见性：正确性路径可无 hint（加分）；遥测仍应暴露 epoch、duty、redirect、Snp stall 计数，否则运行时无法解释长尾。
- 编程模型：无新集合 API；但驱动/固件需配置 duty floor 与压力阈值，并禁止把 COLL_EP 类提示写成唯一使能。SYNC 是屏障不是预测——不得在文档里写成「软件预报相位」。
- 协议/一致性：Ghost Dat 不得按 Snp 语义处理（修订已钉）；Snp 仅在 SNP_EPOCH/duty 窗注入。Drain 期间目录/一致性延迟上界必须进模型——否则「Snp≤1.4×」只是平均数。CHI 通道-id 在 RBRG 的绑定译码是协议扩展面，需与现有互连验证计划对齐。
- 多芯片：12+2 内 SYNC 绕环可行；跨包无定义。多 RBRG 时绑定表副本一致性 = 另一个分布式共识，卡只写了 NIC+RBRG 各一份 one-hot，未写多桥收敛。
- 多租户：织物级 drain 无租户隔离（见最强反对）。与 AODI/CSR 叠加时责任更难拆——评估必须能 rebind-off 单独消融。
