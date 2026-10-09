# P-0198 / PR #1 第四轮（gate r3）只读审计 —— 3DIO 挂接修正 + os512 饥饿判定

- 仓库：lukebest/bufferless-ring-noc PR #1，分支 `cursor/p0198-llm-noc-baseline-aa90`
- 审计 tip：`242aae476225313d1259c2e8e40eccc2053b542c`（`git ls-remote` 核对一致）
- 本轮新增提交：c46bf23（3DIO 挂接改为候选集，按 die×ring 汇总）、242aae4（每个可启动的 3DIO 挂接下报告 os=512 饥饿）
- 审计方式：只读。所有运行都在 scratch 克隆 `/workspace/brn-p198-audit`（分支 pr1r4）和 `/tmp/r4` 下进行。对目标仓**无** commit/push/评论。作者代码**未改动**：探针和敏感性运行都通过 `/tmp/r4/wrap.py` 进行。它原样调用作者的 `run_soc.main()`，只在 gen_config 生成之后编辑**输出目录里的生成配置**（manyring.csv 的 3DIO 行、Network_parameter*.csv 的 Link 延迟），每次编辑都记录在 `<run>/config/audit_edit.json`。
- 构建：`artifacts/soc_sim/build/92c01c043f319bb2/soc_sim`（`run_soc.py --no-sanitize --build-only`，clang 19.1.7）
- 规范：只用相对量；不做硅片结论；不使用 ±15%。
- 饥饿线沿用 R3 §2.1：S0 同一 die、同一 ring、物理 CS 序；S1 R−3·SE_boot>1.10 且 ≥7/8 种子 R_s>1；S2 下游 ≥1.0 cycle/inject 且 Δ≥0.5；S3 方向按 TNetwork.cpp:83-106（cw 下游=高 CS，cc 下游=低 CS）。


## 0. 摘要

- **复现**：288 次运行，与 `os512_starvation_line.csv` 的 672 行逐键比对，均值、R、种子数、starve 全部一致；只有 26 行 dio_bot 的 R−3SE 有小幅 bootstrap 差异，均不越线。
- **挂接**：作者的 8 条崩溃全部复现，审计补测的 coc_up_1x2 同样崩溃。原因都是文档与库的真实不兼容：top 无 3DIO 时找不到路由；空 UP 槽只有 3 个，而 DAW 需要 8 个；1×1 需要换环设备而 top 没有。不属于作者能修的配置 bug。另外，可启动的挂接远多于作者的两种，审计补测的 rsv_up_plus_down 与 mirror 也同样越线（§1.3）。
- **die 不对称**：是 collective root = rank0 落在 die1 造成的 artifact。root=10 时饥饿整体移到 die2（§3.3）。root=5（环中段）时饥饿线不触发，但阻塞反而更重（§3.4）。
- **coc_down r1 cw**：是同一 root incast 的 cw 支路，S2 余量只有 3%（§4）。
- **时延敏感性**：max 角点和 bottom-min 角点下结论保持；top=1 时饥饿类死锁，不构成反转（§5）。
- **闸门判定：放大（有条件）**，详见 §7。章节按写作顺序排列：§1.3 与 §3.4 是后补的小节，位于 §5/§6 之后。

---

## 1. 挂接核查（check 1）

### 1.1 逐项复现作者的崩溃声明

探针基准：kv_decode / none / seed 20260903 / os512 / dest-shuffle，只改 `--top-3dio-place`。结果目录 `/tmp/r4/probe/*`。

| place | 文档依据 | 本审计结果 | 断言/现象 | 判定 |
|---|---|---|---|---|
| none | noc_setup.md:436（top 无 3DIO ConnectDev） | 崩溃 | TBridge.cpp:502 `don't find the dstPort in Router` | 文档/库不兼容（见下） |
| aic_up_1x1 | :123-126 + :137 UP | 崩溃 | TCrossStation.cpp:181 `m_niList.at(direction-UP_PORT)==nullptr` | 库约束：每个 CS 只有一个 UP NI，AIC 已占用 |
| aic_up_1x2 | 同上 | 崩溃 | TCrossStation.cpp:181 | 同上 |
| coc_up_1x1 | :133-135 + :137 UP | 崩溃 | TCrossStation.cpp:181 | 同上（COC 已占 UP） |
| **coc_up_1x2**（作者未列，审计补测） | 同上 | 崩溃 | TCrossStation.cpp:181 | 同上，作者表格的这一空缺已补齐 |
| reserved_up_1x2 | :90 CS9/10/20 | 崩溃 | TBridge.cpp:502 | 只有 3 个空 UP 槽，DAW 却要 8 个端口（topology.md:80-94 `3Dio_daw_entry (8,…)`），所以 0x53-0x57 无路由 |
| aic_down_1x1 | 推断 | 崩溃 | TBridge.cpp:504 `pRouter->m_isCanArrived` | 库约束：top 只有 2 条 HRing、没有 ChangeRing/RBRG（生成的 manyring 中计数为 0）。1×1 把 0x50-53 只挂 ring0、0x54-57 只挂 ring1，而 8 路交织要求每个 AIC 都能到达全部 8 个端口 → ring1 源到不了 ring0 端口 |
| coc_down_1x1 | 推断 | 崩溃 | TBridge.cpp:504 | 同上 |
| aic_down_1x2 | 推断 | 启动，4880 ticks，1920/1920 完成 | — | 可用 |
| coc_down_1x2 | 推断 | 启动，5697 ticks，1920/1920 完成 | — | 可用 |

