# 位宽 / 环数核查 · P-0198/M-5 CRRF T3 与 card-claim（评估审计，只读）

- 被查对象：T3 sim PR #73（`da294cb` smoke / `b0b4cf9` night），card-claim PR #83 tip `9f39cc7`。`sim.py` 在 `da294cb → b0b4cf9 → 9f39cc7` 之间**没有改动**，下文行号三处通用。
- 触发：M-5r1 T1 裁决（PR #95 `reviews/P-0198/M-5r1/`）里 Dr. Archi 报了两个致命问题：Snp 窄环载 Dat 时 k≈6–8；Dat 实际是 2 条子环。
- 本核查**未改** sims/ models/ mechanisms/ results，也没有开 PR。临时脚本和结果放在 `runs/width_ring_check/`（未跟踪、未提交）。

## 结论

1. **(a) 没有建模位宽。** sim 里一个槽装一整笔 512 B 事务（flit=txn），Snp 槽和 Dat 槽一样大。一笔 ghost Dat 只占 **1 个 Snp 槽**，等于默认 **k=1**（Snp 环和 Dat 环一样宽）。代码里没有位宽、拍数或 k 的旋钮。
2. **(b) 环数是 Dat 1 + Snp 1，不是 Dat 2 + Snp 1。** 每个 CHI 通道每方向只有 1 条环。rebind-off 时 Dat 容量 = **1 条环**（每方向每节点每拍 1 槽）。CRRF 被算成把 Dat 从 1 条翻到「1+duty」条。卡、T2 和 T3 一路都用 `C_dat_ideal = 1 + duty_dat`。平台真值是 `sub_channel_cnt … snp 1 dat 2`。
3. **(c) 收益被严重高估。** 用 k=6–8、Dat×2 当基线重估：
   - C_dat_eff（相对 off）从 1.49/1.58/1.63 降到 **≈1.04–1.06（不扣税）**，按原公式扣税后 **≈1.00–1.01**。
   - Dat 受限的 makespan 比值从 0.55–0.72 回到 **≈0.92–0.97**，没有一类能过 0.85 的约束线。
4. **另一个独立的放大项。** card-claim 和 night 用的 bbox 是 |I|=96、t_steady_laps=12。整个作业都落在**第一个 DAT_EPOCH** 里，采样期间一次 flip 也没有。所以 3:1/7:1/15:1 的 makespan 完全相同，实际测的是 duty=1、f=1、零 drain 税。REPORT.md:82 把这归因为「eject/root 串行封顶」，**归因不对**。
5. **建议。** (i) M-5 T3「存活」→ **退回重测**。(ii) card-claim「部分成立」→ **撤回**（withdraw）。两项都属于物理假设错误造成的模型假象，不是诚实地没过杀线，所以不判淘汰。

## 证据

### (a) 位宽 / 每拍载荷
- `sims/P-0198/M-5/sim.py:16` 写明 black box 是 `flit=txn (512 B)`；`:79` 是 `BYTES_PER_TXN = 512`。这个常量只用于 goodput 报表（`:985`），不参与槽占用。
- `sim.py:167-177` 的 `Slot` 只有 kind/chi/phys/src/dst/tid/epoch_tag/is_ghost/nack，**没有宽度、拍数或分片字段**。
- `sim.py:720-726`：ghost 判定成立并且 `new["Snp"][dir][node]` 为空时，整笔 Dat 事务 `_do_inject(node, txn, "Snp", True)` 进 **1 个** Snp 槽。`:731-733` 走主 Dat 槽，用法完全对称。
- `sim.py:599-603`：ghost 在目的端一次 eject 就完成整笔事务，没有重组。
- `SimConfig`（`sim.py:306-327`）没有 width / k / beats / ring-count 参数，**没有现成旋钮**可用来界定影响。
- card-claim bbox 自己也写了 `flit=txn 512 B`（`results/card_claim/REPORT.md:47`；`card_claim.py:524`）。
- 平台侧：`CHIFlitFields` 没有数据字段，Snp/Dat 是同一个结构的 typedef（`bufferless-ring-noc@63163ca tests/esl_wrapper/compat/chi_common.h:92-118`），一个 Dat 拍 64 B（`tests/soc_sim/platform/Endpoint.h:27`）。Archi 给的 k≈6–8 来自 **repo 外**的 AMBA CHI 量级（Snp flit 约 90–120 bit，Dat flit 约 680–730 bit；`reviews/P-0198/M-5r1/Dr.Archi.md:5,61`）。**DV200 实际的 Snp/Dat 链路位宽在 repo 里查不到，记为 unknown。**

