# P-0198 / M-5r1 CRRF-SB — Prof.Bench T1

- 评审人：Prof. Bench（Tier 1 · 负载代表性）
- 输入：机制卡 `mechanisms/P-0198/M-5r1.md`（PR #85）与 `models/P-0198/M-5r1/*`；T0 `reviews/P-0198/M-5r1/tier0.md`（PR #89，PASS_T1，质量 INCREMENTAL）；`problems/P-0198.yaml`；本人上轮 `reviews/P-0198/M-5/Prof.Bench.md`（PR #57）。
- 独立性：未读本轮其他评审人文件。
- 负载核查范围：`/workspace/workloads`、`/workspace/baselines`；平台分支 `lukebest/bufferless-ring-noc@cursor/p0198-llm-noc-baseline-aa90` 的 `workloads/p0198-llm-noc/`（README + catalog.json）与 `tests/soc_sim/platform/{TrafficGen.h,Endpoint.h}`。

## 结论

**有条件通过**：机制切口（去掉 Snp 的排他 epoch 身份）方向对，但「推理混合」负载在库里和 soc_sim 里都不存在。soc_sim 现有流量里没有一条本征 Snp。所以 15:1 Snp KILL 列能否过，取决于一个还没定义的合成 Snp 发生器。按惯例，缺负载库判有条件通过，评估可信度降到 2，不判致命。第 1 条位宽有补救办法（拆拍并计税），也不判致命。

## 五维打分（1–5，沿用上轮 M-5 Prof.Bench 维度）

| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 3 | 无环上缓冲依赖链，无死锁结构（同 T0）。四处没闭合：位宽、ghost NACK 的数据来源、eject 失败后 orbit 拖住 Drain、上游 ghost 饿死下游 Snp。本轮 RTL 不改，Snp 线不能加宽，只能拆拍。 |
| 新颖性 | 2 | 同 T0 的 INCREMENTAL。卡自带 harness 的 `_complete` 到达即完成，不查 `epoch_tag` 和 bind，等于已经只按 header 解码。现有证据里 epoch/bind 没有任何正确性作用，退化成「Dat 借 Snp 环空槽、Snp 优先」的风险高（见第 5 条）。 |
| 预期收益 | 2 | Snp 侧目标只是回到 rebind-off（≤1.4），这是止损，不是收益。Dat 侧 0.55–0.85× 未签字；harness 的 Dat 0.569 和卡自己标为伪影的 0.583 来自同一个 dest-eject 伪影（见下）。 |
| 评估可信度 | 2 | 库里没有 NoC/Snp 负载；soc_sim 不发 Snp；「推理混合」没有成分定义。7.8→1.0 / 19.0→1.0 是减箱（N=12、n=3、flit=txn、无 RBRG/HBM）、单一 benchmark 的未签字探针。 |
| 系统可组合性 | 3 | 和源端流控正交；hint 至多 advisory。依赖库内 i-tag/e-tag 是否覆盖 ghost，卡没写。仿真器改动限定在 bufferless-ring-noc 新分支，范围清楚。 |

## 最强反对意见

**Snp KILL 列测的是作者自定的合成 Snp，不是推理负载。** 证据：

- `/workspace/workloads` 和 `/workspace/baselines` 里 rg `snoop|snp|15:1|duty` 零命中。`workloads/gaps.md` 第 7 条写明 trace 里没有通信模式。
- 平台的 `tests/soc_sim` 只有 TrafficGen 发 Req 和写 Dat；HA 端点只回 Rsp/Dat。`try_send_snp` 存在，但没有任何调用方；`completed_snp` 只是计数。P-0198 CONTEXT 也写明「缓存一致性……不在范围」。所以 soc_sim 现有所有流量类（均匀读写、各集合通信，以及平台推理包的 kv_decode / tp_allreduce / moe_alltoall 等）的本征 Snp 负载都是 0。
- 卡的「推理混合 15:1（KV/P2P+Snp）」没给 Snp 速率、源/目的分布和对应的集合类。spec 里 `λ_snp=0.05` 是假设 H-SNP-SPARSE。harness 的 mixed 列是 48 笔 gather（全部打到节点 0）加 6 笔均匀 Snp。

