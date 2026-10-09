# Tier 0 汇总 · P-0221 保守架构师 M-6..M-10

- 题卡: problems/P-0221.yaml（main@c7522df，含 PR #103 新增：加线判定、一圈 = 链路延迟和、三项先例基线）
- 机制卡: PR #104 head `4b8f7f6`，mechanisms/P-0221/M-6..M-10.md
- 审查人: 设计验证（Tier 0）
- 日期: 2026-10-09
- 本文件不覆盖 SUMMARY.md（Jim M-1..M-5）

## 1. 核查基准与行号
- 模型（`include/`/`src/`、docs）：bufferless-ring-noc `main@63163cad900979ab00edff1e0268f87b37b18e3b`（live main tip 未变）。
- 平台（`tests/soc_sim/`）：`cursor/p0198-llm-noc-baseline-aa90@89f9c88`。
- **结论：作者事实附件里的平台行号全部对应 main@63163ca，不是 89f9c88。** 在 89f9c88 上的漂移：

| 引用（卡） | main@63163ca | 89f9c88 |
|---|---|---|
| `gen_config.py:312-327` top 设备挂载 | ✅ | `:346-361` |
| `gen_config.py:345` top `lats=[2]*21` | ✅ | `:379` |
| `gen_config.py:359-362` 动态 leaf-tag | ✅ | `:397-400` |
| `gen_config.py:429-451` bottom H/V lats | ✅（`:430-449`） | `:476-495` |
| `gen_config.py:486-487` experiment_srcfc | ✅ | `:546-547` |
| `TrafficGen.h:51-54` 512 B / 8 拍 | ✅（`:52-54`） | `:67-69` |
| `Endpoint.h:27` kBeatBytes | ✅ | `:29` |
| `Endpoint.h` `pick_sub`（审查补引） | `:178` | `:193` |
| `gen_config.py:17-19`、`:134`、`:138-141`、`:198`、`:225-233` | ✅ | 不变 |
| `gen_config.py:157` HA insertAfterRemoval | `:156` | `:156`（卡差 1） |
| 「soc_sim 不生成 UturnConnect」 | ✅ | **已加 `uturn` 开关**（`:326-330`、`:384-389`，默认关） |

- 模型行号：`TCsHighWay.cpp:70-71, 83-84, 182, 217-264, 574-577, 745-805, 894-950, 1095-1110, 1151-1158`，`TRing.cpp:48-54`，`TMultiRing.cpp:534-557`，`TMultiRing.h:77`，`TBridge.cpp:253-258`，`TCrossStation.cpp:137-177`，`TNetworkInterfaceBase.cpp:40, 93-114, 664-718`，`TNetworkInterfaceRbrg.cpp:147-155`，`README.ch.md:127, 169`，`docs/noc_simulator_faq.html:109`，`docs/port_ChangeRing_cc.toml:11`，`chi_common.h:92-97` **全部位置正确**。唯一偏差：`include/TCsHighWay.h:136` 应为 `:135`（与 Jim 批次同一错误）。
- 但两处**语义**读错：`TNetworkInterfaceRbrg.cpp:147-155` 是缓冲到缓冲的搬运，不是写目的环槽（M-7）；`arbitration()` `:217-264` 只在 `insertAfterRemoval/directConnect` 为真时先弹出后注入，为假时顺序相反（M-9）。
- 一圈拍数 42 / 72–76 / 132,148,152 与 `L_link` 2/3/4：全部正确（`noc_simulator_faq.html:109` 明写「42 cycles, 42 slots」）。

## 2. 判决表
| 卡 | 机制 | 判决 | 新颖性 | 一句话理由 |
|---|---|---|---|---|
| M-6 | 注入成功让孔 | REJECT | FUNCTIONAL_EQUIVALENT（逐节点限速；库内 FC 令牌门固定速率版；Cambridge Ring 防独占） | 每节点最多吃到达空槽的一半 = 逐节点上限，题面判不闭合；无条件让孔使单源推理流注入减半 |
| M-7 | RBRG 出队隔孔 | REJECT | FUNCTIONAL_EQUIVALENT（= M-6 限在 RBRG 口 + 已有本地 UP/DOWN 轮询；P-0198 M-9/M-16 同族） | 把缓冲间 `xfer` 当成写目的环；逐桥 1/2 上限；反压推回源环导致弹出失败绕圈 |
| M-8 | Dat 拍级子环着色 | REJECT | FUNCTIONAL_EQUIVALENT（平台 `--sub-rr`） | 设备口逐拍交替两子环 = `--sub-rr`；RBRG 重着色需跨子环通路 + 拍号（加线） |
| M-9 | 弹出孔前送 | REJECT | EXACT_MATCH（库内 `insertAfterRemoval=false`） | 弹出当拍不注入就是该开关为 false 时 `arbitration()` 的现成顺序；设备口零代码可得 |
| M-10 | 源 CS 奇偶绑定 Dat 子环 | REJECT | FUNCTIONAL_EQUIVALENT（P-0198 M-3 DPH 同构；被 `--sub-rr` 支配） | DV200 top 上 AIC 与 3DIO 在半环内同奇偶，「上游减半」不成立；RBRG 重绑需加线 |

PASS_T1：0 / 5。KILL：0（五张卡全部关闭 Snp，Snp 小包路径不受影响）。

