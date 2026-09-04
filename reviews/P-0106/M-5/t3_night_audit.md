# T3 night audit · P-0106/M-5 AffineRebind

auditor: 评估审计
scan: night 2026-09-03 (path-fix resubmit)
round: 2
date: 2026-09-04 (Asia/Shanghai)
source: PR #25 (path-fix; merge pending human) `cursor/affinerebind-night-smoke-cb4a`
verdict: 通过

## 判决

对照 round-1 退回清单，本轮 **全部关闭**。签字 smoke 36 行已恢复且 night 不再覆盖；`results/night/` 承载 144 行占用；亲自 `pytest` **20 passed**；night 默认命令 rc=0（~52 s），再生 night 占用 / BW / summary 与 PR #25 逐字节一致。BW 432 行全标 `H-DRAM-BB`，summary 写明 AP 512 reduced-bbox、**不签信封 0.85**。unif-6.25% 不再被 `"25%"` 子串误标。占用无杀线。故 **通过**。不修代码。不混 SNS / P-0105。

`verdict: 通过`

## 相对 round-1（退回项闭合）

1. **已闭：** `results/{occupancy,t2_compare}.csv` 恢复 36 行；3×512B=9、9×512B=9（3 mask × 3 strategy）。与 PR #20 签字 smoke 合同一致。
2. **已闭：** night 占用写到 `results/night/{occupancy,t2_compare}.csv`。默认 `--out=results` 时 night 不碰签字表。亲自 night 重跑后 smoke 两文件 cmp 未变。
3. **已闭：** `test_signed_smoke_tables_include_factor3_doc_s` 只读签字路径；pytest 20 passed。
4. **已闭：** `report.md` 写 night AP=512 reduced-bbox、H-DRAM-BB、0.85 非测得均值；`summary.json` 含 `bbox`。
5. **已闭：** note 改为 `label.startswith("unif-25%")`；`unif-6.25%(n=45)` note 为空，仅 `unif-25%(n=36)` 带 n=36 注。
6. **已闭（如实）：** stack 36 行 `t2_*` 空；有 T2 的 108 行 rel_err=0。未把 stack 空白 T2 当对拍。

## 对照 T2 占用

**签字 smoke（`results/`）：** 36 行。S∈{512B,3x512B,9x512B,2MiB}×mask∈{full-good,n=40,3-biased}×{skip-dead,modn-a1,minimax}。`rel_err_cls=rel_err_n_bank=0`，`flag_gt_30pct=False`，dead=0。

**night（`results/night/`）：** 144 行。S 加 {512KiB,1MiB}；mask 加三档 unif；strategy 加 stack。有 T2 108 行 rel_err max=0、flag=0、t3_dead=0；stack 36 行空白 T2。gcd 仍 AP sanity。

## night BW（H-DRAM-BB）

- 432 行；`hypothesis=H-DRAM-BB` 全表；csr_ports{1,4}；S∈{512B,3x512B,2MiB}；含 3×512B。
- 每行 mean ± 95% CI (n=3)。无 GB/s。无 mean≈0.85。
- bbox：8 cores × 16 outstanding, AP 512, reduced-bbox; not 120-core / Q_tot=15360 envelope 0.85。
- 类数增益 ≠ BW×3。

## 重跑对拍

- pytest：`python3 -m pytest sims/P-0106/M-5 -q` → 20 passed，rc=0。
- night：`python3 sims/P-0106/M-5/sweep.py --mode night --seed 20260903 --n-trials 3` → rc=0，~52 s。
- 再生 vs PR #25：`results/night/{occupancy,t2_compare}.csv`、`bw_ci.csv`、`cycles.csv`、`summary.json` byte-identical；smoke cmp 未变。

## 修复清单

无必须项。

建议（不挡过）：`--out` 落到仿真包外时 `relative_to(_HERE)` 写 summary 会崩；默认路径可复现。

## 禁止自检

未改机制卡 / T2 / SNS；未把 reduced-bbox BW 签成信封 0.85；未用 gcd AP 顶替 XOR_fold6；未把 stack 空白 T2 算进对拍。
