# P-0198 / P-0221 workload baseline 签字审计（第二轮 · 只读）

- 对象：lukebest/bufferless-ring-noc PR #1，分支 `cursor/p0198-llm-noc-baseline-aa90`
- **审计 tip：`94498c7582e05183186811f47d1f6754f3d16fae`**。`94498c7` 与内容提交 `af01e3d` 的差异只在 PHYSICAL_ASSUMPTIONS / PLATFORM_FACTS 两个 md 的 pin 行，共 4 行。修复清单落在 `2095b72`，它在 `905f57d` 之前。
- 方法：box scratch clone `/workspace/brn-p198-audit`（未 commit/push/评论）。clang 19 本地编译 soc_sim，`verify_originals` 通过。用作者自己的 `generate.py --emit-cmd` 生成命令，原样并行执行：
  - 主表 148 个 run，输出在 `/tmp/r2/out`。
  - 扰动探针 106 个 run，输出在 `/tmp/r2/probe`。
  - 分析脚本：`/tmp/r2/analyze.py`。指标 json：`/tmp/r2/{main,probe}_metrics.json`、`thresh.json`。
- 口径：只用相对指标，不做硅片结论，不排序。0.85 是逐行约束，不是均值。以下全部是 smoke（2 top die、outstanding 16、`txns_per_pair` 1）。

## 总判决

| 项 | 结论 |
|---|---|
| a) 逐旋钮结论 | **sub_rr / lib_all_on：只在 p2p_act、tp_allreduce、tp_reducescatter、mix_15_1_large 四行可签（相对、smoke、带注释）；其余行不签或只算趋势。** 其它旋钮大多落在噪声内。见 §4 |
| b) 「lib all-on 后除 Req 外无饥饿」 | **不签**。汇总方法有缺陷；Rsp/Snp 无流量，无从判断；HA 侧 Dat 注入未测；Req/Dat 结论随汇总方法翻转。见 §2.3、§5 |
| c) 升签缺什么 | 见 §6（按优先级排） |
| 复现 | 作者 76 行新臂表（makespan / worst / p99）和 9×10 审计表**逐值一致，0 处不符**。饥饿表的 first/last 均值一致；**比值的算法已查明，它是统计伪影**（§2.4） |
| 修复清单 7 项 | 6 项已修，1 项部分（CRRF 选择关闭，没有加 Snp 生成器）。见 §0 |
| 结构范围 | `include/`、`src/`、`docs/`、RTL 0 改动。范围外只有 `tests/soc_sim/gen_config.py` 和 `run_soc.py`，新增 `--leaf-tag` / `--insert-after-removal` 透传，默认值不变（none 臂数值与 f0ba6fd 时一致） |

**自我更正（上一轮审计）**：上一轮「Dat=2 子环已核」只核了**构建**（readback `[1,2,1,2]`），漏了**使用**。`Endpoint.h:72` 的 `sub_rr=false` 加上 `pick_sub`（`Endpoint.h:193-196`）意味着不开 `--sub-rr` 时 Rsp/Dat **永远只走 sub0**。实测 tp_allreduce_none 的 AIC Dat 注入全部在 sub0（4711 / 0），sub_rr 时为 2452 / 2452。所以除 sub_rr / lib_all_on 外，**所有臂的有效 Dat 子通道数是 1**。

## 0. 修复清单（来自 workload_baseline_audit.md）@94498c7

