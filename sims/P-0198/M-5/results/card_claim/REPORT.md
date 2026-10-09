# Card-claim 补测 · P-0198/M-5 CRRF（未签，不是结论）

- **PR:** https://github.com/lukebest/ArchTeam/pull/83 （#83）
- **base:** `cursor/p-0198-m-5-crrf-t3-a12d`（草稿 #73，不合入、不 base 到 main）
- **起点 SHA:** `b0b4cf968f62d95becfb437cc76512784af2e606`（`b0b4cf9`，与任务要求一致）
- **T4:** 未开。RTL / 机制卡 / T2 / FUNNEL / M-1 / M-2 / M-4 未改。仿真器结构未改。
- **这些数字未经评估审计签字，不是结论。**

## 卡上定义（照此测，不自造指标）

来源：PR #53 `mechanisms/P-0198/M-5.md` §4（卡不在本树）。

| 项 | 定义 |
|---|---|
| 区间 | **0.55–0.85×** |
| 指标 | **makespan**（端到端完成时间，cycle `last_complete − first_issue`） |
| 相对基线（卡原文） | **rebind-off**（经典 1:1，无 ghost），再分两列对照 |
| 负载 | Dat 重集合 / 均匀读饱和区（扣 drain / SYNC / bind 税后） |
| 0.85 | pass bar，不是 measured mean |
| Snp | ≤1.4× rebind-off 为**硬杀**；**不是**本区间。15:1 **仍为 KILL** |

Luke 2026-10-09：主表只围绕**推理**（decode KV / P2P + 推理时集合）。训练标 `secondary`，不与推理混合平均。

## 命令

```bash
python3 sims/P-0198/M-5/sweep.py --mode card_claim --seed 20260903
# 等价：
python3 sims/P-0198/M-5/card_claim.py --seed 20260903
python3 -m pytest sims/P-0198/M-5/tests
```

- seed **20260903**；trials `20260903+i`；**n=3**；mean ± 95% CI (n)
- bbox：12+2 nodes，|I|=96，t_steady_laps=12，hop_lat=1，flit=txn 512 B（减箱；非信封 rd512/wr256）
- 输出只写 `sims/P-0198/M-5/results/card_claim/`

## 负载

`workloads/` 目录不存在；全树 / GitHub 均无 P-0198 推理/训练负载表或 trace。

每一行 `workload_source=existing_config (负载基线表未到)`。未发明 decode-* 发生器：只给现有 `CLASSES` 打推理/训练标签。

| category | workload | 现有 class | role |
|---|---|---|---|
| inference | decode_kv_p2p | uniform_read | primary（decode KV / P2P） |
| inference | decode_kv_gather | gather | primary（推理集合） |
| inference | infer_allgather | allgather | primary（推理集合） |
| inference | infer_allreduce | allreduce | primary（推理集合） |
| training | train_reduce | reduce | secondary |
| training | train_alltoall | alltoall | secondary |

## 两条基线（各成列；提案 = CRRF 开）

同一驱动、同一 txn 列表、同一 outstanding、同一种子。duty `{3:1, 7:1, 15:1}` **从不平均**。

| baseline_type | 列 | outstanding | 实现 |
|---|---|---|---|
| no_cc | 无拥塞控制 | 96 = \|I\| | rebind-off；窗口不绑定；仅 bufferless fail-wait（问题卡「关闭额外流控」） |
| source_fc | 源端流控 | 1 | rebind-off；现有 per-source outstanding 窗口 |

**未改仿真器结构。** 目的端 credit 协议不在现有 inject 路径里；要做必须改注入门控，本次**不实现**。`source_fc` 用已有窗口旋钮表达。没有 `NOT measured` 的必填列；目的端 credit 作为**更强 SSFC 变体**未测。

本 bbox 下 outstanding=32（night）与 outstanding=96 的 Dat makespan 相同（窗口未绑定）。无拥塞控制列与 night 信封窗口等价。

## 推理主表（7:1 为卡示例臂；3:1 / 15:1 同值，见 csv，不平均）

比值 = CRRF makespan / 该列基线 makespan。`in_0.55_0.85` 看比值均值是否落入卡区间。

### 无拥塞控制（no_cc）

| workload | 指标 | 基线 CI | CRRF 7:1 CI | 比值 CI | 落入 0.55–0.85？ | vs T2 | >30% |
|---|---|---|---|---|---|---|---|
| decode_kv_p2p | makespan | 25.00 ± 2.26 (n=3) | 20.67 ± 3.64 (n=3) | **0.8237 ± 0.0844 (n=3)** | **yes** | 0.5820 | **yes** (41.5%) |
| decode_kv_gather | makespan | 49.00 ± 0.00 (n=3) | 27.00 ± 0.00 (n=3) | **0.5510 ± 0.0000 (n=3)** | **yes** | 0.5820 | no (5.3%) |
| infer_allgather | makespan | 45.00 ± 0.00 (n=3) | 30.00 ± 0.00 (n=3) | **0.6667 ± 0.0000 (n=3)** | **yes** | 0.5820 | no (14.6%) |
| infer_allreduce | makespan | 52.00 ± 0.00 (n=3) | 52.00 ± 0.00 (n=3) | **1.0000 ± 0.0000 (n=3)** | **no** | 0.5820 | **yes** (71.8%) |

3:1 / 15:1 与 7:1 **同 makespan**（dest eject 封顶，不是 duty 极限）。不把三臂平均成「CRRF 加速比」。

### 源端流控（source_fc, outstanding=1）