## 3. 先例裁定（按总监要求逐项）
基线 B\* = `--fc-profile experiment_srcfc` + i-tag（默认 policy 0、`itagThreshold=64`）+ 动态 leaf-tag（top Dat 默认开）。五张卡都声明叠加在 B\* 上 ✅。

| 卡 | 与 i-tag 预留槽 | 与库内 FC（experiment_srcfc） | 与 leaf-tag |
|---|---|---|---|
| M-6 | **不等价**：注入成功触发、孔不绑定受益者 | **等价（限速原语）**：同一 NI 注入门，固定 1/2 空槽速率、无饥饿反馈 | 不等价 |
| M-7 | **不等价** | **等价（限速原语）**：同 M-6，限在 RBRG 口 | 不等价；与 change-ring 预留槽极性相反（卡自述成立） |
| M-9 | **不等价** | **不等价**（无速率、无反馈） | 不等价；**等价于库内 `insertAfterRemoval=false`** |

| 卡 | P-0198 M-3 DPH（类→方向） | P-0198 M-5 CRRF（通道–环重绑） | P-0198 M-7 最短 CW/CCW | P-0198 M-10 年龄/类仲裁 | 库 / 平台已有 |
|---|---|---|---|---|---|
| M-8 | 不等价（动态逐拍，非静态分区） | 不等价（不跨通道、不借 Snp） | 不等价 | 不等价 | **平台 `--sub-rr` 功能等价** |
| M-10 | **同构，FUNCTIONAL_EQUIVALENT**（静态键→并行通道） | 不等价 | 不等价 | 不等价 | 被 `--sub-rr` 支配 |

## 4. 物理假设汇总（「不加 flit 位」是否属实）
| 卡 | 「0 新 flit 位」 | 「不加线」 | 备注 |
|---|---|---|---|
| M-6 | ✅ 属实（CS 本地 1 bit） | ✅ | 每 CS 12 bit |
| M-7 | ✅ 属实 | ✅ | 但被挡头的位置写错：在目的环侧 NI 输入缓冲，不在 15 深出缓冲 |
| M-8 | 设备口 ✅；**RBRG 臂 ❌**：着陆点要算 `beat_idx`，flit 上没有（CHI 无 512 B 事务，DW=512 时 DataID 恒 0），需加 flit 位或按 TxnID 状态表 | **❌**：RBRG 按 subID 成对（`TMultiRing.cpp:534-557`），跨子环 = 新数据通路 | HARD 臂 C2 不可实现 |
| M-9 | ✅ 属实 | ✅ | 设备口零代码 |
| M-10 | ✅ 属实（k 是对象下标） | **❌**：RBRG 着陆重绑同 M-8 需跨子环通路 | HARD 臂 P2 不可实现 |

其他物理项：环数（Dat 2 / Snp 1）、`L_link`、一圈拍数、`m_highWayBuf = inLatency+1`、NI head 深度 1、AIC Dat share/out 11/14、ChangeRing `outputBufferDepth=15`、CHI 字段宽（SrcID/TgtID 7–11、TxnID 12、DataID 2、SNP 无 Data）全部核对通过。

## 5. RTL / 落点
- 仓内无 RTL，五张卡均不触 RTL。
- M-6、M-7（正确落点）、M-9 的 RBRG 口变体：`TCsHighWay` 注入门，哈希锁定库 → 新分支。
- M-8、M-10 的设备口部分：在平台层 `Endpoint.h` `pick_sub` 即可实现（不需改库）；RBRG 部分需改拓扑（加线）。
- M-9 设备口：端口 TOML `insertAfterRemoval=false`（平台层 `gen_config.py`），零代码。
- 净室说明：五张卡都不是旧卡的简单改名；M-10 与 P-0198 M-3 DPH 执行原语相同（判 FE），M-6 是 P-0198 M-19 的无条件版，M-7 与 P-0198 M-9/M-16 同属「RBRG 出口加闸」族。

## 6. 给用户 / 总监的决策点
1. **基线漏了 `--sub-rr`（重要）。** 平台 `pick_sub` 在不开 `--sub-rr` 时恒返回子环 0（main `Endpoint.h:180-181`）：**当前基线下 Dat 第二个子环和 Rsp 第二个子环完全闲置**。题面写「Dat 2 子环」，但基线只用了一个。任何把流量分到 Dat1 的卡（M-8、M-10，以及以后的同类卡）相对当前基线都会白拿接近 2× Dat 容量。建议：B\* 加上 `--sub-rr`，或在题面里明写基线只用 Dat0 并说明理由。这一项也影响 P-0198 已有结果的解读：89f9c88 上 `workloads/p0198-llm-noc/configs/` 的 11 个 baseline JSON 都没有设置 `sub_rr`（`run_soc.py --sub-rr` 默认关），即 P-0198 各基线臂同样只用 Dat0。
2. **把 `insertAfterRemoval=false`（设备口）加进基线扫描。** M-9 的效果零代码可测；有效则属于基线调参。
3. **等负载基线重核（已派出）时一并跑**：B\* 基础上 ±`--sub-rr`、±`insertAfterRemoval=false`，看沿环注入等待梯度是否还在。若都消失，按题面待证伪条款收窄。
4. **平台分支行号**：作者事实附件是 main@63163ca 的行号；若 T1 在 89f9c88 上跑，按 §1 表重对齐。89f9c88 已有 `uturn` 开关，与「soc_sim 不生成 UturnConnect」的事实条目不再一致，建议更新事实附件。
