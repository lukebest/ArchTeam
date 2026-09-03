# T3 audit · P-0105/M-4 SNS

auditor: 评估审计
round: 2
date: 2026-09-03 (Asia/Shanghai)
verdict: 通过

## 判决

亲自重跑 pytest **24 passed**、exit 0；smoke `--mode smoke --seed 20260903 --n-trials 3` exit 0（9655 ms），写出 `runs/t3-sns-smoke-r2/` 与 committed `sims/P-0105/M-4/results/` 的 occupancy / t2_compare / bw_ci / cycles / summary.json **byte-identical**（`cmp`/`diff` 空）。未覆盖写 committed results/（mtime 07:47 UTC / 15:47 SGT 未动）。占用 like-to-like 对 T2：t2_compare **336 行**，`flag_gt_30pct` 全 False，`rel_err_n_dmc` 与 `rel_err_n_bank` **max = 0**。签字 S=`{2MiB,1MiB,512KiB,4608B,512B}`，4608B 独立成列。COVERING_BOUND `golden: false`，ROM 未重调。ABL-sbox 在 S=2MiB grain 相位变 DMC **id**。机制占用未杀线。

**相对 round-1（退回 MUST 已关）：**
1. **已关。** round-1 签字表只有 S∈{2MiB,512B}。本次重跑 t2_compare 336 行：2MiB/1MiB/512KiB/512B 各 72、4608B **48 且仅 grain512**；occupancy 336 数据行 + 54 REL_DIFF；4608B 的 S 名就是 `4608B`，`note=4608B alone`，没有并进 2-power / 512B。与盘上 committed **逐字节一致**，不是只信 CSV。
2. **已关。** 签字 `bw_ci.csv` 60 行含 `map_ports∈{1,4}`（各 30）与 `mask∈{full, rand1/16, third}`（各 20），**全部** `hypothesis=H-DRAM-BB`。bbox=8 cores×16 outstanding、AP 256 points；summary 写明 reduced-bbox，**不能**签成 120-core / Q_tot=15360 信封 0.85。
3. **已关（次要）。** 占用 family=`grain512`（GRAIN_BASES n=8：`0x0,0x200,0x400,0x600,0xe00,0x1e00,0x3e00,0x7e00`）与 `align2MiB`（ALIGNED_2MIB n=4：`0x0,0x200000,0x400000,0x600000`）；策略 `{high,low,mod384,sbox,shear,sns}` 各 56 行。

故 **通过**。修复清单=无。

## 对照 T2 占用

重跑：`sweep.py --mode smoke --seed 20260903 --n-trials 3 --out runs/t3-sns-smoke-r2`。占用 `I=min(K,Q_tot)`（smoke 未传 `--n-pts` 给 occupancy）。

Grain512 / base=0x0：

| S | family / base | strategy | T3 n_DMC | T2 n_DMC | rel_err | T3 n_bank | T2 n_bank | flag_gt_30pct |
|---|---------------|----------|----------|----------|---------|-----------|-----------|---------------|
| 2MiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 | 0 |
| 2MiB | grain512 / 0x0 | mod384 | 3 | 3 | 0 | 3 | 3 | 0 |
| 2MiB | grain512 / 0x0 | low | 1 | 1 | 0 | 1 | 1 | 0 |
| 2MiB | grain512 / 0x0 | high | 384 | 384 | 0 | 384 | 384 | 0 |
| 2MiB | grain512 / 0x0 | shear | 384 | 384 | 0 | 2304 | 2304 | 0 |
| 2MiB | grain512 / 0x0 | sbox | 1 | 1 | 0 | 1 | 1 | 0 |
| 1MiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 | 0 |
| 1MiB | grain512 / 0x0 | mod384 | 3 | 3 | 0 | 3 | 3 | 0 |
| 512KiB | grain512 / 0x0 | sns | 384 | 384 | 0 | 2304 | 2304 | 0 |
| 4608B | grain512 / 0x0 | sns | 384 | 384 | 0 | 10523 | 10523 | 0 |
| 4608B | grain512 / 0x0 | mod384 | 128 | 128 | 0 | 128 | 128 | 0 |
| 4608B | grain512 / 0x0 | low | 384 | 384 | 0 | 384 | 384 | 0 |
| 4608B | grain512 / 0x0 | high | 34 | 34 | 0 | 34 | 34 | 0 |
| 4608B | grain512 / 0x0 | shear | 200 | 200 | 0 | 840 | 840 | 0 |
| 4608B | grain512 / 0x0 | sbox | 384 | 384 | 0 | 2304 | 2304 | 0 |
| 512B | grain512 / 0x0 | sns | 384 | 384 | 0 | 9008 | 9008 | 0 |
| 512B | grain512 / 0x0 | mod384 | 384 | 384 | 0 | 384 | 384 | 0 |

