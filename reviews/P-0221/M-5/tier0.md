# Tier 0 · P-0221/M-5 · 路径配额再平衡（Path-Mask Quota Rebalance, PMQR）

- 机制卡: mechanisms/P-0221/M-5.md（PR #100 head `07c78cd`）
- 题卡: problems/P-0221.yaml（main@1909fb0）
- 作者: Jim Keller
- 判决: REJECT
- 可行性: FAIL（每段一条 REBAL、W_q=16 拍：对向控制负载 >100% 环容量；合成单条则向量 3.5–11 kb ≫ 512 b；`Σq=B_s` 在配额龄 > 窗长时不被执行）
- 新颖性: FUNCTIONAL_EQUIVALENT（GSF 帧配额 / max-min 显式速率分配 / RPR fair rate）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc live `main@63163cad`（= 63163ca，无漂移）

## 卡摘要
每段预算 `B_s`，按节点切成 `q_i[s]`，不变式 `Σ_i q_i[s] = B_s`。节点在窗内过路注入 `used_i[s] < q_i[s]` 才可注入，fail 计 `d_i[s]`。段主每 W_q=16 拍按上一窗需求「下游优先」重算 q，用同通道对向 REBAL 下发：Dat 用一条控制 Dat，Data 装 `C_ring×(4+4)` b 向量（≤512 b）；Snp 只传 64 b 饥饿位图，节点按位图本地均分。主列上界写成「越过 / 圆周」：`ρ_pass(s, C_ring) ≤ B_s / C_ring = ρ_max`。

## 轴一 可行性
1. **REBAL 带宽在物理上放不下。** 一条 REBAL 只装**一个段**的向量（`C_ring × 8 b`）。每个子环方向有 CS_NUM 个段，每段每 W_q 拍发一条，每条要逆流经过所有可能穿该段的上游（卡写一圈）。对向「跳 · 槽」需求 = 段数 × 跳数 / W_q：
   - top（21 CS）：21 × 21 / 16 ≈ 27.6 跳槽/拍，对向每拍至多 21 个 CS 出口槽 ⇒ **≈131%**；只走半圈也要 ≈66%。
   - bottom V（37 CS）：37 × 37 / 16 ≈ 85.6 对 37 ⇒ **≈231%**（半圈 ≈116%）。
   卡 §4 写「约 1/16 对向」，少乘了段数 C。若改成一条 REBAL 装全部段：C × C × 8 b = 3528 b（top）/ 10952 b（bottom V）≫ DAT Data 512 b。把税压到 10% 需 W_q ≥ 210 拍（top 全圈）/ ≥ 370 拍（bottom V），配额龄远超一次集合阶段，「把配额从闲上游挪到饿下游」来不及发生。
2. **`Σq=B_s` 不被执行。** REBAL 一圈 = Σlat 拍（top 42，bottom V 132–152），远大于 W_q=16。卡规则「收到新 q 的下一窗边界生效」⇒ 同一窗内有的节点用新 q、有的用旧 q，混合的 Σ 可以超过 B_s。要守住不变式必须给 q 加 epoch、约定在 ≥一圈之后的统一边界生效——再次放大配额龄。`sum_q_fail` 只是对段主计算结果的检查，不是对**生效中**配额的检查。
3. **上界定义自相矛盾。** §2.2 表 `B_s = ⌊ρ_max·W⌋ = 12`（W=16）；§2.4 主列改 `B_s = ⌊ρ_max·C_ring⌋`、`W_ρ = C_ring`，同时 `W_q=16`。若每 16 拍发放 B_s=15（按 C=21）个，速率上界是 15/16 ≈ 0.94，不是 0.75；§2.4「任意一圈越过次数 ≤ B_s」在 W_q < 一圈时不成立（一圈内有 ≥2.6 个配额窗）。再叠加 C_ring 按拍应为 42 而非 21，上界的数值需要整体重写。
4. Snp 侧：64 b 位图 + 本地确定性均分在宽度上可行（可借 SNPFLIT Addr 41–49 b + TxnID/FwdTxnID 12 b 等字段、配 SNP 保留 opcode）；但卡同时写了「ESL 1b/节点捎带」备选——那是新线（同 M-1/M-4）。
5. Sink / 死锁：配额用尽即 fail-wait，数据在端点；无丢包、无死锁。下游优先可能饿死合法上游（卡已列需扫 max-min）。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | 每向每 CS 槽 / 子环数 | 1；Dat 2 / Snp 1 | `TCsHighWay.h:135`；`gen_config.py:308` | ✅ |
| 2 | `CS_NUM ≤ 64` | — | `m_tgtCs` `uint64_t`（`chi_ring_common.h:275`）；实际 21/24/25/33/37/38 | ✅ |
| 3 | `C_ring` | `W_ρ = C_ring = 21`（top） | 一圈 Σlat：top 42，bottom H ≈72–76，V 132/148/152 拍 | ❌ |
| 4 | Dat REBAL 向量宽 | `C_ring×(4+4) ≤ 64×8 = 512 b` = DW | 单段向量放得下（top 168 b、bottom V 304 b）✅；但只覆盖 1 段 | ✅ 单段 / ❌ 全段 |
| 5 | REBAL 税 | 每 W_q 一圈 1 槽，≈1/16 | 每段一条 ⇒ top ≈131%、bottom V ≈231% 对向跳槽容量 | ❌ 少乘 C |
| 6 | Snp 位图 | 64 b，SNP 无 Data | 可塞入 SNPFLIT 头字段（Addr 41–49 + TxnID 12 等）+ 保留 opcode（0x0E–0x0F、0x18–0x1F）✅；「ESL 1b/节点捎带」= 新线 ❌ | ⚠️ |
| 7 | `q/used/d` 存储 | 每节点每段 12 b | 每 CS：段数 × 12 b × 6 子环 × 2 向 ≈ 3.0 kb（top）/ 5.3 kb（bottom V）新寄存器；位于哈希锁定库 | ✅ 量级（卡「寄存器文件」） |
| 8 | B_s / W_q / W_ρ | 12 或 ⌊0.75·C⌋ / 16 / C | 两处定义不一致，见轴一第 3 点 | ❌ |
| 9 | DAT Data 512 b @64 B | Table 13-9 | ✅ | ✅ |
| 10 | CHI Size 64 B 表号 | Table 13-18 | E.a 为 Table 13-20 | ⚠️ |
| 11 | 配额生效 / 配额龄 | `W_q + C_ring` | `W_q + Σlat`：top 58、bottom V ≈168 拍；且不同节点生效窗不同 | ❌ |
| 12 | highway 队列 / Dat 副本 | 0 / 0 | ✅ | ✅ |

