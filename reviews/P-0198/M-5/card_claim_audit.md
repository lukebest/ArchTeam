# Card-claim 补测审计 · P-0198/M-5 CRRF（Credit-Reclaim / Rebind Flip）

auditor: 评估审计
batch: P-0198（不与已淘汰的 M-1 CBC / M-2 CSR / M-4 AODI 混排）
round: card-claim-1（smoke T3 #75 通过、night #76 确认通过之后的补测）
date: 2026-10-09 (Asia/Shanghai)
verdict: **部分成立 · 不签全信封**
PR audited: https://github.com/lukebest/ArchTeam/pull/83 — branch `cursor/p-0198-m-5-card-claim-3cd1`，tip **`83acfe9fed1c39d4906fee7b88bcaa778eeac45b`**（`cc6c586` 加 mode + `83acfe9` 加结果）；base `cursor/p-0198-m-5-crrf-t3-a12d` @ `b0b4cf9`（起点 SHA 一致）
card: PR #53 `mechanisms/P-0198/M-5.md` §4 — 「Dat 重集合 / 均匀读饱和区 **0.55–0.85×** makespan（扣 drain 税后）；0.85=bar≠mean」；信封要求「公开 outstanding」
Prior audits（保持原样，未改）：smoke `t3_audit.md`（#75 通过）、night `t3_night_audit.md`（#76 确认通过）于 `/workspace/archteam-p198-m5-t3/reviews/P-0198/M-5/`；T2 `/workspace/archteam-p198-m5/reviews/P-0198/M-5/t2_audit.md`（#67）。

## 判决

**部分成立 · 不签全信封。** 可复现、无结构改动、数字诚实；在公平基线（= rebind-off @ 卡信封公开 outstanding；本 bbox 下与提交者的 `no_cc` 数值完全相同）下，推理四行中 **gather、allgather 干净过 0.85**，**decode_kv_p2p 只有均值过（CI 上沿 0.908，3 trial 中 2 个 >0.85）**，**allreduce 1.000 不过**；在 `source_fc`（outstanding=1）下只有 allgather 0.814 过，allreduce 反而 **1.14–1.26× 变慢**。0.85 是约束条：推理集合最差行 = 1.000 > 0.85 → 卡的「Dat 重集合 0.55–0.85×」作为全类声明**不成立**，只在 gather/allgather（以及训练 alltoall/reduce）子集上测到落区间。不退回：duty 三臂同 makespan 不是死旋钮（见 §duty）。不是「card-claim 被否」：公平基线下确有收益。

## 1. 对拍 / 可复现（亲自重跑）

| 项 | 结果 |
|---|---|
| worktree | `/workspace/archteam-p198-m5-cc`（`git fetch origin pull/83/head:pr83-cc` → `git worktree add`），HEAD `83acfe9` |
| deps | 临时 venv `/tmp/ptvenv`：simpy 4.1.2、matplotlib 3.11.1、pytest（系统 python 无 simpy/pytest） |
| pytest | `python -m pytest sims/P-0198/M-5/tests -q -p no:cacheprovider` → **31 passed**（与提交者一致） |
| regen | `sweep.py --mode card_claim --seed 20260903 --out runs/card_claim_audit`，n=3，exit 0，wall ≈6.3 s（10:36 CST） |
| cmp vs committed `results/card_claim/` | `card_claim.csv` / `card_claim_trials.csv` / `snp_kill.csv` / `summary.json` **byte-identical** |
| PNG | `card_claim_inference_7_1.png` **不 byte-identical**（matplotlib 版本渲染差；数据 csv 一致，不算伪影） |
| REPORT.md / PROTOCOL.md | **脚本不生成**（手写）。逐项对表：REPORT 所有比值/CI/基线 makespan/Snp 均值与 regen csv 一致；无捏造 |
| smoke `results/` + `results/night/` sha256 | 25 文件，pytest + regen 前后 `diff` **为空**；且 `git diff b0b4cf9..83acfe9` 对这些路径为空。REPORT 列出的 6 个 sha256 与实测一致 |