| # | 项 | 状态 | 证据 |
|---|---|---|---|
| 1 | Snp 生成器 / 声明不可用于 15:1 KILL | **部分**：没有生成器，作者选择「CRRF closed」并明确禁止用于 KILL | README:18,137,155,225；`catalog.json:134-135` |
| 2 | mix_15_1 改述 + 8192/7680 矛盾 | 已修 | `catalog.json:133-135`；README:186 |
| 3 | dat_mcast 重跑、替换旧数、改正根因 | 已修 | README:138；PR body「do not use 578/640 or hit cycle cap」 |
| 4 | P1–P9 标签 | 已修 | `catalog.json` 中 H-AG-CHUNKS-4 / H-MOE-CHUNKS-1 / H-KV-SMOKE-SCALE / H-SMOKE-CYCLES / H-ITAG-SWEEP；envelope_read 改为 推导（`catalog.json:33-35`）；`generate.py:239-240` 引 kSimStepNs |
| 5 | broadcast / reduce 偏差方向写进 README | 已修 | README:180,184 |
| 6 | PHYSICAL_ASSUMPTIONS 补 Snp 位宽、Snp 流量=0 | 已修 | PHYSICAL_ASSUMPTIONS.md:228-229 |
| 7 | 范围声明列出 gen_config / run_soc | 已修 | README:126-129 |

## 1. 复现结果

- 主表：18 臂 × 8 类（mix 拆成 large/small），全部 `done==expected`。weight_reread 只跑了 none / sub_rr / iar_false / lib_all_on，原因见 §2.2。
- 与作者 `tables/inference_new_arms.csv` 对比 76 行 × (makespan, worst, p99)：**0 不符**。README:34-44 审计表全部比值：**0 不符**。
- 闭环多种子：kv_decode_none 和 tp_allgather_none 各再跑 5 颗种子（1–5），makespan 全部相同（1060.6 / 3589.2），确认 `H-SMOKE-SEED-DEAD`。
- 饥饿表：first/last 均值与作者一致（如 none uniform Req0 0.0729→0.2188；lib_all_on all-inference Dat0 10.058→8.809）。作者的比值由一个**未入库**的汇总脚本生成。我按下面的规则复算，**逐值命中** 5.917 / 7.151 / 1.896 / 1.568 / 0.763 / 0.683 / 1.902：每样本 last/first 取均值，first=last=0 计为 0，first=0 且 last>0（∞）**丢弃**。

## 2. 作者自列 5 个问题的裁决

### 2.1 smoke 确定、3 种子无统计意义 → **成立；给出可执行口径**
- 闭环下种子不被消费（`TrafficGen.h:394-411`），任意种子都得到同一条轨迹。我额外跑了 5 颗种子，结果相同。
- 噪声底只能用「最小扰动」估计。做了两种：
  - **P-seed**：kv_decode 加 `--hotspot-frac 0.01`（1% 请求改投一个分区，消费 rng），8 颗种子 × 6 臂，配对比值。none 的 makespan CV 2.8%，range 8.9%。

    | 臂 | 配对比值 mean ± sd [min, max] | 单轨迹比值 |
    |---|---|---|
    | sub_rr | 0.974 ± 0.032 [0.906, 1.028] | 0.924 |
    | lib_all_on | 0.968 ± 0.046 [0.906, 1.056] | 0.940 |
    | iar_false | 1.073 ± 0.062 [**1.001**, 1.167]（8/8 > 1） | 1.071 |
    | leaf_off | 0.991 ± 0.025 | 0.952 |
    | combo_16 | 1.009 ± 0.025 | 0.934 |

    结论：kv 上 sub_rr / lib / leaf_off / combo_16 的单轨迹「收益」在扰动下**不保持**。
  - **P-os**：outstanding 15/16/17，sub_rr 和 lib_all_on × 8 类，看比值的漂移：

    | 类 | none makespan 漂移 | sub_rr 比值 @15/16/17 | lib_all_on 比值 @15/16/17 |
    |---|---|---|---|
    | kv_decode | 6.4% | 0.898 / 0.924 / 0.969 | 0.921 / 0.940 / 0.948 |
    | p2p_act | 0.4% | 0.883 / 0.878 / 0.872 | 0.882 / 0.879 / 0.872 |
    | tp_allreduce | 1.6% | 0.936 / 0.931 / 0.927 | 0.937 / 0.936 / 0.928 |
    | tp_allgather | 9.0% | 1.086 / 1.033 / 1.053 | 1.025 / 1.077 / 1.089 |
    | tp_reducescatter | 2.3% | 0.970 / 0.961 / 0.957 | 0.972 / 0.969 / 0.959 |
    | moe_alltoall | 2.8% | 1.005 / 0.969 / 1.030 | 0.978 / 0.975 / 0.980 |
    | mix_15_1_large | 1.8% | 0.944 / 0.933 / 0.920 | 0.949 / 0.935 / 0.922 |
    | mix_15_1_small | 2.7% | 0.995 / 0.996 / 0.995 | 0.995 / 0.996 / 0.995 |

