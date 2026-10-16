# T2 audit · P-0198/M-5 CRRF

auditor: 评估审计
batch: P-0198 (not Batch A)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 通过
PR audited: https://github.com/lukebest/ArchTeam/pull/63 (draft; tip `0b16165`)

## 判决

诚实重跑 `python3 models/P-0198/M-5/model.py` → exit **0**；无写盘产物。物理槽守恒精确（`S=1`；`C_dat_eff ≤ 1+duty_dat` 且 `<2`；`flag_untaxed_double=False`）；Epoch Drain 税进 `C_dat_eff`（`T_drain=(k_circ+1)·C_ring+n_pipe`，`f_steady` 扣税）；`epoch_committed` 全员屏障探针在 H-COMMIT 开 → `bind_mismatch_redirect=0`、关 → `>0`；duty∈{3:1,7:1,15:1}+rebind-off 分列；默认细量子下 **15:1 H-SNP-LAT=1.5625 踩 1.4× 杀假设（KILL）**，7:1=1.2450 未杀——过敏臂诚实暴露；COLL_EP/`correctness_depends_on_hint=False`；主收益为相对 `T_hat/T_off`（H-DAT-DOM / H-WRITE-SYM），`0.85`/`0.55–0.85×` 标为 card-claim/pass bar 非测得；stdlib-only；未与 M-1/M-2/M-4 混结论；未改 mechanisms/reviews/problems/FUNNEL/P-010*。过线。

**明确不签：** 卡宣称 Dat 重 `0.55–0.85×` 与写侧 `0.85–1.05×` 不是本审计签字的测得信封。机制卡正文仍在 PR #53 tip、**未入 main**（本树无 `mechanisms/P-0198/`）；结论边界 = T1-return-1（#61 on main）+ 本解析对 tip 摘录的守恒/税/屏障/相对界，**不**把机制卡当已着陆正文。Cycle 级五态 FSM / skew 窗逐 flit（Dr.Sim §4）仍属 T3/`tests/soc_sim`。

## 重跑证据

- 命令: `cd /workspace/archteam-p198-m5 && python3 models/P-0198/M-5/model.py`
- 退出码: **0**
- 写盘: 无（仅 stdout；`models/P-0198/M-5/` 仍仅 `spec.md` / `model.py` / `insight.md`）
- 关键数字行（亲自重跑，Asia/Shanghai 2026-09-30）:

```
H-DRAIN k_circ=2.0 C_ring=25.0 n_pipe=2.0 T_drain=77.0
H-FLIP T_steady=500.0 f_steady=0.8666 tau_drain=0.1334
  rebind-off    0.0000   1.0000   0.0000     1.0000     1.0000  True     True False
  3:1           0.7500   1.7500   0.6499     1.6099     0.2166  True     True False
  7:1           0.8750   1.8750   0.7582     1.7182     0.1083  True     True False
  15:1          0.9375   1.9375   0.8124     1.7724     0.0542  True     True False
  H-COMMIT held ... bind_mismatch_redirect=0  target≈0? True
  H-COMMIT violated ... bind_mismatch_redirect=12  must be >0? True
  correctness_depends_on_hint=False
uniform_read/gather H-DAT-DOM 3:1/7:1/15:1 T_hat/T_off=0.6212/0.5820/0.5642
  3:1   T_lat/T_off=1.0900 kill=False  N_comp=26.9/26.9
  7:1   T_lat/T_off=1.2450 kill=False  N_comp=26.9/26.9
  15:1  T_lat/T_off=1.5625 kill=True   N_comp=16.4/26.9 comp_drop=True
HARD-1 probe: rebind-off T_hat (537.2) > best on-arm T_hat (303.1)? True
7:1  H-SNP-LAT=1.2450 kill=False  15:1 H-SNP-LAT=1.5625 kill=True
done
```

## 对拍表（T1 kill-line ↔ model probe）

| # | T1 条件 / kill-line | 模型探针 | 结果 |
|---|---|---|---|
| 1 | Epoch Drain / skew；全员 `epoch_committed` 后再允新世代注入（Archi/Sys） | `T_drain=(k_circ+1)·C_ring+n_pipe`；`f_steady`/`τ_drain`；H-COMMIT 开/关 → redirect 0/12；接受集 `{local,local−1}` 交∩={E} | PASS（代数屏障探针；非按拍 FSM——spec §4 / insight 已划界） |
| 2 | `bind_mismatch_redirect` 稳态≈0；有界 staging；禁静默丢/永久 stall | H-MISMATCH0；集外 NACK/re-inject 声明；H-STAGING 深度-1 holding（非 highway 队列） | PASS（稳态目标在 H-COMMIT 下为 0；违反则 >0） |
| 3 | duty∈{3:1,7:1,15:1}+rebind-off；Snp makespan/completions 与 1.4× 同表 | CONSERVATION / PER-CLASS / SNP PATH / ABLATION 四臂分列 | PASS；**默认 15:1 KILL** |
| 4 | 相位仅本地压力；runtime hint 至多 advisory | PHASE ARM；`correctness_depends_on_hint=False`；SYNC≠预测 | PASS |
| 5 | 时间复用 ≠ 永久第二 Dat 槽；税必须扣 | `C_dat_eff=1+duty_dat·f_steady−τ_sync−τ_bind`；`untaxed_double=False`；`C_dat_eff<2` | PASS（7:1 eff 1.7182 vs ideal 1.8750） |
| 6 | 分流量类；禁 Dat 均值藏 Snp；禁与 CBC 兄弟混结论 | PER-CLASS 分列；SNP 强制表；banner「this card only」；消融仅 rebind-off | PASS |
| 7 | broadcast 非 H-DAT-DOM 强缩 | broadcast `T_hat=n/a` | PASS |

