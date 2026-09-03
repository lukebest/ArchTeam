# T3 audit · P-0105/M-4 SNS

auditor: 评估审计
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 退回

## 判决

亲自重跑 pytest 20 passed、exit 0；smoke `--seed 20260903 --n-trials 3` exit 0（1.761 s），写出 `runs/t3-sns-smoke/` 与 committed `sims/P-0105/M-4/results/` 的 occupancy / t2_compare / bw_ci / cycles / summary.json **byte-identical**。占用 like-to-like 对 T2 `model.py`：全部 48 行 `flag_gt_30pct=False`、`|T3−T2|/T2 = 0`（n_DMC 与 n_bank），mapper bit-exact，COVERING_BOUND 标 `golden: false` 未当黄金，ABL-sbox 在 S=2MiB grain 相位变 DMC **id**。机制占用未杀线，故非淘汰。但签字 smoke 表只含 S∈{2MiB,512B}，缺 T2 pass-pack 的 1MiB / 512KiB / 4608B（4608B 须单列）。规范：smoke 漏 T2 pass-pack S ⇒ **退回（incomplete T3）**，不是机制淘汰。T3 BW 为假设 H-DRAM-BB 新度量（8 核×16 outstanding、256-point AP、1-port），已标 reduced-bbox，不能签成信封 0.85。

## 对照 T2 占用

重跑命令：`.venv/bin/python sims/P-0105/M-4/sweep.py --mode smoke --seed 20260903 --n-trials 3 --out runs/t3-sns-smoke`。占用用 T2 issued-set `I=min(K,Q_tot)`（smoke 未传 `--n-pts` 给 occupancy）。

| S | family / base | strategy | T3 n_DMC | T2 n_DMC | rel_err | T3 n_bank | T2 n_bank | flag_gt_30pct |
|---|---------------|----------|----------|----------|---------|-----------|-----------|---------------|
| 2MiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 | 0 |
| 2MiB | grain512 / 0x0 | mod384 | 3 | 3 | 0 | 3 | 3 | 0 |
| 2MiB | grain512 / 0x0 | sbox | 1 | 1 | 0 | 1 | 1 | 0 |
| 2MiB | grain512 / 0x0 | shear | 384 | 384 | 0 | 2304 | 2304 | 0 |
| 512B | grain512 / 0x0 | sns | 384 | 384 | 0 | 9008 | 9008 | 0 |

- 签字 `t2_compare.csv` 48 行：`rel_err_n_dmc` 与 `rel_err_n_bank` **max = 0.0**；`flag_gt_30pct` 全 False。与 committed 表 `diff` 空。
- SNS S=2MiB grain `{0,512,1024,1536}`：n_DMC 全 384，`rel_diff=0.0000`；align `{0,2MiB}` 同。bks/DMC=6-6，`bank%8` kinds=1，maxload=11 minload=10，min/mean=0.9375（base=0）。
- COVERING_BOUND（uniform raw，**非黄金**）：max=11 min=10 CV=0.0442；`summary.json` `"golden": false`。未改 ROM/S-box。S=2MiB SNS 是 12b 置换，fold384 算术上必实现该 covering，报告已如实写，不是贴数。
- ABL-sbox S=2MiB，计数恒 1，**id 随 grain 相位变**（亲自跑 `occupancy("sbox", …)`）：
  - grain: `0x0→(0,) 0x200→(1,) 0x400→(2,) 0x600→(3,) 0xe00→(7,) 0x1e00→(15,) 0x3e00→(63,) 0x7e00→(287,)`
  - align2MiB: 全 `(0,)`（x12 冻 0，与 T2 一致）
  smoke 用前 4 个 grain，id 已变；unit test `test_abl_sbox_varies_phase_id_at_2mib` 过。
- 审计员额外对缺列 S 做了 mapper compare（**非正式签字表**）：S∈{1MiB,512KiB,4608B}×{sns,mod384,low,high,shear,sbox} 在 base=0、`min(K,Q_tot)` 下 rel_err 仍为 0；4608B SNS n_DMC=384 min/mean=0.7000 单列口径与 T2 审计一致。这只说明 mapper 未坏，**不能**把缺列 smoke 改判通过。

## T3 BW（H-DRAM-BB 新度量，非 T2 差）

bbox（smoke，已在 `report.md` 标明，**不能签信封 0.85**）：**8 cores × 16 outstanding**，AP **256 points**，map_ports=1，map_lat=1，page=open，mask=full，warmup 丢前 10% completions，n_trials=3，seed=`20260903+trial`。μ_d UNKNOWN；无 GB/s；0.85 是问题过线不是测得均值。T2 无 BW 列，不把缺列当 discrepancy。