- **口径（提议）**：
  - 有效 ⇔ |1 − r| > T_c，T_c = max(3·ε_c, 2%)。ε_c = 该类在 P-os 下比值的最大半幅（kv 再与 P-seed 配对 sd 取大）。
  - 实测 T：kv 0.106、p2p 0.02、allreduce 0.02、allgather 0.096、RS 0.02、moe 0.092、mix_L 0.04、mix_S 0.02。
  - 另加方向判据：所有扰动下同号，且 |mean − 1| > 2%，记为「方向稳定」，**只算趋势，不算有效**。
  - 注意：ε 只用 2 个臂估计，套用到其它臂；P-seed 只做了 kv。未覆盖处按未核处理。
- 逐行判定（`+` 有效变快，`-` 有效变慢，`~` 噪声内）：

| arm | kv | p2p | allreduce | allgather | RS | moe | mix_L | mix_S |
|---|---|---|---|---|---|---|---|---|
| srcfc | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ |
| exp_srcfc | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 0.983~ | 1.000~ | 1.000~ |
| dat_mcast | 1.000~ | **0.938+** | 0.986~ | 0.919~ | 1.000~ | 1.000~ | 0.973~ | **0.898+** |
| itag_8 | 0.968~ | 1.000~ | 1.005~ | 0.971~ | 1.008~ | 1.046~ | 1.006~ | 1.000~ |
| itag_16 | 0.934~ | 1.000~ | 0.996~ | 0.948~ | 0.994~ | 0.983~ | 1.001~ | 1.000~ |
| itag_32 | 1.040~ | 1.000~ | 1.014~ | 0.983~ | 1.021-（临界） | 0.966~ | 1.012~ | 1.000~ |
| issue_arrival | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ |
| issue_longest | 0.950~ | 1.000~ | 0.987~ | 0.914~ | 0.980（临界） | **1.149-** | 0.962~ | 0.999~ |
| issue_shortest | 1.000~ | 1.000~ | 1.000~ | 1.000~ | 1.000~ | **1.175-** | 1.000~ | 1.000~ |
| uturn | 0.960~ | 1.004~ | 0.991~ | 1.104-（临界） | 0.985~ | 1.048~ | 0.987~ | 1.000~ |
| sub_rr | 0.924~ | **0.878+** | **0.931+** | 1.033~（3/3 > 1） | **0.961+** | 0.969~ | **0.933+** | 0.996~ |
| leaf_off | 0.952~ | 0.997~ | 0.994~ | 0.989~ | 0.992~ | 1.033~ | 0.993~ | 1.008~ |
| iar_false | 1.071~（8/8 种子 > 1） | 1.000~ | 1.019~ | 0.973~ | 1.030-（临界） | 1.016~ | 1.004~ | 1.010~ |
| combo_exp_itag_8/16/32 | 与 itag_8/16/32 逐值相同（moe 除外） | | | | | | | |
| lib_all_on | 0.940~ | **0.879+** | **0.936+** | 1.077~（3/3 > 1） | **0.969+** | 0.975~ | **0.935+** | 0.996~ |

