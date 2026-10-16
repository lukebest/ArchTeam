# T3 audit · P-0198/M-1 CBC

auditor: 评估审计
batch: P-0198 (not Batch A)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 淘汰
PR audited: https://github.com/lukebest/ArchTeam/pull/62 (tip `1349297`)
T2 context: reviews/P-0198/M-1/t2_audit.md from PR #56; signed pins T2 PR #54 / audit #56

## 判决

亲自重跑 pytest **31 passed**、exit 0；smoke `--mode smoke --seed 20260903 --out runs/t3-cbc-smoke-r1` exit 0（~2.8 s CST）。regen 与 committed `sims/P-0198/M-1/results/` 的 occupancy / t2_compare / cycles / inject / dual_tenant / bw_ci / t2_signed_pins / pngs **byte-identical**（`cmp`）；`summary.json` 仅 `occupancy_csv`/`t2_compare_csv` 路径串因 `--out` 不同，数值体一致。未覆盖写 committed results/（mtime 11:42:40 CST 未动）。

守恒过线：`sum_ok=True` 全 168 行，`Δρ_empty=0`。FSM/日历/steal 有动作（CBC 臂 emit>0、steal 随 duty 升），**无**到达神谕（`oracle_used=False`）、无 mint。但 **HARD-1 诚实失败**：gather calendar-off makespan **34 ≯ 34** CBC；全部 8 流量类 × 7 臂 makespan 与 `p_inj` **逐类恒等**；H-INJ-DOM T3 相对比 **1.0000** vs T2 签字 0.7368 / 0.5833（|rel| 0.357 / 0.714，flag>30%）。双租户 `fail_T=True`（Sys 洞确认）不能补救单租户归因。card-claim 0.55–0.85× **未测**。

这不是 wiring / 结果造假 / 覆盖不全的 **退回**：再生一致、测试过、气泡在发、steal 在涨而 `steal+raw` 钉死。这是 bufferless 环上 **H-PLACE / 注入收益在 cycle 级不成立** — 诚实错过 T1 因果/杀线 ⇒ **淘汰**。勿开 T4；勿改 sim 贴 T2 数。

## 杀线对照（亲自重跑）

| # | T1/T2 杀线 | T3 证据 | 结果 |
|---|------------|---------|------|
| 1 | 空槽守恒 / no mint：`sum_ok`，`Δρ_empty=0` | occ 168/168 `sum_ok=True`；`delta_rho_empty` min=max=0；gather trial0 全臂 `ρ_empty=0.746429` | **PASS**（再分配，不 mint） |
| 2 | H-INJ-DOM 相对 `T_hat/T_off` vs T2 0.7368 (d=1/4)、0.5833 (d=1/2)；\|rel\|>30% 必标 | gather/reduce/allgather/allreduce/alltoall 上 CBC-coll T3 比 **全 1.0000**；rel 0.357 / 0.714；`t2_compare` **105/168** `flag_gt_30pct=True` | **FAIL**（诚实偏差，T3 数站） |
| 3 | HARD-1：calendar-off makespan **严格差于** CBC | gather off=34 vs CBC-coll-1/2=34；allgather 25=25；allreduce 23=23；reduce 34=34；alltoall 15.67=15.67；smoke 打印 `False` | **FAIL**（归因杀线） |
| 4 | Dual-tenant Sys：`fail_T` 方向 | 6/6 行 `fail_T=True`（与 T2 同向）；ms_B dual/solo ≈2.59 / 3.31 / 3.00；d_A=1/4 与 1/2 **同** dual 比（bbox 已饱和） | **PASS 探针**（Sys 不能默认；不救 HARD-1） |
| 5 | 无到达神谕 / 无 magic gap 贴数 | `cycles.csv` `oracle_used=False`；日历静态行；card-claim `NOT measured`；未签信封 0.85 / TB/s | **PASS** |
| 6 | 结果可再生产 / 非伪影 | `--out` regen ≡ committed 表；pytest 31；emit 随 duty 升而 p_inj/makespan 不变 | **非伪影** → 淘汰而非退回 |

## 关键数字（SEED=20260903，n_trials=3）

### 守恒 / no-mint

- gather trial 0，七臂：`ρ_empty=0.746429`，`Δρ_empty=0`，`sum_ok=True`。
- bubble 仅 CBC 臂非零（0.107–0.237）；calendar-off / duty=0 的 `ρ_bubble=0`。
- inject gather trial0：`steal+raw=64` 全臂恒定；steal 0/15/30/32/28… 随 duty 升，**再分配** raw↔steal，不抬 `p_inj`（全臂 `p_inj=0.300469`，fail=149）。

### H-INJ-DOM / T2 vs T3