## 2. 结构 diff（`git diff b0b4cf9..83acfe9 -- sims/`）

- 改动文件：新增 `card_claim.py`、`tests/test_crrf_card_claim.py`、`results/card_claim/*`；`sweep.py` 仅 +14/−1（docstring + `--mode card_claim` 分支，在调用 `sweep()` 前 return）。
- **`sim.py`、`t2_pins.py`、`_lib/`、smoke/night 代码路径零改动。** `source_fc` 用的是 `sim.py` 现有 `cfg.outstanding` 旋钮（L650/717/742），未新增注入门控。
- `--out results` 时被重定向到 `results/card_claim/`；`_assert_not_signed_dir` 拒写 `results/` 与 `results/night/`。
- 结论：只加 mode/sweep，**无改变 smoke/night 语义的改动**。非红旗。

## 3. 逐行 × 基线 vs 0.85（约束条；不平均、不互相掩护）

比值 = CRRF makespan / rebind-off makespan，同 txn、同 seed、同 outstanding。duty 三臂 makespan 除 allreduce@source_fc 外完全相同（见 §5），表中给 7:1 并注明例外。pass = 比值 ≤0.85；另列 CI 上沿与逐 trial，以判断是否稳健过条。

### 推理（primary）

| workload (class) | baseline | outstanding | base / CRRF makespan | 比值 7:1 (mean ± CI95, n=3) | 逐 trial | CI 上沿 | vs 0.85 |
|---|---|---|---|---|---|---|---|
| decode_kv_p2p (uniform_read) | no_cc | 96 | 25.00 / 20.67 | 0.8237 ± 0.0844 | 0.852 / 0.880 / 0.739 | 0.908 | **边缘：均值过，2/3 trial 不过，CI 跨条 → 不签为稳健 PASS** |
| decode_kv_p2p | source_fc | 1 | 47.67 / 45.00 | 0.9434 ± 0.0363 | 0.980 / 0.930 / 0.920 | 0.980 | **FAIL** |
| decode_kv_gather (gather) | no_cc | 96 | 49 / 27 | 0.5510 ± 0 | 0.551×3 | 0.551 | **PASS** |
| decode_kv_gather | source_fc | 1 | 49 / 49 | 1.0000 ± 0 | 1.000×3 | 1.000 | **FAIL**（零收益） |
| infer_allgather (allgather) | no_cc | 96 | 45 / 30 | 0.6667 ± 0 | 0.667×3 | 0.667 | **PASS** |
| infer_allgather | source_fc | 1 | 70 / 57 | 0.8143 ± 0 | 0.814×3 | 0.814 | **PASS** |
| infer_allreduce (allreduce) | no_cc | 96 | 52 / 52 | 1.0000 ± 0 | 1.000×3 | 1.000 | **FAIL**（零收益） |
| infer_allreduce | source_fc | 1 | 186 / 235 | **1.2634** ± 0（3:1 1.1398 / 15:1 1.2312） | 常数 | 1.263 | **FAIL（CRRF 更慢）** |

- **no_cc 下推理通过：** gather、allgather（稳健）；p2p 仅均值过（边缘）；allreduce 不过。→ 稳健 2/4，宽松 3/4；最差行 1.000。
- **source_fc 下推理通过：** 仅 allgather；p2p/gather 不过，allreduce 退化。→ 1/4；最差行 1.263。
- **没有把 no_cc 的好行拿去盖 source_fc 的坏行，也没有跨基线/跨 duty/跨推理训练平均**——提交者的表同样分列，核实无误。

### 训练（secondary，不与推理平均）