### 2.2 kv_decode 与 weight_reread 相同 → **成立；算 1 个数据点**
- 两者的 run_soc 命令对全部 18 臂逐参数相同：都是 `uniform` / `read` / `txns_per_pair 1`，类名只是标签。
- 4 臂的 `events.csv` 与 `core_ring_counts.csv` **字节级相同**。
- 所有表和饥饿汇总都要去重。作者的 uniform 池 n=4 实为 n=2（die1、die2 各 1），all-inference 池 n=18 实为 16。

### 2.3 注入等待单位与「p99」 → **成立；饥饿结论受影响**
- `inject_fail` 是 `TCsHighWay::m_inputFailCntList`（`src/TCsHighWay.cpp:664-671`）：**每个周期、每个方向**，头 flit 注入失败就 +1；`inject_succ` 是 `m_niInputCnt`。
- 所以 `mean_wait_cyc` 的含义是：每次成功注入平均伴随的「环时钟周期 × 方向」阻塞事件数（CC/CW 同周期可能双计）。它是近似的平均阻塞周期，不是时延分布，也不是尝试失败率。标「cyc」可以接受，但要注明「×方向」。
- 「p99_of_cs_means」= `percentile(10 个 CS 均值, 99)`，按 `inject_wait.py:32-37`，i = int(0.99×9) = 8，**就是 10 个 CS 里第 2 大的均值**。不是尾延迟，不能叫 p99。
- 计数极小：uniform Req 每个 CS 成功 48 次，失败 1–11 次。none die2 Req0 首 CS 只有 1 次失败（1/48 = 0.0208）。
- 结论：Req 的「梯度」由个位数事件决定，且是单条确定轨迹，**只能当 smoke 现象，不能签饥饿**。

### 2.4 none Req0 last/first 5.917 vs 首末值 ≈3.0 → **原因已查明（汇总伪影）**
- 5.917 = 4 个样本 last/first 的**算术平均**：die1 = 0.229/0.125 = 1.833，die2 = 0.208/0.0208 = **10.0**，kv 和 weight 各算一次，(1.833 + 10 + 1.833 + 10)/4 = 5.917。
- 3.0 = 均值之比 0.21875/0.07292。差异来自分母 0.0208（1 次失败 / 48 次成功）把比值放大到 10，加上 kv/weight 重复计数。
- 同一算法在 all-inference 池更严重：
  - first=last=0 的样本计为比值 0：lib Dat0 有 5 个、Dat1 有 6 个，**直接把均值拉向 NO**。
  - first=0 且 last>0（最强的下游饥饿）被**丢弃**：none Req0 18 个样本丢了 6 个。
- 改用均值之比（ratio-of-means）后：
  - lib_all_on all-inference **Req0 0.81、Req1 0.83 → 无 last>first**（作者给 1.90 / 2.07「YES」）。
  - lib Dat0 0.876、Dat1 0.928（作者 0.763 / 0.683）。
  - none Dat0 1.76 / Dat1 1.71。
  - none uniform Req0 3.0、Req1 3.67（作者 5.92 / 6.20）。
  - lib uniform Req0 1.69、Req1 2.09。
- **饥饿判定随汇总方法翻转 → 不签。**

### 2.5 bbox 只有 2 top die、outstanding 16 → **成立；对结论的影响**
- 负载深度：闭环 16 outstanding，远低于信封 512/256。
  - srcfc 和 exp_srcfc 在所有类上 `fc_blocked=0`（moe 为 2）。**流控根本没被触发**，所以「srcfc 无效」不可签，只能说「此负载下未被激活」。
  - i-tag / leaf-tag / iar 这类拥塞机制同样处在低争用区，效果被低估或不可见。
- 拓扑：2 top die 只接 bottom0，bottom7 未构建，跨 bottom 和 12-die 的 3DIO 聚合争用全部缺失；20 rank 不是信封规模。
- 闭环、确定、单轨迹：makespan 对 ±1 outstanding 漂移 0.4–9%（allgather 9%、kv 6.4%）。比值的有效分辨率受这个限制。
- sub_rr 的收益本质是「打开第二个本已建模的 Dat/Rsp 子通道」，是**基线配置修正**，不是 NoC 机制收益。信封负载下它的幅度未知（可能更大）。
- 结论：所有比值只能作 smoke 方向，不能外推到信封，也不能做硅片论断。