Snp 稀疏到这个程度，steal-back 几乎触发不到（harness `steal_back=6`），T_snp/off=1.000 是负载设定直接给出的结果，不是机制挣来的。评估层若由作者自选 Snp 速率和位置，KILL 线可以被负载设计绕过。

## 评估层必须验证的一个假设

**「只在本地空槽上让 Snp 赢、不设 ghost 段密度上限」就够把下游 Snp 压在 ≤1.4。**

做法：

1. Snp 发生器参数由评审方钉死，不由作者选：Snp 速率至少扫 3 档（含卡默认 0.05），另加 H-SNP-CAP 饱和对照；Snp 源放在热 ghost 源的下游。热 ghost 源指 gather/reduce/allreduce 的扇入路径，以及 alltoall。
2. duty 15:1 下，按节点位置分列报 Snp makespan、p99 和最坏注入等待，相对 rebind-off。
3. 任一节点位置、任一速率档的 `snp_path` 列或推理混合列 >1.4，即该臂失败。

若 ghost 必须服从 Snp 环的 i-tag 保留槽才能过线，要写进卡，成为机制的一部分。

## 负载特征核对

| 负载 | 来源 | 是否在库 | 15:1 是否出现 | 备注 |
|---|---|---|---|---|
| 均匀读 / 均匀写（基线） | `problems/P-0198.yaml` SYMPTOM；平台 `counter_uniform_read` | 在（问题自带 soc_sim） | 否 | 读约 4403.2 ns、写约 4834.6 ns，各 46080 笔。纯 Req/Dat/Rsp，无 Snp。 |
| 集合：gather / reduce / allreduce / allgather / alltoall / broadcast | `problems/P-0198.yaml`；`TrafficGen.h` `build_collective` | 在（soc_sim） | 否 | 除 broadcast 外多数 collapsed=true；broadcast 8192 B、outstanding 4096 约 117.76 B/ns，不 collapse。经 HA 中转，无 AIC↔AIC P2P，无 Snp。 |
| 推理 kv_decode / weight_reread | 平台分支 `workloads/p0198-llm-noc/catalog.json` | 仅在平台分支；`/workspace/workloads` 没有 | 否 | 均匀读拓扑，Llama 2 70B 推导字节。无 Snp。 |
| 推理 p2p_act / tp_allreduce / tp_allgather / tp_reducescatter / moe_alltoall | 同上 | 仅平台分支 | 否 | p2p 用 broadcast 代理（H-P2P-AS-BROADCAST），RS 用 reduce 代理（H-RS-AS-REDUCE）。无 Snp。 |
| 平台 `mix_15_1` | 同上 | 仅平台分支 | **是，但含义不同** | 15:1 是大小包尺寸比（7680 B : 512 B），两次 run 顺序执行（H-NO-SIMULTANEOUS-MIX），不是 Dat:Snp 占空比。假设 H-MIX-15-1 原文：公开 NCCL/LLM 表征没有给出 15:1；取 15 是为了对齐 M-5 的扫描粒度，与机制循环。 |
| 卡「推理混合 15:1（KV/P2P+Snp）」 | 卡 §4、§6 | **不在** | 卡内定义 | 无成分定义；本征 Snp 发生器需要新写（仿真器结构改动）。 |
| harness `mixed` | `models/P-0198/M-5r1/harness.py` | 不在（作者探针） | 是（rebind 15:1） | gather 48 Dat→节点 0 + 6 笔均匀 Snp。N=12、n=3、flit=txn、到达即完成（无 eject 竞争），是减箱。 |
| harness `snp_path` | 同上 | 不在 | 是 | 48 笔均匀 Snp，无 Dat。 |
| LLM `decode-*` / `mlperf-*` / `prefill-*` | `/workspace/workloads` | 在 | 否 | 是服务级 ISL/OSL trace，不是 NoC 流量。按规定不得代替 NoC 负载，本评审未使用。 |

负载代表性三问：

