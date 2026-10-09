# T1 综合 · P-0198/M-5r1 CRRF-SB

- 裁决：**FAIL**，未过线，退回架构师 Jim Keller（T1-return）；不进 Tier 2 / #eval
- 卡：PR #85 `mechanisms/P-0198/M-5r1.md`（本综合不改卡）；T0：PR #89（PASS_T1 / INCREMENTAL，本综合不改 T0）
- 规则：≥3 通过/有条件通过 **且无致命** → Tier 2。有条件通过计过线票；致命缺陷一票否决
- 票：3 有条件 + 1 致命 → 否决
- 分歧最大意见：Dr. Archi（Snp 窄环载 Dat；无 per-node ghost 密度帽）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 裁决表

| 评审 | 结论 |
|---|---|
| Dr. Archi | **致命缺陷** |
| Prof. Sys | 有条件通过（两条前置不满足即升致命：位宽；跨通道循环依赖死锁） |
| Prof. Bench | 有条件通过 |
| Dr. Sim | 有条件通过 |

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 1 | 3 | 3 | 3 | 3 |
| 新颖性 | 2 | 2 | 2 | 3 | 2 |
| 预期收益 | 1 | 3 | 2 | 3 | 2.5 |
| 评估可信度 | 1 | 3 | 2 | 2 | 2 |
| 系统可组合性 | 2 | 2 | 3 | 3 | 2.5 |

## 一致点（主持五项，摘自四份，不改写）

- **位宽**：四票均判未闭合。Archi = OPEN-致命（Snp 无数据字段；ghost 要 k≈6–8 个 Snp 槽或加线；Dat 已 2 子环 vs Snp 1，卡 `1+duty_dat` 基线少算一条环；soc_sim 四通道同构 flit，静默把 Snp 当 Dat 宽）。Sys 前置：不选加宽/拆拍并计入 `C_dat_eff` 即升致命。Bench：RTL 不动则只能拆拍，k 未声明则两列偏乐观。Sim：须选拓宽或拆拍，禁止 1 flit=1 txn。
- **优先级反转 / i-tag**：四票均判卡未闭合。Archi = OPEN-致命（无 per-node 密度帽；库内 i-tag 只保证活性/终会注入，不保证 ≤1.4）。Sys/Sim：ghost 须服从 Snp 环保留槽，且 **ghost 不得在 Snp 环上发 i-tag**；否则自带段/节点密度帽。Bench：最坏在热 ghost 源下游；i-tag 依赖若为过线必要须写进卡。
- **Ghost orbit vs Drain**：四票有条件。须定义 ghost 弹出落点与 e-tag 归属；Drain 看门狗 + 上界（圈数/`looped_times` 分布）；harness dest 必弹出，现有探针测不到。
- **NACK 重注入数据来源**：四票有条件。合法路径 = 原地 Snp→Dat、1 深 holding、禁止源端副本；holding 满 = 留环，不丢不排队。源端保留副本：Archi/Sys/Sim 升致命。
- **drain-off + header-only**：四票必须跑（含跨 die / RBRG）。Archi 在作者默认负载上两臂数字完全相同（1.000 / 0.569），epoch/bind 大概率赘余。

## 分歧点

- **致命 vs 有条件**：Archi 位宽 + 无密度帽已结构性击穿；Sys 把位宽与跨通道循环依赖写成升致命前置；Bench/Sim 认为两项有合法闭合路径，不升致命。
- 新颖性：Sim 3 vs Archi/Sys/Bench 2（header-only 若等价再降）。
- 预期收益：Archi 1（k≥6 时 Dat 下界 ≈0.94–0.95）vs Sys/Sim 3、Bench 2（Snp 侧只是止损）。

## 分歧最大意见（摘自 Archi / Sys，不改写）