| Pin | T2 signed | T3 smoke | \|T3−T2\|/T2 | flag>30% |
|-----|-----------|----------|--------------|----------|
| sum_ok | True | True（168 行） | 0 | no |
| H-INJ-DOM d=1/4 | 0.7368 | **1.0000** | 0.357 | **yes** |
| H-INJ-DOM d=1/2 | 0.5833 | **1.0000** | 0.714 | **yes** |
| HARD-1 | 537.2 > 313.4 (ns) | cycle **34 ≯ 34** | n/a | inequality **fails** |
| dual d_A=1/4 | 1.3333 fail_T | ms 2.59 fail_T=True；p_inj ratio 0.85 | quant flag | fail_T agrees |
| dual d_A=1/2 | 2.0000 fail_T | ms 2.59 fail_T=True；p_inj ratio 0.85 | quant flag | fail_T agrees |
| card-claim | 0.55–0.85× | **NOT measured**（T3 gather 比=1.00） | — | 仅印刷 |

### HARD-1 / 臂恒等

全部流量类在七臂上 **makespan 与 p_inj 均值完全相同**（含 calendar-off）：

| class | makespan (all arms) | p_inj (all arms) |
|-------|---------------------|------------------|
| gather / reduce | 34.00 ± 0.00 | 0.300469 |
| allgather | 25.00 ± 0.00 | 0.488550 |
| allreduce | 23.00 ± 0.00 | 0.460432 |
| alltoall | 15.67 ± 0.65 | 0.475348 |
| broadcast | 41.00 ± 0.00 | 1.000000 |
| uniform_read / write | 16.33 ± 3.46 | 0.506730 |

### Dual-tenant（Sys）

| trial | d_A | ms_B dual/solo | pinj solo/dual | fail_T |
|-------|-----|----------------|----------------|--------|
| 0 | 1/4 & 1/2 | 44/17 = 2.59 | 0.85 | True |
| 1 | both | 43/13 = 3.31 | 0.65 | True |
| 2 | both | 45/15 = 3.00 | 0.77 | True |

### 机制读数（非贴数）

- `_arbitrate`：`empty` **与** `bubble` 皆可注入；标签只改 steal vs raw 计数，不创造新空槽。
- CBC 臂 `emit`>0（gather trial0：34/66/63/68），calendar-off `emit=0` — FSM/日历在动。
- 故 T2 `η>η0`（H-PLACE）在本 bufferless 环 **cycle 不可实现**；提交者 `report.md` 已写清，审计同意该模型发现，**不**据此改判为通过。

## 相对 T2（#56）

T2 在解析模型上签字：守恒、HARD-1 True（ns）、H-INJ-DOM 0.74/0.58、dual fail_T。T3 cycle 保留守恒与 dual 定性，**推翻** HARD-1 与 H-INJ-DOM 相对收益。单位不同（ns vs cycle）不豁免不等式方向；cycle 级归因失败。

## 代码（亲自重跑）

- pytest: `/workspace/archteam-p198-t3/.venv/bin/python -m pytest sims/P-0198/M-1/tests -q`
  - exit **0**；**31 passed**（microbench 10 + signed_tables 6 + structural 15）；~0.12–0.3 s；log `runs/t3-P-0198-M-1-r1-pytest.log`
- smoke: `.venv/bin/python sims/P-0198/M-1/sweep.py --mode smoke --seed 20260903 --out runs/t3-cbc-smoke-r1`
  - exit **0**；~2.8 s（11:43:16–11:43:18 CST）；log `runs/t3-P-0198-M-1-r1-smoke.log`
  - `--out` **supported**；未覆盖 committed `sims/P-0198/M-1/results/`
  - CSV/PNG vs committed：`cmp` 空；`summary.json` 仅 out 路径字段差
- deps：venv 需 `simpy` + `matplotlib`（缺 matplotlib 时 sweep 在写完 CSV 后于 plot 处失败；本轮已装齐后 exit 0）
- SEED=20260903；trials `SEED+i`
- 未改 `sim.py` / `sweep.py` / `tests` / `results` / `models/` / `mechanisms/` / `problems/` / `FUNNEL.md`

## 修复清单

无（淘汰，不退回修代码）。若架构侧重开：须改变 **机制**（使 empty 与 bubble 注入机会不等价，或证明另一 bbox 上 HARD-1 严格成立），而非改 sim 贴 T2。本审计不修卡。

## 禁止自检

未改 sim/spec/机制卡/models/problems/FUNNEL；未把 reduced-bbox 签成信封 0.85；未签 card-claim；未与 Batch A / SNS / Affine 混排名；未开 GitHub PR（本文件为本地 audit draft）。