## 收益阀门

- 主结果 = **相对** `T_hat/T_off`（H-DAT-DOM 仅 Dat 重已坍 + 均匀读饱和；均匀写 H-WRITE-SYM；broadcast n/a）+ Amdahl 伴列 + Snp 相对比/completions。
- `0.85` 开篇钉为及格线/约束条，非均值；`card-claim` 列显式 NOT measured。
- 无 H100 / team-384dmc / decode-* / 硅 ±15%；信封 DV200 `tests/soc_sim` / bufferless-ring-noc。
- 阈值判定: **过线**（守恒 + 税 + 屏障 + 15:1 杀假设诚实命中 + 标签诚实）；**不**把默认假设下落入 0.55–0.85 的比值当信封签字。

## 魔法缺口 / 无神谕

| CLAIM / 风险 | 模型可解释 | 缺口 |
|---|---|---|
| 「近乎双 Dat 无税」 | 否定；税进 `C_dat_eff`；untaxed_double 禁 | 无（构造禁止） |
| Dat 重 0.55–0.85× | 默认 H-DAT-DOM ≈0.621/0.582/0.564 落入；Amdahl ~0.735/0.707/0.695 | 依赖高 `f_steady` 与 H-DAT-DOM；灵敏度短驻留可推出区间——**不签为测得** |
| Snp ≤1.4× 全 duty | 默认 15:1=1.5625 **KILL**；7:1=1.245 ok；粗 `q` 下 7:1 也可杀 | 只报 7:1 甜区 = 减箱（已防） |
| 稳态 redirect=0 | H-COMMIT 假设下为 0；违反探针 >0 | Cycle 若把 flip 建成原子栅栏会人为打成 0（insight 已写）；跨 die sniff≠全局空 → T3 |
| 无公开 Snp T_off | 只报相对比 | 不得写成 ns 测得 |
| HARD-2 / 偏斜窗逐 flit | 未建模 | 留给 soc_sim（spec §4） |

缺口过大?: **否** — 卡区间未当输入校准；15:1 杀假设默认触发；魔法缺口与 H-SNP-CAP 饱和对照已写清。

## Epoch Drain / 容量 / Snp 杀假设（专项）

- Drain：`T_drain=77`（k_circ=2, C_ring=25, n_pipe=2）；`f_steady≈0.8666`；ghost 仅 STEADY·DAT_EPOCH。
- 容量界：全 on-arm `C_dat_eff ≤ ideal`、`<2`、`untaxed_double=False`。时间复用 ≠ 第二永久 Dat 端口。
- Snp：H-SNP-LAT 主列；H-SNP-CAP 暴露饱和失败（7:1≈9.2×、15:1≈18.5× ≫1.4）。15:1 completions drop `16.4/26.9`。
- rebind-off：`C_dat_eff=1`；HARD-1 gather `537.2 > 303.1` True。

## spec ↔ model ↔ insight

- 守恒、drain 税、屏障/接受集、mismatch、duty 扫描、Snp 1.4×、completions、COLL_EP advisory、灵敏度两对均在代码中出现。
- insight 数字（`T_drain=77`、`f_steady≈0.8666`、7:1 `C_dat_eff≈1.718`、H-DAT-DOM `0.621/0.582/0.564`、Snp `1.09/1.245/1.563`、15:1 KILL、Amdahl/`HARD-1`）与重跑一致。
- **非阻塞笔误：** spec §3.4 压力臂写「request duty 7:1 **或** 15:1」，`model.request_duty` 高 Dat 压力只返回 `7:1`（15:1 仍在强制扫描臂）。不构成退回——过敏暴露靠扫描表，不靠压力臂默认选 15:1。
- **非阻塞：** `G_PEAK_READ` / collapse-band 常量定义未使用；PHASE ARM 的 hint 对照未把 hint 当作独立输入（同函数双调）——结论仍由「正确性路径忽略 hint」构造保证。
- Scope: tip 仅 `models/P-0198/M-5/{spec,model,insight}` + `models/README.md`（P-0198 新区一行 + Batch A 分隔声明）。未改 `mechanisms/` / `reviews/` / `problems/` / `FUNNEL` / `models/P-010*`。README：**New card. Not mixed with Batch A ranking.**

## 代码（亲自重跑）

- 与 spec 一致 / 无网络 fetch / 仅 `math`+`sys` / 假设具名 / 灵敏度 `(T_steady,k_circ)` 与 `(q,L_snp)`: PASS
- 问题: 无（不修代码）。Cycle 级 FSM / skew 窗 / HARD-2 目的坍缩已标出 of scope。

## 准则

- 第一性原理（槽守恒精确；税与相对缩放假设具名） / CLAIM 与模型输出分列 / 未填硅: PASS

## 修复清单

无（不修代码）。建议（非退回条件）：
1. 若改 spec，把 §3.4 压力臂「7:1 或 15:1」与 `request_duty` 实际返回值对齐（或注明 15:1 仅为扫描过敏臂）。
2. 去掉未使用的 goodput 常量，或在 stdout 打印均匀读 collapse-band 对照列。

## 禁止自检

未改 spec/model/机制卡/problems/FUNNEL；未与 M-1/M-2/M-4 或 Batch A 混排名；未把 `0.55–0.85×` 或未签字数字当周报；未开 GitHub PR（本文件为本地 audit draft，供父代理另开 audit-only PR）。