**结论：作者的 8 条崩溃声明全部复现，断言行号一致。**

这些崩溃都不是作者能用配置修掉的 bug，而是“文档描述”与“库的建模约束”之间的真实不兼容：

1. 文档 :436 说 top die 没有 3DIO ConnectDev，跨 die 走 DAW + `connectDevice(..., is_cross_die=true)`。但库里的 `connectDevice` 仍要求端口出现在本 die 的 ConnectDev 中（否则在 TMultiRing.cpp:527-529 断言），路由表也需要 0x50 这一目的端口（TBridge.cpp:502）。所以“top 不挂 3DIO”在库里不可运行。文档要么描述的是另一层抽象，要么不完整。
2. 文档 :137 说“所有设备通过 UP 挂载”。AIC 占 10 个 CS、COC 占 8 个 CS 的 UP，空 UP 只剩 CS9/10/20 三个，而 DAW 需要 8 个 3DIO 端口。因此**按文档字面不存在可启动的 8 端口挂接**，任何可启动方案都必须用 DOWN（或者让 DAW 少于 8 个端口，这需要改 daw，不属于配置）。DOWN 本身是库支持的合法方向：bottom 的 D2U_SLLC 0x21 就用 DOWN（noc_setup.md:263-267）。
3. 1×1 要求每个源都能到达每个 3DIO 端口，top 又没有换环设备，所以 1×1 只能配合“按环分区的 DAW”，现有配置无法表达。**1×2（每个端口同时挂两条环）是唯一可行的结构。**

小问题（不影响结论）：
- `gen_config.py:631`、`run_soc.py` 的 `generate_config`、`generate.py:91/499` 中 `--top-3dio-place` 的默认值仍是 `aic_up_1x1`，即一个**必崩**的选项。不显式传参的旧脚本会直接崩溃。建议默认改成一个可启动候选，或者干脆不设默认值、强制显式指定。
- `analyze_signoff`/`pool.main` 的 roles 元组 `("dio_bot")` 少了逗号，实际是字符串。`role in "dio_bot"` 对现有 role 名碰巧无害，但属于潜在 bug。

### 1.2 候选空间是否覆盖文档允许的范围

作者只给了两个可启动候选（aic_down_1x2 = DOWN@CS{0,2,4,6,8,11,13,15}；coc_down_1x2 = DOWN@CS{1,3,5,7,12,14,16,18}）。两者都**偏向低 CS 段**：aic 不含 17/19，coc 不含 17/19/20。这恰好与 cc 方向下游（低 CS）重合，存在“挂接几何决定梯度”的风险。审计补测了以下生成配置（同一基准探针）：

| 审计候选 | 挂接 | 启动？ |
|---|---|---|
| rsv_up_plus_down | 0x50-52 UP@CS9/10/20（文档 :90 保留槽，1×2）+ 0x53-57 DOWN@CS{2,6,13,17,19} | 启动（4827 ticks） |
| split_ring_down | 每端口 ring0 DOWN@AIC CS、ring1 DOWN@COC CS（跨环错位 1×2） | 启动（6044 ticks） |
| mirror（高 CS 镜像）| DOWN@CS{19,17,15,13,11,8,6,4} | 启动（5537 ticks） |
| spread（均匀）| DOWN@CS{0,3,5,8,11,13,15,18} | 启动（5047 ticks） |
| DOWN 含 CS20（{0,2,4,6,8,11,13,20}，或 mirror 含 20） | — | **段错误 rc=-11**（原因未定位，未核） |
| spread 含 CS10（{0,3,5,8,10,13,15,18}） | — | 段错误 rc=-11（单独把 CS10 加入 aic 集合则能启动；原因未核） |
| 同一 CS 两个 DOWN（9/10/20 重复） | — | TCrossStation.cpp:181（DOWN 槽同样唯一） |

