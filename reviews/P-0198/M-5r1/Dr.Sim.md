# Dr. Sim · T1 · P-0198/M-5r1 · CRRF-SB

- reviewer: Dr. Sim
- 机制卡: `mechanisms/P-0198/M-5r1.md`（PR #85，`cursor/p-0198-m-5r1-crrf-snp-31d9` @ `cac6a4b`）
- T0: `reviews/P-0198/M-5r1/tier0.md`（PR #89，`cursor/p-0198-m-5r1-tier0-9a70`；判决 `PASS_T1` / `INCREMENTAL` = **纸面放行，不是 T1 方法学通过**）
- 日期: 2026-10-09
- 本票只评 M-5r1；未读 `reviews/P-0198/M-5r1/` 下其他人格、未读 M-5 旧 Dr.Sim 票

## 结论

有条件通过

纸面所有权谓词（本征 Snp 公民权不进 Drain 闸；ghost Dat 只借空槽）可 cycle 建，五项主持点都有合法闭合路径，没有一项把机制写成物理不可能。方法学风险不低：KILL 钉死的 12+2 / 512 B / 公开 outstanding / duty 15:1 双列尚未存在；PR #85 的 7.8→1.0 / 19.0→1.0 是减箱探针自洽数字，分析模型对不上这组幅度，且位宽、i-tag、orbit/Drain、NACK 副本、header-only 臂全部未建模。不得把 T0 `PASS_T1` 或 harness `1.000` 当成 T1 通过。

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 3 | 本征残留仲裁（空槽同拍 Snp 赢）+ 资格位与 channel-id 分离可建；位宽、NACK 载荷驻留、ghost 是否服从 i-tag 未钉，但都有不改 steal-back 谓词的闭合方式。 |
| 新颖性 | 3 | 相对 M-5 是所有权改写（排他身份 → 宾客资格），不是调 duty；若 drain-off + header-only 与 on-arm 等价，新意降到「低优先级类借邻环空槽」，INCREMENTAL 还要再降。 |
| 预期收益 | 3 | 去掉排他窗后 Snp 等待从 `O(T_drain+粗量子)` 回到等空槽，15:1 有物理空间回到 ≤1.4；Dat 甜区只剩扣税后的残差。全部 UNSIGNED，满信封可被拆拍/过路饥饿吃掉。 |
| 评估可信度 | 2 | `model.py` 是 `ρ/(1-ρ)` 几何近似（15:1 SB=1.059、M5_coarse=22.64），不是周期模型；`harness.py` 复现了 7.800/19.000→1.000，但是 N=12 / ost=16 / dest 必弹出 / 无 RBRG / 1 flit=1 txn 的减箱恒等式。无 p99、无多种子 CI。 |
| 系统可组合性 | 3 | 与静态 1:1 四环、源端 FC、库内 i-tag/e-tag 切面可叠；ghost 跨物理环后 tag 覆盖未定义，Drain 期本征 Snp 与 orbit ghost 共环，attribution 必须靠 sb-off / ghost-off / header-only 分列。 |

## 最强反对意见

评估若沿用 PR #85 harness 的「1 flit = 1 txn、dest 必弹出、无 RBRG/NACK、无 i-tag、N=12、ost=16、mixed 仅 6 条 Snp」并把 `7.8→1.0 / 19.0→1.0` 写成 15:1 KILL 已过，通过的是减箱空环恒等式，不是机制。`snp_path` 下 m5r1 与 rebind-off 的 `ms_snp` 同为 15.0——没有 Dat 时 Snp 环本来就是空的，steal-back 无物可抢；`mixed` 的 1.000 来自 gather dest-eject 限制 + 6 条稀疏 Snp，不是争用下的等空槽。一旦 Dat 按 Snp 位宽拆拍、上游 ghost 过路占满下游槽、dest 弹出失败在 Snp 环上绕圈，本征 Snp 等待和 Drain 时长都没有纸面界。数字会记在 CRRF-SB 头上，失败模式却是「探针从未给 Snp 环制造合法争用，也未给 ghost Dat 一个合法物理宽度」。

## 评估层必须验证的一个假设

