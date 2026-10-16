# T2 audit · P-0198/M-4 AODI

auditor: 评估审计
batch: P-0198-new (not Batch A; not mixed with M-1 CBC / M-2 CSR / M-5 CRRF)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 通过
PR: https://github.com/lukebest/ArchTeam/pull/65 (head a69c0b0; draft; audit is local-only)

## 判决

诚实重跑 `python3 models/P-0198/M-4/model.py` exit **0**。2×2 槽守恒真值表钉死双忙 `inject-hole≡0`（断言 PASS；`SUM hole_dual=0.0000`）；φ 走步为逐包剩余首选向跳，明确非 Σage；deflect-off 消融分列且不对称类回退；hole 分不对称/双忙桶；alltoall 双忙饱和 **单独行** `T_mix=1.0000` / 增益≈0，未折进 0.50–0.85× 或 0.70–0.95×；分流量类、card-claim 列标非测得；无硅 ±15%；stdlib-only；结论未与 M-1/M-2/M-5 混排。信封 DV200 `tests/soc_sim` / bufferless-ring-noc；T1 #61；机制 #53 tip。PR #65 仅触 `models/P-0198/M-4/{spec,model,insight}` + `models/README.md` 索引，未改 `mechanisms/`/`reviews/`/`problems/`/`FUNNEL.md`/`models/P-010*`。过线。

## 收益阈值

- 合格线: 问题 0.85 是 pass bar（CONSTRAINT），**不是**测得均值；主结果=相对 makespan `T_mix` / 分桶 hole；禁止类间平均过关
- 重跑关键数（引自 runs/P-0198-M-4.log，勿编造）:
  - exit 0；stdlib `math`+`sys`；无 RNG
  - 双忙 hole: `SUM hole_dual across classes = 0.0000`；`assert dual-busy hole≡0: PASS`
  - φ: `phi reached 0? True age_end=1 (Σage would be 1, which does not measure arrival)`；`probe: preferred forever full ⇒ phi freeze=True`
  - alltoall 单独行: `regime=dual-busy-sat` `T_mix=1.0000` `hole_asym=0.0000 hole_dual=0.0000` `expected gain≈0 ? True`；`DO NOT fold into 0.50-0.85x`
  - deflect-off: `HARD probe: deflect-off T >= AODI-on T on asymmetric classes? True`；alltoall 两臂皆 `T_mix=1.0000`
  - 默认不对称/混合 `T_mix`（模型相对，非测得）: uniform_read 0.8770 / uniform_write 0.8999 / broadcast 0.9927 / gather=reduce 0.8448 / allgather 0.8223 / allreduce 0.8425
  - gather `T_inj=0.6257`（纯注入过誉，低于卡下沿）；`T_mix=0.8448` 落入 card-claim[0.70,0.95] 且列标 **NOT measured**
- T1 必须带进 T2 的条件（tier1_synthesis；逐条）:
  1. 双忙周期 `inject-hole==0`；违例=机制失败: **PASS**（硬断言 + 分桶和=0）
  2. deflect-off 分列；对向 util + completions；分桶 hole（不对称 vs 双忙）: **PASS**（消融表含 opp_util/C_time；禁 inject-success-only 已打印）
  3. 逐包 φ 有界下降；首选向满时不得假装闭合: **PASS**（走步非 Σage；freeze 旗诚实标出）
  4. alltoall 双忙饱和单独成行，不得用聚合宣称 0.50–0.85×: **PASS**
- 阈值判定: **过线**（相对；绝对 makespan 仅 H-INJ-DOM 缩放 T_off；card-claim ≠ 测得；未对硅）

## 魔法缺口

| CLAIM | 模型可解释 | 缺口 |
|-------|------------|------|
| 不对称 0.70–0.95× | gather `T_mix=0.8448` 落带；纯 `T_inj=0.6257` 过誉，靠 H-USE/H-VICTIM | card-claim 列已标非测得 |
| 双忙/alltoall 0.95–1.05×（≈0） | `T_mix=1.0000` hole_dual=0 单独行 | 拒绝折进 0.50–0.85× |
| 均匀读峰值后 5761→2.8–3.4e3 | 模型明示 1 拍 hole 不 mint 容量，不解释数量级崩塌 | 须 soc_sim 曲线；GAP 已打 |
| φ 活锁闭合 | 成功 rejoin 走步 φ↓；永满 ⇒ freeze | 条件进度，非定理；已标旗 |
| 同拍偷第三槽 | 解析钉 hole_dual≡0 | cycle 同拍采样 / swap⊕inject 本解析不可替代（spec §4） |

- 缺口过大?: **否** — CLAIM 未当输入；过誉注入与崩塌/φ 冻结均分列打假

## spec

- 变量/公式来源/无膻造: **PASS**（Frechet 联合、2×2 槽守恒、H-* 具名；T_off/N_txn SOURCE 钉）
- 问题: 无退回项。H-RHO-CLASS 为假设非实测——已标签；κ_mig=0 主表对向不升，灵敏度扫镜像灌满——诚实。spec↔model↔insight 数字一致（insight 钉默认 `T_mix`/hole）。范围锁同 CHI 通道 CW↔CCW。

## 代码（亲自重跑）

- 命令: `python3 models/P-0198/M-4/model.py`
- 退出码 / 耗时 / log: **0** / ~0.05s / `runs/P-0198-M-4.log`
- 与 spec 一致 / 无魔数带宽 / 基线 / 种子 / 灵敏度: **PASS**
  - `p_hole_dual = 0.0  # HARD CONTRACT`；真值表 illegal 第三槽行单独 FAIL
  - φ = `phi_walk` 剩余跳；注释与打印反复 `NOT Σage`
  - 消融 `deflect_on=False`；对向 util + C_eq_time_rel
  - `DUAL_BUSY_CLASSES = {"alltoall"}` 永不折入不对称聚合
  - 灵敏度: (ρ_pref,ρ_opp,c) 与 η_use×κ_mig
  - 无 numpy/pandas；无 H100/decode/team-384dmc；无 ±15% 硅
- 问题: 无（不修代码）。解析层把 dual-busy hole 恒等钉 0 是契约实现，不是从占用「算出再假装验证」——cycle 级同拍断言仍属 T3/Dr.Sim 列表。

## 准则

- 第一性原理 / CLAIM 与相对结果分列 / 未填硅 / 相对主结果 / 0.85 非均值: **PASS**
- 禁止混结论 M-1 CBC（T3）/ M-2 CSR / M-5 CRRF: **PASS**（stdout 明示；insight 拒借公式）
- 禁止编辑 mechanisms/reviews/problems/FUNNEL/P-010*: **PASS**（PR #65 = 4 files；`changed_files:4`）

## 修复清单

无（不修代码）

## 禁止自检

未改 spec/model/机制卡/FUNNEL；未向 GitHub 开审计 PR；未与他卡混排名；未把 card-claim 或未签字数字当周报测得收益。
