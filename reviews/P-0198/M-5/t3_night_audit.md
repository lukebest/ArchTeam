# T3 night audit · P-0198/M-5 CRRF（Credit-Reclaim / Rebind Flip）

auditor: 评估审计
batch: P-0198 (not Batch A; keep separate from eliminated M-1 CBC / M-2 CSR / M-4 AODI)
round: night-1 (follow-up to smoke T3 通过)
date: 2026-09-30 (Asia/Shanghai)
verdict: 确认通过（night）
PR audited: https://github.com/lukebest/ArchTeam/pull/73 (tip `b0b4cf9`; night on top of smoke `da294cb`)
Prior smoke T3: `/workspace/archteam-p198-m5-t3/reviews/P-0198/M-5/t3_audit.md`（通过; PR #75; tip `da294cb`）
T2 context: `/workspace/archteam-p198-m5/reviews/P-0198/M-5/t2_audit.md`（signed 通过; model draft PR #63 tip `0b16165`）。Card-claim **NOT signed**。Ablation = rebind-off only。T2 `models/P-0198/M-5/` is **not** on this PR。

## 判决

亲自重跑 tip `b0b4cf9`：pytest **25 passed**、exit 0（0.08 s）；night `--mode night --seed 20260903 --out runs/t3-crrf-night-r1` exit **0**（21:11:29–21:11:31 CST，wall ≈2 s）。regen 与 committed `sims/P-0198/M-5/results/night/` 的 capacity / t2_compare / bw_ci / cycles / dat_makespan / hard2_dest / snp_path **byte-identical**（`cmp`）。`summary.json` 去掉两条 out 路径串后数值体一致。三张 PNG：`snp_ratio.png`（写在 out 根）与两张 t2_vs_*（写在 `out/night/`）相对 committed night/ **byte-identical**。未覆盖写 committed `results/` smoke 夹具（mtime 仍为 12:11:33 CST）；未覆盖写 committed `results/night/`（mtime 仍为 checkout 21:11:05 CST）。未改 `sims/` / `models/` / `mechanisms/`。本文件独立于 smoke `t3_audit.md`，不污染 #75。

Night 确认 smoke 通过的同一杀线结构，bbox 放大（|I|=96、outstanding=32、t_steady_laps=12、全 CLASSES 含 broadcast）后数字移动但方向不变：`flag_gt_30pct=2`（仅两行 15:1 H-SNP-LAT），T3 数字站着，**没有**把 T2 1.5625 贴进结果。专用 `snp_path` 15:1 = **17.0533 KILL**（426.33/25）vs T2 1.5625（|rel| 9.91）；Snp-on-gather 15:1 三 trial 均值 **32.5873 KILL**（|rel| 19.86）。`Snp 15:1 kill_1.4` 行 **True/True**（rel_err=0）。混合窗 3:1 / 7:1 均值 **27.51 / 30.84 也 KILL**；completions Snp **12/12**、Dat **96/96**、`comp_drop=False`。诚实加严，不是编码伪影，不是把 Snp 折进 Dat 均值过关。

其它钉全 <30%：最大非 flag |rel| = gather 3:1 **0.113**（0.551 vs 0.6212）。`T_drain=75` vs 77（|rel| 2.6%）；`f_steady` gather 7:1 **0.7727** vs 0.8666（|rel| 10.8%，相对 smoke 0.709 因更长 steady 抬高）；`C_dat_eff` gather 钉 1.000/1.4879/1.5845/1.6328 vs 1.000/1.6099/1.7182/1.7724（|rel| 0 / 7.6% / 7.8% / 7.9%）。H-COMMIT held **0** / violated **12**。HARD-1 **49 > 27** True。108/108 `leq_ideal`/`lt2`/`untaxed_double=False`；on-arm tax≥0.1714；rebind-off `C_dat_eff=1`、`tax=0`。`aligned=True`、`oracle_used=False`、`hint_depends=False`、`card_claim_is_measured=False` 全 108 cycle 行。card-claim 0.55–0.85× **NOT measured**（gather 0.551 落在区间内也不签字）。0.85 是约束条，不是被平均的均值。无硅、无 ±15%。未与 M-1/M-2/M-4 混排。未开 T4。机制卡正文不改。