- **推理混合有没有代表性？** 没有。库里没有，soc_sim 也没有本征 Snp。平台推理包的 7 个推理类全部不含 Snp。卡称推理 Snp「稀疏但延迟敏感（目录/一致性栅栏进推理尾）」，在库里、平台里都找不到出处，只能当假设。
- **15:1 在库里普遍吗？** 不普遍。`/workspace/workloads` 与 `/workspace/baselines` 零出现。平台里唯一的 15:1 是尺寸比扫描点，而且是从 M-5 反推出来的。15:1 只能当压力扫描点，过线是必要条件，不是代表性证据。卡 §4 自己要求的 3:1 / 7:1 列必须同表报。
- **收益是不是只在单一 benchmark 上出现？** 是。全部数字（7.8→1.0、19.0→1.0、Dat 0.569）来自同一个减箱 harness：一个 Dat 图案（gather→节点 0），一个 Snp 图案（均匀），3 个种子。Dat 0.569 的成因和卡自己承认的 0.583 伪影相同：harness 到达即完成，ghost 等于给 root 第二个 eject 口。soc_sim 的 AIC 终端 RX 深度是 4，HA 的 Dat RX 是 13（`Endpoint.h`），eject 有限，这条收益不能外推。

## 五条逐项结论

### 1. Snp flit 无数据载荷，Dat 走 Snp 线的物理位宽

- **结论：未闭合，但有补救，不判致命。**
  - 卡 §5 只列了 FSM、4×4 绑定表、计数器，没有 Snp 导线加宽，也没说明拆拍。T0 第 7 条已点名这是整条 M-5 线共有的问题。
  - soc_sim 里 Dat 与 Snp 是不同的 flit 结构（`CHIDatInfo` / `CHISnpInfo`）。Dat 按 64 B beat 计（`kBeatBytes=64`，512 B = 8 beat）。Snp 导线位宽在卡、T0、库里都**未知**。
  - 本轮钉死 RTL 不改，所以加宽 Snp 线不在本轮合法空间里，只剩拆拍：一个 Dat beat 在 Snp 线上占 k 个槽，k 未知。
- **对负载和评估的含义：**
  - 拆拍会让 ghost 在 Snp 环上的占用（卡的 `ρ_wire`）变成 k 倍，直接抬高 Snp 等待。15:1 KILL 列必须在拆拍后测。
  - Dat 侧 `C_dat_eff_sb` 要除以 k。
  - 新分支的仿真器若把 ghost Dat 当成一个 Snp 槽（像 harness 的 flit=txn），Snp 和 Dat 两列都会偏乐观，结果作废。评估层必须先声明 k（或位宽比）再跑。

### 2. 优先级反转：上游 ghost 有过路优先、可能饿死下游 Snp、没有密度上限

- **结论：成立，卡未闭合。**
  - 卡 §2.2 规则 1「过路 flit 仍赢」对 ghost 同样适用。steal-back 只看**本地** `Snp pending`，没有 ghost 段密度上限。
  - 卡**没有**声明依赖库内 i-tag 注入饥饿预留（T0 指出在 `src/TCsHighWay.cpp:894` `tryItagProcess`），也没说 ghost 是否服从 Snp 环的 i-tag 保留槽。现在「下游 Snp 等待有界」没有任何依据。
- **对负载和评估的含义：**
  - 最坏情况出现在 gather/reduce/allreduce 的扇入路径和 alltoall 上，即推理集合本身，Snp 源位于热 ghost 源下游的时候。
  - harness 的均匀 Snp 加 6 笔稀疏 Snp 暴露不出这种情况。评估必须按节点位置分列报 Snp p99 和最坏值，并跑一个对照臂：ghost 服从 i-tag 与不服从。
  - 只有服从 i-tag 才能过线的话，i-tag 依赖要写进机制卡。

### 3. 弹出失败的 ghost 在 Snp 环上绕圈，会不会让 Drain 无限期卡住

- **结论：可能，卡没给上界，现有探针也测不到。**
  - DRAIN 要求清空旧世代 ghost（卡 §2.3）。ghost 在目的地弹出失败就留在 Snp 环上 orbit。卡既没定义 orbit 圈数上限，也没定义 Drain 超时或逃逸路径。e-tag 是否跨物理环覆盖 ghost 也没定义（T0 第 3 条）。
  - harness 的 `_complete` 到达即完成，eject 永不失败，所以这条在现有证据里**完全没被测过**。