| S | strategy | ports | map_lat | page | mask | txns/cycle mean ± 95% CI |
|---|----------|-------|---------|------|------|--------------------------|
| 2MiB | sns | 1 | 1 | open | full | 1.000000 ± 0.000000 (n=3) |
| 2MiB | mod384 | 1 | 1 | open | full | 0.064953 ± 0.000000 (n=3) |
| 512B | sns | 1 | 1 | open | full | 1.000000 ± 0.000000 (n=3) |
| 512B | mod384 | 1 | 1 | open | full | 1.000000 ± 0.000000 (n=3) |

此 bbox 下 S=2MiB SNS 打到 1-port mapper 天花板，mod384 约 0.065 txn/cyc（3 DMC）；**不是**「只赢 min/mean、输绝对值」。S=512B 两侧都是 1.0（port-bound）。Refresh 未建模（已标）。cycle 占用 n_DMC≈216–224（256 点）≠ occupancy 表的 384，勿混用。

## spec/sim 一致

T3 `MAPPERS` 与冻结 `models/P-0105/M-4/model.py` 同网表：`x'=(x+((y<<3)-y))&0xFFF`；ROM=`u^5+u^3+u mod 256`，`S(0..15)=(0,3,42,17,68,183,62,5,8,139,146,89,204,255,166,141)`；`z=ROM[x'[11:4]] XOR y[7:0]`；fold384 粗商+一次校正；`bank_in=x'[9:4] mod 48`。无 AES/GF(256)、无 H100、无硬编码 GB/s（仅「no GB/s」）。

Dr.Sim cycle must-verify（查卡、不改卡）：

| # | 项 | 结果 |
|---|----|------|
| 1 | 12b shear truncate | PASS（`shear` + `test_shear_12bit_truncate`） |
| 2 | 整数 ROM checksum | PASS |
| 3 | fold384 | PASS（12b 上 ≡ `raw%384`） |
| 4 | bank 6b 窗直方图 | PASS（S=2MiB SNS 6-6，bank%8=1） |
| 5 | 消融 shear / sbox | PASS（shear 384；sbox 计数 1 且 grain id 变） |
| 6 | grain vs 2MiB-aligned | PASS **仅** smoke 已跑的 S={2MiB,512B} |
| 7 | S 集 {2MiB,1MiB,512KiB,4608B,512B}，4608B 单独 | **FAIL on signed smoke**（只有 2MiB+512B）。`sweep.py --mode night` 代码有全 S，但 committed results/ 与本次签字重跑都是 smoke。 |
| 8 | covering 非黄金 | PASS |
| 9 | DRAM 时序标 假设 | PASS（H-DRAM-BB） |
| 10 | warmup | PASS（10%） |
| — | partial-good 1/16 与 1/3 + PE 1-cycle | 代码+单测 PASS；**smoke 未出这些占用/BW 行**（night 才扫 mask） |
| — | inflight 15360 按周期占槽 | occupancy 用 Q_tot；**cycle 驱动是 8×16=128**（已标 reduced-bbox） |

## 代码（亲自重跑）

- pytest: `/workspace/archteam-audit/.venv/bin/python -m pytest sims/P-0105/M-4/tests -q`
  - exit **0**；20 passed；~0.40 s；log `runs/t3-P-0105-M-4-pytest.log`
- smoke: `/workspace/archteam-audit/.venv/bin/python sims/P-0105/M-4/sweep.py --mode smoke --seed 20260903 --n-trials 3 --out /workspace/archteam-audit/runs/t3-sns-smoke`
  - exit **0**；elapsed **1761 ms**（07:35:45 UTC / 15:35:45 SGT）；log `runs/t3-P-0105-M-4-smoke.log`
- SEED=20260903；trials `SEED+i`
- 未覆盖写 committed `sims/P-0105/M-4/results/`

## 修复清单

退回（不修代码、不改 ROM；下列为签字缺口）：

1. **必须**：签字 occupancy / t2_compare 补全 T2 pass-pack S=`{2MiB,1MiB,512KiB,4608B,512B}`，4608B 单独成列、不并进 2-power 行。当前 smoke 与 `results/` 只有 2MiB 与 512B。`sweep.py --mode night` 已枚举 `SNS_STRIDES`，重跑并提交缺列即可；不要用 covering 11/10/CV≈0.044 当黄金去调 ROM。
2. 若要以本 T3 覆盖 Dr.Sim 位图 1/16、1/3 residue、map_ports∈{1,4}：在签字 CSV 里产出这些行，并继续标 假设 H-DRAM-BB。不要把 8×16 / 256-pt / 1-port smoke 签成 120-core / Q_tot=15360 信封的 0.85。
3. （次要，T2 对照完整度）smoke 占用现为 grain 4 个 base + align 2 个、策略缺 B-low/B-high；扩到 T2 的 `GRAIN_BASES`/`ALIGNED_2MIB` 与四基线+两消融，避免「单表过瘦」。

## 禁止自检

未改 sim.py / sweep.py / tests / results / spec.md / model.py / 机制卡；未把未签字数字（缺列 S 的 auditor spot-check、reduced-bbox BW）当周报或信封 0.85。
