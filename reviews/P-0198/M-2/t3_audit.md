# T3 audit · P-0198/M-2 CSR（Rendezvous–Grant）

auditor: 评估审计
batch: P-0198 (not Batch A; keep separate from M-1 CBC / M-4 AODI / M-5 CRRF)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 淘汰
PR audited: https://github.com/lukebest/ArchTeam/pull/72 (tip `1990cb7`)
T2 context: reviews/P-0198/M-2/t2_audit.md from PR #68; signed pins T2 draft PR #66 / audit #68

## 判决

亲自重跑 pytest **24 passed**、exit 0；smoke `--mode smoke --seed 20260903 --out runs/t3-csr-smoke-r1` exit 0（~3.5 s CST）。regen 与 committed `sims/P-0198/M-2/results/` 的 occupancy / t2_compare / cycles / alltoall_residual / probes / bw_ci / t2_signed_pins / t2_vs_t3_ratio.png **byte-identical**（`cmp`）；`summary.json` 仅 `occupancy_csv`/`t2_compare_csv` 路径串因 `--out` 不同，数值体一致。未覆盖写 committed results/（mtime 12:03:59 CST 未动）。

结构契约过线：`Dat_beats_held_max≡0`、`retention_depth_max≡0`、`n_cam=4`、`invariant_ok=True` 全 96 occupancy / compare 行；CSR gather `inject_before_grant=0`；gate-off 探针抬至 109 且 r→1.05；FORCE_FALLBACK notify 界（timeout=8 探针 `ff_notify_max=1`、`collect_timeout_fallback=0`）；alltoall TREE/RESIDUAL 分列（`alltoall_residual.csv` 注「勿均值」）；card-claim **NOT measured**；`oracle_used=False` 全 cycles；未与 M-1 CBC / M-4 AODI / M-5 CRRF 混排。

但 **spine-off HARD 诚实失败** 且 **主相对收益 ≈1**：gather/reduce cycle off **192 ≯** CSR **194**（r=**1.0104**）vs T2 签字 HARD True（537.2>289.3 ns）与 gather r=**0.5386**（|rel| 0.876，flag>30%）。allgather r=1.000；allreduce **1.466**；alltoall op-makespan **1.335**（TREE 单列 xfer 可降而残差 p99/op 尾不降）。gate-off ≈1.0469（vs T2 1.0362，rel 1.0%）是唯一接近的进度钉，不能补救归因。high-ost 8-op 波 f_ov=**0.375**（dominates=False）vs T2 a=8 Erlang-B **0.5746→INVALID** — 诚实偏差，T3 数站。

这不是 wiring / 结果造假 / 覆盖不全 / 不可再生的 **退回**：再生一致、测试过、CAM 零占用钉死、提交者 `report.md` 已自述同一 HARD/r≈1 miss。这是 bufferless 环上 **Rendezvous–Grant 脊骨不缩短 last-completion**（fold 口地板 + GRANT 公民税）— 诚实错过 T1 因果/主收益杀线 ⇒ **淘汰**（同型 M-1 CBC / M-4 AODI）。勿开 T4；勿改 sim 贴 T2 0.5386；勿改机制卡。

## 杀线对照（亲自重跑）