1. **位宽（Archi OPEN-致命）**：Snp flit 无数据字段；ghost Dat 需要 k≈6–8 个 Snp 槽，或新增 ≥512 bit/方向/链路导线。Dat 已有 2 条子环、Snp 1 条，卡 §1「四条独立双向环」与 `C_dat_ideal = 1 + duty_dat` 把 Dat 当成 1 条，基线错了一倍。soc_sim 用同一 `CHIFlitFields`，任何 flit 占一个槽，静默把 Snp 当 Dat 宽。
2. **密度帽（Archi OPEN-致命）**：无 per-node / per-tenant ghost 密度上限。库内 i-tag（`TCsHighWay.cpp`）只保证终会注入，不保证 ≤1.4；默认约 128 拍才打标。作者 harness 只加大 Dat 量（规则不动），推理混合列 Snp 已到 1.41–8.8×。
3. **Sys 最强反对**：Snp/Dat 共一条物理环，拆掉 CHI 通道独立 → 可能协议级循环依赖：Dat 入口满（等事务）→ 事务等 Snp → Snp 上不了环（被绕圈 ghost 占）→ ghost 出不了环（Dat 入口满）。本征优先只在本地空槽成立，打不破这个环。
4. **Archi 消融**：作者 harness 的 drain-off / header-only 臂与完整机制在默认负载上**完全相同**（Snp/Dat 均为 1.000 / 0.569）；epoch/bind 大概率赘余，只剩拙劣的全局密度窗。

## 单一视角会漏的盲点

- Archi：`snp_path` 无 Dat ⇒ 1.000 由构造给出；dest 双环无限 eject；`1+duty` 相对 Dat×2 少算一条环。
- Sys：跨通道循环依赖不是 i-tag 阈值能修的；须结构性保底（段保留槽或 eject 口与 Dat 入口解耦）。
- Bench：「推理混合」在库与 soc_sim 里都不存在（本征 Snp=0）；KILL 列测的是作者自定合成 Snp。
- Sim：harness `snp_path` 两臂 `ms_snp` 同为 15.0（空环恒等）；`model.py` 几何近似对不上 7.8/19.0/1.0。

## 退回须回应的核心（交 Jim Keller，不改写四份条件）

1. **位宽**：二选一并计入面积 / `C_dat_eff`——加宽 Snp 到 Dat 宽，或 k 拍拆分；禁止再用 `1+duty_dat`。未选或 k=1 当主列 = 维持致命。
2. **密度帽 + i-tag**：per-node / per-tenant ghost 密度上限；写明 i-tag 策略（ghost 服从 Snp 环保留槽，**ghost 不得在 Snp 环上发 i-tag**）。
3. **弹出 / Drain**：定义 ghost eject 口与 e-tag 归属；Drain 看门狗与上界；报 `looped_times` / Drain 时长分布。
4. **NACK**：原地 Snp→Dat、1 深 holding、无源端副本；holding 满行为写死（留环）。源端拷贝 = 致命。
5. **强制消融**：drain-off + header-only，须含跨 die / RBRG 流量；与 on-arm 同表。等价则删 epoch/bind、重评新颖性。
6. **Bench 负载条件**：定义 15:1 推理混合成分；Snp 发生器 ≥3 档速率（含 0.05），Snp 源放在热 ghost 源下游；15:1 / 7:1 / 3:1 同表。
7. **Sim 评估条件**：同一分支 / 同一 harness / 同一 i-tag/e-tag，只切换 rebind；多种子 p99 / p99.9 + bootstrap CI + 分位样本数。

## KILL 条件（原文复述）

duty 15:1 下，Snp makespan 相对 rebind-off 必须 ≤1.4（<1.5625），**snp_path 与推理混合两列各自满足**；不允许平均，不允许用 Dat 收益抵扣。卡上 7.8→1.0 / 19.0→1.0 未签字，只当假设（Sim：减箱空环恒等式；`snp_path` 两臂 `ms_snp` 同为 15.0）。

## 约束

RTL 不改。仿真器结构改动只允许开在 `bufferless-ring-noc` **新分支**。主指标：推理 makespan + 尾延迟。
