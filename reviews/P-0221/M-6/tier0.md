# Tier 0 · P-0221/M-6 · 注入成功让孔

- 机制卡: mechanisms/P-0221/M-6.md（PR #104 head `4b8f7f6`）
- 题卡: problems/P-0221.yaml（main@c7522df，含 PR #103 新增「加线判定 / 一圈按链路和 / 三项先例基线」）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: FAIL（闭合条件不满足：本质是逐节点静态上限；非工作保持，单源流注入时间翻倍）
- 新颖性: FUNCTIONAL_EQUIVALENT（逐节点限速 = 库内 FC 令牌桶门的固定速率形态；教科书 Cambridge Ring 防独占规则；P-0198 M-19 的无条件版）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 核查基准: 模型行号 bufferless-ring-noc `main@63163ca`（live tip 仍为此提交）；平台行号 `cursor/p0198-llm-noc-baseline-aa90@89f9c88`

## 卡摘要
每个（CS, 子环, 方向）一个本地 1-bit `OWE`。本地注入成功后置 1；之后第一个无预留空槽本 CS 不注入、放给下游，然后清 0。i-tag / leaf-tag 预留槽优先履约。Snp 关闭。卡给出 `λ_s ≤ (1−ρ_tr)/2`，只保证紧邻下游，多跳后孔率按「每个注入站减半」衰减。

## 轴一 可行性
1. **闭合条件不满足。** 题面 CONSTRAINT：「只给逐节点上限、不能对逐环段占用密度给出上界的方案不算闭合」。OWE 规则就是「每个节点最多吃到达空槽的一半」——逐节点上限，上限值相对空槽率而不是相对时间。卡 §3 自认：多个上游都在注入时，第 k 个下游看到的残差孔率约为 `(1/2)^k`，`ρ_tr→1` 时上界退化为 1。正是题面「上游合计把下游环段填满」的场景。
2. **非工作保持，主指标可能变差。** OWE 不看下游有没有需求，无条件让孔。单源主导的推理流量——decode P2P、broadcast 根、reduce/gather 中的单发送端——注入速率被砍到空槽率的一半，最坏把这一跳的注入时间翻倍，直接拉长 makespan。卡 §4 只把这一点写成「训练大块允许变差」，但 decode P2P 是主指标里的推理流量。
3. Sink / 死锁：被挡的头留在既有 `m_inputHead`（深度 1，`TNetworkInterfaceBase.cpp:110-113`），无丢失、无死锁 ✅。预留优先于 OWE，不破坏 i-tag / leaf-tag ✅。
4. 与基线 B\* 叠加：库内 FC（`experiment_srcfc`）在下游饥饿时已经把上游 NI 降速到 112/128；OWE 再无条件降到 ≤1/2 空槽，两层限速叠加，没有说明何时由谁生效。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | 每向每拍槽数 | 1，`TCsHighWay.cpp:83-84,182` | `m_sendFlit.resize(HIGHWAY_DIRECTION_NUM)` `:83-84`；`isHighwayEmpty` `:182` | ✅ |
| 2 | 槽声明 | `include/TCsHighWay.h:113,136` | `m_highWayBuf` `:113` ✅；`m_sendFlit` 在 `:135`（差 1 行） | ⚠️ |
| 3 | `m_highWayBuf` 容量 | `inLatency+1`，`:70-71` | `:70-71` ✅ | ✅ |
| 4 | 环上 payload 队列 | 0，`README.ch.md:127` | ✅ | ✅ |
| 5 | 一圈拍数 | top 42 / H 72–76 / V 132,148,152 | `docs/noc_simulator_faq.html:109`「42 cycles, 42 slots」✅；top `lats=[2]*21`、bottom H 3、V 4（行号见下表） | ✅ |
| 6 | 跳延迟 `L_link` | 2 / 3 / 4 | ✅（bottom ring 0 有 4 拍链路、偶数和修正 ±1） | ✅ |
| 7 | Dat / Snp 子环 | 2 / 1，`TRing.cpp:48-54` | 每通道 `sub_channel_cnt` 个 `TNetwork`（`:48-54`）；值 `req 1 rsp 2 snp 1 dat 2` | ✅ |
| 8 | NI head 深度 | 1，`TNetworkInterfaceBase.cpp:93-114` | `m_inputHead` 容量 1（`:110-113`） | ✅ |
| 9 | 新增 flit 位 | 0 | OWE 是 CS 本地寄存器，不随 flit 传 | ✅ 「不加线」属实 |
| 10 | 新增存储 | 1 bit/（CS,子环,向） | 每 CS 6 子环 × 2 向 = 12 bit；Snp 关则 10 | ✅ |
| 11 | 反向环占用 | 0 | ✅ 无信令 | ✅ |
| 12 | CHI 字段宽 | SrcID/TgtID 7–11、TxnID 12、DataID 2、SNP 无 Data | 与 CHI E 一致；本卡不用任何 CHI 字段 | ✅（与本卡无关） |
| 13 | 拍 / HBM | 64 B / 0 | `Endpoint.h` `kBeatBytes=64`：main `:27`，89f9c88 `:29`；HBM 0：89f9c88 `gen_config.py:49` | ✅（行号见下表） |
| 14 | i-tag 时延 | 饿 `2·thr=128` 拍才打标 | `wantItag` policy 0 `thr*2`，`itagThreshold=64` | ✅ |

