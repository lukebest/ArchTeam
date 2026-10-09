# Tier 0 · P-0221/M-8 · Dat 拍级子环着色

- 机制卡: mechanisms/P-0221/M-8.md（PR #104 head `4b8f7f6`）
- 题卡: problems/P-0221.yaml（main@c7522df）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: FAIL（HARD 臂 C2 的 RBRG 着陆重着色在物理上需要跨子环数据通路，且着陆点拿不到 `beat_idx`，除非加 flit 位或加按流状态表）
- 新颖性: FUNCTIONAL_EQUIVALENT（平台已有 `--sub-rr`：Dat 逐拍在两个子环间轮转）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 核查基准: 模型 `main@63163ca`；平台 `89f9c88`

## 卡摘要
Dat 设备 NI 与 RBRG 入环口按 `k = (cs_id + beat_idx) mod 2` 选 Dat 子环；所选子环满就等，不改投。跨环时以着陆 CS 号重算 k。不改路由表、不写 flit。宣称单源每子环 `λ ≤ 1/2`、单子环列车 ≤ ⌈B/2⌉；不宣称多源合计上界。

## 轴一 可行性
1. **设备口部分已经存在。** 平台 `Endpoint::pick_sub` / `send_dat_on`（main `Endpoint.h:178-206`；89f9c88 `:193-221`）在 `--sub-rr` 打开时，每发一拍 Dat 就把 `sub_next_` 推到下一个子环，所选子环没 credit 时顺延到另一个；HA 回读数据（`Endpoint.h:672`）与写数据（`TrafficGen.h` `flush_write_data`）都走这条。即：**同一源的连续拍在 Dat0/Dat1 之间交替，8 拍 txn 每子环 4 拍**——正是卡的单源性质。卡与 `--sub-rr` 的差别只有两点：(a) 加了 `cs_id` 相位；(b) 去掉了「满则改投」。(b) 是退化：卡自己的 C4 臂也承认改投可能更差，但在一个子环被过路占满、另一个空闲时傻等，会直接加长该拍的注入等待。
2. **RBRG 重着色在物理上不成立。** `connectNoChiRBRG`（`TMultiRing.cpp:534-557`）按 `subID` 成对建桥：源环 Dat sub k 的 RBRG NI 只连目的环 Dat sub k 的 RBRG NI。着陆时把一拍从 sub0 改到 sub1，需要在每个 RBRG 增加 sub0↔sub1 的交叉数据通路（2×2 交叉 + 对应 credit 回路）= 加线。另外着陆 RBRG 需要该拍的 `beat_idx`：CHI 里 512 B 不是一个事务（Size 最大 64 B），平台的「8 拍 txn」只是 `TrafficGen` 的抽象（`beats_per_txn=8`），flit 上只有 TxnID；DataID 在 DW=512 时恒为 0。卡又禁止用 DataID / RSVDC，那么着陆点要么新增 flit 位（加线），要么在 RBRG 维护按 TxnID 的计数表（新存储，卡未计）。HARD 臂 C2 不可实现。
3. **基线问题（重要）。** 不开 `--sub-rr` 时，`pick_sub` 恒返回 0（`Endpoint.h:180-181`）：**基线下 Dat 第二个子环完全闲置**，Rsp 同理。任何「把流量分到 Dat1」的卡在当前基线上都能拿到接近 2× 的 Dat 容量，这份收益属于平台已有开关，不是新机制。M-8 的 C0/C1 对照若不含 `--sub-rr`，结论无效。
4. 不宣称多源合计上界（卡 §3 自认）→ 题面闭合条件不满足。
5. Sink / 死锁：等待留在既有 share 缓冲 ✅。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | Dat / Snp `TNetwork` 数 | 2 / 1，`TRing.cpp:48-54` | ✅ | ✅ |
| 2 | 每子环每向槽 | 1 | ✅ | ✅ |
| 3 | 默认子环 | 0，`TMultiRing.h:77` | `defaultSubChannel = 0` ✅；平台注入口另由 `pick_sub` 决定，默认恒 0 | ✅ |
| 4 | 512 B → 8 拍 | `TrafficGen.h:51-54` | main `:52-54`；**89f9c88 `:67-69`** | ⚠️ 行号 |
| 5 | beat 64 B | `Endpoint.h:27` | main `:27`；89f9c88 `:29` | ⚠️ 行号 |
| 6 | AIC Dat share / out | 11 / 14，`gen_config.py:138-141` | 两边均 `:138-141` ✅ | ✅ |
| 7 | `dualRingRR` | `TBridge.cpp:253-258`，等长双路径 RR | ✅ | ✅ |
| 8 | L1 swap | `TNetworkInterfaceBase.cpp:664-718` | `updateSwapState` 起 `:664` ✅ | ✅ |
| 9 | 子环是对象树下标、不是 flit 字段 | `README.ch.md:169` | ✅ | ✅ |
| 10 | 新增 flit 位 | 0 | 设备口 ✅；**RBRG 重着色需要 beat_idx → flit 位或按 TxnID 状态表** | ❌（C2） |
| 11 | 跨子环通路 | 未提 | RBRG 按 subID 成对，跨子环 = 新数据通路（加线） | ❌ |
| 12 | CHI DataID | 2 b，仅 DAT | ✅；DW=512 时恒 0，本来也不能当拍号 | ✅ |
| 13 | 两 Dat 子环拓扑相同 | 假设 | 同一 `TRing` 用同一配置建两个 `TNetwork`（`:48-54`）✅ | ✅ |
| 14 | 一圈 | 42 / 72–76 / 132,148,152 | ✅ | ✅ |