（结论：可启动空间比作者给出的两点大得多。镜像、均匀、跨环错位的 DOWN 1×2，以及“3 个保留 UP 槽 + 5 个 DOWN”的混合，都能启动；但含 CS20 DOWN 的组合，以及某些含 CS10 的组合会段错误，原因未定位。）

为检验“两个候选都饿 → 与挂接无关”这一推论，审计对 rsv_up_plus_down（最接近文档：用满 3 个保留 UP 槽）和 mirror（几何翻转到高 CS）各跑了 lib_all_on × 8 种子 × 全部 9 个运行单元，结果见 §6。

## 2. 复现作者数字（check 4）

范围：os512 dest-shuffle，8 个种子（generate.SHUFFLE_SEEDS：20260903/11/23/31/41/53/67/79）× 9 个运行单元（8 类，mix_15_1 拆成 large/small）× {lib_all_on, none} × {aic_down_1x2, coc_down_1x2}，共 **288 次运行，全部 rc=0**（`/tmp/r4/os512`）。分析直接调用作者的 `inject_wait.analyze_run` + `pool.pool_gradients`（all_inference；cc/cw；aic/ha/dio_top/dio_bot；end/half），再与 `tables/os512_starvation_line.csv`（672 行）逐键比对：
- 键：arm, place, roles, die, ring, channel, direction, metric。
- 字段：mean_upstream, mean_downstream, R, R_minus_3SE, seeds_R_gt1, n_samples, starve。

结果：
- 672/672 行都找到对应键。
- **mean_upstream / mean_downstream / R / seeds_R_gt1 / n_samples / starve 在 672 行上全部一致**（相对容差 1e-4），**starve 无翻转**。
- 26 行仅 R_minus_3SE 有小差异（≤约 5% 相对）。它们全部是 `dio_bot cw half`，且两边 R−3SE 都远小于 0（不饥饿），对判定无影响；推测是 bootstrap 抽样顺序差异，未深究。

作者声明逐条核对（lib_all_on，die1，Dat，half 指标）：

| 声明 | 作者 | 审计复现 |
|---|---|---|
| aic_down d1 r0 cc：下游 / R / R−3SE / Δ / 种子 | 2.096 / 5.678 / 3.460 / 1.727 / 8/8 | 2.096 / 5.678 / 3.460 / 2.096−0.369=1.727 / 8/8 ✔ |
| coc_down d1 r0 cc：下游 / R−3SE / Δ / 种子 | 1.119 / 8.057 / 1.040 / 8/8 | 1.119 / 8.057 / 1.119−0.079=1.040 / 8/8 ✔ |
| die2 同位置（aic_down r0 cc） | 0.160，不饿 | 0.160（R 1.18，R−3SE 0.83，6/8）✔ |
| end 指标 aic 行 | 下游 2.070 / R 28.72 / R−3SE 9.73 | 2.070 / 28.72 / 9.73 ✔ |

每种子下游（half）：
- lib aic_down d1r0 cc：1.86 2.78 2.11 1.40 2.31 2.24 1.35 2.74，全部 >1。
- lib coc_down d1r0 cc：0.77 0.63 1.59 1.08 1.37 1.34 1.25 0.95，3/8 低于 1.0；池化均值 1.119 只略高于 S2 门限。

越线行的分布：
- lib：所有满足 S0∧S1∧S2∧S3 的行都在 **die1 dio_top Dat**。包括 aic_down 的 r0/r1 cc（end+half）；coc_down 的 r0/r1 cc（end+half）以及 r1 cw（end+half）。
- none：同样只在 die1 越线。包括 aic_down 的 r0/r1 cc half 和 r1 cw end；coc_down 的 r0/r1 cc 与 cw（end+half）。
- **die2 在任何臂、任何挂接下都没有行越线。**

## 3. die1 饿、die2 不饿：artifact 还是真实？（check 2）

### 3.1 配置差异

两颗 top die 的 top 侧配置完全相同：同一份 gen_config 输出，3DIO 同为 0x50-0x57、同一挂接。差异只在两处：

1. **bottom 侧 3DIO 位置**（`soc.cpp wire_mux`，idx = local×8+i）：
   - die1（local 0）用 idx 0-7：H 对在 ring0-3；V 对在 ring12-19 的 CS13/15/18/20。
   - die2（local 1）用 idx 8-15：H 对在 ring4-7；V 对在 ring12-19 的 CS8/9/24/27。
   - HA→3DIO 由 `kHa3dioIdx[partition][local]` 选择，两 die 的 per-port 分布模式相同（i = idx−8·local）。
