# T2 insight · P-0198/M-5 CRRF

## 模型结构

三层，严格分离（**不是** CBC 空槽日历，也不是 M-2/M-4 的会合/造洞）：

1. **精确守恒**：每物理环每方向每拍 `S=1`。CRRF 只把 Snp **导线**在 DAT_EPOCH 时分成 ghost Dat。`C_dat_ideal = 1+duty_dat`，且 **永远** `C_dat_eff ≤ C_dat_ideal < 2`（duty=1 会饿死 Snp，扫描不含）。时间复用 ≠ 永久第二 Dat 槽。
2. **税**：`C_dat_eff = 1 + duty_dat·f_steady − τ_sync − τ_bind`。`f_steady` 来自 Epoch Drain：ARM_DRAIN → DRAIN（≥1–2 环周）→ FLIP + bind pipe → 全员 `epoch_committed` 后再允新世代注入。本地 sniff ≠ 全局空。
3. **相对 makespan / Snp 杀假设**：Dat 重已坍类与均匀读饱和启用 H-DAT-DOM（`T∝1/C_dat_eff`）及可选 Amdahl（`f_dat`）。Snp **分列** H-SNP-LAT（稀疏混合等 SNP_EPOCH）与 H-SNP-CAP（饱和对照）。均匀写走 H-WRITE-SYM。broadcast 不算 H-DAT-DOM 绝对值。

对照物：`github:lukebest/bufferless-ring-noc` 的 `tests/soc_sim`；T_off 钉问题 YAML + `docs/srcfc_ca_model/data.json` 的 `off`（与兄弟卡同一组钉）。Snp **无公开 ns**，只报相对比。

## 假设（全部具名）

| ID | 含义 | 风险 |
|----|------|------|
| H-SLOT | 物理槽不增加 | 若实现偷偷加端口/队列，零和叙事崩 |
| H-TMUX | `C_dat_eff ≤ 1+duty_dat`，税>0 | 「近乎双 Dat 无税」是卡明文撒谎 |
| H-DRAIN | `T_drain=(k_circ+1)·C_ring+n_pipe` | 跨 die 聚合比单环周更长 → 税更重 |
| H-COMMIT | 全员 `epoch_committed` 后才新世代注入 | 早注入 → 晚节点接受集未命中 → redirect>0 |
| H-ACCEPT / H-MISMATCH0 | 接受集 `{local, local−1}`；稳态 redirect=0 | 稳态非零 = 屏障未闭合 |
| H-STAGING | 失配 1 深 holding，非 highway 队列 | 无界重试会变成静默侧缓或活锁 |
| H-PRESSURE | 相位只看 Dat EMA / Snp pending | hint 当正确性开关 → 过关无效 |
| H-FLIP | 最小 STEADY 驻留 | 过频 flip 吃光 Dat 净利 |
| H-DAT-DOM | 已坍 Dat 重 / 均匀读饱和由 Dat 槽主导 | 非坍塌类禁用 |
| H-AMDAHL | `f_dat` 时间占比 | 与作业相位绑定 |
| H-WRITE-SYM | 写侧阻尼 `β_write` | 已对称负载受益窄 |
| H-EPOCH-Q / H-SNP-LAT | epoch 量子 `q` 与 Snp 服务时延 | 粗量子或短 `L_snp` 易踩 1.4× |
| H-SNP-SPARSE | Snp 提供负载 `λ_snp≪1` | 饱和则改走 H-SNP-CAP，杀假设必炸 |

## 默认假设下的预测（模型输出，非测得）

跑 `python3 models/P-0198/M-5/model.py` 核对数字。下列是该默认点的结构结论，不是硅。

- **税**：`k_circ=2`、`C_ring=25`、`n_pipe=2` → `T_drain=77`；`T_steady=20·C_ring` → `f_steady≈0.8666`。7:1 `C_dat_eff≈1.718`（理想 1.875）——无税双 Dat 被构造禁止。
- **Dat 重已坍 + 均匀读（H-DAT-DOM）**：3:1 / 7:1 / 15:1 的 `T_hat/T_off ≈ 0.621 / 0.582 / 0.564`，落在卡 **0.55–0.85×**；Amdahl `f_dat=0.70` 约为 `0.735 / 0.707 / 0.695`。同分列，不平均。
- **HARD-1**：rebind-off gather `T_hat=537.2` > 15:1 `303.1`——归因必要非充分。
- **均匀写**：7:1 H-WRITE-SYM `≈0.903`，落在 **0.85–1.05×** 对照带（窄）。
- **Snp（强制列）**：细量子 `q=1`、`L_snp=C_ring/2` 时 H-SNP-LAT `3:1/7:1/15:1 ≈ 1.09 / 1.245 / 1.563`——**15:1 踩 1.4× 杀假设**（过敏暴露）。H-SNP-CAP `≈4.6 / 9.2 / 18.5`——Snp 若饱和则机制失败。`λ_snp=0.05` 下 15:1 Snp completions `16.4/26.9` 下降。
- **屏障**：H-COMMIT 开 → `bind_mismatch_redirect=0`；早注入 → 晚节点对 `tag=E+1` mismatch>0。接受集外交 NACK/re-inject，不是静默丢。
- **hint**：`correctness_depends_on_hint=False`。SYNC 只对齐，不预测。

## 灵敏度（两个最敏感）

1. **`(T_steady, k_circ)`**：直接定 `f_steady` 与 Dat 比值。驻留短或 drain 按 4 周算，H-DAT-DOM 可退出 0.55–0.85。
2. **`(q, L_snp)`**：直接定 Snp 是否过 1.4×。粗量子（`q=C_ring`）下 7:1 也会 KILL。

## 魔法缺口（卡宣称 − 模型能解释）

1. **「近乎双 Dat 无税」**：模型否定。有效槽必须扣 drain 死时间 + SYNC 摊还 + bind pipe。
2. **0.55–0.85× Dat 重**：依赖高 `f_steady` 与 H-DAT-DOM；Amdahl 或过频 flip 会把点推出区间——区间是 **card-claim**。
3. **Snp ≤1.4× 在所有 duty**：默认细 TDM 下 15:1 已可杀；粗 epoch 下 7:1 也可杀。只投稿 7:1 = 减箱。
4. **稳态 redirect=0**：解析在「屏障被遵守」下为 0；cycle 级若把 flip 建成原子栅栏会**人为**打成 0（Dr.Sim）。跨 die sniff≠全局空必须进 T3。
5. **无公开 Snp T_off**：不得把相对比写成 ns 测得。
6. **HARD-2 目的坍缩、偏斜窗逐 flit**：本解析未建模；留给 `tests/soc_sim`。

## 交给评估审计 / 后续 cycle

- 路径：`models/P-0198/M-5/{spec.md,model.py,insight.md}`
- 跑：`python3 models/P-0198/M-5/model.py`（stdlib，exit 0）
- 审计焦点：drain 税是否进 `C_dat_eff`；`epoch_committed` 屏障探针；mismatch redirect≈0 且集外走 NACK；duty∈{3:1,7:1,15:1}+rebind-off 分列；Snp makespan **与** completions 及 1.4× 杀假设；**COLL_EP 不得当正确性依赖**；无 Dat 均值藏 Snp；不与 M-1/M-2/M-4 混结论
- Tier 3 必须按 Dr.Sim 列表建五态 FSM 与 skew 窗，禁止用本文件的平均 duty 冒充测得 makespan