## 接口落点与行号核查
| 卡引用 | 实际 | 结论 |
|---|---|---|
| `arbitration()` `TCsHighWay.cpp:217-264`，OWE 插在 `tryLocalToWay` 前 | `:217-264` ✅；`tryLocalToWay` `:598`，本地 UP/DOWN 轮询 `:603-608` | ✅ 新分支（哈希锁定库） |
| i-tag `:1095-1110,1151-1158,894-950`；leaf-tag `:745-805` | 全部 ✅ | ✅ |
| `gen_config.py:225-233` EXP_FC | main 与 89f9c88 均 `:225-233` | ✅ |
| `gen_config.py:486-487` `experiment_srcfc` 也开 Req FC | main `:486-487` ✅；**89f9c88 为 `:546-547`** | ⚠️ 引的是 main 行号 |
| `gen_config.py:359-362` 动态 leaf-tag | main `:359-362` ✅；**89f9c88 为 `:397-400`** | ⚠️ |
| `gen_config.py:345` top `lats` | main `:345`；**89f9c88 `:379`** | ⚠️ |
| `gen_config.py:429-451` bottom H/V | main `:430-449`；**89f9c88 `:476-495`** | ⚠️ |
| `gen_config.py:17-19` CS 数 | 两边均 `:17-19` | ✅ |
| `Endpoint.h:27` | main ✅；89f9c88 `:29` | ⚠️ |
| `--cc-scheme ishs` 开关 | `soc_main.cpp:80` 可加名；门本身必须进 `TCsHighWay` | 新分支 |
| RTL | 仓内无 RTL | ✅ |
- 结论：作者的平台行号全部对的是 **main@63163ca**，不是 89f9c88；在 89f9c88 上有 5 处漂移（见 SUMMARY-cons §1）。

## 先例裁定（基线 B\* = experiment_srcfc + i-tag + 动态 leaf-tag）
- **与 i-tag 预留槽：不等价。** i-tag 由饥饿触发，孔绑定给打标者（`sender_tagged`），上游不可用；OWE 由注入成功触发，孔不绑定，下一个有就绪流量的站就能吃掉。
- **与库内 FC：功能等价（限速原语）。** 库内 FC 的执行原语是 NI 级令牌桶注入门（`TCsHighWay.cpp:626`，`updateTokenBucket` `TNetworkInterfaceBase.cpp:1141`）；OWE 是令牌按「到达空槽」计、速率固定 1/2 的同一个门，只是去掉了「下游饥饿才降速」的反馈，变成无条件。
- **与 P-0198 M-19（邻节点饥饿气泡中继，REJECT FE）：** M-19 是「邻居饿了才让一槽」；M-6 是「每注一拍就让一槽」，无条件版。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| 题面「逐节点上限」 | **FUNCTIONAL_EQUIVALENT** | 上限按空槽计的 1/2 逐节点上限，题面已判为不闭合 |
| 教科书 Cambridge Ring 防独占（站点发完必须放过一个槽） | FUNCTIONAL_EQUIVALENT | 「发送后强制放过下一个空槽」就是这条规则 |
| 库内 FC 令牌桶门 | FUNCTIONAL_EQUIVALENT | 同一门控原语，固定速率、无反馈 |
| 库内 i-tag | 不等价 | 见上 |
| 库内动态 leaf-tag | 不等价 | leaf-tag 由饥饿分级触发、按设备类保留 |
| P-0198 M-19 | 同族 | 无条件版 |
| P-0198 M-6 TDMA | 不等价 | 无时隙表 |
- 显式标注（captain 规则）：属 **token / 速率限制类 → FUNCTIONAL_EQUIVALENT**。

## 指标核对
单源推理流注入减半 → makespan 可能变差；多源扇入时孔在中间站被吃掉，最差下游节点不一定受益。只在「紧邻上游是唯一注入源」这一窄场景有效。

## 判决理由
REJECT。机制不加线、不丢数据，但本质是按空槽计的逐节点 1/2 上限（题面判不闭合），也是库内 FC 令牌门的固定速率版本、Cambridge Ring 防独占规则；非工作保持，会拉长单源推理流 makespan。
