# T2 audit · P-0198/M-1 CBC

auditor: 评估审计
batch: P-0198 (not Batch A)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 通过
PR audited: https://github.com/lukebest/ArchTeam/pull/54 (draft; tip `1690835`)

## 判决

诚实重跑 `python3 models/P-0198/M-1/model.py` → exit 0；无写盘产物。空槽守恒精确、`delta_rho_empty=0` 按构造不 mint；主收益列为相对 `T_hat/T_off`（H-INJ-DOM，仅已坍集合）与消融/双租户/灵敏度探针，无绝对 TB/s 冒充测得。calendar-off 消融存在且 HARD-1 探针 True。双租户在默认假设下 `T_B_dual/T_B_solo=1.33/2.0`，`fail_T=True`，明确超出 Sys <10%。`0.55–0.85×` 仅作 `card-claim` 列且 stdout 标注 NOT measured。stdlib-only、确定性、无网络。README 将本卡与 Batch A 分列。过线。

**明确不签：** 卡宣称 `0.55–0.85×` 不是本审计签字的测得信封。机制卡正文仍在 PR #44 tip、**未入 main**（本树无 `mechanisms/P-0198/`）；结论边界 = T1(#52 on main) + 本解析模型对 #44 tip 摘录的守恒/相对界，**不**把机制卡当已着陆正文。

## 重跑证据

- 命令: `cd /workspace/archteam-p198 && python3 models/P-0198/M-1/model.py`
- 退出码: **0**
- 写盘: 无（仅 stdout；`models/P-0198/M-1/` 仍仅 `spec.md` / `model.py` / `insight.md`）
- 关键数字行（亲自重跑，CST 2026-09-30）:

```
H-RHO rho_empty=0.2
H-PLACE eta0=0.35 eta=0.85
CONSTRAINT: CBC does not mint empty; delta_rho_empty=0 by construction
gather ... d=0.2500 ... T_hat/T_off=0.7368  card-claim 0.55-0.85x
gather ... d=0.5000 ... T_hat/T_off=0.5833  card-claim 0.55-0.85x
           amdahl ... (card-claim column is NOT measured)
HARD-1 probe: calendar-off T_hat (537.2) > CBC T_hat (313.4)? True
d_A=0.2500  T_B_dual/T_B_solo=1.3333  fail_T=True fail_G=False
d_A=0.5000  T_B_dual/T_B_solo=2.0000  fail_T=True fail_G=False
at d=1/2 default assumptions: T_hat/T_off=0.5833 in card-claim[0.55,0.85]? True
done
```

## 对拍表（T1 kill-line ↔ model probe）

| # | T1 条件 / kill-line | 模型探针 | 结果 |
|---|---|---|---|
| 1 | Archi **H-CBC-empty-supply**：calendar-on 不得 mint empty；ρ_empty 提升&lt;5% 且 inject-success&lt;10% ⇒ 因果失败 | `partition_empty`；每 d 打印 `delta_vs_off=0.0000`；CONSTRAINT 句 | PASS（Δρ_empty=0 by construction；收益只许再分配） |
| 2 | Bench/Sim：分流量类；calendar-off 须使已坍集合变差；P2P duty≤1/8 不得再掉一个数量级进 2.8–3.4 TB/s；固定高 duty 单列 | PER-CLASS 分列；ABLATION calendar-off / duty=0 / CBC-coll / fixed-high；P2P GOODPUT SIDE-EFFECT | PASS（HARD-1 True；P2P d≤1/8 下 G_hat 仅轻度下降、`flag_collapse_band=False`；模型自承线性 keep 解释不了 YAML 数量级崩塌） |
| 3 | Sys 双租户：A 高 duty 不得把 B 恶化 ≥10% 或压进崩塌带 | DUAL-TENANT `fail_T` / `fail_G` | PASS 探针（`fail_T=True` 于 d_A∈{1/4,1/2}；支持「不能当整机默认织物」警告，非宣称 Sys 过关） |
| 4 | Sim：无消息级到达神谕；epoch 为静态类 schedule；禁只报注入成功率代理 makespan | 无到达序列/神谕输入；duty 为静态臂；端点为相对 T 与 p_inj 分列 | PASS |
| 5 | Archi：日历端口等 cycle 级项不得用平均 ρ 冒充测得 | spec §4 / insight 明确 FSM×环 out of scope | PASS（边界声明；非替代 cycle） |