## 3. 物理假设核对

列：假设 / 值 / 仓内出处 / 是否与平台一致 / 核验（已核 = 本轮读代码或运行 readback 确认；未核 = 不签）。

| 假设 | 值 | 仓内出处 | 是否与平台一致 | 核验 |
|---|---|---|---|---|
| 子通道构建 req/rsp/snp/dat | 1/2/1/2 | `soc.cpp:39 kSubs`；`gen_config.py:344` | readback `first_die_subs [1,2,1,2]`；输出含 Dat_sub0/1 | 已核 |
| **子通道实际使用** | 默认**只用 sub0**（Dat、Rsp）；仅 sub_rr / lib_all_on 用 2 个 | `Endpoint.h:72` `sub_rr=false`；`:193-196` `pick_sub` | 实测 none Dat 4711/0，sub_rr 2452/2452；与 PLATFORM_FACTS:7-11 一致 | 已核（**更正上一轮**） |
| Snp 环数 | 每物理环 1 个 sub | 同上 | 一致 | 已核 |
| Snp 流量 | 0 | 每个 run `summary traffic.snp=0` | 与 PHYSICAL_ASSUMPTIONS:229 一致 | 已核 |
| Snp / Dat flit 位宽 | **模型不表达**（一 flit 一 slot） | 无字段 | PHYSICAL_ASSUMPTIONS:228 已标不签 | **未核，不签** |
| Dat beat | 64 B | `Endpoint.h:29`；`noc_setup.md:166` | top 一致；bottom 文档 128 B 未用（`gen_config.py:593`） | top 已核 / bottom 未核 |
| CHI txn | 512 B = 8 beat | `hardware_setup.md:57`；summary `beats_per_txn 8` | 一致 | 已核 |
| top 物理环 | 2 | `gen_config.py:345-346`；readback `ring_cnt 2` | 一致 | 已核 |
| bottom 环 | 28（12 H + 16 V） | `docs/bottom_manyring.csv` | log `rings=28` | 已核 |
| top CS/环 | 21 | `gen_config.py:19` | 推断（topology 无此数） | 值已核，出处为推断，**不签** |
| bottom H/V CS | 24/25；33/37/38 | `gen_config.py:17-18` | 推断 | 值已核，物理**未核** |
| top 链路时延 | 2 cyc/段 | `gen_config.py:381` | 推断（ASSUMPTIONS:46） | **未核** |
| bottom 链路时延 | H 3（ring0 文档 3/4/3…wrap 3）、V 4 | `gen_config.py:491-514`；`topology.md:274-278` 只给 ring0 前 3 段和 wrap | ring0 部分有文档，其余推断 | ring0 部分已核，其余**未核** |
| **一圈时延 42/72/76/132/148/152** | 见右 | 我从生成的 `Network_parameter*.csv` 逐段求和：top 21×2=42；H24 3×24=72；H25 75+1（even_sum）=76，ring0 文档 3+4+3×23=76；V33/37/38×4=132/148/152 | 与库内定义一致：`TRingConfig.cpp:428-433` 的 `m_oneCycleLatency` 就是 FullRing 各 CS LEFT 口链路时延之和，且 assert 偶数（`:439`），解释了 +1 | **算式已核；物理值未核**（输入时延多为推断）。与「导演期望」一致不构成独立证据。单位是各自环时钟：top 2.5 GHz，bottom 1.8 GHz |
| 时钟 top/bottom/AIC/HA/mux | 2.5/1.8/1.5/1.8/2.5 GHz | `Endpoint.h:19-23` | 一致；HA 文档另有 2.2（未用） | 已核（代码） |
| 3DIO 链路宽 | 32 B/cycle（64 B beat = 2 cyc） | `Mux3dio.h:22,29,53-54` | 文档写「typically 32B」 | 代码已核，物理**未核** |
| Mux buffer / pipe / afifo | 5/20/6/15 | `Mux3dio.h:20-26`；`run_soc.py:224-229` | summary.mux 一致 | 已核 |
| HA RX / TX 深度 | 10/13/10/13；17/16/16/20 | `Endpoint.h:132-136,148-151` | 一致 | 已核（代码） |
| AIC RX credit | 4 | `Endpoint.h:28` | 无文档 | **未核** |
| HA trackers | 512 | `Endpoint.h:26`；`hardware_setup.md:163` | 一致 | 已核 |
| outstanding 信封 / smoke | 512/256（推导）；16 | `TrafficGen.h:145-148`；`catalog.json:33-44` | 16 出自外部 M-5 README | 信封已核；16 **未核** |
| 端口 buffer（share/output） | PHYSICAL_ASSUMPTIONS §8 | `gen_config.py:130-222` | 抽查一致 | 抽查已核，其余未逐项核 |
| srcfc 硬件表 | rate 72 / credit 4 … 仅 top Req | `gen_config.py:23-31`；`flowcontrol_setup.md:297-304` | 一致；运行 `fc_blocked=0`（未触发） | 值已核；**行为未被激活** |
| experiment_srcfc | rate 112 / credit 2 / window 16 …，top Req+Dat | `gen_config.py:226-234` | **无文档出处**（PHYSICAL_ASSUMPTIONS:212 标 code） | **未核，不签** |
| leaf-tag 参数 | sta 0 2 4 6 8 / 1 3 5 7 9，dyn 100 / 80 90 95 | `gen_config.py`（noc_setup 3.2 风格） | 推断 | **未核** |
| insertAfterRemoval | 设备口 true；SLLC/ChangeRing 恒 true | `TPortConfig.cpp:61`；`docs/port_*.toml:2` | 一致 | 已核 |
| HBM 时延 | 0 | `gen_config.py:49` | 无文档 | 假设，**不签** |