### (b) 环数
- `sim.py:65` `CHI = ("Req","Rsp","Snp","Dat")`，`:66` `DIRS = ("CW","CCW")`。`:395` 的 `self.slots = {c: {d: [Slot]*n}}` 表示每通道每方向 1 条环、每节点 1 槽。`:855-862` 每通道各转一跳。**Dat 只有 1 条环。**
- 注入：每节点每拍最多注入 1 笔 Dat（ghost 和主环二选一，`sim.py:716-739`）。
- 容量记账：`sim.py:916` `ideal = 1.0 + duty_dat`，`:917` `raw = 1.0 + duty_dat·f_st − τ_sync − τ_bind`，`:918` off 时 `c_eff = 1.0`。也就是基线 1 条环，借用 1 条 Snp 环、而且按 **同宽** 计。注意 C_dat_eff 是**公式**（FSM 时间占比代入），不是从槽占用测出来的。
- 卡：PR #53 `mechanisms/P-0198/M-5.md:18`「Req/Rsp/Snp/Dat 静态 1:1 绑四条独立双向环」，`:20`「Dat 逻辑在 DAT_EPOCH temporarily 获得第二物理环……理想有效 ≤1+duty_dat」，`:46,94` 同。§2.1 结构表**没有位宽这一行**（`:28-36`）。
- T2：PR #63 `models/P-0198/M-5/spec.md:76,108-110` 和 `insight.md:7` 都写 `C_dat_ideal = 1+duty_dat`，「Dat 环始终 1」。
- 平台真值：`bufferless-ring-noc tests/soc_sim/gen_config.py:308,532` 是 `sub_channel_cnt req 1 rsp 2 snp 1 dat 2`。**Dat 有 2 条子环，Snp 只有 1 条。**
- 已有审计（#67/#75/#76/#86）全都没有核过位宽或子环数（grep `位宽|width|子环|sub_channel` 无命中）。这是审计漏项。

### 附：duty 没有被测到（card-claim / night 的 Dat makespan）
- `card_claim.py:247,250` 设 |I|=96，`t_steady_laps=12`（`sweep.py:135-139` 的 night 设置相同）。`sim.py:391-392` 给出 t_steady=168 拍，3:1 时 dat_dwell=126、15:1 时为 158。
- `sim.py:417,535-538` 第一次 flip 就进 DAT_EPOCH。`:325,652` 的 `hold_app_until_aligned=True` 让应用流量等到「已提交 + STEADY」才开始。
- 临时探针（scratch，gather，seed 20260903）：采样期内所有 die 的状态集合**只有 `('Dat','STEADY')`**，makespan 为 27（3:1）和 27（15:1）。把 `t_steady_laps` 改成 1，同一负载 makespan 变成 101，比 off 的 49 还慢。所以 0.551/0.667/0.719 是「Snp 环在作业期间 100% 借给 Dat、零税」的结果。

## 估算（第一性）

记 g = duty·f_steady。基线换成 Dat×2 子环，一个 Dat 拍 = k 个 Snp 槽：

- 原 sim：C_off = 1，C_on = 1 + g − τ，相对增益 = g − τ。
- 修正后：C_off = 2，C_on = 2 + g/k − τ'，**相对增益 = (g/k − τ')/2**。

night gather 行（`results/night/capacity.csv`）：f=0.7727，τ_sync+τ_bind=0.0916，g = 0.580 / 0.676 / 0.724（3:1 / 7:1 / 15:1）。

| | 3:1 | 7:1 | 15:1 |
|---|---|---|---|
| 原签 C_dat_eff | 1.488 | 1.585 | 1.633 |
| k=6，不扣税 | 1.048 | 1.056 | 1.060 |
| k=8，不扣税 | 1.036 | 1.042 | 1.045 |
| k=6，按原公式扣税 τ（对 2 环归一） | 1.003 | 1.011 | 1.015 |
| k=8，按原公式扣税 | ≈1.00（钳位） | 0.997→1.00 | 0.9995→1.00 |

Dat 受限的 makespan 比值 ≈ 1/C_rel。gather 的瓶颈是汇点 eject：off 时每拍 4 个口（2 子环 × 2 向），ghost 再加 2/k。
- card-claim 机制（实际 g=1，零税）：4/(4+2/k) = **0.923（k=6）/ 0.941（k=8）**。
- night 的 duty（g=0.58–0.72）：**0.952–0.974**。

allgather、alltoall、uniform_read 是环链路受限，同一公式给出 **0.92–0.97**。

| 签字 / 声称数 | 原值 | 重估（k=6–8，Dat×2） | vs 0.85 |
|---|---|---|---|
| gather T/off | 0.551 | ≈0.92–0.97 | 不过 |
| allgather | 0.667 | ≈0.92–0.97 | 不过 |
| alltoall | 0.719 | ≈0.92–0.97 | 不过 |
| decode_kv_p2p | 0.824 | ≈0.95–0.98 | 不过 |