在 **同一** `bufferless-ring-noc` 新分支、同一 harness、同一 i-tag/e-tag 设置、只切换 rebind/SB 的前提下，DV200 12+2、512 B、outstanding 读 512 / 写 256、duty 15:1、禁完美预测 / 无限带宽：`snp_path` 与推理混合（decode KV / 权值 P2P + 推理期 Snp）两列各自满足 `T_snp / T_snp(rebind-off) ≤ 1.4` 且 `< 1.5625`（分列，不平均，不用 Dat 增益抵消）。Snp makespan 必须计入首次 ready→done（含注入前 stall），completions 不丢。任一列 `>1.4` ⇒ 该臂 KILL。同时必须报推理 makespan 与 per-txn 尾（p99/p99.9 + bootstrap CI + 每分位样本数）；单 run p99 无效。该假设对 PR #85 的 7.8/19.0/1.0 **不成立对照**——那些数字不得进分母或分子。

## 主持指定五项（逐条单列结论）

### 1. Snp flit 无载荷；Dat 骑 Snp 线的物理位宽

**结论：有条件**

卡未闭合。§2.1 表头有「位宽」列，正文只写 FSM / 4×4 / 仲裁拍数，没有 Snp 导线宽度、没有 Dat 载荷拆拍、没有 `C_dat_eff` 的拍数税。CHI Snp 是控制 flit，Dat 在本信封是 512 B 请求；ghost Dat 一拍骑上 Snp 物理环在物理上不成立，除非 (A) 把 Snp 环拓宽到 Dat 宽度并计入面积/功耗，或 (B) 按 `n_beats = ceil(Dat_payload_bits / Snp_wire_width)` 拆拍，把多拍占用写进 Snp `ρ_wire` 与 `C_dat_eff`。不选 (A)/(B) 就把「第二 Dat 高速」建成免费无限带宽。这是 M-5 线共有的未审洞，r1 没有修。

**仿真必须怎么记账**：默认禁止 (A) 的静默拓宽。若选 (A)，面积单独列，Snp 环不再是控制宽度。若选 (B)，ghost 注入一次占用 `n_beats` 个连续 Snp 槽（或等价的序列化状态机），steal-back 只在整段空槽上赢，过路多拍 ghost 仍赢；`C_dat_eff` 扣 `(n_beats−1)` 税；KILL 两列在拆拍打开后重测。不得用 1 flit=1 txn 的 harness 代替。未选方案或拆拍未扣税 = 该 run 作废，不是「近似可接受」。

不判 未闭合-致命：两种记账都能让 ghost Dat 成为合法事务，不必改 steal-back 谓词。若评估拒绝拓宽又拒绝拆拍，ghost Dat 物理不可能，那时再升为致命。

### 2. 优先级反转：上游 ghost 过路饿下游 Snp

**结论：有条件**

卡未依赖、也未声明库内 i-tag。steal-back 只在**本地空槽**上让 Snp 赢；在途 ghost 过路优先（§2.2 规则 1、5）。上游无 Snp pending 时可持续注入 ghost，填满下游 Snp 槽——这是无缓冲环经典的上游饿下游，卡没有段密度上界（duty 只偏置「借多少」，不按段计数）。

库内 i-tag（T0 引 `src/TCsHighWay.cpp:894` `tryItagProcess`）**可以**成为合法界，当且仅当它按 **Snp 物理环槽** 保留、且 ghost Dat 作为该环公民必须让出保留槽。这不是自动成立：基线 i-tag 按网络/通道走，ghost 是 Dat 身份骑 Snp 导线，可能被译成「这不是 Snp 注入饥饿」。卡若要借用 i-tag，必须写进机制（ghost 服从 Snp 环保留槽）；否则必须自带 ghost 段密度上限或 generational cap。

**不得**只说「库里有 i-tag」。T2/T3 必须：(i) 探针 `ghost_obeys_itag`；(ii) 按节点位置分列 Snp 注入等待最坏值 / p99；(iii) i-tag-off 消融应暴露下游饥饿。若 `ghost_obeys_itag==false` 且无密度帽，等待无界 = 该臂方法学失败，需改机制后再评，不是调 duty。

### 3. 弹出失败的 ghost 在 Snp 环上绕圈，Drain 可否无限等

**结论：有条件（必须 cycle 级；当前未闭合）**

必须 cycle 级建模，禁止用「稳态 `bind_mismatch_redirect==0`」或几何 `ρ/(1-ρ)` 代替。DRAIN 清的是 `epoch_tag==old` 的在途 ghost（§2.3）。dest 忙则 ghost 留在 **Snp 环**上 orbit，每圈占一个本征槽，Drain sniff 持续为真，`epoch_committed` 不前进。M-5 已有同一活锁，r1 没恶化 Drain 完成条件，但本征 Snp 现在与 orbit ghost 共环，Drain 期 Snp 尾直接受击。