| workload | baseline | 比值 7:1 | 逐 trial | vs 0.85 |
|---|---|---|---|---|
| train_reduce (reduce) | no_cc | 0.5510 | 0.551×3 | PASS |
| train_reduce | source_fc | 1.0000 | 1.000×3 | FAIL |
| train_alltoall | no_cc | 0.7193 ± 0.1027 | 0.615 / 0.760 / 0.783 | PASS（3/3 trial ≤0.85） |
| train_alltoall | source_fc | 0.9840 ± 0.1028 | 0.943 / 0.921 / 1.088 | FAIL |

注意：`sim.gen_txns` 中 `gather` 与 `reduce` 走同一分支（`cls in ("gather","reduce")`），decode_kv_gather 与 train_reduce 数字**完全相同**——它们是同一 txn 形态，**不是两条独立证据**。allreduce 驱动 = 半段 gather-to-root + 半段 root-scatter（broadcast 形），被 root 串行钉住。

### card 0.55–0.85× 是否被支持？

**部分支持。** 公平基线下 gather（=reduce）0.551、allgather 0.667、训练 alltoall 0.719 落在区间；uniform_read（decode KV/P2P）0.824 均值落区间但未稳健过条；allreduce 1.000 完全在外。卡 §4 的 Dat 重集合声明是对整类，约束条按最差行判 → **全类声明不成立**；只能签「gather/allgather 型集合在本减箱 bbox 下测得落区间」。

### 哪条基线公平？（两条都报，不挑讨好的）

审计探针（`runs/audit_probe/ost_probe.py` → `ost_probe.csv`，同 seed/bbox，仅扫 outstanding；未改 sims，未进 committed 结果）：

| class | ost=1 | 2 | 4 | 8 | 16（sim 默认） | 32（night 信封） | 96（no_cc） |
|---|---|---|---|---|---|---|---|
| uniform_read | 0.943 | 0.811 | 0.828 | 0.824 | 0.824 | 0.824 | 0.824 |
| gather | 1.000 | 0.571 | 0.531 | 0.551 | 0.551 | 0.551 | 0.551 |
| allgather | 0.814 | 0.843 | 0.689 | 0.667 | 0.667 | 0.667 | 0.667 |
| allreduce | 1.14–1.26 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| alltoall | 0.984 | 0.796 | 0.719 | 0.719 | 0.719 | 0.719 | 0.719 |

（rebind-off makespan 在 ost≥8 后也不再变化：uniform_read 25、gather 49、allgather 45、allreduce 52。）

- **公平基线 = rebind-off @ 卡信封「公开 outstanding」（sim 默认 16 / night 已签 32）。** 本 bbox 下 ost≥8 窗口即不绑定，`no_cc`(96) 与 16/32 **逐比特同数**。所以 `no_cc` 在这里**不是**会被「96 outstanding 无流控」抬高收益的稻草人：rebind-off makespan 没有因过量 outstanding 而恶化（25/49/45/52 在 8 与 96 处相同），收益不来自拥塞崩溃。但标签「无拥塞控制」容易被误读成稻草人，建议改称「envelope outstanding（窗口不绑定）」。
- **`source_fc`（ost=1）过度保守**：每源串行一笔，CRRF 的 ghost 第二环没有第二笔 inflight 可载，等于把机制要利用的并行性先拿掉；不是现实 CHI RN 的源端窗口。作为下界敏感性列有价值（暴露 allreduce 退化 1.26×），但不是卡 §4 的公平对照。ost=2 时 uniform_read/gather/allgather 已回到 0.81/0.57/0.84。
- **仍缺的公平性**：Dr.Sim 规范要求基线是有竞争力的替代方案。目的端 credit / ECN / 令牌桶都**NOT measured**（需改注入门控，提交者如实未做）。因此只能签「相对无额外流控、公开 outstanding 的 rebind-off」，**不能**签「相对带现实拥塞控制的 fabric 也有 0.55–0.85×」。

## 4. 魔法缺口

