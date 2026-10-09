# Tier 0 · P-0221/M-7 · RBRG 出队隔孔

- 机制卡: mechanisms/P-0221/M-7.md（PR #104 head `4b8f7f6`）
- 题卡: problems/P-0221.yaml（main@c7522df）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: FAIL（落点读错：`TNetworkInterfaceRbrg::xfer` 是缓冲到缓冲的搬运，不是写目的环；逐桥 1/2 上限不闭合；反压推回源环造成弹出失败绕圈）
- 新颖性: FUNCTIONAL_EQUIVALENT（= M-6 限定在 RBRG 注入口 + 库内本地 UP/DOWN 轮询；库内 FC 限速原语；P-0198 M-9 RBRG 闸窗同族）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 核查基准: 模型 `main@63163ca`；平台 `89f9c88`

## 卡摘要
每个 RBRG 口 / 子通道 / 目的方向一个本地 1-bit `GAP`。桥成功往目的环写入一拍后置 1；下一拍若目的环仍空，不给桥，空槽交给着陆 CS 本地设备或继续前送。队头留在「既有 15 深出缓冲」。Snp 关闭。卡给出 `ρ_ℓ^rbrg ≤ 1/2`。

## 轴一 可行性
1. **落点读错。** 卡写「RBRG `xfer` 成功把队头写入目的环空槽」（`TNetworkInterfaceRbrg.cpp:147-155`）。实际 `xfer()` 是：本 NI 输出缓冲（从源环弹出的 flit）在对端 credit>0 时 `pushFlitToInBuffer` 进**对端 NI（目的环一侧）的输入缓冲**（`:147-155`）。真正写目的环槽的是对端 NI 作为本地端口走 `TCsHighWay::tryLocalToWay`（`:598` 起）。所以 GAP 必须加在 `TCsHighWay` 的注入门上、对 RBRG 端口生效——这就是 M-6 的 OWE 只开在 RBRG 端口。队头被挡时待在对端输入缓冲（credit 管理），不是源侧 15 深输出缓冲。
2. **与现有本地仲裁的关系。** 同一 CS 的 UP/DOWN 两个本地 NI 已在 `tryLocalToWay` 中轮询（`m_localInputTokenList`，`:603-608`，注入后更新 `:1049`）。桥口和设备同时就绪时，现有 RR 已经让它们交替。GAP 只在「设备没就绪」时多做一件事：把空槽空着放下去（= M-6 效果）。
3. **闭合条件不满足。** `ρ^rbrg ≤ 1/2` 是对单个桥的逐节点上限，不约束「多个上游（含过路列车）合计」；卡自认更远下游不保证、`T_up→1` 时零作用。
4. **反压后果。** 桥注入速率减半 → 对端输入缓冲 credit 耗尽 → 源侧输出缓冲（ChangeRing `outputBufferDepth=15`，`docs/port_ChangeRing_cc.toml:11`；`gen_config.py:211-213`）填满 → **源环上要换环的 flit 弹出失败、继续绕圈**（`TCsHighWay.cpp:574-577` `eject_failed_times++`）。拥塞从目的环着陆点搬到源环整圈，跨 die 集合的 makespan 可能变差。卡 §4 列了「出缓冲满」，但没写出绕圈后果。
5. ChangeRing 端口开 L1/L2 swap（`gen_config.py:212-216`）：swap 状态下库内 FC 不限速（`docs/flowcontrol_setup.md:53`）。GAP 与 swap 的交互卡未定义。
6. Sink / 死锁：靠既有 credit，不丢 ✅；但绕圈 flit 的活性靠 e-tag，GAP 会放大绕圈次数。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | 每向槽 | 1 | `TCsHighWay.cpp:83-84` | ✅ |
| 2 | RBRG 出缓冲 | 15，`port_ChangeRing_cc.toml:11` | `docs/port_ChangeRing_cc.toml:11` `outputBufferDepth = 15` ✅；但这是**源环侧**弹出缓冲 | ✅ 数值 / ⚠️ 角色 |
| 3 | 被挡队头所在 | 「既有 15 深出缓冲」 | 被挡的是对端（目的环侧）NI 输入缓冲里的头；ChangeRing `shareBufferEn=False, singleSplitEn=True`（`gen_config.py:212`） | ❌ 位置错 |
| 4 | 出队条件 | `getCredit(dir)>0`，`TNetworkInterfaceRbrg.cpp:147-155` | 行号 ✅；语义是缓冲到缓冲 | ⚠️ |
| 5 | RBRG 着陆 | `TMultiRing.cpp:534-557` | `connectNoChiRBRG` `:534-557`：源/目的 NI 按**同一 subID** 成对 | ✅ |
| 6 | 一圈 / `L_link` | 42 / 72–76 / 132,148,152；2/3/4 | ✅（RBRG 只在 bottom：`docs/bottom_manyring.csv` 有 192 条 `ConnectPoint`；top 无 RBRG） | ✅ |
| 7 | change-ring 预留槽 | `TCrossStation.cpp:137-177`，给桥留槽 | `initRbrgSlot` `:137-177` ✅；bottom 各环 `reservedChangeRingSlot false`（`gen_config.py` ASSUMPTIONS `:42`） | ✅ |
| 8 | 新增 flit 位 | 0 | GAP 是本地寄存器 | ✅ 属实 |
| 9 | 新增存储 | 1 bit/桥口/子通道/向 | ✅ | ✅ |
| 10 | 反向占用 | 0 | ✅ | ✅ |
| 11 | Dat / Snp 子环 | 2 / 1 | ✅ | ✅ |
| 12 | NetworkFlowCtrl 路径 | `docs/flowcontrol_setup.md:30-53` | 所引段落为 §1.1–1.3 概述 ✅ | ✅ |