相对 smoke（#75 / tip `da294cb`）：同一 2-flag 模式、同一 15:1 KILL、同一不贴 1.5625；night 幅度从 11.67/23.22 抬到 17.05/32.59（更大窗 / 更长 drain 暴露），仍是加严不是软化。`snp_path` 7:1 仍双峰（trial vals 258/253/**23**，均值 178 ±151.9）——均值比 7.12 KILL 但不是稳定钉，与 smoke 宽 CI 同源。broadcast 首次进表：on/off 均 100.00 ±0，不签 H-DAT-DOM。

提交者声称（flag=2、15:1 snp_path 17.05× / mixed 32.59×、KILL True、其它 <30%、card-claim 未测、未覆写 smoke、未改 sim、无 T4、与 eliminated 兄弟分离）**全部核实**。这不是「结构绿、主收益/HARD 诚实失败」。Night 确认 smoke 通过 → **确认通过（night）**。卡 T3 **仍存活**。

## 杀线对照（亲自重跑 night）

| # | T1/T2 杀线 | Night T3 证据 | vs smoke audit | 结果 |
|---|------------|---------------|----------------|------|
| 1 | Epoch Drain 税；`T_drain=(k_circ+1)·C_ring+n_pipe`；`f_steady` 扣税 | N=25 探针 `T_drain=75`（公式 77）；gather 7:1 `f_steady=0.7727`、`tau_drain=0.2273` | smoke 75 / 0.709 → night 同 drain、f↑ | **PASS**（|rel| 2.6% / 10.8%，不贴 77/0.8666） |
| 2 | `epoch_committed` 屏障：开 → redirect 0，关 → >0 | held **0**（completed 12）/ violated **12**（completed 0） | 与 smoke / T2 同数 | **PASS** |
| 3 | 时间复用 ≠ 第二永久 Dat 槽；税必须扣；`C_dat_eff<2` | 108/108 `leq_ideal`、`lt2`、`untaxed_double=False`；on-arm tax≥0.1714；off=1.000；max C=1.7718 | smoke 48 行同构 → night 全类扩行 | **PASS** |
| 4 | duty∈{3:1,7:1,15:1}+rebind-off 分列；禁 Dat 均值藏 Snp | 四臂分列；gather 三 on-arm 同为 27 **未平均**；Snp 另表；broadcast 中性 | smoke 14 打平 → night 27 打平 | **PASS** |
| 5 | 默认 **15:1 H-SNP-LAT KILL**（T2 1.5625）；不得抹成 pass | snp_path 15:1 **17.05 KILL**；mixed 15:1 **32.59 KILL**；`kill_1.4` True/True；flag 2 | smoke 11.67/23.22 → night 加严 | **PASS**（加严，非软化；未贴 1.5625） |
| 6 | HARD-1：rebind-off makespan **严格差于** 最佳 on-arm | cycle **49 > 27** True（T2 ns 537.2>303.1） | smoke 24>14 → 同向 | **PASS** |
| 7 | hint 至多 advisory；SYNC ≠ oracle | `oracle_used=False`；`hint_depends=False`；108/108 | 同 smoke | **PASS** |
| 8 | card-claim 不签测得；\|rel\|>30% 必须留 T3 | card-claim 行 `NOT measured`；两行 Snp flag，未替换 1.5625 | 同 smoke | **PASS** |
| 9 | 可再生；不混 M-1/M-2/M-4；smoke 夹具不被 night 覆盖 | CSV `cmp` 一致；pytest 25；summary 明示 eliminated sibling；smoke mtime 未动 | — | **非伪影** → 确认通过而非退回/淘汰 |

## 关键数字（SEED=20260903，n_trials=3，mode=night）

### 容量 / Drain / 屏障

