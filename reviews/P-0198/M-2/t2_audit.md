# T2 audit · P-0198/M-2 CSR（Rendezvous–Grant）

auditor: 评估审计
batch: P-0198 (not Batch A)
round: 1
date: 2026-09-30 (Asia/Shanghai)
verdict: 通过
tip: e6d8ca86dcf8f47905be0b27552cd52fddb6f629 (PR #66)
scope: 本卡结论独立；**不**与 M-1 CBC（已 T3 淘汰）、M-4 AODI、M-5 CRRF 混排名或混过关叙事

## 判决
诚实重跑 `python3 models/P-0198/M-2/model.py` exit **0**。结构不变式 `occupancy(CAM_i,Dat_beats)=[0,0,0,0]`、`RBRG_reject_retention_depth=0`、`N_cam=4` / `invariant_ok=True`。完成守恒分列；回退主导杀开关在 high-ost a=8 触发 `card_claim=INVALID`（默认 a=2 / a=5 未主导）。H_inject_gate / FORCE_FALLBACK / spine-off / alltoall 树·残差分列均在 stdout。相对主列；0.85 明示为 pass bar 非均值；card-claim 标 NOT measured / NOT signed pass；无硅 ±15%；stdlib-only。tip 仅 `models/P-0198/M-2/{spec,model,insight}` + `models/README.md` 索引，无 mechanisms/reviews/problems/FUNNEL/P-010* 编辑。过线。

## 收益阈值
- 合格线: 0.85 = CONSTRAINT / pass bar（**不是**均值）；本卡主结果 = 相对 r / 守恒分列 / 不变式，非测得硅 makespan
- 重跑关键数（亲自跑，勿编造）:
  - exit=0
  - CAM Dat=[0,0,0,0] all_zero=True；retention=0 ok=True；modeled_live=4≤4；invariant_ok=True
  - a=2: f_ov=0.0952 f_to=0.0000 f_grant=0.9048 sum=1 dominates=False
  - a=5 (alltoall_seg): f_ov=0.3983 f_to=0 f_grant=0.6017 dominates=False flag_sys_fb(>10%)=True
  - a=8: f_ov=0.5746 dominates=True → card_claim=INVALID
  - gather-family default: T_hat/T_off=0.5386（T_hat gather/reduce=289.3；allgather=898.7；allreduce=533.5）；claim_valid=ok（=未因回退主导作废，**非** pass）
  - alltoall: TREE r=0.6932 T_tree=2840.5；RESIDUAL r=1.0000 T_res=4098.0；mix=0.8159（伴生，非过关）
  - gate ON tax_orbit=0；gate OFF tax_orbit=0.5500 r_gate_off=1.0362 returns_toward_1=True
  - spine-off: gather T_hat_off=537.2 > T_hat_on=289.3 HARD True；alltoall tree on/off=0.6932
- T1 带进条件逐条:
  1. `occupancy(CAM_i,Dat_beats)==0` 与 `RBRG_reject_retention_depth==0`: PASS（结构构造 + 打印断言）
  2. `cam_overflow_fallback`/`collect_timeout_fallback` endpoints；spine-off；N_cam=4 真并发: PASS（Erlang-B / 迟到份额分列；消融；N_cam=4 常量 + 灵敏度反事实）
  3. H_inject_gate；FORCE_FALLBACK 可观测: PASS（on/off 臂；H-FF-NOTIFY 具名假设/探针；congested f_to 打印）
  4. alltoall 多树/残差与回退主导分列，禁均值过关: PASS
- 阈值判定: 过线（解析相对界 + 杀开关诚实；**未**签 card-claim 为测得 pass；绝对 ns 仅 H-REL-SCALE）

## 魔法缺口
| CLAIM | 模型可解释 | 缺口 |
| gather 系 0.45–0.80× | 默认点 r≈0.5386 落带内（gate on、a=2、f_fanin=0.60） | 依赖具名假设；a=8 或 gate off 则带失效/回 ~1；标 label only |
| alltoall 0.60–0.95×+res | TREE 0.693；RES 1.0；mix 0.816 | a=5 已 material overflow；卡带偏乐观；残差必须单列 |
| FORCE_FALLBACK 通知 | H-FF-NOTIFY=true → flag_orphan=false | 探针非已测路径；T3 须补公民/双端超时 |
| 绝对 ns（289.3 等） | T_off·r | 非硅；无 ±15% |
- 缺口过大?: 否 + 卡区间未当输入/未签 pass；杀开关与 magic-gap 段已打印

## spec
- 变量/公式来源/无膻造: PASS
- 问题: 无阻塞。T_off 集合类钉自称 `docs/srcfc_ca_model/data.json`（树内无该文件；均匀读/写与 `problems/P-0198.yaml` 4403.2/4834.6 一致；常量区钉写符合「无外部数据文件」契约）。Amdahl 扇入界显式非 CBC `T∝1/p_inj`。正交声明完整。

## 代码（亲自重跑）
- 命令: `python3 models/P-0198/M-2/model.py`
- 退出码 / 耗时 / log: **0** / ~0.04s /（stdout 见上；未另落 runs/）
- 与 spec 一致 / 无魔数当测得 / 基线钉 / 灵敏度: PASS
- 问题: 无（不修）。`occupancy_cam_dat`/`retention_depth` 恒返 0 是机制代数构造，已标 exact/violation=mechanism fail；非隐藏拟合。imports = `__future__`/`math`/`sys` only。

## 准则
- 第一性原理 / card-claim 与模型分列 / 未填硅 / 相对主结果 / 分流量类 / 禁混 M-1·M-4·M-5: PASS
- 信封: DV200 `tests/soc_sim` / `lukebest/bufferless-ring-noc`；T1 #61；机制 #53 tip（正文可能未合 main）— 与 insight/spec 一致
- tip 禁止自检: 无 mechanisms/ / reviews/ / problems/ / FUNNEL.md / P-010* 编辑

## 修复清单
无（不修代码）

## 禁止自检
未改 spec/model/机制卡；未开 GitHub PR 评论；未与 M-1/M-4/M-5 混排名或混结论；未把未签字 card-claim / 绝对 ns 当周报测得。
