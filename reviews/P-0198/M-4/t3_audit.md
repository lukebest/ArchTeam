# T3 audit · P-0198/M-4 AODI

auditor: 评估审计
batch: P-0198 (not Batch A; keep separate from M-1 CBC / M-2 CSR / M-5 CRRF)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 淘汰
PR audited: https://github.com/lukebest/ArchTeam/pull/70 (tip `74960d9`)
T2 context: reviews/P-0198/M-4/t2_audit.md from PR #69; signed pins T2 PR #65 / audit #69

## 判决

亲自重跑 pytest **25 passed**、exit 0；smoke `--mode smoke --seed 20260903 --out runs/t3-aodi-smoke-r1` exit 0（~1.0 s CST）。regen 与 committed `sims/P-0198/M-4/results/` 的 occupancy / t2_compare / t2_signed_pins / cycles / holes / bw_ci / pngs **byte-identical**（`cmp`）；`summary.json` 仅 `occupancy_csv`/`t2_compare_csv` 路径串因 `--out` 不同，数值体一致。未覆盖写 committed results/（mtime 11:58:06 CST 未动）。

结构契约过线：`hole_dual≡0` 全 54 holes 行 + 全 occupancy/cycles/compare 行；强制 dual-busy-sat 探针 288 双忙周期、`hole_asym=hole_dual=deflect=0`、无注入；φ=`t2_phi_walk` →0、`age_end=1`（非 Σage）；hole 桶分 `asymmetric/mixed` vs `dual-busy`；alltoall 单独行（`alltoall_separate=True`），未折进 0.50–0.85×；card-claim **NOT measured**；无到达神谕（sim 无 `oracle_used`；`illegal_third=0`/`dropped=0`）；未与 M-1/M-2/M-5 混排。

但 **主不对称类 makespan 归因诚实失败**：gather/reduce `T_mix=1.0000`（34/34）vs T2 签字 **0.8448**（rel 0.184，flag>30% 未触发但 **无 makespan 收益**）；`hole_asym=43` 抬 `p_inj` 0.300→0.356 而尾延迟不变 ⇒ H-INJ-DOM 相对赢 **不可实现为 cycle 尾**。deflect-off HARD 在声称受益类上 gather/reduce/broadcast/allreduce 为 True（等号），但 P2P/allgather/alltoall **False**（尾回归）。alltoall 自有行 T3 `T_mix` **1.529 / 1.105 / 1.294**（负增益），诚实未折入 0.95–1.05× 测得。`t2_compare` **8/24** `flag_gt_30pct=True`；T3 数站，未贴 T2。

这不是 wiring / 结果造假 / 覆盖不全 / 不可再生的 **退回**：再生一致、测试过、双忙洞钉死、报告已自述。这是 bufferless 环上 **不对称 inject-hole 不缩短 last-completion** — 诚实错过 T1 因果/主收益杀线 ⇒ **淘汰**。勿开 T4；勿改 sim 贴 T2 数；勿改机制卡。

## 杀线对照（亲自重跑）

| # | T1/T2 杀线 | T3 证据 | 结果 |
|---|------------|---------|------|
| 1 | `hole_dual≡0` 全行 + 强制 dual-busy 探针 0 | holes 54/54 `hole_dual=0`；forced `dual-busy-sat` 两臂 `hole_asym=hole_dual=deflect=0`，288 dual-busy cycles，`inject_ok=0` | **PASS**（硅契约 cycle 真） |
| 2 | φ 逐包 →0，`age_end≠progress`（非 Σage） | `t2_phi_walk(6,1,8,rejoin)` → φ=0、`age_end=1`、freeze=False；sweep 硬断言过；unit `test_phi_walk_is_not_sum_age` | **PASS** |
| 3 | Hole 桶不对称 vs 双忙 | holes `bucket∈{asymmetric/mixed, dual-busy}`；alltoall/`dual-busy-sat`→dual-busy；gather 等→asymmetric/mixed | **PASS** |
| 4 | alltoall 双忙增益≈0 **自有行**；不得折进 0.50–0.85×；T3 可 >1 | 类行 trial0/1/2 `T_mix=1.529/1.105/1.294`，`alltoall_separate=True`；forced 探针增益≡0；pins/note 拒折 | **PASS 分列**（类行负增益诚实；非伪影） |
| 5 | deflect-off HARD：声称受益类 off T ≥ on T | gather/reduce/broadcast/allreduce：**True**（34≥34 / 41≥41 / 23≥23）；uniform_read/write、allgather、alltoall：**False**（尾回归） | **部分 FAIL**（归因仅等号类；回归类否决「普遍受益」） |
| 6 | H-INJ-DOM / `T_mix` vs T2 0.8448：gather/reduce 无 makespan 改进则归因失败 | gather/reduce T3 `T_mix=1.0000`；`hole_asym=43`；makespan 34=34 | **FAIL**（主不对称收益杀线） |
| 7 | 结果可再生产；无神谕；不混 M-1/M-2/M-5 | `--out` regen ≡ committed；pytest 25；summary siblings 明示勿混；无 oracle | **非伪影** → 淘汰而非退回 |

## 关键数字（SEED=20260903，n_trials=3）

### 结构 / dual-busy

- `hole_dual` min=max=sum=**0**（holes 54、occ 48、cycles 54、compare 24）。
- Forced dual-busy-sat：两臂 `completed=0`、`p_inj=0`、`deflect=0`、`hole_*=0`、`dual_busy_cycles=288`。
- `illegal_third=0`、`dropped=0` 全 cycles 行；无第三槽。

### φ

- 签字走步：`age_end=1`，φ 序列降至 0；注释钉 **NOT Σage**。
- cycle 有 `phi_freeze` 计数（如 alltoall AODI-on trial0=48）— 错向等待，非进度证明。