PR #85 `harness.py` **没有**这条路径：`dst==n` 时 `_complete` 必成功，无 eject 争用、无 e-tag、无 orbit 计数、无 Drain 超时。该探针不能为活锁证伪。库内 e-tag（T0 引 `dest_port_tagged`）是否跨物理环覆盖「Snp 环上的 Dat 载荷、弹出到 Dat NI」卡未定义。

**周期探针（必做）**：`ghost_orbit_count` 分布与最大值；`drain_duration` 分布 / p99 / max；超时或 escape 次数；e-tag 对 ghost 的命中。接受域：`max_orbit` 有限且 Drain p99 ≤ `k·(k_circ+1)·C_ring`（k 事先钉死，建议 ≤2）。超时必须有 escape（NACK 走持有锁或打回 Dat 环），禁止静默永等。任一 seed Drain 挂死或 Snp 在 Drain 期 completions 丢失 = 该臂失败。

### 4. NACK 后重注入，数据从哪来

**结论：有条件**

卡同时写了「接受集外 → NACK / 原 Dat 环重注入」（§2.2）和「失配路径深度 1 holding、只服务宾客 Dat」（§2.1），但没说 NACK 当下那份 512 B 载荷住在哪里。无缓冲信封禁止源 NI 在 ghost 上环后仍留副本——源端 retention buffer 是片上 flit 缓冲，必须按 outstanding×512 B 计价，否则就违反 bufferless。

合法闭合（不改 steal-back）：失配 flit **本人**进已声明的 RBRG 1-deep holding，从失配点偏转到该 die 的 Dat 环；holding 深度探针恒 ≤1；禁止源侧再留一份。`bind_mismatch_redirect` 稳态目标 0 仍然要报，但这是正确性目标，不是「所以不必说副本在哪」。

非法闭合：源 NI 静默 retention；NACK 后丢载荷（completions 暗掉）；holding 滑成深度>1 的 highway 队列。这三项任一出现 = 机制越界，run 作废。不判 未闭合-致命，是因为 1-deep holding 偏转已经写在卡上，不必发明新缓冲；T2 必须把这条路径锁死并断言，不能改写成源端副本。

### 5. Control arm：drain-off + 只按 header 译码

**结论：有条件（必须 cycle 消融；当前未跑）**

本征 Snp 已按 `channel-id` 无条件转发。逻辑下一步：ghost Dat 也可以只按 `channel-id=Dat` 弹出，不再看 bind / `epoch_tag` / Drain。卡仍保留 ARM_DRAIN→DRAIN→FLIP→`epoch_committed` 只服务 ghost 世代。T0 已指出：若 drain-off + header-only 与 on-arm 在 Snp/Dat makespan、completions、`bind_mismatch_redirect` 上不可区分，epoch/bind 只剩开销，新颖性降到多物理子网负载均衡，Drain 税应从机制删除并重评。

PR #85 无此臂。`m5r1` 的 Snp 注入已 `snp_ok=True`，但 ghost 仍门控 `bind_ghost ∧ STEADY ∧ committed`；`snp_path` 下 FSM 空转且 `steal_back=48`（凡在 `bind_ghost` 期注入的本征 Snp 都记一笔），说明 epoch 在无 Dat 时仍在跑、归因已经脏了。

**必须 cycle 消融，不能解析**：同一种子、同一流量，三列并列——on-arm（卡原文）、`drain-off`（FSM 永 STEADY、不停 ghost）、`header-only`（RBRG/NIC 只看 channel-id，bind/epoch 不参与译码）。判据：若 `|T_on−T_ctrl|` 落在多种子噪声内且 mismatch 均为 0，则 epoch/bind 冗余，本卡新颖性下调，不得再把 Drain 写成正确性必要。该臂与 KILL 独立：header-only 即使过 1.4，也只说明「借空槽 + Snp 优先」够用，不够证明 CRRF 世代机还值留。

## 必须 cycle 级建模、不能解析近似

