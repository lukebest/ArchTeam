# Insight · P-0198/M-5r1 CRRF-SB

## 诊断（对照已签字 T3 night，不改写那些数字）

M-5 的 15:1 KILL 不是「duty 选错」。T3 night：`snp_path=17.05` 在 **无 Dat 混合** 时已经炸，mixed 再加到 32.59。T2 的 `q=1 → 1.5625` 不是合法周期日程（每次身份翻转必须 Epoch Drain）。主因是 **排他环身份**：本征 Snp 被写成 DAT_EPOCH 的非公民。加重项是粗量子 drain 叠在短 SNP_EPOCH 前。参数改 7:1/3:1 不够——混合 3:1 夜测已 27.51×。

## 结构切口

绑定表从「此环现在是谁」改为「ghost Dat 可否借空槽」。本征 `channel-id=Snp` 残留权不进 Drain 闸。这不是 TDM 日历，也不是年龄仲裁。

## 模型能解释 / 不能解释

能：排他窗等待跟踪 `T_steady+T_drain`（与 T3 加严同向）；SB 等待跟踪 `ρ_wire/(1-ρ_wire)`；steal-back 税进 `C_dat_eff` 而不是锁 Snp。

不能：满 12+2 RBRG / 推理 KV 真迹 / p99 墙钟。那些必须 soc_sim 新分支（见卡 §7）。本目录 `model.py` 与 `harness.py` 的数字 **全部 UNSIGNED**。

## UNSIGNED harness（SEED=20260903，n=3，N=12，减箱；不得贴 T3 / 不得当 card-claim）

`python3 models/P-0198/M-5r1/harness.py`：

| mode | arm | T_snp/off | T_dat/off | kill 1.4 | 备注 |
|------|-----|-----------|-----------|----------|------|
| snp_path | rebind-off / src-fc / m5r1-15:1 | 1.000 | n/a | no | 本征路径 |
| snp_path | m5-15:1 | **7.800** | n/a | yes | sb-off 消融仍杀 |
| mixed | rebind-off / src-fc | 1.000 | 1.000 | no | 源端 FC 本 bbox 未缩短 Dat（dest-0） |
| mixed | m5-15:1 | **19.000** | 0.583 | yes | 0.583 是 dest-eject 伪影，**不是** card-claim |
| mixed | m5r1-15:1 | **1.000** | 0.569 | no | steal_back=6；ghost 25.7 vs M-5 的 27；Snp completions 6/6 |

方向与 T3 night 的「排他杀 Snp、Dat 仍能短」一致，**幅度不是** 17.05/32.59，禁止外推成满信封测得。

## 交给审计

- 卡：`mechanisms/P-0198/M-5r1.md`（勿改 M-5.md / reviews）
- 跑：`python3 models/P-0198/M-5r1/model.py`；`python3 models/P-0198/M-5r1/harness.py`
- 消融：`m5-15:1` 必须仍杀 Snp；`m5r1-15:1` 必须在诚实周期缩短 Snp makespan；只涨注入次数不算