2. **流量**：`TrafficGen::build_collective` 的 root 默认为 `--collective-root 0`，即 rank0 = die1 core0（AIC 0x0/0x1，ring0/ring1 的 CS0）。
   - reduce（RS）与 allreduce（AR、mix_15_1）的 phase1 是 `add(root, 1, Read, src, src)`，即**由 root 一个 rank 读回全部 20 个 rank 的数据**（×chunks：AR 32、RS 32、mix_L 15）。
   - 这些读回的 DAT 全部经 die1 的 top 3DIO 注入 die1 的环，汇向 CS0。

dio_top Dat inject_succ（die1 / die2；seed 20260903，aic_down，lib）：

| 类 | die1 | die2 |
|---|---|---|
| kv | 7680 | 7680 |
| weight | 30720 | 30720 |
| allgather | 6400 | 6400 |
| alltoall | 1600 | 1600 |
| p2p | 2304 | 2560 |
| **AR** | **7265** | **2560** |
| **RS** | **4961** | **0** |
| **mix_L** | **3424** | **1200** |

### 3.2 按类拆分

aic_down r0 cc：die1 dio_top Dat 下游（half）的 8 种子均值：

| 类 | 下游 |
|---|---|
| RS | 7.39 |
| mix_L | 5.32 |
| AR | 4.90 |
| kv | 0.21 |
| alltoall | 0.19 |
| mix_S | 0.19 |
| weight | 0.18 |
| allgather | 0.17 |
| p2p | 0.08 |

对称类在两颗 die 上都没有梯度（下游 0.1-0.3）。池化后的 all_inference 饥饿**完全由三个汇聚到 root 的类贡献**。

aic_down lib die1 r0 cc 的 CS 剖面（均值）：

| CS | 0 | 2 | 4 | 6 | 8 | 11 | 13 | 15 |
|---|---|---|---|---|---|---|---|---|
| 等待 | 2.13 | 1.75 | 2.86 | 1.60 | 0.91 | 0.50 | 0.10 | 0.07 |

等待随离 root(CS0) 越近而升高。这是**目的地汇聚（incast）在最后几跳上的注入阻塞**，不是单纯的环位置不公平。

### 3.3 移动 root（廉价判别实验）

方法：
- 只重跑受 root 影响的 5 个单元（p2p/AR/RS/mix_L/mix_S）；其余 4 类的 traffic 与 root 无关，直接复用 §2 的运行。
- lib_all_on，8 种子，两种挂接。
- `--collective-root 10` = die2 core0（同样在 CS0）。

| 挂接 | 行 | root=0（作者） | root=10（审计） |
|---|---|---|---|
| aic_down | d1 r0 cc half：下游 / R−3SE / starve | 2.096 / 3.46 / **是** | 0.161 / 0.79 / 否 |
| aic_down | d2 r0 cc half | 0.160 / 0.83 / 否 | **2.140 / 2.26 / 是**（8/8） |
| aic_down | d2 r1 cc half | 0.154 / 否 | **2.316 / 2.69 / 是** |
| coc_down | d1 r0 cc half | 1.119 / 8.06 / **是** | 0.113 / 0.59 / 否 |
| coc_down | d2 r1 cc half | 0.094 / 否 | **1.443 / 9.84 / 是** |
| coc_down | d2 r1 cw half | 0.098 / 否 | **1.273 / 9.20 / 是** |
| coc_down | d2 r0 cc / cw half | 否 | 0.872 / 0.812（R−3SE 8.45/5.79，8/8，但 S2 未过） |

流量随之翻转：root=10 时 RS 的 die1/die2 dio_top Dat（8 种子合计）为 0 / 39568。

**判定：**
- die1 饿、die2 不饿是 root=rank0 落在 die1 造成的 **artifact**，与 die 本身或 bottom 3DIO 位置无关。**饥饿跟着 root 走。**
- 现象本身是真实的：在任何承载 reduce/allreduce root 的 die 上，3DIO→root 的 Dat 注入都会在靠近 root 的下游出现 >1 cycle/inject 的阻塞，两种挂接都如此。

## 4. coc_down r1 cw 越线（check 3）

**复现：**
- lib coc_down d1 r1 cw half：上游 0.071 → 下游 1.030，R 14.51，R−3SE 8.23，8/8，Δ 0.959，四条全过。
- 同 die 的 r0 cw half 下游只有 0.733，S2 不过。