1. **KILL 双列（主持钉死）**：DV200 12+2、512 B、ost 读 512 / 写 256、duty 15:1；`snp_path` 与推理混合各自 `T_snp/off ≤ 1.4` 且 `<1.5625`；分列；禁止平均；禁止用 Dat 0.55–0.85× 抵消。Snp makespan = 该列已完成 Snp 的 `min(ready_at)→max(done_at)`，ready 取首次注入尝试（含排他/争用导致的注入前 stall）。pass/fail 脚本对两列分别断言，任一列失败即打印 KILL 并退出非 0。
2. **rebind-off 公平基线**：同一分支、同一 `tests/soc_sim` harness、同一 i-tag/e-tag/outstanding/warmup，只把 rebind/SB 关掉。禁止精简拓扑基线、禁止两臂不同 i-tag、禁止源端 FC 冒充 no-CC。src-fc 另列（只削 Dat ost，不重绑）。
3. **位宽 / 拆拍状态机**（主持项 1）：`n_beats` 或拓宽二选一；多拍占用进 Snp 槽与 `C_dat_eff`；禁止 1 flit=1 txn。
4. **i-tag 与下游 Snp 饥饿**（主持项 2）：ghost 是否让出 Snp 环保留槽；按节点分列注入等待；i-tag-off 消融。
5. **Drain 活性探针**（主持项 3）：`max ghost_orbit_count`、`drain_duration` 分布 / 超时 / escape；dest 弹出失败必须可发生（Dat NI 口与 Dat 环到达者争用）。禁止 dest 必成功。
6. **NACK 载荷驻留**（主持项 4）：RBRG holding 深度探针 `≤1`；`source_retention_depth==0`；`bind_mismatch_redirect` 稳态与 completions。禁止源侧副本、禁止静默丢包。
7. **header-only / drain-off 臂**（主持项 5）：与 on-arm 同表；等价则降新颖性。另加 `sb-off`（回到 M-5 排他，15:1 Snp 应回 KILL 量级）、`ghost-off`（Dat 回到无 CC 量级）、建议 `tail-only`（M-15 子集）。
8. **推理主列**：decode KV + 权值 P2P + 推理期 broadcast/小 allgather + 其一致性 Snp。训练 AllReduce 等只附注。HARD-1：rebind-off 的推理 Dat makespan 必须严格差于 SB 最佳 on-arm；只涨 `p_inj` / 注入次数不得分。
9. **尾延迟统计**：per-txn 完成时间的 p99 / p99.9，≥10 个独立种子，bootstrap CI，报表写明每个分位的样本数。禁止单 run p99、禁止用 3-trial 批次 makespan 冒充尾。mixed 列 Snp 样本必须够支撑 p99（3×6=18 条不够）。
10. **Warm-up**：丢弃 bind/epoch 对齐前与首次 `epoch_committed` 前的瞬态；稳态后才采 makespan / 尾 / steal_back / ghost_inject / ghost_gated / orbit / Drain。`steal_back` 只计「本地 Snp pending 且空槽被本征抢走、否则该槽会给 ghost」——PR #85 把 `bind_ghost` 期所有本征 Snp 注入都记 steal_back（`snp_path` 下 48 笔、当时 `ghost_inject=0`），该定义不得沿用。
11. **禁止**：把 `model.py` 的 `E[wait_empty]=ρ/(1-ρ)`、Amdahl `1/C_dat_eff`、T2 `q=1 → 1.5625`、T3 night 17.05/32.59、harness 7.8/19.0/1.0 写成测得 pass。分析模型只作对照列，标明 `NOT a legal cycle schedule`。

## 给 T2/T3 的必须验证假设清单

1. **H-SNP-LAT-SB-PATH（KILL，snp_path）**  
   - 度量：`T_snp_path / T_snp_path(rebind-off)`，ready→done 批次 makespan + 同列 per-txn p99。  
   - 阈值：`≤1.4` 且 `<1.5625`；completions = 提供数。  
   - 消融：`sb-off` 必须回到 >1.4（与 T3 排他同向量级，不要求数值等于 17.05）。失败 = 该臂 KILL。

2. **H-SNP-MIX-SB（KILL，推理混合）**  
   - 度量：decode KV / P2P + 推理期 Snp 的 `T_snp_mix / T_snp_mix(rebind-off)`，与推理 makespan、Snp p99 并列。  
   - 阈值：单独 `≤1.4` 且 `<1.5625`；不得与 snp_path 平均，不得用 Dat 比抵消。  
   - 消融：`sb-off` 混合 Snp 应变差；`ghost-off` 不得改善 Snp 比（Snp 本就本征）。失败 = 该臂 KILL。H-SNP-CAP（Snp 饱和）允许 >1.4，但必须单列，且该情形 Dat 甜区作废。

