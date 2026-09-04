# T3 night audit · P-0105/M-4 SNS

auditor: 评估审计
scan: night 2026-09-03
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 通过

## 判决

独立审计对照 PR #22 / `main` 已合入的 night 产物重跑对拍，**通过**。pytest **24 passed**，rc=0。night 命令 rc=0、elapsed 29s。再生 `bw_ci.csv` / `cycles.csv` / `summary.json` 与 PR #22 逐字节一致。占用沿用已签字 smoke 表（336 行 `rel_err=0`），不是 night 另签的独立占用。COVERING max=11 min=10 CV=0.0442、`golden=false`，ROM 未重调。night BW 480 行皆 `hypothesis=H-DRAM-BB`、`mean ± 95% CI (n=3)`、无 GB/s；**不签信封 0.85**（0.85 是约束，不是测得均值）。未声称硅校准，也未声称 120-core / `Q_tot=15360` 全信封。修复清单=无。

`verdict: 通过`

## 占用来源

**占用签字是已签字的 smoke 表，不是 night 另签的独立占用。**

- 签字源：smoke `sims/P-0105/M-4/results/t2_compare.csv`（`reviews/P-0105/M-4/t3_audit.md` round 2 已签）
- 336 行：`rel_err_n_dmc = rel_err_n_bank = 0`，`flag_gt_30pct = 0`
- night 用同一占用旋钮重算（`SNS_STRIDES` × grain512/align2MiB × 策略；4608B 无 align2MiB），写出字节与已签字 smoke 表一致
- COVERING_BOUND（uniform raw，**非黄金**）：max=11 min=10 CV=0.0442；`summary.json` `"golden": false`。ROM / S-box 未为 covering 重调

night 不另开占用签字。占用结论仍以 smoke 表为准。

## night BW

新度量：假设 **H-DRAM-BB**（非 T2 差、非硅校准）。每格 `mean ± 95% CI`，n=3。无 GB/s。**0.85 是问题过线约束，不是测得均值；本表不签信封 0.85。**

- 文件：`sims/P-0105/M-4/results/bw_ci.csv` **480 行**，全部 `hypothesis=H-DRAM-BB`，`n=3`（`cycles.csv` 1440 行 = 480×3）
- S=`{2MiB,1MiB,512KiB,4608B,512B}`
- strategies=`{sns,mod384,low,high}`
- `map_ports`=`{1,4}`，`map_lat`=`{1,2}`，`page`=`{open,close}`，`mask`=`{full,rand1/16,third}`
- bbox：**8 cores × 16 outstanding**，AP **512** points（reduced-bbox）。**不是** 120-core / `Q_tot=15360` 全信封

抽格（与 PR #22 已合入表一致，仅作核对，不扩签字范围）：

| S | strategy | ports | lat | page | mask | txns/cycle mean ± 95% CI |
|---|----------|-------|-----|------|------|--------------------------|
| 2MiB | sns | 1 | 1 | open | full | 0.991379 ± 0.000000 (n=3) |
| 2MiB | mod384 | 1 | 1 | open | full | 0.065341 ± 0.000000 (n=3) |
| 2MiB | sns | 4 | 1 | open | full | 3.231885 ± 0.014800 (n=3) |
| 2MiB | sns | 1 | 2 | open | full | 0.500000 ± 0.000000 (n=3) |
| 2MiB | sns | 1 | 1 | close | full | 1.000000 ± 0.000000 (n=3) |
| 2MiB | low | 1 | 1 | open | full | 0.021739 ± 0.000000 (n=3) |
| 2MiB | high | 1 | 1 | open | full | 0.970464 ± 0.000000 (n=3) |

AP512 与 smoke AP256 的 BW 格不可混比。Refresh 未建模。

## 重跑对拍

对照 PR #22 / `main` 已合入 `sims/P-0105/M-4/results/`（未覆盖写 committed 树）：

- pytest：`python3 -m pytest sims/P-0105/M-4/tests -q` → **24 passed**，rc=0
- night：`python3 sims/P-0105/M-4/sweep.py --mode night --seed 20260903 --n-trials 3` → rc=0，elapsed **29s**
- 再生 `bw_ci.csv`、`cycles.csv`、`summary.json` 与 PR #22 **byte-identical**
- 占用：night 重算同一旋钮，`t2_compare.csv` 与已签字 smoke **byte-identical**（336 行，`rel_err=0`，`flag_gt_30pct=0`）
- SEED=20260903；trials `SEED+i`

## 修复清单

无

## 禁止自检

未改机制卡、T2 spec/model、T3 sim/sweep/tests/results、已有 smoke `t3_audit.md`。未碰 P-0106/M-5 AffineRebind，结论不混写。未把 reduced-bbox / AP512 的 H-DRAM-BB 测值签成信封 0.85，也未标硅校准或 120-core / `Q_tot=15360` 全信封。