- **对负载和评估的含义：**
  - soc_sim 的 eject 深度有限（AIC RX 4、HA Dat RX 13），orbit 必然出现。最热的汇点正是 gather/reduce/allreduce 的 root，也就是推理集合。
  - orbit 期间 ghost 占着 Snp 槽，Snp 尾变差；Drain 卡住时 FSM 不回 STEADY，Dat 收益也丢了。
  - 必须报：Drain 时长分布与最坏值、orbit 圈数分布、ghost eject 失败率。Drain 最坏值不收敛，按正确性缺陷处理。

### 4. 被 NACK 的 ghost 重注入时，数据从哪里来

- **结论：未闭合。**
  - 卡写「接受集外 → NACK / 原 Dat 环重注入」，失配 holding 深度为 1，没写数据副本在哪里。有两种读法：
    - 数据在 RBRG 的 1 深 holding 寄存器里，就地转到原 Dat 环。卡没明说，而且 holding 满了以后怎么办没有答案。
    - 源 NI 保留副本直到确认。这需要新的保留存储，卡 §5 没有计入。
  - soc_sim 的 HA 回读：`service_replies` 发出 Dat beat 后条目即释放，没有副本。
- **对负载和评估的含义：**
  - 若需要源端副本，HA 的 Dat TX 条目（`Endpoint.h` 注释 hardware_setup 2.6：TX Dat 深度 20）占用时间会变长，HA 吞吐下降。在 kv_decode / weight_reread 这类 HA 读密集负载上会直接显形。
  - 评估必须报 `bind_mismatch_redirect` 计数（稳态目标 0），以及 NACK 时的数据来源实现。卡称不丢包，评估不能只看 completions，要逐笔核对。

### 5. 对照项：关 drain、只按 header 解码；效果相同的话 epoch/bind 就是赘余，新颖性再降

- **结论：高风险，预期大概率等价。**
  - 现有唯一探针已经是「只按 header 解码」：到达即完成，不查 `epoch_tag`/bind。Drain 在 harness 里只起到门控 ghost 新注入的作用。
  - soc_sim 现有全部流量类的本征 Snp 为 0，steal-back 根本不触发。在问题自带的 endpoint 上，M-5r1 实际上等于「Dat 借 Snp 环空槽」。
- **对负载和评估的含义：**
  - 必须同表跑 drain-off + header-only 臂，与 `sb-off`、`ghost-off`、`tail-only`、rebind-off、源端流控并列，不平均。负载覆盖问题自带的全部流量类加评审钉死的 Snp 档。
  - 若 drain-off + header-only 在 Snp 列和推理 makespan/尾两项上都不差于 on-arm，epoch/bind 应删除，新颖性降到多物理子网负载均衡一级（T0 已列近亲）。
  - 本评审的新颖性 2 分以这个臂的结果为准，可上调也可下调。

## 有条件通过的条件（评估层）

1. 本征 Snp 发生器在 bufferless-ring-noc 新分支实现，默认关闭。参数由评审方钉死（见「评估层必须验证的一个假设」），不得由作者事后选。
2. 先声明 Snp 线位宽比，或拆拍系数 k，再跑；ghost 不得按一个 Snp 槽计。
3. 主列是推理 makespan 与 p99，跑平台推理包的各类。15:1 / 7:1 / 3:1 同表，每个流量类分列。问题自带的均匀读写与全集集合（含 alltoall）作 full-envelope 对照。
4. 第 2–5 条的遥测（按位置的 Snp p99/最坏值、Drain 最坏值、orbit 圈数、NACK 来源、redirect 计数）全部要出。
5. 卡和 harness 的数字（7.8、19.0、1.000、0.569、0.583、17.05、32.59、1.5625、0.55–0.85）一律未签字，不进周报，不当 card-claim。

## KILL 条件复述（原样）

- cycle 级 KILL：duty 15:1 下 Snp makespan 相对 rebind-off 必须 ≤1.4（<1.5625），snp_path 与推理混合两列都要满足，不允许平均、不允许用 Dat 收益抵扣。
- 卡上 7.8→1.0 / 19.0→1.0 未签字，只当假设。
- 主指标：推理 makespan 与尾延迟。RTL 不改；仿真器结构只在 bufferless-ring-noc 新分支上改。