3. **H-WIDTH-CHARGE**  
   - 度量：`n_beats` 或 `Snp_wire_width/Dat_width`；`C_dat_eff` 拆拍税；Snp 槽占用含多拍 ghost。  
   - 阈值：未声明方案、或 `n_beats>1` 却按 1 拍记账 → run 作废。拓宽必须有面积列。  
   - 消融：`serialize-off`（作弊 1 拍）只作对照，不得当主列。主列打开拆拍后重测假设 1、2。

4. **H-ITAG-GHOST**  
   - 度量：`ghost_obeys_itag`；按节点 `snp_inject_wait` max / p99；下游相对上游的等待比。  
   - 阈值：`ghost_obeys_itag==true` 或存在显式段密度帽；下游 p99 wait ≤ 事先钉死的有界倍数（建议 ≤4× 同列上游中位数）。  
   - 消融：`itag-off` 应使下游等待显著变差；若 i-tag-off 无差异，说明不是 i-tag 在提供有界性，必须改用密度帽。

5. **H-DRAIN-LIVE**  
   - 度量：`ghost_orbit_count` max；`drain_duration` p50/p99/max；timeout/escape 次数；Drain 期 Snp 尾。  
   - 阈值：`max_orbit` 有限；Drain p99 ≤ `k·(k_circ+1)·C_ring`（k 预钉，建议 2）；timeout=0 或每次 timeout 都走声明的 escape；Drain 期 Snp completions 不丢。  
   - 消融：强制 dest 弹出失败（Dat NI 饱和）应仍满足有界 Drain；若出现无限 orbit = 活锁，机制失败。

6. **H-NACK-LOCUS**  
   - 度量：`holding_depth_max`；`source_retention_depth`；`bind_mismatch_redirect`；Snp/Dat completions。  
   - 阈值：`holding_depth_max≤1`；`source_retention_depth==0`；稳态 redirect→0；completions 不丢。  
   - 消融：人为制造 bind 失配，载荷必须从 holding 偏转到 Dat 环并完成；源 NI 在 ghost 上环后读 payload RAM 必须为空。

7. **H-HEADER-ONLY**  
   - 度量：on-arm vs `drain-off` vs `header-only` 的 `T_snp`、`T_dat`、completions、`bind_mismatch_redirect`。  
   - 阈值：若多种子下差值落入 bootstrap CI 且 mismatch 均为 0 → 判定 epoch/bind 冗余，新颖性下调，Drain 不得再当正确性项。  
   - 消融：本臂本身就是消融；必须与 KILL 主列同信封，不能只在 N=12 减箱上做。

8. **H-TAIL-CI**  
   - 度量：推理事务 per-txn 完成时间 p99、p99.9；Snp 与 Dat 分列。  
   - 阈值：≥10 seed；每个分位注明 `n`；bootstrap 95% CI；`n` 不足以估 p99.9 则该分位标 `INSUFFICIENT`，不得填点估计。  
   - 消融：无。统计失败 = 不得宣称尾改善。

9. **H-HARD-1-DAT**  
   - 度量：推理 Dat makespan（KV/P2P/推理集合）on-arm vs rebind-off。  
   - 阈值：`T_dat(rebind-off) > T_dat(SB best on-arm)`（严格）；只涨 `p_inj`/ghost 注入次数不算。  
   - 消融：`ghost-off` 应回到 no-CC Dat 量级，否则 Dat 收益不归因 SB。

10. **H-FAIR-OFF**  
    - 度量：rebind-off 与 on-arm 的 git 分支、harness 版本、i-tag 开关、outstanding、warmup 哈希。  
    - 阈值：除 rebind/SB 资格位外全部相同。  
    - 消融：无。配置漂移 = 整表作废。

**PR #85 模型复核（本票已跑，不是 T2 结果）**：`python3 models/P-0198/M-5r1/{model,harness,test_sb}.py`，`SEED=20260903`，`trials=3`。harness **复现** insight 表：`snp_path` m5-15:1 = 7.800（KILL）、m5r1 = 1.000；`mixed` m5-15:1 = 19.000 / Dat 0.583，m5r1 Snp = 1.000 / Dat 0.569；`test_sb` 3 项过。`model.py` **不是**周期模型，15:1 给出 M5_coarse=22.64、SB_empty=1.059，**对不上** 7.8/19.0/1.0。两组数字都是 UNSIGNED 减箱，都不能当作主持 KILL 的测得值。