**解释：这是同一 incast 的另一侧。**
- coc_down 把 3DIO 放在 CS1/3/5/7 和 12/14/16/18。到 root(CS0) 的最短路：CS1-7 走 cc（1-7 跳）；CS12-18 走 cw（经 19→20→0，3-9 跳，短于 cc 的 12-18 跳）。
- 两组 3DIO 从两侧汇向 CS0，cw 侧下游（高 CS 半区）同样被上游 CS12/14 的 Dat 占满。
- die1 r1 cw 剖面：

  | CS | 12 | 14 | 16 | 18 | 低 CS 半区 |
  |---|---|---|---|---|---|
  | 全部类 | 0.41 | 0.79 | 1.58 | 1.41 | ≈0.07 |
  | RS 单类 | — | — | 7.08 | 6.30 | — |

- 对照：aic_down 只有 CS11/13/15 三个 3DIO 走 cw，cw 下游只到 0.25-0.44，不越线。

**强度：**
- r1 cw 的 8 种子下游为 0.93 1.57 0.64 1.88 1.24 1.11 0.18 0.69，4/8 低于 1.0。池化值只比 S2 门限高 3%，r0 cw 则不过。
- root=10 时，die2 的 r1 cw 过（1.273）、r0 cw 不过（0.812），与 root=0 时的 ring 选择一致。

**结论：** r1 cw 越线是真实的，属于同一机制（root incast 的 cw 支路）。但 S2 余量很薄，ring0/ring1 之间也不稳定，不应作为独立证据计数。

## 5. 链路时延敏感性（check 5 的一部分）

### 5.1 方法

- 通过 `/tmp/r4/wrap.py` 改写**生成配置**中 `Network_parameter*.csv` 的 Link 时延字段，不改动作者代码，weighted_latency 保持不变。
- 范围取文档值：top 1–3（`noc_setup.md:103`），bottom H 2–4、V 1–7（`noc_setup.md:208`）。
- 库约束 `TRingConfig.cpp:439-440`：一圈时延必须为偶数且 <200。按此约束，各角点的实际一圈时延为：

  | 角点 | top 环 | H 环 | V 环 |
  |---|---|---|---|
  | min（top=1，H=2，V=1） | 22（1×20 + 一段 2） | 50 | 38 |
  | max（top=3，H=4，V=5） | 62 | 100 | 184 / 190 |
  | 作者默认 | 42 | 76 | 148 / 152 |

  **V=7 在库里不可行**：37 段 × 7 = 259 ≥ 200，会触发断言。V 上限最多只能取到 5。所以文档区间的 V 上界本身与库不兼容，记为未核。
- 运行：lib_all_on，os512，aic_down_1x2，8 种子 × 全部 9 个单元，每个角点 72 次。

### 5.2 结果（die1 dio_top Dat cc，half 指标）

| 角点 | 池 | d1r0 下游 / R / R−3SE / 种子 | d1r1 | 是否越线 |
|---|---|---|---|---|
| 默认 | all_inference | 2.096 / 5.68 / 3.46 / 8/8 | 1.890 / 5.38 / 4.01 / 8/8 | 是 |
| **max** | all_inference | 1.633 / 6.07 / 4.35 / 8/8 | 1.733 / 6.04 / 4.57 / 8/8 | **是** |
| 默认 | 只算饥饿类（AR+RS+mix_L） | 5.869 / 7.09 / 3.37 / 8/8 | 5.335 / 6.95 / 4.29 / 8/8 | 是 |
| **max** | 只算饥饿类 | 4.553 / 8.20 / 5.05 / 8/8 | 4.915 / 7.99 / 5.01 / 8/8 | **是** |
| **min** | all_inference | 1.229 / 3.62 / **0.40** / 7/8 | 1.164 / 3.26 / 0.38 / 8/8 | 形式上否（S1 失败），**原因是系统死锁，见下** |

- max 角点：die2 仍不越线（0.128 / 0.115）。lat_max 下 d1r0 每种子下游为 1.64 1.95 1.71 0.94 2.04 1.66 1.57 1.55。
- **min 角点出现死锁**：
  - 完成情况：AR 0/8、RS 0/8、mix_L 2/8、alltoall 2/8 未在 80000 周期内完成；kv、weight、allgather、p2p、mix_S 全部完成。
  - 现象（`latloc/top1/C/out/cycles.csv`）：写 phase0 中 rsp 卡在 349/640；从 <10000 周期起 highway_occ 恒为 35132，ni_inject_fail 持续线性增长。这是环满后永久停滞，不是慢。
  - 定位（AR seed 20260903，每次只改一个维度）：**只把 top 设为 1 就死锁**；只改 H=2、V=1、V=2 都能正常完成。所以触发因素是 top 环一圈 22 ≈ CS 数 21（每个 CS 约 1 个 slot）。
  - 是库的固有行为，还是 itag/etag/leaf 预留在这么小的一圈下的配置问题：**未核**。
  - 能完成的 2 个 mix_L 种子下游达到 25.4 / 14.5，比默认更差。
  - 结论：min 角点的 “S1 不过” 是因为饥饿类在多数种子里进入了死锁，导致样本缺失。这比饥饿更严重，**不能当作“饥饿消失”**。