## 4. 逐旋钮签字

签字级别：**可签** = 相对、smoke、带注释；**趋势** = 只算 smoke 方向；**不签**。

| 旋钮 | 作者结论 | 裁决 | 理由 |
|---|---|---|---|
| sub_rr | 最有效（kv/weight 0.924，p2p 0.878，AR 0.931，mix 0.933） | **可签**：p2p 0.878、AR 0.931、RS 0.961、mix_L 0.933（P-os 下漂移 ≤0.024，均过阈）。**不签**：kv/weight 0.924（种子扰动配对 0.974 ± 0.032，有 >1 的样本）。allgather 1.033 只算**趋势**（变慢，3/3 同号，幅度未过阈） | 注释：这是打开已建模的第 2 个 Dat/Rsp 子通道，属基线修正；kv 和 weight 是 1 个数据点 |
| lib_all_on | 0.88–0.97，allgather 1.077 | 与 sub_rr 同：p2p/AR/RS/mix_L **可签**。kv **不签**。allgather 1.077 **趋势**（3/3 > 1，未过阈 0.096）。lib 与 sub_rr 的差 ≤0.01（allgather 例外），**其余组件的增量不可分辨** | i-tag 16 的选择依据是 class-mean 差 1.5%（2801.7 vs 2843.5），在噪声内，**不签**这个选择 |
| srcfc / exp_srcfc | 单独无效 | **不签**「无效」；可签「outstanding 16 smoke 下 FC 从未触发（fc_blocked=0）」 | 机制未被激活，不能判断有效与否 |
| iar_false | 单独 kv 1.071 | **趋势**（变慢）：8/8 种子扰动 > 1，均值 1.073，但 \|Δ\| 小于 kv 的阈值 0.106。RS 1.030 临界 | — |
| i-tag 8/16/32（含 combo） | — | **不签**：全部 ~（itag_32 RS 1.021 临界） | combo 与 itag 逐值相同，因为 exp_srcfc 是空操作 |
| leaf_off / issue_arrival | — | **不签**（全部 ~；issue_arrival 与 none 逐值相同） | — |
| dat_mcast | — | **可签**：p2p 0.938、mix_S 0.898（相对、smoke）。注释：p2p 用 broadcast 代理，偏向 multicast | allgather 0.919 未过阈，算**趋势** |
| issue_longest / shortest | — | **可签**：moe 变慢 1.149 / 1.175。其余 ~ 或临界 | 跳数代理是 HA raw（H-ISSUE-HOPS-RAW） |
| uturn | — | allgather 1.104 临界，算**趋势**；其余**不签** | eject_fail 在 smoke 下为 0 |
| 0.85 逐行约束 | — | 没有任何行低于 0.85（最低 0.878） | — |