## 接口落点与行号核查
| 卡引用 | 实际 | 结论 |
|---|---|---|
| 在 `TNetworkInterfaceBase.cpp` 选子环 | 子环在平台层选：`Endpoint.h` `pick_sub`（main `:178`，89f9c88 `:193`），`chi_send_dat(flit, 0, sub)` | ⚠️ 设备口可在**平台层**做（main 允许），不需改库 |
| `TNetworkInterfaceRbrg.cpp` 入目的环着色 | RBRG 按 subID 成对（`TMultiRing.cpp:534-557`），改子环 = 改拓扑 | ❌ 加线 |
| `--cc-scheme dat-color` | 平台开关可加 | ✅ |
| RTL | 无 | ✅ |

## 先例裁定
- **与平台 `--sub-rr`：FUNCTIONAL_EQUIVALENT**（逐拍两子环交替，单源每子环 ≤ ⌈B/2⌉）。
- 与 P-0198 M-5 CRRF（跨通道借环）：不等价（M-8 不跨通道，不借 Snp）。
- 与 P-0198 M-3 DPH（类→方向分区）：不等价（M-8 是动态逐拍交替，不是静态分区）。
- 与 P-0198 M-7 最短 CW/CCW、M-10 年龄/类仲裁：不等价。
- 与库内 `dualRingRR` / L1 swap / i-tag / FC / leaf-tag：不等价（卡自述成立）。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| **平台 `--sub-rr`** | **FUNCTIONAL_EQUIVALENT** | 设备口行为相同，差在 cs 相位与不改投 |
| 教科书多通道 / 多车道条带化（逐 flit 轮转到并行链路） | FUNCTIONAL_EQUIVALENT | 标准条带化 |
| P-0198 M-14 PSCK / M-18（多播） | 不等价 | — |
- 显式标注：不是 token / credit / window；是**并行子环条带化 → FUNCTIONAL_EQUIVALENT**。

## 指标核对
相对「只用 Dat0」的基线会有明显收益，但这份收益全部来自启用第二个子环，`--sub-rr` 已提供；相对 `--sub-rr` 的增量只剩 cs 相位，且被「不改投」抵消。

## 判决理由
REJECT。设备口部分与平台 `--sub-rr` 功能等价；HARD 臂的 RBRG 重着色需要跨子环通路和拍号信息，不满足「不加线」。另揭示一个基线问题：当前基线不开 `--sub-rr`，Dat1 闲置。