- 签字 `t2_compare.csv` **336 行**：`rel_err_n_dmc` 与 `rel_err_n_bank` **max = 0.0**；`flag_gt_30pct` 336/336 False。与 committed 表 `diff` 空。
- 4608B **standalone**：S 列字面 `4608B`（48 行，仅 family=grain512，8 base × 6 strategy）；occupancy 48 行 `note=4608B alone`；无 align2MiB 行、未折入 512B/2MiB。SNS 4608B n_DMC 全 384、min/mean=0.7000、rel_diff=0.0000。
- SNS S=2MiB grain 8 base：n_DMC 全 384，`rel_diff=0.0000`；align2MiB 4 base 同。bks/DMC=6-6，`bank%8` kinds=1，maxload=11 minload=10，min/mean=0.9375（base=0）。
- SNS 在全部签字 S 上 grain/align 的 n_DMC REL_DIFF 均为 0.0000。唯一跨 base rel_diff≠0 是 **4608B shear 消融** `200.38 ± 0.52 (n=8) rel_diff=0.0100`（n_DMC 199–201）；每行仍 T3=T2（rel_err=0），不是占用 miss。
- COVERING_BOUND（uniform raw，**非黄金**）：max=11 min=10 CV=0.0442；`summary.json` `"golden": false`。未改 ROM/S-box。S=2MiB SNS 是 12b 置换，fold384 算术上必实现该 covering，不是贴数。
- ABL-sbox S=2MiB，计数恒 1（rel_diff=0），**id 随 grain 相位变**（亲自跑 `occupancy("sbox", …, n=4096)`）：
  - grain: `0x0→(0,) 0x200→(1,) 0x400→(2,) 0x600→(3,) 0xe00→(7,) 0x1e00→(15,) 0x3e00→(63,) 0x7e00→(287,)`
  - align2MiB: 全 `(0,)`（x12 冻 0，与 T2 一致）
  unit test `test_abl_sbox_varies_phase_id_at_2mib` 过。

## T3 BW（H-DRAM-BB 新度量，非 T2 差）

bbox（smoke，`summary.json` 已标明，**不能签信封 0.85**）：**8 cores × 16 outstanding**，AP **256 points**，`map_ports∈{1,4}`，map_lat=1，page=open，`mask∈{full, rand1/16, third}`，warmup 丢前 10% completions，n_trials=3，seed=`20260903+trial`。μ_d UNKNOWN；无 GB/s；0.85 是问题过线不是测得均值。T2 无 BW 列，不把 T2 缺 BW 当 discrepancy。`bw_ci.csv` 60 行全部 `hypothesis=H-DRAM-BB`。

| S | strategy | ports | mask | txns/cycle mean ± 95% CI |
|---|----------|-------|------|--------------------------|
| 2MiB | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 2MiB | mod384 | 1 | full | 0.064953 ± 0.000000 (n=3) |
| 2MiB | sns | 1 | rand1/16 | 0.940068 ± 0.005007 (n=3) |
| 2MiB | sns | 1 | third | 0.745953 ± 0.003168 (n=3) |
| 2MiB | sns | 4 | full | 3.709677 ± 0.000000 (n=3) |
| 1MiB | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 1MiB | mod384 | 1 | full | 0.064953 ± 0.000000 (n=3) |
| 512KiB | sns | 1 | full | 0.843531 ± 0.004032 (n=3) |
| 512KiB | mod384 | 1 | full | 0.064953 ± 0.000000 (n=3) |
| 4608B | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 4608B | mod384 | 1 | full | 0.942623 ± 0.000000 (n=3) |
| 512B | sns | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 512B | mod384 | 1 | full | 1.000000 ± 0.000000 (n=3) |
| 512B | sns | 4 | full | 3.709677 ± 0.000000 (n=3) |

此 bbox 下 S=2MiB/1MiB SNS 打到 1-port mapper 天花板（1.0 txn/cyc），4-port 抬到 ≈3.71；mod384 约 0.065（3 DMC）。**不是**「只赢 min/mean、输绝对值」。S=512B 两侧 full 都是 1.0 / 3.71（port-bound）。`rand1/16` 与 `third` 在签字 CSV 里（不是 night-only）。Refresh 未建模（已标）。cycle 占用 S=2MiB SNS 256 点 n_DMC≈216–217 ≠ occupancy 表的 384，勿混用。4608B 是自己的 BW 行。

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
| 6 | grain vs 2MiB-aligned | PASS（签字 S 分列；4608B 按设计无 align2MiB） |
| 7 | S 集 {2MiB,1MiB,512KiB,4608B,512B}，4608B 单独 | **PASS**（签字 smoke + committed 336 行；重跑 byte-match） |
| 8 | covering 非黄金 | PASS（golden: false；11/10/CV=0.0442） |
| 9 | DRAM 时序标 假设 | PASS（H-DRAM-BB） |
| 10 | warmup | PASS（10%） |
| — | partial-good 1/16 与 1/3 + PE 1-cycle | PASS；**签字 bw_ci 已出这些行**（ports 1/4 亦在） |
| — | inflight 15360 按周期占槽 | occupancy 用 Q_tot；**cycle 驱动是 8×16=128**（已标 reduced-bbox） |

## 代码（亲自重跑）

- pytest: `/workspace/archteam-audit/.venv/bin/python` / `.venv/bin/pytest sims/P-0105/M-4/tests -q`
  - exit **0**；**24 passed**（mapper 6 + microbench 8 + signed_tables 3 + structural 7）；~0.82 s；log `runs/t3-P-0105-M-4-r2-pytest.log`
- smoke: `sweep.py --mode smoke --seed 20260903 --n-trials 3 --out /workspace/archteam-audit/runs/t3-sns-smoke-r2`
  - exit **0**；elapsed **9655 ms**（07:58:16–07:58:26 UTC / 15:58:16–15:58:26 SGT）；log `runs/t3-P-0105-M-4-r2-smoke.log`
  - `t2_compare.csv` / `occupancy.csv` / `bw_ci.csv` / `cycles.csv` / `summary.json` 相对已提交 `sims/P-0105/M-4/results/` **diff 空**
- SEED=20260903；trials `SEED+i`
- 未覆盖写 committed `sims/P-0105/M-4/results/`

## 修复清单

无

## 禁止自检

未改 sim.py / sweep.py / tests / results / spec.md / model.py / 机制卡；未把 reduced-bbox BW 签成信封 0.85；未与 AffineRebind 混结论。