重估与 Archi 独立给出的「环受限 T_dat/off ≥0.94–0.95」（`Dr.Archi.md:22,66`）一致。上表是**乐观上界**，因为没算这几项：拆拍要连续 k 槽（注入概率约 (1−ρ)^k）、按源重组缓冲、SerDes、以及 ghost 把 Snp 环的占用放大 k 倍。

**Scratch 交叉验证**（`/tmp/m5scratch`，副本见 `runs/width_ring_check/`，3 trials，no_cc，未提交）。我在 sim 副本上加了两处改动：Dat 第 2 条子环；ghost 拆成 k 个 Snp 子片，第 k 片到达才算完成（重组按免费处理，这对 CRRF 偏乐观）。
- 先验证副本：Dat=1、k=1 时，原版 0.551 / 0.667 / 0.827 / 1.000 / 0.716 全部复现。
- 改成 Dat=2、k=6–8，ghost 只在主环槽满时溢出使用：|I|=96 时 allgather 0.926，其余**均 >1**（例如 gather 1.48–1.96）；|I|=768 时 uniform 0.955–0.959、allgather 0.975、alltoall 0.962–0.979，gather 和 allreduce 都 >1.2。
- 原版的贪心 lsb steer（gather 全部 dst=0，全部走 ghost）在 k>1 时更差，最高到 2.2×。
- 解读：真实 k 下，CRRF 好的情况是 ≈0.95–0.98，差的情况是净变慢（慢道把尾部拖长）。**没有任何一格能到 0.85。**
- 对照组：Dat=2、k=1，也就是「把 Snp 加宽到 Dat 宽」，相当于加了第 3 条 Dat 宽环。这时 gather 0.68–0.70、allgather 0.78–0.90。这个对照被「Dat 子环直接 2→3」支配，正是 Archi 说的路径 (a)。

## 建议

- **(i) M-5 T3 存活 → 退回重测。** 核心容量假设（Snp 与 Dat 同宽、Dat 只有 1 条环）在物理上不成立，所有 Dat 收益数字（C_dat_eff、H-DAT-DOM、T2/T3 对比）**都不能签**。按审计规范，这是模型假象抬高了结果，不是诚实地没过杀线，所以判退回而不是淘汰。重测前提：
  1. 实现 `ghost_beats_per_dat = k_real`，或者声明加宽并把对照改成「Dat 子环 3」。
  2. 基线改为 Dat×2。
  3. 作业长度必须跨过多次 flip（|I| 远大于 dwell，或者 t_steady 小于 makespan），确保 duty 和 drain 真被测到。
  4. 拿到 DV200 的 W_snp / W_dat 出处（目前 unknown）。

  按上面的估算，重测大概率会落到「Dat 收益 <5%，再加上 Snp KILL」，到时再判淘汰。
- **(ii) card-claim「部分成立」→ 撤回（withdraw）。** gather 0.551、allgather 0.667、alltoall 0.719 是 k=1、Dat×1、duty=1 零税三重假设下的数，不能当「部分成立」的证据。卡上收益区间 0.55–0.85× 也不再缩窄到 gather/allgather 型，等重测。REPORT.md:82 的归因需要更正。

## 不受影响 / 只会更糟的部分

- **15:1 Snp KILL 照旧成立，而且只会更糟。** sim 里 Snp 在 DAT_EPOCH 一律停发（`sim.py:745-748`），混合窗口的 Snp makespan 由 duty 底座决定，与 k 无关。scratch 中 off / 3:1 / 7:1 / 15:1 = 1.0 / 27.4 / 30.7 / 32.4×，k=1/6/8 完全相同。物理上 ghost 占 Snp 槽的时间是 k 倍，只会让 Snp 更糟。「所有 duty 都 KILL」这个结论保留。
- **H-COMMIT barrier、Epoch Drain FSM、SYNC 偏斜接受集、late-newgen 断言、NACK holding（深度 1）** 是控制和正确性逻辑，与位宽、环数无关，结论可以保留。不过 T_drain 和 f_steady 的数值是在 Dat×1 环模型上测的，跨到 2 子环或加入 k 拆拍之后（drain 要等 k 片都离开）需要复核。
- allreduce 的 1.000 和 source_fc 列的「不过」，在修正后只会更差，结论不变。
- **未核实：** DV200 实际的 Snp/Dat 位宽（repo 里没有）；k 是拆拍还是加宽，卡上未选；2 条 Dat 子环在 NI 侧是否能同拍双注入（scratch 按可以处理）。