## 收益阀门

- 主结果 = **相对** `T_hat/T_off`（H-INJ-DOM，仅 `INJ_DOM` 集合类）+ Amdahl 伴列 + p_inj / C_eff；均匀读/写与 broadcast 打印 `T_hat=n/a`。
- `0.85` 开篇钉为及格线/约束条，非均值；`card-claim` 列显式非测得。
- 无 H100 / team-384dmc / decode-* / 硅 ±15%。
- 阈值判定: **过线**（守恒 + 相对探针 + 标签诚实）；**不**把默认假设下落入 0.55–0.85 的比值当信封签字。

## 魔法缺口 / 无神谕

| CLAIM / 风险 | 模型可解释 | 缺口 |
|---|---|---|
| 「制造并循环空槽」 | 否定 mint；Δρ_empty=0；气泡=tag 再分配 | 若 cycle 测得 ρ_empty≈0 且 steal 无抬升 → 降级优先级准入（insight 已写） |
| 已坍类 0.55–0.85× | 默认 η/η0 下纯 H-INJ-DOM ≈0.74/0.58 落入区间；η→η0 时比→~1 | 区间依赖 H-PLACE；**不签为测得**；Amdahl 更保守 (~0.82/~0.71) |
| 均匀读峰值后数量级崩塌 | κ_keep 线性项仅轻度压 G_hat | 动力学崩塌不在本解析内（已标） |
| RBRG 对侧气泡 | 未建模 | Sys 盲点保留 |
| 到达神谕 | 无 | 无神谕路径 |

缺口过大?: **否** — 卡区间未当输入校准；魔法缺口与双租户失败已写清。

## 空槽守恒 / no mint（专项）

- `ρ_raw+ρ_bubble=ρ_empty` 全 d 扫描 `sum_ok=True`。
- 日历只标 eligible empty；不提高 `ρ_empty`。
- 与 Archi H-CBC-empty-supply 解析形式一致。

## spec ↔ model ↔ insight

- 守恒、partition、H-INJ-DOM、Amdahl、消融、双租户、灵敏度均在代码中出现；insight 数字 `0.74/0.58`、`1.33/2.0`、Amdahl ~0.82/0.71 与重跑一致。
- **非阻塞笔误：** spec §3.4 短写 `p_inj_cbc=ρ_empty·((1−d)+d·η)` 省略 raw 份额上的 η0；model 用更紧的 `((1−d)·η0 + d·η·λ_age)`，与 §3.3 叙述及 insight 一致。不构成退回。
- Scope: tip commit 仅 `models/P-0198/M-1/{spec,model,insight}` + `models/README.md`；未改 `mechanisms/` / `reviews/` / `problems/` / `FUNNEL` / 旧 `models/P-010*`。README：**New card. Not mixed with Batch A ranking.**

## 代码（亲自重跑）

- 与 spec 一致 / 无网络 fetch / 无 numpy 等 / 假设具名 / 灵敏度两对: PASS
- 问题: 无（不修代码）。线性 P2P keep 与「数量级崩塌」之间的缺口已在 insight 标明，留给 T3/`tests/soc_sim`。

## 准则

- 第一性原理（守恒精确；相对缩放假设具名） / CLAIM 与模型输出分列 / 未填硅: PASS

## 修复清单

无（不修代码）。建议（非退回条件）：后续若改 spec，把 §3.4 的 `p_inj_cbc` 与 model 的 η0 形式对齐，避免读者用短写复算得到更乐观比值。

## 禁止自检

未改 spec/model/机制卡/problems/FUNNEL；未与 Batch A 混排名；未把 `0.55–0.85×` 或未签字数字当周报；未开 GitHub PR（本文件为本地 audit draft，供父代理另开 audit-only PR）。