- 为把 bottom 时延和 top=1 的死锁分开，另跑了 bottom-min 角点（top 保持 2，H=2，V=1），只跑饥饿类 × 8 种子，结果见 §5.3。

### 5.3 bottom-min 角点（top 保持 2，H=2，V=1），只跑饥饿类（AR+RS+mix_L × 8 种子 = 24 次，全部完成）

| 行 | 下游 / R / R−3SE / 种子 | 越线 |
|---|---|---|
| d1r0 cc half | 5.493 / 7.10 / 3.13 / 8/8（每种子：5.53 7.66 4.88 3.72 6.87 3.63 5.10 6.55） | 是 |
| d1r1 cc half | 6.111 / 7.07 / 4.04 / 8/8 | 是 |

与默认值（5.869 / 5.335）基本相同，说明 bottom 时延对这一判定几乎不起作用。

### 5.4 时延敏感性小结

- 在 **max 角点**和 **bottom-min 角点**下，die1 饥饿判定都保持，S1/S2 余量都充足。
- **top=1** 时，饥饿类不是“不饿”，而是环满后永久死锁；能完成的种子饿得更厉害。
- 结论：在文档时延区间内，没有任何一个角点能把判定翻成“不饿”。
- 未核项：
  - V=7 在库里不可行（一圈 <200 的断言），未能测试；
  - top=1 死锁的根因未核。

## 1.3（补）挂接敏感性：另外两种可启动挂接下的 os512 结果

条件：lib_all_on，8 种子，全部 9 个单元，root=0。

| 挂接 | die1 越线行（half） | die1 r0 cc 下游 / R−3SE | die2 |
|---|---|---|---|
| aic_down_1x2（作者） | r0 cc、r1 cc | 2.096 / 3.46 | 不越线 |
| coc_down_1x2（作者） | r0 cc、r1 cc、r1 cw | 1.119 / 8.06 | 不越线 |
| **rsv_up_plus_down**（审计；3 个文档保留 UP 槽 CS9/10/20 + 5 个 DOWN） | **r0 cc、r1 cc、r0 cw、r1 cw** | 1.475 / 10.22（8/8） | 不越线（0.135） |
| **mirror**（审计；DOWN@19,17,15,13,11,8,6,4） | r1 cc（1.098）、r0 cw（1.103）、r1 cw（1.116） | 0.884 / 4.67（S2 不过） | 不越线 |

- 各挂接下都有 die1 的行越线，饥饿在 cc、cw 之间的分配随 3DIO 相对 root(CS0) 的位置而变化。
- 这个变化与 §3/§4 的 incast 解释一致：3DIO 位于 root 的哪一侧，就在哪个方向上饿。
- 在测试过的 4 种互相差别很大的几何（低 CS 集中、COC 位、文档保留槽 + DOWN 混合、高 CS 镜像）里，“root 所在 die 的 3DIO Dat 注入越过饥饿线”这一结论**不随挂接改变**。
- 但越线的具体 ring/方向、以及 S2 余量会随挂接变化：mirror 的 r0 cc 是 0.884，不过线。
- 因此**不必等待真实挂接**也能回答 gate 的“是否越线”。真实挂接只会影响越线位置和幅度（例如 coc/mirror 下余量只有 0.1 cycle 量级）。

## 6. 物理假设核对（check 5；硬性规则：未核的假设不能支撑“放大”，除非敏感性显示它不影响结论）

