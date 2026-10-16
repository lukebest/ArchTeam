# T3 audit · P-0198/M-5 CRRF（Credit-Reclaim / Rebind Flip）

auditor: 评估审计
batch: P-0198 (not Batch A; keep separate from eliminated M-1 CBC / M-2 CSR / M-4 AODI)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 通过
PR audited: https://github.com/lukebest/ArchTeam/pull/73 (tip `da294cb`)
T2 context: `/workspace/archteam-p198-m5/reviews/P-0198/M-5/t2_audit.md` (signed 通过; model draft PR #63 tip `0b16165`). Card-claim **NOT signed**. Ablation = rebind-off only. T2 `models/P-0198/M-5/` is **not** on this PR.

## 判决

亲自重跑 pytest **25 passed**、exit 0（0.07 s）；smoke `--mode smoke --seed 20260903 --out runs/t3-crrf-smoke-r1` exit 0（12:12:07–12:12:08 CST）。regen 与 committed `sims/P-0198/M-5/results/` 的 capacity / t2_compare / cycles / dat_makespan / snp_path / drain_probe / h_commit_probe / hard2_dest / bw_ci / t2_signed_pins **byte-identical**（`cmp`）。`summary.json` 仅 `capacity_csv` / `t2_compare_csv` 路径串因 `--out` 不同，数值体一致。三张 PNG **非**字节相同（同 1320×528；zlib 原始约 0.5% 字节差，Matplotlib 3.11.2 抗锯齿，**不是**换数）。未覆盖写 committed results/（mtime 12:11:33 CST 未动）。未改 `sims/` / `models/` / `mechanisms/`。

结构与容量钉过线：`C_dat_eff ≤ ideal` 且 `<2`（max 1.6391）、`untaxed_double=False` 全 48 行；on-arm `tax>0`（min 0.2956）；rebind-off `C_dat_eff=1`、`tax=0`（`tax_gt_0` 列对 off 臂恒 True，是「豁免通过」不是伪税）。Drain 探针 N=25：`T_drain=75` vs 签字 77（|rel| 2.6%，不替换）。H-COMMIT held redirect **0** / violated **12**，与 T2 同数。`aligned=True`、`oracle_used=False`、`hint_depends=False` 全 48 cycle 行。HARD-1 gather **24 > 14** True，方向与 T2 **537.2 > 303.1** 相同。Gather `T/T_off` 三 on-arm均为 **0.5833**（未折成一条 duty 均值），相对 T2 0.6212/0.5820/0.5642 的 |rel| 为 6.1% / 0.2% / 3.4%，**无** >30% flag。

Snp 杀假设**没有被抹软**：`t2_compare` 两行 `flag_gt_30pct=True`（2/16），T3 数字站着，**没有**把 T2 1.5625 贴进结果。专用 `snp_path` 15:1 = **11.6667 KILL**（175/15，三 trial 均 175）vs T2 1.5625（|rel| 6.47）。Snp-on-gather 15:1 三 trial 均值 **23.2222 KILL**（|rel| 13.86）。混合窗 3:1 / 7:1 均值 **20.02 / 22.16 也 KILL**；completions Snp **6/6**、`comp_drop=False`（makespan 是失败端点，不是丢完成）。这是合法 drain/flip/`epoch_committed` 付不起 q=1 TDM 的诚实加严，不是编码伪影，也不是把 Snp 折进 Dat 均值过关。

`f_steady` gather 7:1 = **0.709** vs 0.8666（|rel| 18.2%）；`C_dat_eff` 1.000/1.4185/1.5072/1.5515 vs 1.000/1.6099/1.7182/1.7724（|rel| 0 / 11.9% / 12.3% / 12.5%）。均 <30%。card-claim 0.55–0.85× **NOT measured**（gather 0.583 落在区间内也不签字）。0.85 是约束条，不是被平均的均值。无硅、无 ±15%。未与 M-1/M-2/M-4 混排。未开 T4。

非阻塞：`snp_path` 7:1 makespan 双峰（trial0 **14/14=1.0** 未杀；trial1–2 **171**），均值 118.67 ± **102.57**，均值比 **7.91 KILL** 但不是稳定钉——报告已写 wide CI。`report.md` 混合窗「18.8/20.8/21.8」是 smoke 打印的 **trial 0**，不是三 trial 均值（均值 20.02/22.16/23.22）；两边都是 KILL，都不是 1.5625。Smoke 类不含 broadcast（代码有该类，night 才扫）；本审计不把未跑的 broadcast 当成 Dat 强缩。

这不是 M-1/M-2/M-4 那种「结构绿、主收益/HARD 诚实失败」。HARD 方向在、容量界在、15:1 仍 KILL 且 flag 诚实。过线。

## 杀线对照（亲自重跑）

| # | T1/T2 杀线 | T3 证据 | 结果 |
|---|------------|---------|------|
| 1 | Epoch Drain 税；`T_drain=(k_circ+1)·C_ring+n_pipe`；`f_steady` 扣税 | N=25 探针 `T_drain=75`（公式 77）；gather 7:1 `f_steady=0.709`、`tau_drain=0.291` | **PASS**（|rel| 2.6% / 18%，T3 站，不贴 77/0.8666） |
| 2 | `epoch_committed` 屏障：开 → redirect 0，关 → >0 | `h_commit_probe` held **0**（completed 12）/ violated **12**（completed 0） | **PASS**（与 T2 0/12 同数） |
| 3 | 时间复用 ≠ 第二永久 Dat 槽；税必须扣；`C_dat_eff<2` | 48/48 `leq_ideal`、`lt2`、`untaxed_double=False`；on-arm tax≥0.2956；off=1.000 | **PASS** |
| 4 | duty∈{3:1,7:1,15:1}+rebind-off 分列；禁 Dat 均值藏 Snp | 四臂分列；gather 三 on-arm 同为 14 **未平均**；Snp 另表 | **PASS** |
| 5 | 默认 **15:1 H-SNP-LAT KILL**（T2 1.5625）；不得抹成 pass；7:1 代数未杀只是 T2 默认 | snp_path 15:1 **11.67 KILL**；mixed 15:1 **23.22 KILL**；`kill_1.4` 行 True/True；flag 2 | **PASS**（加严，非软化） |
| 6 | HARD-1：rebind-off makespan **严格差于** 最佳 on-arm | cycle **24 > 14** True（T2 ns 537.2>303.1） | **PASS**（同向） |
| 7 | hint 至多 advisory；SYNC ≠ oracle | `oracle_used=False`；`hint_depends=False`；48/48 | **PASS** |
| 8 | card-claim 不签测得；\|rel\|>30% 必须留 T3 | card-claim 行 `NOT measured`；两行 Snp flag，未替换 1.5625 | **PASS** |
| 9 | 可再生；不混 M-1/M-2/M-4 | CSV `cmp` 一致；pytest 25；summary 明示 eliminated sibling 不混 | **非伪影** → 通过而非退回/淘汰 |

## 关键数字（SEED=20260903，n_trials=3）

### 容量 / Drain / 屏障

- `T_drain`：T3 **75** vs T2 **77**；|rel| **0.0260**；flag no。公式仍印 77，探针不替换。
- `f_steady`（compare 钉 = gather 7:1，三 trial 均 0.709）vs T2 **0.8666**；|rel| **0.1819**；flag no。类间并不相同（uniform ~0.68–0.70，snp_path ~0.78–0.79）；禁止再平均成一个「CRRF f」。
- `C_dat_eff` gather 均值（compare 全精度）：**1.000 / 1.418532 / 1.507152 / 1.551461** vs **1.000 / 1.6099 / 1.7182 / 1.7724**；|rel| 0 / 0.119 / 0.123 / 0.125；flag no。ideal 1.000/1.750/1.875/1.9375，全部 `≤ ideal`。
- H-COMMIT：**0 / 12** vs **0 / 12**。

### H-DAT-DOM / HARD-1（gather；\|I\|=48；三 trial 钉死）

| Arm | makespan | C_dat_eff | T / off | T2 ratio | \|rel\| | flag |
|-----|----------|-----------|---------|----------|---------|------|
| rebind-off | 24.00 ± 0 | 1.000 | 1.000 | — | — | no |
| 3:1 | 14.00 ± 0 | 1.4185 | **0.5833** | 0.6212 | 0.061 | no |
| 7:1 | 14.00 ± 0 | 1.5072 | **0.5833** | 0.5820 | 0.002 | no |
| 15:1 | 14.00 ± 0 | 1.5515 | **0.5833** | 0.5642 | 0.034 | no |

HARD-1：**24 > 14** True。三 duty 的 Dat makespan 在本 bbox **打平**（dest-0 eject，不是 duty 在买 span）。不得发布 duty 平均加速。0.583 落在未签字的 0.55–0.85 里 ≠ 测得信封。

uniform_read/write 同驱动、非主钉：off 15.00±1.13，on 12.33±1.31（trial 并不恒等）。不拿来签 card-claim。

### Snp（分列；勿并进 Dat）

| Window | Arm | T3 T_snp/off | kill 1.4× | T2 | flag>30% | completions |
|--------|-----|--------------|-----------|----|----------|-------------|
| snp_path | rebind-off | 1.00（15/15） | no | 1.0 | no（未单列） | Snp **48/48**，Dat 0 |
| snp_path | 3:1 | **1.00** | no | 1.090 | — | 48/48，无 drop |
| snp_path | 7:1 | **7.91**（118.67/15） | **yes**（CI ±102.6；trial0=1.0） | 1.245 未杀 | 非 compare 行 | 48/48 |
| snp_path | 15:1 | **11.6667**（175/15） | **yes** | 1.5625 KILL | **yes** \|rel\| 6.467 | 48/48，三 trial 均 175 |
| snp_on_gather | 3:1 | **20.022** 均值（trial0 18.833） | **yes** | 1.090 | — | Snp **6/6**，Dat 48，`comp_drop=False` |
| snp_on_gather | 7:1 | **22.156**（trial0 20.833） | **yes** | 1.245 | — | 6/6 |
| snp_on_gather | 15:1 | **23.2222**（trial0 21.833） | **yes** | 1.5625 | **yes** \|rel\| 13.862 | 6/6 |

`t2_compare.csv`：**2/16** `flag_gt_30pct=True`（仅上述两行 15:1）。KILL 行本身 rel_err=0（True vs True）。T3 未替换为 T2。

### 探针 / 其它

| 项 | T3 | 备注 |
|----|----|------|
| card-claim | **NOT measured** | `card_claim_is_measured=False`；0.55–0.85× 与写侧 0.85–1.05× 均不签 |
| oracle_used | **False** 48/48 | SYNC 不是流量神谕 |
| hint_depends | **False** | 正确性不依赖 COLL_EP |
| aligned | **True** 48/48 | 暖机到 SYNC-aligned STEADY |
| HARD-2 | uniform ghost dest 6，main 8–9；`hard2_collapsed=False` | gather 目的地本就是 workload 单点，不把 gather 直方图当机制坍缩 |
| broadcast | smoke **未跑** | 不签 H-DAT-DOM；night 才含 COLL 全类 |

## 相对 T2（#63 / t2_audit 通过）

T2 签字：守恒 + 税、`T_drain=77`、`f_steady≈0.8666`、`C_dat_eff` 1/1.610/1.718/1.772、H-COMMIT 0/12、gather 0.621/0.582/0.564、HARD True、**15:1 Snp=1.5625 KILL**、7:1=1.245 未杀、card-claim 不签。单位是代数 ns / 相对比，不是 cycle。

T3 cycle **保留**杀的方向与 HARD 方向，容量界仍成立，Dat gather 相对比在 30% 内。被推翻的是 **q=1 细槽 H-SNP-LAT 的幅度**：合法 drain 不能摊进 1-cycle TDM，所以 15:1 从 1.56× 变成 11.7×（专用）/ 23.2×（混合），并且混合窗把 3:1 与 7:1 也打过 1.4×。这是机制在 cycle 上的真实加严，魔法缺口 =「q=1 代数声称」减去「占用/屏障能解释的粗量子」。**不签** 1.5625，**不签** card-claim。缺口大在 Snp 幅度，但杀假设本身命中且被标 flag——不构成淘汰（淘汰要的是把杀线做成 pass，或主收益/HARD 像 M-2 那样塌成 ≈1 / False）。

提交者 `sims/P-0198/M-5/report.md` 与 smoke 的 `DISCREPANCY` 行已经自述同一 15:1 flag 与「不替换 T2」。审计同意。机制卡正文不改。

## 代码（亲自重跑）

- pytest: `/workspace/archteam-p198-m5-t3/.venv/bin/python -m pytest sims/P-0198/M-5/tests --override-ini='addopts=' -q`
  - exit **0**；**25 passed** in 0.07 s（accept 5 + fsm 6 + signed_tables 5 + structural 9）
  - 默认 `pytest.ini` 的 `-q` 同样 25 点、exit 0（不印 summary 行）
- smoke: `.venv/bin/python sims/P-0198/M-5/sweep.py --mode smoke --seed 20260903 --out runs/t3-crrf-smoke-r1`
  - exit **0**；约 1 s（12:12:07–12:12:08 CST）
  - `--out` **supported**；committed `sims/P-0198/M-5/results/` mtime 仍为 12:11:33 CST
  - CSV vs committed：`cmp` 空（10 个 csv 全同）
  - `summary.json`：仅两条 out 路径
  - PNG：`snp_ratio.png`、`t2_vs_t3_c_dat_eff.png`、`t2_vs_t3_gather_ratio.png` 非字节相同；尺寸相同；不作为数字分歧
- deps：本树 `.venv` 的 `simpy` 4.1.2 + `matplotlib` + `pytest` 9.1.1
- SEED=20260903；trials `SEED+i`（20260903/04/05）
- 未改 `sim.py` / `sweep.py` / `tests` / `results` / `t2_pins.py` / `models/` / `mechanisms/` / `problems/` / `FUNNEL.md`
- 本文件只写 `reviews/P-0198/M-5/t3_audit.md`；未 commit、未开 GitHub PR

## 修复清单

无（通过，不退回）。建议（非退回条件，且本审计不改卡、不改 sim）：

1. `report.md` 混合 Snp 行标明 trial 0，或改印三 trial 均值 20.02/22.16/23.22，避免读者以为 23.22 与 21.83 是两套模型。
2. `snp_path` 7:1 的双峰（14 vs 171）若进周报，必须带 CI，不得写成稳定 7.9× 钉。
3. 不要把 gather 0.583 或 T2 1.5625 写成测得信封。勿开 T4 把 q=1 代数再跑成 pass。

## 禁止自检

未改 sim/spec/机制卡/models/problems/FUNNEL；未把 card-claim 或 0.85 签成测得均值；未把 Snp 折进 Dat 或贴 T2 1.5625；未与 Batch A / M-1 CBC / M-2 CSR / M-4 AODI 混排名；未开 GitHub 审计 PR；未开 T4。