- **CLAIM 未作输入**：`CLAIM_LO/HI` 只用于 `_in_interval` 标签与画线；`CARD_CLAIM_DAT` 是字符串 `"0.55-0.85x"`，只写进 csv 标签列。makespan 全部来自 `run_arm` cycle 模型。`card_claim_is_measured=False`、`unsigned=True` 全行在。
- **占用解释 vs 测得**（T3 自身 C_dat_eff 是占用比，不是测得带宽）：

| 行 (no_cc, 7:1) | C_dat_eff | 占用可解释 1/C | 测得 | 缺口（测得−占用） |
|---|---|---|---|---|
| gather | 1.5845 | 0.631 | 0.551 | **−0.080**（测得优于占用可解释） |
| allgather | 1.5970 | 0.626 | 0.667 | +0.041 |
| uniform_read | ≈1.55 | ≈0.645 | 0.824 | +0.18 |
| allreduce | 1.6580 | 0.603 | 1.000 | +0.40 |
| source_fc 各行 | 1.55–1.72 | 0.58–0.65 | 0.81–1.26 | +0.2 ~ +0.66 |

  gather 0.551 比占用能解释的还低 ~8 pt（三 duty C_dat_eff 1.49/1.58/1.63 不同但 makespan 同为 27 → 收益由 dest-eject 天花板决定，不是由 Dat 占用决定）；其余行占用涨了但 makespan 没跟上。**卡区间下沿 0.55 恰好 = 现 bbox gather 天花板 27/49**，属于 bbox 巧合，不是占用推出来的；不得把 0.551 外推为信封值。
- **有没有在无公平基线时把卡区间签成测得？** 提交者没有（REPORT/summary 均标未签、不是结论）。本审计也只签上表子集，且限定基线为「公开 outstanding、无额外流控」。

## 5. duty 3:1 / 7:1 / 15:1 同 makespan —— 死旋钮还是天花板？

**不是死旋钮，是 makespan 天花板（与 night 已审的 gather 27×3 打平同源）。** 证据：
1. 同一行三臂 `c_dat_eff` 单调不同（如 gather no_cc 1.4879 / 1.5845 / 1.6328；uniform_read 1.44 / 1.53 / 1.57），duty 确实改变了 ring 占用；
2. Snp 列三臂显著不同（no_cc snp_path 均值 1.00 / 6.89 / 16.85）；
3. allreduce@source_fc 三臂 makespan 212 / 235 / 229 不同；
4. 审计探针 ost=1…96 全部 cls：只要不是 ost=1 allreduce，三臂 makespan 恒相同 → Dat makespan 被 dest eject / hop / root 串行封顶，duty 增加的占用买不到 span。

后果（非伪影，但须写明）：本 bbox 下更高 duty 对 Dat 收益为零而 Snp 代价递增 → 3:1 支配 7:1/15:1；「7:1 是卡示例臂」不应暗示 7:1 有额外 Dat 收益。tax 列三臂相同（同一 drain 窗口记账）与 night 一致。不构成退回。

## 6. 15:1 Snp KILL（未软化）

| baseline | window | 3:1 | 7:1 | 15:1（trial 均值） | kill_1.4 @15:1 |
|---|---|---|---|---|---|
| no_cc | snp_path | 1.00 | 6.89（9.56/10.12/1.00） | **16.85**（18.93/20.20/11.43） | True×3 |
| no_cc | snp_on_gather | 27.51 KILL | 30.84 KILL | **32.59** | True×3 |
| source_fc | snp_path | 3.79（5.18/1.00/5.20） | 7.37 | **17.76** | True×3 |
| source_fc | snp_on_gather | 3.28 KILL | 3.67 KILL | **3.88** | True×3 |

15:1 双基线双窗口全 KILL，`softened=False`，与 night 17.05/32.59 同量级（no_cc 数与 night 吻合）。注意：混合窗下 **3:1/7:1 同样 KILL**（night 已记录）；source_fc 下 snp_path 3:1 也有 2/3 trial KILL。Dat 侧落区间的每一行都与 Snp-on-gather KILL 共存——任何引用 card-claim Dat 数字的地方必须同表列出 Snp。