| # | T1/T2 杀线 | T3 证据 | 结果 |
|---|------------|---------|------|
| 1 | CAM `Dat_beats≡0` / `retention≡0` / `N_cam=4`（结构） | occ+compare 96/96 `dat_beats_held_max=0`、`retention_depth_max=0`、`n_cam=4`、`invariant_ok=True`；payload_rbrg_reject=0 | **PASS**（结构绿） |
| 2 | spine-off HARD：off makespan **严格差于** CSR-on | gather 192 ≯ 194；reduce 同；allgather 256=256；allreduce 103 ≯ 151；alltoall 147.33 ≯ 196.67；smoke 打印 `False` | **FAIL**（归因杀线） |
| 3 | 相对 r vs T2 gather 0.5386；提交者 T3≈1.010（194/192）；无尾收益 | gather/reduce **1.0104**；flag 30/96；card-claim 未测 | **FAIL**（无收益） |
| 4 | H_inject_gate / FORCE_FALLBACK；gate-off ~1.04 | CSR `inject_before_grant=0`；gate-off r=**1.046875** vs 1.0362（rel 1.0%，flag False）；timeout=8：`ff_notify_max=1`、f_to 路径可观测 | **PASS 探针**（不救 HARD） |
| 5 | high-ost INVALID 路径（T2 a=8 f_ov=0.5746）；T3 可异 — 诚实记录 | 8-op 波 f_ov=**0.375** ov=3 dominates=**False**；|rel| 0.347 flag；**未**把 T2 INVALID 贴到本波 | **PASS 诚实分列**（量化偏差，非伪影） |
| 6 | alltoall TREE/RESIDUAL 分列；禁均值过关 | `alltoall_residual.csv` 12 行 TREE vs RESIDUAL + p50/p90/p99；note 拒折；op r>1 未当 pass | **PASS 分列** |
| 7 | 可再生；无神谕；不混 M-1/M-4/M-5 | `--out` regen ≡ committed；pytest 24；`oracle_used=False`；summary/report 明示勿混 | **非伪影** → 淘汰而非退回 |

## 关键数字（SEED=20260903，n_trials=3）

### 结构 / CAM

- occupancy 96 行：`dat_beats_held_max` min=max=**0**；`retention_depth_max`≡0；`n_cam=4`；`invariant_ok=True`。
- CSR gather trial0：`grant_emits=2`、`inject_before_grant=0`、`cam_overflow_fallback=0`、`collect_timeout_fallback=0`、`f_grant=1`、`oracle_used=False`、`fold_orbits=56`（spine-off 同 class 更高 orbit，不缩短尾）。
- live_cam_max：默认 gather=1；overflow 探针另行使满 4（unit/structural）。

### H-FANIN / T2 vs T3（ost=256 类均值；三 trial）

