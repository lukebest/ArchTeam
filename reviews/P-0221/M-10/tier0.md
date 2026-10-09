# Tier 0 · P-0221/M-10 · 源 CS 奇偶绑定 Dat 子环

- 机制卡: mechanisms/P-0221/M-10.md（PR #104 head `4b8f7f6`）
- 题卡: problems/P-0221.yaml（main@c7522df）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: FAIL（DV200 top 挂载下主要 Dat 源同奇偶，「上游减半」不成立；RBRG 按着陆奇偶重绑需跨子环通路 = 加线；无段级上界）
- 新颖性: FUNCTIONAL_EQUIVALENT（静态键 → 并行通道分区，与 P-0198 M-3 DPH 同构；被平台 `--sub-rr` 支配）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 核查基准: 模型 `main@63163ca`；平台 `89f9c88`

## 卡摘要
Dat 注入口按源 CS 奇偶整笔绑定子环：`k = (cs_id & 1) ^ FLIP`；所选子环满则等。RBRG 入目的环时按着陆 CS 奇偶重绑。宣称「每个子环段上的上游注入源集合约减半」，`ρ` 仍可到 1。

## 轴一 可行性
1. **DV200 top 的实际挂载让「减半」落空。** 卡的前提是设备沿环奇偶交错。实际 top 环（main `gen_config.py:312-327`；89f9c88 `:346-361`）：
   - ring 0：AIC 在 CS 0,2,4,6,8（偶）和 11,13,15,17,19（奇）；COC 在 1,3,5,7（奇）和 12,14,16,18（偶）；3DIO（bottom→top 的 HBM/KV 读数据入口）在 CS 0,2,4,6,8,11,13,15（`DOWN`，与 AIC 同 CS）。ring 1 同构。
   - 所以在 CS 0–8 半环上，AIC 与 3DIO **全为偶**，全部绑到 Dat0；CS 11–19 半环上 AIC 与 3DIO 全为奇，全部绑到 Dat1。另一个子环在该半环只剩 COC。decode KV 读数据主流（3DIO→AIC）在每个半环内仍挤在同一子环上，可叠加上游**并没有减半**；同时每个源只能用一个子环。卡 §4 列了「挂载不交错则失效」，DV200 top 正是这种挂载。
2. **RBRG 按着陆奇偶重绑需要加线。** `connectNoChiRBRG`（`TMultiRing.cpp:534-557`）按 subID 成对建桥；把 sub0 来的 flit 放进目的环 sub1 需要新的跨子环数据通路与 credit 回路（加线）。HARD 臂 P2 不可实现。（RBRG 只在 bottom：`docs/bottom_manyring.csv` 192 条 `ConnectPoint`。）
3. **被 `--sub-rr` 支配。** 平台 `--sub-rr`（`Endpoint.h` `pick_sub`/`send_dat_on`，main `:178-206`）让每个源逐拍交替用两个子环，有 credit 时改投；M-10 让每个源只用一个子环。单源可用 Dat 带宽：`--sub-rr` 为 2 槽/拍/向，M-10 为 1。
4. 基线问题同 M-8：不开 `--sub-rr` 时 Dat1 闲置（`Endpoint.h:180-181` 恒返回 0）。M-10 相对这个基线的收益主要来自「启用 Dat1」，属平台已有开关。
5. 无段级上界（卡自认 `ρ` 仍可到 1）→ 题面闭合条件不满足。
6. Sink / 死锁：满则等，留在既有缓冲 ✅。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | Dat / Snp 子环 | 2 / 1，`TRing.cpp:48-54` | ✅ | ✅ |
| 2 | 每子环每向槽 | 1 | ✅ | ✅ |
| 3 | 默认 sub 0 | `TMultiRing.h:77` | ✅；平台口 `pick_sub` 默认恒 0 | ✅ |
| 4 | top 设备分环 | 偶端口号→ring0、奇→ring1，`gen_config.py:312-327` | 端口号奇偶分物理环 ✅（main 行号；89f9c88 `:346-361`） | ✅ / ⚠️ 行号 |
| 5 | 设备沿环奇偶交错 | 「评估须实测」 | **不交错**：同一半环内 AIC 与 3DIO 同奇偶，COC 反奇偶（见轴一 1） | ❌ 前提不成立 |
| 6 | 新增 flit 位 | 0 | 设备口 ✅（k 只是对象下标）；RBRG 重绑不需要 flit 位，但需要跨子环通路 | ✅ 位 / ❌ 线 |
| 7 | 新增逻辑 | 1-bit XOR | ✅ | ✅ |
| 8 | 一圈 | 42 / 72–76 / 132,148,152 | ✅（本卡无闭环，未误用） | ✅ |
| 9 | CHI DataID / SNP Data | 2 b 仅 DAT / 无 | ✅（本卡不用） | ✅ |
| 10 | 反向占用 | 0 | ✅ | ✅ |

## 接口落点与行号核查
| 卡引用 | 实际 | 结论 |
|---|---|---|
| Dat NI 入环 `k=(cs_id&1)^FLIP` | 设备口子环由平台 `Endpoint.h` `pick_sub` 决定（main `:178`，89f9c88 `:193`）；平台层可改 | ✅ 不需改库 |
| RBRG 着陆重绑 | `TMultiRing.cpp:534-557` 按 subID 成对 | ❌ 改拓扑 / 加线 |
| `gen_config.py:312-327` | main ✅；89f9c88 `:346-361` | ⚠️ |
| `--cc-scheme src-parity` | 可加开关 | ✅ |
| RTL | 无 | ✅ |

## 先例裁定
- **与 P-0198 M-3 DPH（类→CW/CCW 方向分区，REJECT FE）：同构，FUNCTIONAL_EQUIVALENT。** DPH 用静态键（流量类）把流量分到两条并行通道（两个方向）；M-10 用静态键（源 CS 奇偶）把流量分到两条并行通道（两个 Dat 子环）。键不同，执行原语相同，不是简单改名。
- 与 P-0198 M-5 CRRF（通道–环重绑）：不等价（不跨通道）。
- 与 P-0198 M-7 最短 CW/CCW：不等价（不改方向）。
- 与 P-0198 M-10 年龄/类仲裁：不等价（不改仲裁）。
- **与平台 `--sub-rr`：同解且被其支配。**
- 与库内 i-tag / FC / leaf-tag / `dualRingRR`：不等价。
- 与 P-0221 M-8：同族（M-8 逐拍动态，M-10 逐源静态）。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| **P-0198 M-3 DPH** | **FUNCTIONAL_EQUIVALENT** | 静态键分区到并行通道 |
| 教科书静态车道分配（按源哈希选并行链路，ECMP 类） | FUNCTIONAL_EQUIVALENT | 以源号为哈希键 |
| 平台 `--sub-rr` | 支配 | 动态交替优于静态绑定 |
- 显式标注：不是 token / credit / window；是**静态并行通道分区 → FUNCTIONAL_EQUIVALENT**。

## 判决理由
REJECT。静态奇偶绑定与 P-0198 M-3 DPH 同构，且被平台 `--sub-rr` 支配；DV200 top 的实际挂载让主要 Dat 源在半环内同奇偶，「上游减半」不成立；RBRG 重绑需要跨子环通路（加线）。