- `T_drain`：Night **75** vs T2 **77**；|rel| **0.0260**；flag no。公式仍印 77，探针不替换。
- `f_steady`（compare 钉 = gather 7:1）**0.7727** vs T2 **0.8666**；|rel| **0.1084**；flag no。（smoke 同钉 0.709；night 更长 `t_steady_laps` 抬高 STEADY 占比，仍 <30%。）
- `C_dat_eff` gather 均值（compare 全精度）：**1.000 / 1.487915 / 1.584506 / 1.632801** vs **1.000 / 1.6099 / 1.7182 / 1.7724**；|rel| 0 / 0.076 / 0.078 / 0.079；flag no。ideal 1.000/1.750/1.875/1.9375，全部 `≤ ideal`。
- H-COMMIT：**0 / 12** vs **0 / 12**。

### H-DAT-DOM / HARD-1（gather；|I|=96；三 trial 钉死）

| Arm | makespan | C_dat_eff | T / off | T2 ratio | \|rel\| | flag |
|-----|----------|-----------|---------|----------|---------|------|
| rebind-off | 49.00 ± 0 | 1.000 | 1.000 | — | — | no |
| 3:1 | 27.00 ± 0 | 1.4879 | **0.5510** | 0.6212 | 0.113 | no |
| 7:1 | 27.00 ± 0 | 1.5845 | **0.5510** | 0.5820 | 0.053 | no |
| 15:1 | 27.00 ± 0 | 1.6328 | **0.5510** | 0.5642 | 0.023 | no |

HARD-1：**49 > 27** True。三 duty 的 Dat makespan 在本 night bbox **打平**（dest-0 eject，不是 duty 在买 span）。不得发布 duty 平均加速。0.551 落在未签字的 0.55–0.85 里 ≠ 测得信封。

broadcast（night 首扫）：on/off 均 **100.00 ± 0**；`card_claim=n/a-neutral`；不签 H-DAT-DOM。

### Snp（分列；勿并进 Dat）