| 假设 | 值 | 仓内出处 | 是否与平台一致 | 已核/未核 |
|---|---|---|---|---|
| top 3DIO 端口数 | 8（0x50-0x57） | `topology.md:80-94` `3Dio_daw_entry`；`TDaw.h++:24` | 一致 | 已核 |
| top 3DIO 挂接：文档字面 | 无 ConnectDev（:436）/ UP（:137） | `noc_setup.md:436,137` | 库里不可运行：TBridge.cpp:502 / TCrossStation.cpp:181，本审计已复现 | 已核（文档与库不兼容） |
| top 3DIO 挂接：候选 aic_down_1x2 | DOWN@CS0,2,4,6,8,11,13,15，两条环 | `gen_config.py:388-391` | 文档未给出，属推断 | **未核**；敏感性见 §1.3，不影响是否越线 |
| top 3DIO 挂接：候选 coc_down_1x2 | DOWN@CS1,3,5,7,12,14,16,18 | `gen_config.py` coc_down_1x2 | 推断 | **未核**；同上 |
| top 3DIO 挂接：审计补测 rsv_up_plus_down / mirror / split / spread | 见 §1.2 | 审计生成的配置（`/tmp/r4/probe`、`pl_*`） | 推断；rsv 用到了文档 :90 的保留槽 | **未核**；rsv、mirror 都越线 |
| 1×1 挂接 | 不可行 | TBridge.cpp:504；top 无 ChangeRing | 库约束 | 已核 |
| 含 CS20 的 DOWN（以及 spread+CS10） | 段错误 | 审计探针 | — | **未核**（原因未定位） |
| top 链路时延 | 2（区间 1–3） | `gen_config.py` ASSUMPTIONS；`noc_setup.md:103` | 在区间内，常数值无出处 | **未核**；max 角点与默认结论相同；**top=1 死锁**（§5） |
| bottom H 时延 | 3（ring0 前 3 段有文档），区间 2–4 | `noc_setup.md:208`；`topology.md` 5.1 | 只有局部一致 | **未核**；H=2 与 H=4 下结论都保持 |
| bottom V 时延 | 4，区间 1–7 | `noc_setup.md:208` | V=7 违反库的一圈 <200 断言 | **未核**；V=1 与 V=5 下结论保持，V=7 无法测试 |
| 一圈偶数且 <200 | — | `TRingConfig.cpp:439-440` | 库约束 | 已核 |
| bottom 3DIO 位置（die1 用 idx0-7，die2 用 idx8-15） | 见 §3.1 | `soc.cpp wire_mux`；`TDaw.h++:63-83` | 来自 bottom daw.cfg 的抄录 | 实现已核；它**不是** die 不对称的原因（§3.3） |
| collective root | rank0（die1 core0，CS0） | `run_soc.py --collective-root` 默认 0；`TrafficGen.h:243-310` | 是流量假设，不是平台字段 | **已核：die 不对称的根因**；root=10 时饥饿整体移到 die2 |
| reduce/allreduce 的实现方式 | root 单点读回全部 rank（不是 ring/tree 算法） | `TrafficGen.h:295-305` | 与真实 NCCL 风格的 ring-allreduce **不同** | **未核**（流量建模假设；放大后要随 rank 映射一起复核） |
| outstanding | 512（信封 read） | `TrafficGen.h:160-163`；R3 | 信封推导 | 信封已核（R3） |
| CC/CW 方向 | cw → 高 CS；cc → 低 CS | `TNetwork.cpp:83-106`；`TCsHighWay.cpp:1135-1142` | 库内一致 | 已核 |
| 饥饿线 | S0-S3（R3 §2.1） | 审计约定 | 不是平台字段 | 约定 |
| HBM 时延 / AIC credit | 0 / 4 | `gen_config.py:49`；`Endpoint.h:28` | 无文档 | **未核**（沿用 R3，本轮未扫） |

## 3.4（补）root 移到环中段：root=5（die1 core5 = AIC 0xa/0xb，CS11）

条件：lib，8 种子；重跑受 root 影响的 5 个单元，其余单元复用 §2。

| 挂接 | die1 dio_top Dat half（cc / cw） | 越线 |
|---|---|---|
| aic_down | cc：上游 0.220 → 下游 0.106（R 0.48）；cw：1.023 → 1.277（R 1.25，R−3SE 0.62，3/8） | **否** |
| coc_down | cc：1.209 → 0.068（R 0.06）；cw：1.055 → 0.065 | **否**（梯度反向） |
| 两种挂接下的 die2 | — | 否 |

但阻塞并没有消失，只是移到了环中段。RS 单类 aic_down d1r0 cw 的 CS 剖面：

| CS | 0 | 2 | 4 | 6 | 8 | 11 | 13 | 15 |
|---|---|---|---|---|---|---|---|---|
| 等待 | 1.08 | 2.58 | 4.37 | 6.65 | **11.03** | 7.47 | 0 | 0 |

最严重的点出现在紧邻 root 的上游一侧，绝对值比 root=0 时还大。