| Pin | T2 signed (#68) | T3 smoke | \|T3−T2\|/T2 | flag>30% |
|-----|-----------------|----------|--------------|----------|
| CAM Dat / retention / N_cam | 0 / 0 / 4 | **0 / 0 / 4** | 0 | no |
| gather r | 0.5386 | **1.0104** (194/192) | 0.876 | **yes** |
| reduce r | 0.5386 | **1.0104** | 0.876 | **yes** |
| allgather r | 0.5386 | **1.0000** (256/256) | 0.857 | **yes** |
| allreduce r | 0.5386 | **1.4660** (151/103) | 1.722 | **yes** |
| alltoall op r (vs TREE 0.6932) | 0.6932 | **1.3348** | 0.91 | **yes** |
| alltoall RESIDUAL | 1.0 单列 | residual 仍 RING_P2P（分列） | — | 残差列 |
| gate-off r | 1.0362 | **1.046875** | 0.010 | no |
| high-ost f_ov | 0.5746 → INVALID | **0.375** dominates=False | 0.347 | **yes** (quant) |
| spine-off HARD | True (537.2>289.3 ns) | cycle **192 ≯ 194** | n/a | inequality **fails** |
| card-claim | NOT signed | **NOT measured** | — | 仅印刷 |

`t2_compare.csv`：**30/96** `flag_gt_30pct=True`。T3 未替换为 T2。

### Makespan / HARD（ost=256；ost=512 同类钉死）

| class | spine-off | CSR | CSR/off | HARD (off>on) |
|-------|-----------|-----|---------|---------------|
| gather / reduce | 192.00 ± 0 | 194.00 ± 0 | **1.010** | **False** |
| allgather | 256.00 ± 0 | 256.00 ± 0 | 1.000 | False |
| allreduce | 103.00 ± 0 | 151.00 ± 0 | **1.466** | False |
| alltoall | 147.33 ± 4.71 | 196.67 ± 8.34 | **1.335** | False |
| broadcast | 102.00 ± 0 | 104.00 ± 0 | 1.020 | False |
| uniform_read/write | 65.33 ± 7.53 | 65.33 ± 7.53 | 1.000 | False（中性） |

### alltoall TREE vs RESIDUAL（trial 0, ost=256）— 勿均值

| arm | TREE ms / n | RESIDUAL ms / n | p50 / p90 / p99 |
|-----|-------------|-----------------|-----------------|
| spine-off | 96 / 24 | 83 / 48 | 24 / 54 / 83 |
| CSR | 38 / 24 | 117 / 48 | 22 / 65 / 117 |

TREE 单 xfer 可变好；op makespan 与 residual 尾变差。mix 非过关数。

### 探针

| probe | T3 | T2 | note |
|-------|----|----|------|
| gate-off | r=1.046875；inject_before_grant=109 | 1.0362 | 回到 ~1；H_inject_gate 可观测 |
| high-ost-8ops | f_ov=0.375；ov=3；dominates=False | 0.5746 INVALID | T3 离散波站；不贴 INVALID |
| timeout=8 | collect_timeout_fallback=0；ff_notify_max=1 | late-fraction 假设 | 默认 COLLECT 刷新；非热路径 |

## 相对 T2（#68）

T2 解析签字：CAM 零、N_cam=4、HARD True、gather r=0.5386、gate-off≈1.036、a=8 INVALID、alltoall TREE/RES/mix 分列、card-claim 未签测得。T3 cycle **保留**结构不变式与 gate/FF 探针方向，**推翻** HARD 与 gather-family 相对收益（1.01 vs 0.5386），并暴露 allreduce/alltoall 负增益。单位不同（ns 解析 vs cycle last-completion）不豁免「spine-off 须严格更差」的归因不等式；cycle 级主杀线失败。

提交者 `sims/P-0198/M-2/report.md` 已诚实写清同一偏差（fold 口地板 + GRANT 税；H-FANIN-BOUND 非本 bbox 瓶颈）— 审计同意该模型发现，**不**据此改判为通过（结构绿 ≠ 收益绿；同 M-1/M-4）。

## 代码（亲自重跑）

- pytest: `/workspace/archteam-p198-m2-t3/.venv/bin/python -m pytest sims/P-0198/M-2/tests -q`
  - exit **0**；**24 passed**（invariants 6 + microbench 6 + signed_tables 3 + structural 9）；~0.55 s；log `runs/t3-P-0198-M-2-r1-pytest.log`
- smoke: `.venv/bin/python sims/P-0198/M-2/sweep.py --mode smoke --seed 20260903 --out runs/t3-csr-smoke-r1`
  - exit **0**；~3463 ms（12:04:35–12:04:38 CST）；log `runs/t3-P-0198-M-2-r1-smoke.log`
  - `--out` **supported**；未覆盖 committed `sims/P-0198/M-2/results/`
  - CSV/PNG vs committed：`cmp` 空；`summary.json` 仅 out 路径字段差
- deps：venv `simpy` + `matplotlib` + `pytest`
- SEED=20260903；trials `SEED+i`（20260903/04/05）
- 未改 `sim.py` / `sweep.py` / `tests` / `results` / `models/` / `mechanisms/` / `problems/` / `FUNNEL.md`
- 本文件为本地 audit 仅写 `reviews/P-0198/M-2/t3_audit.md`；未开 GitHub PR

## 修复清单

无（淘汰，不退回修代码）。若架构侧重开：须改变 **机制**（使 Rendezvous–Grant 真正缩短 last-completion——例如更宽 fold/多 GRANT 窗且基线可证 livelock，或另一 bbox 上 HARD 严格 `<` 且 r≪1），而非改 sim 贴 T2 `0.5386`。本审计不修卡、不开 T4。

## 禁止自检

未改 sim/spec/机制卡/models/problems/FUNNEL；未把 reduced-bbox / card-claim 签成信封 0.85 或测得 pass；未与 Batch A / M-1 CBC / M-4 AODI / M-5 CRRF 混排名；未开 GitHub 审计 PR。