## 接口落点与行号核查
| 卡引用 | 实际 | 结论 |
|---|---|---|
| `src/TNetworkInterfaceRbrg.cpp` 出队后置 GAP | 应在 `src/TCsHighWay.cpp` `tryLocalToWay`（对 RBRG 端口） | ❌ 落点错；无论哪处都是哈希锁定库，新分支 |
| `gen_config.py:359-362` leaf-tag | main ✅；89f9c88 `:397-400` | ⚠️ |
| `gen_config.py:345`、`:429-451`、`:17-19` | main ✅；89f9c88 `:379`、`:476-495`、`:17-19` | ⚠️ |
| `--cc-scheme rbrg-gap` | 只能挂开关 | 新分支 |
| RTL | 无 | ✅ |

## 先例裁定（B\* = experiment_srcfc + i-tag + 动态 leaf-tag）
- **与 i-tag：不等价**（不打标、不绑定受益者）。
- **与库内 FC：功能等价（限速原语）**——同 M-6，RBRG 口的固定 1/2 空槽速率门。
- **与 change-ring 预留槽：极性相反**，卡自述成立。
- **与 P-0198 M-9（RBRG 闸窗，REJECT 可行性 FAIL：把 skid 当队列）/ M-16（RBRG 空槽拼接）：** 同属「在 RBRG 出口加闸」族；M-7 没有重犯 M-9 的「无合法拒绝动作」错误（credit 反压合法），但落到源环弹出失败绕圈。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| P-0221 M-6 | 同一机制的子集 | OWE 限在 RBRG 端口 |
| 库内本地 UP/DOWN 轮询（`TCsHighWay.cpp:603-608`） | 部分重合 | 桥与设备都就绪时已交替 |
| 库内 FC 令牌门 | FUNCTIONAL_EQUIVALENT | 固定速率版 |
| 题面「逐节点上限」 | FUNCTIONAL_EQUIVALENT | 逐桥 1/2 上限 |
| P-0198 M-9 / M-16 | 同族 | RBRG 出口闸 |
- 显式标注：**速率限制类 → FUNCTIONAL_EQUIVALENT**。

## 判决理由
REJECT。卡把 RBRG 缓冲间搬运当成写目的环，真实落点是 `TCsHighWay` 注入门，于是机制等于 M-6 只开在桥口，再加上已有的本地 RR；逐桥 1/2 上限不闭合，反压会把拥塞变成源环弹出失败绕圈。