## 接口落点核查（live `main@63163cad`）
| 卡声称 | 实际 | 结论 |
|---|---|---|
| `TCsHighWay.cpp:1041-1117` `used<q` 谓词，i-tag 服从 | `sendFlitToWay` `:1041-1118`；i-tag `:1095-1110`、`:894-950` | ✅；新分支 |
| 越过计数在 `:289-351` 与转发臂 | `tryWayToLocal` 起 `:289` | ⚠️ 转发臂不在该区间 |
| Dat REBAL 在 `tests/soc_sim/platform/` 组包，highway 识别 opcode | 平台可组包；逐 CS 截获、读改写 q 只能在 `TCsHighWay` | 新分支 |
| RTL | 仓内无 RTL | ✅ |

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| **GSF（Globally Synchronized Frames, Lee–Ng–Asanović, ISCA 2008）** | **FUNCTIONAL_EQUIVALENT** | 每帧给各源注入配额，使任一链路的帧内合计不超过容量——即 `Σ_i q_i[s] ≤ B_s` 每窗 |
| max-min 公平显式速率（ATM ABR ERICA 等）/ IEEE 802.17 RPR fair rate | FUNCTIONAL_EQUIVALENT | 按链路需求重算各源份额并下发；「下游优先」只是分配策略的一种选择 |
| 教科书 token bucket | 同类 | 每窗不结转的配额 = 窗口化令牌 |
| P-0198 M-6 TDMA | 不同 | 卡自述「只给拍数不给拍位」成立 |
| 逐节点 cap | 不同 | Σ 锁死这一点成立，但是 GSF 已有 |
| 环库 in-ring FC / i-tag | 不同执行点 | 同解下游饥饿 |
- 显式标注（captain 规则）：**窗口化配额 / token → FUNCTIONAL_EQUIVALENT**，理由同上。

## 指标核对
- 若 REBAL 税真实计入，对向 Dat / Snp 环被控制流量占满，双向 KV、all-to-all makespan 必然恶化；把 W_q 拉长到可承受则配额龄 ≥ 数百拍，赶不上集合阶段切换，下游优先失去意义。卡 §6 自己预留的 `uniform-q` 对照很可能吃掉全部收益。

## 判决理由
REJECT。机制本体是 GSF / max-min 显式速率分配在环段上的投影（FUNCTIONAL_EQUIVALENT）；物理上每段每 16 拍一条 REBAL 的控制负载超过对向环容量（top ≈131%、bottom V ≈231%），合成单条又放不进 512 b；`Σq=B_s` 在配额龄 ≫ 窗长时不被执行，上界定义前后不一。

## 若作者重提须先回答
1. REBAL 的真实跳槽负载（按段数 × 跳数 / W_q）与可承受的 W_q 下限，以及该 W_q 下配额能否跟上集合阶段。
2. 配额 epoch 与统一生效边界，证明生效中的 Σq ≤ B_s。
3. 统一 B_s / W_q / W_ρ 定义，按 Σlat 拍数重写上界。