| workload | 指标 | 基线 CI | CRRF 7:1 CI | 比值 CI | 落入 0.55–0.85？ | vs T2 | >30% |
|---|---|---|---|---|---|---|---|
| decode_kv_p2p | makespan | 47.67 ± 4.57 (n=3) | 45.00 ± 5.19 (n=3) | **0.9434 ± 0.0363 (n=3)** | **no** | 0.5820 | **yes** |
| decode_kv_gather | makespan | 49.00 ± 0.00 (n=3) | 49.00 ± 0.00 (n=3) | **1.0000 ± 0.0000 (n=3)** | **no** | 0.5820 | **yes** |
| infer_allgather | makespan | 70.00 ± 0.00 (n=3) | 57.00 ± 0.00 (n=3) | **0.8143 ± 0.0000 (n=3)** | **yes** | 0.5820 | **yes** |
| infer_allreduce | makespan | 186.00 ± 0.00 (n=3) | 235.00 ± 0.00 (n=3) | **1.2634 ± 0.0000 (n=3)** | **no** | 0.5820 | **yes** |

allreduce + source_fc 下 CRRF **更慢**（drain 税 + 单 outstanding）。3:1 = 1.1398，15:1 = 1.2312，同样在区间外。

## 训练（secondary，不单独成报告，不与推理平均）

| workload | baseline | 比值 CI (7:1) | 落入 0.55–0.85？ |
|---|---|---|---|
| train_reduce | no_cc | 0.5510 ± 0.0000 (n=3) | yes |
| train_reduce | source_fc | 1.0000 ± 0.0000 (n=3) | no |
| train_alltoall | no_cc | 0.7193 ± 0.1027 (n=3) | yes |
| train_alltoall | source_fc | 0.9840 ± 0.1028 (n=3) | no |

## 15:1 Snp 仍为 KILL（未写软）

杀假设：`T_snp / rebind-off > 1.4`。completions 未掉。

| baseline | window | 15:1 T_snp/off（trial 均值） | kill_1.4 |
|---|---|---|---|
| no_cc | snp_path | 16.85 (min 11.44) | **True** |
| no_cc | snp_on_gather | 32.59 | **True** |
| source_fc | snp_path | 17.76 | **True** |
| source_fc | snp_on_gather | 3.88 | **True** |

不把 Snp 折进 Dat 均值。本区间不是 Snp 列。

## >30% vs T2（T3 数字成立，不替换 T2）

T2 对照：gather 用签字 H-DAT-DOM（0.6212 / 0.5820 / 0.5642）；其余 Dat-heavy 用 `1/C_dat_eff`。先查了现有驱动，再写原因。

1. **infer_allreduce / no_cc = 1.00 vs T2 ≈0.58（rel 61–77%）**  
   现有 allreduce 驱动 = 半段 gather-to-root + 半段 root-scatter（broadcast 形态）。night 已显示 broadcast 各臂 makespan **1.00×**（root / dest-0 串行，不是 Dat 槽极限）。合并 makespan 被较长半段钉死。T3 成立。

2. **decode_kv_p2p / no_cc = 0.8237 vs T2 ≈0.58（rel 33–46%）**  
   本 bbox 下 uniform_read 更受 hop / dest-eject 限制，三臂 makespan 相同。T2 代数是 `1/C_dat_eff`。与 T3 report 里 gather 三臂打平是同一类封顶。T3 成立。

3. **所有 source_fc 行 vs T2 1/C_dat_eff**  
   T2 针脚假定默认 outstanding 窗口，不是 outstanding=1。窗口=1 时 ghost 第二环没有第二笔 inflight 可载，gather/reduce → 1.00。T2 不是这个信封的代数孪生。T3 成立。

4. **infer_allreduce / source_fc = 1.14–1.26**  
   上两条叠加：root 串行 + drain 税在单 outstanding 下无法摊销。CRRF 比源端流控基线更差。T3 成立。

night gather 0.551 vs T2 0.564–0.621 仍 <30%，与本目录 no_cc gather 一致。

## NOT measured / 结构改动

| 列 | 状态 |
|---|---|
| 无拥塞控制 × 推理四负载 × {3,7,15}:1 | 已测（unsigned） |
| 源端流控（outstanding=1）同上 | 已测（unsigned） |
| 目的端 credit / ECN / 令牌桶 SSFC | **未实现**（需改 inject 门控；本次不改结构） |
| 负载基线 Bot 推理/训练表 | **未到**；`workload_source=existing_config (负载基线表未到)` |
| 签字 smoke / night 数字当 card-claim | **仍未签**；本目录不把它们改写成已测结论 |

结构改动列表：**无**（`sim.py` FSM / 仲裁 / 时序未动）。

## 签字产物未改（SHA-256，扫前扫后一致）

| 文件 | sha256 |
|---|---|
| results/capacity.csv | d7f50438ea625086e97803eebc983091fea73aa228e33cc8b7c4a9e50f995741 |
| results/t2_compare.csv | c5cf19815927c27a4f27f6b2cc7ac0b70a02f6b655f071a2960a09ed51f3738a |
| results/summary.json | c891ae2e601f113adb2e8a0a0aa013c37c32a842512997044addc021b446417d |
| results/night/capacity.csv | 4613fb08a799fef4a9702f13a5b15a8ec69fefd53a0d89144e337ce71442bc22 |
| results/night/t2_compare.csv | bec23f10cc5ba6085fd8f19768850ff9277ab6809f9ac02fec37bbb067b2f599 |
| results/night/summary.json | 08317f71b2ac8d03f8fa192b16e3f2c0445da6313afc344ba032ba181b7ed63a |

`python3 -m pytest sims/P-0198/M-5/tests` → 31 passed。

## 产物

- `card_claim.csv` / `card_claim_trials.csv` / `summary.json`
- `snp_kill.csv`
- `card_claim_inference_7_1.png`
- `PROTOCOL.md`（协议） / 本 `REPORT.md`

**再次：未签字，不是结论，不开 T4。**
