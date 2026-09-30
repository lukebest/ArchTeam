# Dr. Archi · T1 微架构评审 · P-0198/M-5 CRRF（T1-return-1）

## 结论
有条件通过

## 五维打分
| 维 | 分 | 一句话理由 |
|---|---|---|
| 可行性 | 3 | Drain+skew+redirect 语义上堵住鬼影译码，但无缓冲下 NACK 暂存与跨 die `epoch_committed` 聚合仍欠硅级钉死 |
| 新颖性 | 4 | CHI 四环绑定世代 + ghost Dat 强制屏障，对本 DV200 信封是切面级新做法，非第二 Dat 端口伪装 |
| 预期收益 | 3 | 零和时分复用诚实；1–2× 环周 drain + committed 税重，集合净利依赖低 flip 率与 7:1 甜区 |
| 评估可信度 | 4 | Snp≤1.4×、duty 扫描、redirect==0、skew cycle 模型均已写成可杀 endpoints |
| 系统可组合性 | 3 | 不占第三 highway 槽，但 Req 环 SYNC/DRAIN 与 Snp duty stall 会耦合他机制的注入与会合窗 |

## 最强反对意见
跨 die 本地 sniff≠全局瞬时清空，正确性靠 skew 接受集 + `bind_mismatch_redirect` 兜底；而信封禁止 flit 队列——NACK/原 Dat 环重注入若无显式 1 深 staging（或等价不占 highway 的暂存）就会在硅里变成静默发明侧缓或重注入活锁，T0 的 CLOSED 在稳态 redirect≈0 被证伪前只是纸面闭合。

## 评估层必须验证的一个假设
稳态（STEADY、无 flip 窗）`bind_mismatch_redirect == 0`，且单次 flip 窗内 redirect 有上界、不触发永久 inject stall；否则跨 die drain 协议在硅上未闭合。

## 微架构要点

### 原致命点再审计（§0 自称 CLOSED）
1. **Epoch Drain + skew 接受集** — **协议层可标 CLOSED，硅层有条件**。ARM_DRAIN→DRAIN→FLIP→`epoch_committed` 顺序清楚；接受集 `{local, local−1}` 与「永不按 Snp 语义重解释 Dat」写死。无缓冲环上「本地嗅探 ≥1 环周未见 old tag」在「停旧世代注入 + highway 每拍前进」前提下是完备的（在途 flit 必过本节点）。**漏洞在跨 die 异步**：各 die 本地 DRAIN 完成时刻不同；若 `epoch_committed` 只是早到节点发出的巡游位而非「全员已 FLIP」的 AND 屏障，则晚节点仍停在 epoch `e` 时可能收到 tag=`e+1` 的 ghost Dat → 接受集未命中 → 依赖 redirect。卡文强调「晚节点不得提前按新绑定注入」，却未同等钉死「早节点不得在全员 flip 前注入新世代」。T1 条件：committed 必须是全员 drain+flip 的聚合屏障，或新世代注入门控与之等价。
2. **Ghost Dat @ RBRG + `bind_mismatch_redirect`** — **channel-id 毒化路径协议 CLOSED**。头保留 Dat id + `epoch_tag`；RBRG 按绑定表+epoch 译码；禁当 Snp 嗅探、禁静默丢。与 T0/SUMMARY close-call 一致：正确性闭合倚 redirect。**未闭合的是数据通路**：§5 只写「控制路径 + CSR」，未声明失配 flit 在等原 Dat 环空槽时住在哪里。信封「无片上 flit 队列」下，允许且必须显式化的是 RBRG 侧有界（建议深度 1）redirect holding register / 等价端口占用，并证明与 highway 单槽零和、不引入突发吸收队列；禁止用「NACK」一词掩盖无限重试占槽。

### Drain 协议 / 环周完备性
- Marker 双回或连续 ≥1–2× 周长 sniff 清 old tag：单环方向内成立。
- 税：ARM_DRAIN→DRAIN ≥1–2× 环周，加 `epoch_committed` +1 环周，再加 bind pipe 1–2 拍——每次 flip 的死时间必须进 makespan；作者已承认「近乎双 Dat 无税」是撒谎，保留此诚实。
- 嗅探漏检风险：仅当 ARM_DRAIN 后仍有节点漏停旧注入，或 committed 聚合失败；属屏障实现 bug，不是「倒数不够」的简单问题。

### 压力臂 / 非预测
- 主臂改为 Dat util EMA + Snp pending：**拔掉 COLL_EP 预言主臂，SYNC≠预测**——此前「软件相位暗示」致命点可 CLOSED。
- 残余非正确性风险：EMA 滞后 → duty 来回抽打 → flip 过频，drain 税吃掉 0.55–0.85× 声称区间。需 STEADY 最小驻留 / 迟滞；属收益与稳定性，不把卡打回致命。

### Snp duty floor 与杀假设
- min 1/8 地板 + Snp makespan≤1.4× rebind-off + duty∈{3:1,7:1,15:1} 扫描：诚实可证伪，15:1 过敏必须暴露。Stall 有界声称成立当且仅当 SNP_EPOCH 窗真正可注入（不被 Req 环 SYNC 风暴与 divert 饿死）。

### 时分复用 vs「第二 Dat 端口」
- 卡文明确：每方向每拍仍 1 槽；有效 ≤1+duty_dat − drain − SYNC − pipe。**未把 time-mux 卖成并行第二 Dat**——这一点通过作者自证，评审不记为掩盖。
- 面积：FSM+2b tag+4×4 one-hot×(NIC,RBRG)+EMA 计数，量级可接受；真正成本是环上税与 Snp 退化，不是门数。

### 条件（全部满足才维持「有条件通过」；否则升级致命）
1. 显式声明 mismatch 路径的有界 staging（深度、压在哪一端口、是否计入零和槽），证明无静默丢、无永久 inject stall、无活锁重注入。
2. `epoch_committed` 定义为跨 die 全员 drain+flip 聚合（或等价门控），cycle 模型打 SYNC 采样偏斜；稳态 `bind_mismatch_redirect==0`，flip 窗 redirect 有上界并进 endpoints。
3. 压力臂带最小 STEADY 驻留/迟滞；评估强制报 drain 税占比与 Snp makespan/completions，不得只报 Dat 甜区。

T0 PASS_T1 / 原致命点 CLOSED ≠ 本评审硅通过：纸面毒化洞已堵，无缓冲 redirect 与跨 die 屏障仍是流片前必须钉死的条件。