### H-INJ-DOM / T2 vs T3（trial 0 代表；gather/reduce 三 trial 同）

| Pin | T2 signed | T3 smoke | \|T3−T2\|/T2 | flag>30% |
|-----|-----------|----------|--------------|----------|
| hole_dual | 0 | **0** | 0 | no |
| φ age_end | 1 | **1** | 0 | no |
| gather T_mix | 0.8448 | **1.0000** | 0.184 | no |
| reduce T_mix | 0.8448 | **1.0000** | 0.184 | no |
| alltoall T_mix | 1.0 | **1.529 / 1.105 / 1.294** | 0.53 / 0.11 / 0.29 | **yes** (t0) |
| allgather T_mix | 0.8223 | **1.24** (all trials) | 0.508 | **yes** |
| uniform_read T_mix | 0.877 | 1.105 / 1.471 / 1.923 | 0.26 / 0.68 / 1.19 | **yes** (t1–2) |
| deflect-off HARD | True | 受益声称类等号 True；P2P/allgather/alltoall False | — | HARD 不全 |
| card-claim | 0.70–0.95× / 0.95–1.05× | **NOT measured** | — | 仅印刷 |

`t2_compare.csv`：**8/24** `flag_gt_30pct=True`（allgather×3、alltoall×1、uniform_read×2、uniform_write×2）。T3 未替换为 T2。

### Makespan / HARD（AGE_MAX=8）

| class | deflect-off | AODI-on | HARD (off≥on) | hole_asym (AODI t0) |
|-------|-------------|---------|---------------|---------------------|
| gather / reduce | 34.00 ± 0 | 34.00 ± 0 | **True**（无改进） | 43 |
| broadcast | 41.00 ± 0 | 41.00 ± 0 | True | 0 |
| allreduce | 23.00 ± 0 | 23.00 ± 0 | True | 17 |
| allgather | 25.00 ± 0 | 31.00 ± 0 | **False** | 24 |
| alltoall（单独） | 17.67 ± 1.31 | 23.00 ± 2.99 | **False** | 12–15 |
| uniform_read/write | 16.33 ± 3.46 | 23.67 ± 2.61 | **False** | 16–26 |
| dual-busy-sat（强制） | 1 / p_inj=0 | 1 / p_inj=0 | True（无洞） | 0 |

gather：`p_inj` 0.300469 → 0.355556，但 makespan 钉 34 — 注入机会≠尾完成。

### alltoall 负增益（诚实）

| trial | off ms | on ms | T3 T_mix | T2 | separate |
|-------|--------|-------|----------|-----|----------|
| 0 | 17 | 26 | 1.529 | 1.0 | True |
| 1 | 19 | 21 | 1.105 | 1.0 | True |
| 2 | 17 | 22 | 1.294 | 1.0 | True |

残留单侧空仍触发 `hole_asym`；AODI 迁载对向（`ρ_opp` 0→0.06–0.08），尾变差。强制双忙探针才是「增益≈0」原子 — 与流量类 alltoall **分列**。

## 相对 T2（#69）

T2 解析签字：`hole_dual≡0`、φ、deflect-off HARD True、alltoall 单独 `T_mix=1`、gather `T_mix=0.8448` 落入 card 带但标非测得。T3 cycle **保留**双忙洞与 φ 契约，**推翻**不对称类相对 makespan 收益（1.0 vs 0.8448）并暴露 alltoall/P2P 尾回归。单位不同（解析混合比 vs last-completion）不豁免「声称受益类应缩短尾」的归因；cycle 级主杀线失败。

提交者 `sims/P-0198/M-4/report.md` 已诚实写清同一偏差 — 审计同意该模型发现，**不**据此改判为通过（与 M-1 CBC 同型：结构绿 ≠ 收益绿）。

## 代码（亲自重跑）

- pytest: `/workspace/archteam-p198-t3/.venv/bin/python -m pytest sims/P-0198/M-4/tests -q`
  - exit **0**；**25 passed**（microbench 7 + signed_tables 5 + structural 13）；~0.06–0.3 s；log `runs/t3-P-0198-M-4-r1-pytest.log`
- smoke: `.venv/bin/python sims/P-0198/M-4/sweep.py --mode smoke --seed 20260903 --out runs/t3-aodi-smoke-r1`
  - exit **0**；~1.0 s（11:58:23 CST 写出）；log `runs/t3-P-0198-M-4-r1-smoke.log`
  - `--out` **supported**；未覆盖 committed `sims/P-0198/M-4/results/`
  - CSV/PNG vs committed：`cmp` 空；`summary.json` 仅 out 路径字段差
- deps：既有 venv `simpy==4.1.2` + `matplotlib` + `pytest`
- SEED=20260903；trials `SEED+i`（20260903/04/05）
- 未改 `sim.py` / `sweep.py` / `tests` / `results` / `models/` / `mechanisms/` / `problems/` / `FUNNEL.md`
- 本文件为本地 audit 仅写 `reviews/P-0198/M-4/t3_audit.md`；未开 GitHub PR

## 修复清单

无（淘汰，不退回修代码）。若架构侧重开：须改变 **机制**（使 inject-hole 真正缩短 last-completion，或拒绝 deflect 近目的地 victim；或证明另一 bbox 上 HARD 严格 `<` 且 `T_mix<1`），而非改 sim 贴 T2 `0.8448`。本审计不修卡、不开 T4。

## 禁止自检

未改 sim/spec/机制卡/models/problems/FUNNEL；未把 reduced-bbox 签成信封 0.85；未签 card-claim 为测得；未与 Batch A / M-1 CBC / M-2 CSR / M-5 CRRF 混排名；未开 GitHub 审计 PR。