## 7. workload_source = existing_config

六行全部是现有 `CLASSES` 驱动加推理/训练标签，没有 decode trace、没有 KV 布局/批次/序列长度，负载基线表未到。限制：
- 「decode_kv_p2p / decode_kv_gather / infer_*」只是**命名**，不能签为推理相关性证据；只能签为「uniform_read / gather / allgather / allreduce 合成驱动」的结果。
- gather 与 reduce 同形；reduced bbox（12+2，|I|=96，hop_lat=1，clock UNKNOWN），非全信封 rd512/wr256。
- 负载表到位前，任何「CRRF 对推理 decode 有 0.55–0.85×」的表述都不可签。

## 可签 / 不可签

**可签（unsigned→审计确认的测得事实，限定本 bbox、existing_config、rebind-off@公开 outstanding）：**
- gather(=reduce) 0.551、allgather 0.667、alltoall 0.719 落入 0.55–0.85 且逐 trial ≤0.85；
- uniform_read 0.824 均值落区间但不稳健（CI 上沿 0.908）；
- allreduce 1.000 无收益；outstanding=1 下 allreduce 退化至 1.14–1.26×；
- 15:1 Snp KILL 双基线成立；Dat makespan 对 duty 不敏感（天花板）。

**不可签：** 卡 §4「Dat 重集合 / 均匀读饱和 0.55–0.85×」作为全类声明；任何推理/decode 相关性；相对现实拥塞控制（dest credit / ECN / token bucket）的收益；全信封数字；把 0.551 当信封值；把三 duty 平均或推理训练平均。

## T3 存活状态

**不变：仍存活。** 理由：卡 §4 明写该区间是「预期区间（非过关宣称）」；T1/T2 杀线（drain 税、epoch_committed、C_dat_eff<2、HARD-1、15:1 Snp KILL 暴露）已在 smoke/night 通过，本补测没有触碰杀线、没有发现伪影。card-claim 在公平基线下**部分**诚实失败（allreduce、uniform_read 不稳）是对卡收益宣称的修正信息，应把卡收益从「Dat 重集合 0.55–0.85×」收窄为「gather/allgather 型集合，本 bbox」，不是淘汰理由。但需提醒：Snp 混合窗在所有 duty 下 KILL 的事实（night 已知）仍是 M-5 最大风险，不因本补测而缓解。不开 T4。

## 意见 / 修复建议（非退回条件；审计不改 sims/卡）

1. `in_0.55_0.85` 只看均值；建议加 CI 上沿 / 逐 trial 列，按约束条判 uniform_read（2/3 trial >0.85）。
2. `no_cc` 标签改为「envelope outstanding（ost≥8 不绑定，与 16/32 同数）」，并在 REPORT 写明 ost 敏感性，免得被当作稻草人或被当作「无 CC 夸大」。
3. decode_kv_gather 与 train_reduce 同形，报表应注明不是独立证据。
4. REPORT.md/PROTOCOL.md 是手写，建议由脚本生成或在 REPORT 注明「手写，数值源自 csv」。PNG 依赖 matplotlib 版本，不作为对拍对象。
5. 若要签更强声明：需负载基线表（真实 decode/推理 trace）+ 目的端 credit 基线（结构改动，需另立轮次与审批）。

## 禁止自检

未改 `sims/` / `mechanisms/` / `models/` / `problems/` / FUNNEL；未修补任何数字；未开 GitHub PR；未 commit；未开 T4；未把 card-claim 或 0.85 当均值签字；未把 Snp 折进 Dat；未与 M-1/M-2/M-4 混排；smoke/night 审计文件未动。探针与 regen 只写 `/workspace/archteam-p198-m5-cc/runs/`。