| Window | Arm | Night T_snp/off | kill 1.4× | T2 | flag>30% | completions |
|--------|-----|-----------------|-----------|----|----------|-------------|
| snp_path | rebind-off | 1.00（25/25） | no | 1.0 | no | class size |
| snp_path | 3:1 | **1.00** | no | 1.090 | — | 无 drop |
| snp_path | 7:1 | **7.12**（178/25） | **yes**（CI ±151.9；trial vals 258/253/**23**） | 1.245 未杀 | 非 compare 行 | 无 drop |
| snp_path | 15:1 | **17.0533**（426.33/25） | **yes** | 1.5625 KILL | **yes** \|rel\| 9.914 | 三 trial 511/505/263 |
| snp_on_gather | 3:1 | **27.508** 均值 | **yes** | 1.090 | — | Snp **12/12**，Dat 96，`comp_drop=False` |
| snp_on_gather | 7:1 | **30.841** | **yes** | 1.245 | — | 12/12 |
| snp_on_gather | 15:1 | **32.5873** | **yes** | 1.5625 | **yes** \|rel\| 19.856 | 12/12 |

`t2_compare.csv`：**2/16** `flag_gt_30pct=True`（仅上述两行 15:1）。KILL 行本身 rel_err=0（True vs True）。T3 未替换为 T2。非 flag 最大 |rel| = **0.113**（gather 3:1）。

### 探针 / 其它

| 项 | Night | 备注 |
|----|-------|------|
| card-claim | **NOT measured** | `card_claim_is_measured=False`；0.55–0.85× 与写侧 0.85–1.05× 均不签 |
| oracle_used | **False** 108/108 | SYNC 不是流量神谕 |
| hint_depends | **False** 108/108 | 正确性不依赖 COLL_EP |
| aligned | **True** 108/108 | 暖机到 SYNC-aligned STEADY |
| HARD-2 | hard2_dest 写入；gather 目的地本就是 workload 单点 | 不把 gather 直方图当机制坍缩 |
| broadcast | night **已跑**；中性 100/100 | 不签 H-DAT-DOM |
| smoke `results/` | mtime **12:11:33 CST 未动** | night 只写 `results/night/`（提交者）/ `runs/…`（本审计） |

## 相对 smoke T3（#75）与 T2（#63）

| 钉 | T2 signed | Smoke T3 | Night T3 | night flag |
|----|-----------|----------|----------|------------|
| T_drain | 77 | 75 | 75 | no |
| f_steady 7:1 | 0.8666 | 0.709 | **0.7727** | no |
| C_dat_eff 3/7/15 | 1.610/1.718/1.772 | 1.419/1.507/1.551 | **1.488/1.585/1.633** | no |
| H-COMMIT | 0/12 | 0/12 | **0/12** | no |
| gather T/off | 0.621/0.582/0.564 | 0.583×3 | **0.551×3** | no |
| HARD-1 | 537>303 | 24>14 | **49>27** | no |
| Snp 15:1 snp_path | 1.5625 KILL | 11.67 KILL | **17.05 KILL** | **yes** |
| Snp 15:1 mixed | 1.5625 KILL | 23.22 KILL | **32.59 KILL** | **yes** |
| kill_1.4 | True | True | **True** | no |
| card-claim | NOT measured | NOT measured | **NOT measured** | — |
| flag count | — | 2 | **2** | — |

T2 签字方向与 HARD 方向在 night 仍成立；容量界仍成立；Dat gather 相对比在 30% 内。被推翻的仍是 **q=1 细槽 H-SNP-LAT 的幅度**——night 比 smoke 更狠，仍标 flag、仍 KILL、仍不贴 1.5625。**不签** card-claim。缺口大在 Snp 幅度，但杀假设本身命中——不构成淘汰。

## 代码（亲自重跑）

- tip：`b0b4cf968f62d95becfb437cc76512784af2e606`（`git fetch origin pull/73/head` → checkout）
- pytest: `/workspace/archteam-p198-m5-t3/.venv/bin/python -m pytest sims/P-0198/M-5/tests --override-ini='addopts=' -q`
  - exit **0**；**25 passed** in 0.08 s
- night: `.venv/bin/python sims/P-0198/M-5/sweep.py --mode night --seed 20260903 --out runs/t3-crrf-night-r1`
  - exit **0**；21:11:29–21:11:31 CST（wall ≈2 s）
  - stdout：`T2 |T3-T2|/T2 > 30% flags: 2`；`HARD-1 cycle: rebind-off (49.0) > best on-arm (27.0)? True`；DISCREPANCY 样例为 snp_path 15:1=17.05（T3 stands）
  - `--out` **supported**；committed smoke `results/` 与 committed `results/night/` mtime 均未动
  - CSV vs committed night：`cmp` 空（capacity / t2_compare / bw_ci / cycles / dat_makespan / hard2_dest / snp_path）
  - `summary.json`：仅两条 out 路径不同，去路径后一致
  - PNG：三张相对 committed night **byte-identical**（本环境可复现）
- deps：本树 `.venv` 的 `simpy` 4.1.2 + `matplotlib` 3.11.2 + `pytest` 9.1.1
- SEED=20260903；trials `SEED+i`（20260903/04/05）
- 未改 `sim.py` / `sweep.py` / `tests` / `results` / `results/night` / `t2_pins.py` / `models/` / `mechanisms/` / `problems/` / `FUNNEL.md`
- 本文件只写 `reviews/P-0198/M-5/t3_night_audit.md`；smoke `t3_audit.md` 保持原样；未 commit、未开 GitHub PR

## 修复清单

无（确认通过，不退回）。建议（非退回条件，且本审计不改卡、不改 sim）：

1. `report.md` 仍以 smoke 表为主；若周报引用 night，请另表标明 17.05/32.59 与 gather 0.551，避免与 smoke 11.67/23.22 / 0.583 混成一套。
2. `snp_path` 7:1 双峰（258/253 vs 23）若进周报，必须带 CI，不得写成稳定 7.1× 钉。
3. 不要把 gather 0.551 或 T2 1.5625 写成测得信封。勿开 T4 把 q=1 代数再跑成 pass。

## 禁止自检

未改 sim/spec/机制卡/models/problems/FUNNEL；未把 card-claim 或 0.85 签成测得均值；未把 Snp 折进 Dat 或贴 T2 1.5625；未与 Batch A / M-1 CBC / M-2 CSR / M-4 AODI 混排名；未开 GitHub 审计 PR；未开 T4；未覆盖写 signed smoke `results/`；未编辑机制卡。卡 T3 **仍存活**。