## 5. 「lib all-on 后除 Req 外无饥饿」→ **不签**
1. 作者的汇总（均值-of-比值，0/0 计 0，∞ 丢弃）对结论起决定作用。改用均值之比后，lib all-inference Req **无** last>first（0.81 / 0.83），与作者「Req 仍饥饿」**相反**；Dat 0.88 / 0.93 <1，但 last>first 的样本仍有 5/18、4/18。
2. Rsp / Snp「NO」没有意义：AIC 不注入 Rsp/Snp，Snp 流量为 0，这是没有测，不是没有饥饿。
3. 只测了 **top-die AIC UP 口**（`inject_wait.py:116`）。读数据的主 Dat 流（HA→bottom 环→3DIO）的注入等待完全没测。
4. lib_all_on 下 AIC Dat 的绝对等待从 3.7 涨到 10.1（首 CS 均值，约 2.7×）。「无梯度」也可能是「全环都差」。序列不单调，峰在 CS15 附近，形状更像中段热点，不是下游斜坡。
5. 单条确定轨迹；计数是个位数；kv/weight 重复计数。
6. 汇总脚本没有入库（仓内找不到 `all_inference` / `yes_count` 的生成代码），**不可复现**，只能靠我反推。

可签的只有一句（smoke、描述性）：「lib_all_on 下 top AIC Req 环 uniform 读的首/末 CS 阻塞比由 3.0/3.7 降到 1.7/2.1（均值之比，2 个样本）」。

## 6. 升签清单（按优先级）
1. **汇总方法**：入库汇总脚本，改为均值之比或分子分母合计、去掉 weight 重复、报每样本分布；∞ 和 0/0 单列，不能丢弃也不能计 0。把「p99_of_cs_means」改名为「CS 均值第 2 大」，或者导出逐次尝试的分布。
2. **补测 HA / 3DIO 侧（bottom）Dat 注入等待**和 3DIO mux 排队，否则无法回答「下游是否饥饿」。
3. **随机性和噪声底**：把种子接到 uniform 的目的地洗牌或起点偏移、集合 plan 的 cell→HA 映射（作为新列，不改已发表的 none）。每类每臂 ≥8 种子，阈值按 §2.1 公式。
4. **负载深度**：outstanding 128/512 扫描（至少 16/64/256/512），确认 srcfc / i-tag 在被激活后的效果。一条开环 offered-load 曲线（`collapse_batch`）。
5. **规模**：至少 6 top die + bottom0，最终 12+2 信封。
6. **拆开 kv 与 weight**（不同的 txn 数、地址或 HA 分布），否则它们永远是 1 个点。
7. **lib_all_on 消融**：逐个去掉组件（-sub_rr、-itag16、-iar、-exp_srcfc），在噪声口径下给增量；i-tag 选择用同一口径重做。
8. 物理：top / bottom 链路时延、top CS=21、AIC RX credit、experiment_srcfc 表、leaf-tag 参数，找到文档出处或标为不签。lap 时间在输入时延有文档之前只签算式，不签物理值。