**含义：**
- S0-S3 是按“环端点 / 半环”定义的位置梯度。只有 incast 的 root 落在环端（CS0）附近时，它才会把 incast 识别为“下游饥饿”。root 在中段时，最热的 3DIO 落在两个半区的分界处，线就不触发，而实际阻塞反而更重。
- 所以“饥饿线越过”依赖于 **root 的环位置**这一流量假设（默认 rank0 = CS0）。它不依赖于 die，也不依赖于挂接。
- 本轮另外确认：**R3 的 os512 数值（下游 1.235）与本轮 2.096 并不冲突**。R3 把 die1 和 die2 混在一个池里，(2.096+0.160)/2 ≈ 1.13，量级一致；本轮按 die×ring 拆开后，die1 更高、die2 不饿。

## 7. 扩规模闸门判定（check 6）

**判定：放大（有条件）。** 判定仅限于模型内、相对量、os512、2 top die + 1 bottom die；不做硅片结论。

### 理由

1. **挂接已修正，且结论与挂接无关。**
   - 文档字面的挂接在库里都不可运行，8 条崩溃全部复现，coc_up_1x2 也补测为崩溃；这是文档与库之间的真实不兼容，不是作者的配置 bug。
   - 在 4 种几何差异很大的可启动挂接下（aic_down、coc_down、审计的 rsv_up_plus_down、mirror），root 所在 die 的 top 3DIO Dat 注入都有行满足 S0∧S1∧S2∧S3，例如 rsv_up_plus_down：r0 cc 1.475，R−3SE 10.22，8/8。
   - 按硬性规则，“挂接未核”这一假设已由敏感性证明不影响“是否越线”。
2. **结论与链路时延无关。**
   - max 角点（1.633 / R−3SE 4.35）和 bottom-min 角点（5.49，饥饿类）都保持越线。
   - top=1 下饥饿类死锁，比饥饿更严重，不构成反转。
3. **复现：** 288 次运行，672 行中均值、R、种子数、starve 全部一致。

### 必须同时写进结论的限定

- **die1 / die2 不对称是 artifact**：根因是 collective root = rank0 在 die1。root=10 时饥饿完整地移到 die2。“die2 不饿”不能被解释为位置或 bottom 布局上的优势。
- **饥饿的本质是 collective root incast**：AR/RS/mix_L 由单个 root 读回全部 rank 的数据，汇入 root 所在 die 的 3DIO。对称类（kv/weight/allgather/alltoall/p2p）在任何 die、任何挂接下都没有梯度。
- **饥饿线依赖 root 的环位置**：root=5（CS11）时线不触发（R<1.3），但 CS8 的绝对阻塞达到 11 cycles/inject。
- **coc_down r1 cw 越线**：真实，是同一 incast 的 cw 支路；但 S2 余量只有 3%，4/8 种子低于 1.0，不单独计数。
- top=1 死锁的根因未核。

### 放大到 12+2 时必须携带的实验要求（否则放大结果不可签）

- **root 位置扫描**：环端 CS0、环中段 CS11，以及 root 所在的 die。
- **饥饿判定**：除半环 S-线外，同时报告“相对 root 的距离剖面”，避免 root 在中段时漏判。
- **挂接**：至少带 aic_down 与 rsv_up_plus_down 两种。
- **时延**：带 top=1 的死锁复核。
- **reduce/allreduce 建模**：单 root 读回是流量建模假设，需要同时跑一个 ring/分段式 collective 作为对照。

### 什么会把判定翻转

- **翻成「不放大」**：
  - 船长认定饥饿线必须在 root 位置扰动下仍成立（root=5 时不成立）；或
  - 船长认定饥饿线针对的是对称流量下的环位置不公平（对称类从未越线）；或
  - 改用真实 collective 算法（无单点 incast）之后，饥饿类不再越线。
- **翻成「先要真实挂接再定」**：
  - 真实平台的 top 3DIO 不在 top HRing 上注入（例如经独立通路直达），使 3DIO→root 的 Dat 不再与 top 环 slot 竞争。这种情况超出了本审计测试过的全部几何。
- **保持「放大」**：任何 top 环注入式挂接；max / bottom-min 时延下的结论均已覆盖。

## 8. 产物与可复核路径

- 复现：`/tmp/r4/os512`（288 次）、`/tmp/r4/repro_rows.json`、比对脚本 `/tmp/r4/cmp.py`
- 探针：`/tmp/r4/probe/*`（含 `config/audit_edit.json`）
- root：`/tmp/r4/root10`、`/tmp/r4/root5`
- 时延：`/tmp/r4/lat_min`、`lat_max`、`lat_botmin`、`latloc`（死锁定位）
- 挂接：`/tmp/r4/pl_rsvup`、`pl_mirror`
- 驱动与分析：`/tmp/r4/wrap.py`（只改生成配置）、`an4.py`、`anset.py`、`starved.py`、`hang.py`
- 未对目标仓做任何 commit/push/评论；本文件未提交。
