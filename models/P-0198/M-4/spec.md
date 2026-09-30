# T2 spec · P-0198/M-4 AODI（年龄有界对向偏转注入）

## 1. Identity / scope / sources

| Field | Value |
|-------|--------|
| ID | P-0198 / M-4 |
| Name | Age-Bounded Opposite-Ring Deflection Inject (AODI) |
| Problem | `problems/P-0198.yaml` |
| Mechanism | `mechanisms/P-0198/M-4.md`（PR #53 tip；main 尚未着陆卡正文，本 spec 摘自 T1-return-1 卡 + T1） |
| T1 | `reviews/P-0198/M-4/tier1_synthesis.md`（PR #61 已合 main；T1-return-1，过线 → T2 / #eval） |
| Envelope | DV200 `tests/soc_sim`（同源 `github:lukebest/bufferless-ring-noc`） |
| Style | LIMINAL / roofline（2×2 公路槽守恒 + 不对称占用造洞；非吞吐曲线拟合） |
| Out of scope | cycle 级 2×2 / Rejoin 同拍时序；多节点同步偏转相关突发；RBRG 跨环；team-384dmc / decode-* / STREAM 代理 |

**禁止编辑** `mechanisms/`、`reviews/`、`problems/`、`FUNNEL.md`。本树只新增 `models/P-0198/M-4/{spec.md,model.py,insight.md}`。

**禁止混结论**：本卡不引用、不合并 M-1 / M-2 / M-5 的收益或失败叙事。

### 信封（口径冻结）

| Quantity | Value | SOURCE |
|----------|--------|--------|
| 拓扑 | 12 top + 2 bottom；CHI Req/Rsp/Snp/Dat 各自独立成环；环间经 RBRG | 问题 YAML / bufferless-ring-noc |
| highway | 每方向每拍 **1** 槽；无片上 flit 队列 | 问题 YAML；卡 §1 |
| 请求粒 | 512 B（均匀读/写基线） | 问题 YAML |
| outstanding | 读 512 / 写 256（AIC；额外流控关） | 问题 YAML；卡 §4 |
| 端点 | 分流量类 makespan、完成事务数、collapsed；opposite-ring util；分桶 inject-hole | 问题 YAML；T1 条件 2 / 4 |
| 范围 | 仅同 CHI 通道 CW↔CCW；禁跨 Req/Rsp/Snp/Dat | 卡 §2.1 |

### 公开基线钉（harness 输出，非硅；与兄弟 P-0198 解析模型同一组 T_off）

Makespan（`docs/srcfc_ca_model/data.json` scheme=`off`，与问题 YAML 一致处优先 YAML）：

| 流量类 | T_off (ns) | collapsed（公开扫描） | SOURCE |
|--------|------------|----------------------|--------|
| uniform_read | 4403.2 | 峰值后坍至 ~2.8–3.4 TB/s（YAML） | 问题 YAML；data.json |
| uniform_write | 4834.6 | 平台 ~5.5 TB/s（YAML） | 问题 YAML；data.json |
| broadcast | 492.0（data.json）；YAML 强调 peak goodput ~117.76 B/ns、collapsed=false | false | YAML + data.json |
| gather | 537.2 | true | data.json + collapse_settings |
| reduce | 537.2 | true | 同上 |
| allgather | 1668.6 | true | 同上 |
| allreduce | 990.6 | true | 同上 |
| alltoall | 4098.0 | true | 同上 |

均匀读负载曲线钉：offered ~5767 B/ns → goodput ~5761 → 崩至 ~2.8–3.4 TB/s。SOURCE: 问题 YAML。

均匀读/写完成事务数钉：各 **46080**。SOURCE: 问题 YAML。集合类 N_txn **未公开**——不得编造；只报相对完成比。

**0.85** = 问题及格线 / 卡约束条，**不是**测得均值。禁止用各类平均加速或 min/mean≥0.85 叙事过关。

**卡宣称区间（card-claim，非测得）**：

| 占用态 | card-claim T/T_off | 置信 |
|--------|-------------------|------|
| 不对称占用（偏读 / 偏一侧环） | **0.70–0.95×** | 中 |
| 双忙饱和 / alltoall 打满 | **0.95–1.05×**（预期增益 **≈0**） | 高 |

alltoall / 双忙饱和 **单独成行**，**不得**折进 0.50–0.85× 或 0.70–0.95× 聚合。

**无公开硅**：不得做 ±15% vs silicon。2×2 槽会计精确；绝对 makespan 仅在假设 H-INJ-DOM 下由相对比缩放 T_off，并分列标注。

**禁止外卡钉**：H100、team-384dmc、decode-*、team-interleave-microbench 不进本卡评测。

## 2. Variables

| Symbol | Unit | Domain | SOURCE |
|--------|------|--------|--------|
| N_dir | 1 | 2（CW/CCW） | 卡 / 拓扑 |
| N_chi | 1 | 4（Req/Rsp/Snp/Dat） | 卡 §2；禁跨通道 |
| S | slot/cycle | **1** per direction × ring | 卡 §1；公路槽守恒 |
| ρ_pref, ρ_opp | 1 | [0,1] | 首选向 / 对向过路占槽率；**UNKNOWN 实测**，H-RHO-CLASS |
| c | 1 | [−1,1] | Frechet 相关；双忙饱和取 +1 | H-CORR |
| P(pref_only) | 1 | [0,1] | P(pref busy ∧ opp empty) |
| P(dual) | 1 | [0,1] | P(pref busy ∧ opp busy) |
| I | 1 | {0,1} | 本拍 inject pending；H-PEND 下饱和相取 1 |
| λ_age | 1 | (0,1] | P(age < AGE_MAX \| transit)；H-AGE |
| AGE_MAX | 1 | 8（可配） | 卡 §2；**只**界偏转次数 |
| age | 1 | 0..15（头 4b） | 每次**提交**偏转 age++ |
| φ(p) | hop | ≥0 | 重入武装后、沿首选向最短路径剩余跳；**禁止 Σage** |
| H | hop | ~6（12 节点环半周量级） | 解析尺度；H-HOP |
| η_use | 1 | [0,1] | 不对称态下 pending 注入真正吃洞的份额；H-USE |
| κ_mig | 1 | [0,1] | 偏转 flit 滞留对向的占用回填；H-OPEN 默认 0 |
| p_hole_asym | 1 | [0,1] | 单忙桶 inject-hole 率 |
| p_hole_dual | 1 | **≡0** | 双忙桶；硬断言 |
| p_inj | 1 | [0,1] | 单口有效注入成功（诊断，非端点） |
| ρ_opp_hat | 1 | [0,1] | AODI 后对向利用率（须上报） |
| T_off | ns | 上表 | 公开基线 |
| T_hat | ns | — | 模型预测 makespan（相对缩放） |
| N_txn | 1 | 46080（仅均匀读/写公开） | 问题 YAML |
| G_peak | B/ns | ~5761 | 均匀读峰值；YAML |
| G_coll | B/ns | ~2.8e3–3.4e3 | 坍塌带 |

## 3. First-principles equations

### 3.1 公路槽守恒（精确，无拟合）

每节点、每 CHI 通道、每拍恰好 **两个** 物理公路槽（CW 一槽 + CCW 一槽）。无第三槽、无侧缓、无静默丢。

```
S_cw + S_ccw = 2
occupied ≤ 2
```

AODI **不能 mint 槽**。合法造洞 = 把挡路 flit 挪到**已经 empty** 的对向槽，首选向出口留给注入。双忙时两槽已满，注入必须等待。

### 3.2 2×2 真值表（硅片契约；穷举）

对 inject pending = yes、首选向 = CW（CCW 对称）：

| CW in | CCW in | 合法动作 | inject-hole | 占用（后） |
|-------|--------|----------|-------------|------------|
| busy T | empty | T→CCW 偏转；CW 注入 | **1** | 2 ≤ 2 |
| empty | busy U | 不挡首选向：CW 直接注入；**不必**偏转 U | 0 | ≤2 |
| empty | empty | CW 直接注入 | 0 | 1 ≤ 2 |
| busy T | busy U | **仅**直通或门控 swap；**禁止注入** | **≡0** | 2 |
| busy T | busy U + 声称 inject | **非法第三槽** — 硅片不得实现 | — | 3 > 2 |

行 2 与卡表「empty/busy/yes → 偏转 U 并在 CCW 注入」对齐的是 **首选向 = CCW** 的对称行，不是「首选向已空还去挡自己」。解析实现：`preferred` 参数化，只在 `pref busy ∧ opp empty` 时置 hole=1。

**CONSTRAINT (dual-busy hole≡0):**

```
P(dual) > 0  ⇒  p_hole | dual  ≡  0
```

仿真或模型若在双忙原子上给出 hole>0 → **机制失败**（发明第三槽或丢/缓）。`model.py` 硬断言。

双忙下 AODI = 基线 fail-wait。**预期增益 ≈0**。H-SWAP：本解析取双忙 **只许直通**（swap 若允许必须 age++ 且受 AGE_MAX 截止；无限 swap 不降 φ → 活锁）。

### 3.3 占用联合（Frechet；H-CORR）

```
P_ind  = ρ_pref · ρ_opp
P_lo   = max(0, ρ_pref + ρ_opp − 1)
P_hi   = min(ρ_pref, ρ_opp)
P(dual) = clip( P_ind + c · (P_hi − P_ind if c≥0 else P_ind − P_lo) , [P_lo, P_hi] )

P(pref_only) = ρ_pref − P(dual)      # 不对称、可合法造洞
P(opp_only)  = ρ_opp  − P(dual)
P(empty)     = 1 − ρ_pref − ρ_opp + P(dual)
# 守恒：pref_only + opp_only + dual + empty = 1
```

alltoall 双忙饱和：`c → +1` ⇒ `P(dual) → P_hi` ⇒ `P(pref_only) → 0` ⇒ 合法洞消失。**不得**用独立假设（c=0）给 alltoall 假装还有不对称窗。

### 3.4 Inject-hole 分桶（禁止只报 inject-success）

H-PEND：注入饥饿相 I=1。H-AGE：过路 flit 以 λ_age 可被偏转。H-USE：η_use 吃洞效率。

```
p_hole_asym = η_use · P(pref_only) · λ_age · deflect_enable
p_hole_dual = 0                         # HARD；与 ρ、η 无关
p_inj_off   = 1 − ρ_pref                 # fail-wait：首选向空才注入
p_inj_on    = p_inj_off + p_hole_asym    # 合法额外洞
```

`deflect_enable=0`（消融臂）：`p_hole_asym=0`，`p_inj_on=p_inj_off`。

诊断列可打 p_inj；**端点列必须同时打** opposite-ring util、completions、分桶 hole。禁止 inject-success-only 叙事。

### 3.5 逐包 φ（不是 Σage）

包 p 的进度：

```
若已在首选向：     φ(p) = 沿首选向到目的的剩余跳数
若在错向且已武装： φ(p) = 1（rejoin）+ 首选向剩余跳
若在错向且未武装： φ 不计入「已前进」；包仍占错向槽等待（bufferless）
```

**进度引理（解析探针，非测得）：** `n_deflect(p) ≤ AGE_MAX`。截止后仅直通 + 条件 Rejoin（首选向出口空才 1 拍 U-turn）。每次成功 rejoin 或首选向前进：φ 严格下降。φ=0 到达。

**禁止**：用全环 Σage 或平均 age 当进度。age 上涨只说明发生过偏转事件。

**φ 冻结（Archi 条件）：** Rejoin 无抢占。

```
P(rejoin) = P(on_wrong_ring) · (1 − ρ_pref)
E[wait_rejoin] = 1 / max(1 − ρ_pref, ε)     # H-REJOIN，几何
flag_phi_freeze = (1 − ρ_pref < ε)
```

`flag_phi_freeze` 为真时机制 **不** 保证有界到达——延迟可无限拉长。本解析标旗，不假装闭合。

### 3.6 对向利用率与完成数

开环（H-OPEN，主表默认 κ_mig=0）：

```
ρ_opp_off = ρ_opp
ρ_opp_on  = ρ_opp                         # 一阶不回填
```

闭环迁移（H-MIGRATE，灵敏度）：

```
Δρ = κ_mig · p_hole_asym · E[wait_rejoin]
ρ_opp_on = min(1, ρ_opp + Δρ)
```

κ_mig→1 时不对称窗可被镜像灌满 → 退化为双忙 → 增益坍到 ≈0。须报 `ρ_opp_on`，禁止只报首选向注入成功。

完成数：

```
# 等功（跑完同一批事务）：C_eq_work = N_txn（公开者）或 n/a
# 等时（T_off 窗）：C_eq_time / C_off ≈ T_off / T_hat   （H-INJ-DOM 代理）
# 对向完成代理：C_opp_rel = ρ_opp_off / max(ρ_opp_on, ε) 的倒数占用惩罚
#                若 ρ_opp_on 上升而 C_opp_rel<1 → 迁移伤害旗
```

等功下列完成数相同不是「无效果」；效果在 makespan 与对向 util。

### 3.7 相对 makespan（H-INJ-DOM + 受害税）

对 inject-fail 主导的已坍集合类，以及占用窗下的均匀读写对照：

```
T_inj / T_off = p_inj_off / p_inj_on      # 纯注入机会；双忙下 ≡1
```

偏转受害包多走 ≥1 跳并等待 Rejoin（H-VICTIM）：

```
extra   = 1 + E[wait_rejoin]
f_vic   = min(1, p_hole_asym / max(ρ_pref, ε))
T_vic/T = 1 + extra / H
T_mix / T_off = (1 − f_vic) · (T_inj / T_off) + f_vic · (T_vic / T)
```

双忙：`p_hole_asym=0` ⇒ `T_inj=T_mix=T_off`（增益 **≈0**）。**单独成行。**

broadcast 与未坍类：主列仍打印占用与 hole 桶；T_hat 标为模型相对，不把 card-claim 当测得。均匀读峰值后 goodput **不**用 1 拍 hole 解释数量级崩塌（见魔法缺口）。

**禁止**把 alltoall 的 ≈1.0 与 gather 的不对称比平均成「AODI 加速比」。

### 3.8 消融臂（必须分列）

| Arm | deflect_enable | 含义 |
|-----|----------------|------|
| deflect-off | 0 | 主消融；不对称下 makespan 应回退到基线；无差异不得归因 AODI |
| AODI-on | 1 | 满机制（Rejoin 仍条件空口） |
| rejoin-off（可选对照） | 1 | 关 Rejoin；φ 在错向可冻结——诊断，不主归因 |

**禁止** inject-success-only 列替代上表。每臂上报：T_hat、ρ_opp、completions、hole_asym、hole_dual。

### 3.9 流量类占用（H-RHO-CLASS；假设，非实测）

与基线读/写不对称同向；alltoall 钉死双忙相关。数值可扫，不得当硅。

| class | ρ_pref | ρ_opp | c | 占用态 |
|-------|--------|-------|---|--------|
| uniform_read | 0.72 | 0.28 | 0.0 | 不对称 |
| uniform_write | 0.68 | 0.38 | 0.1 | 不对称（更弱） |
| broadcast | 0.40 | 0.18 | 0.0 | 不对称；基线未坍 |
| gather | 0.78 | 0.25 | 0.0 | 不对称 |
| reduce | 0.78 | 0.25 | 0.0 | 不对称 |
| allgather | 0.82 | 0.48 | 0.2 | 混合 |
| allreduce | 0.80 | 0.52 | 0.25 | 混合 |
| alltoall | 0.93 | 0.93 | **1.0** | **双忙饱和（单独行）** |

## 4. What must stay cycle-level（Dr.Sim；本解析禁止替代）

下列不得用平均占用冒充测得 makespan：

1. 每节点 × 四通道 2×2 同拍求值；`inject-hole` 与 busy 掩码 **同拍** 采样  
2. 分桶 hole 计数（单忙 / 双忙）；双忙桶总和必须为 0  
3. age++ 仅偏转提交；AGE_MAX 后 `deflect_enable=0`  
4. Rejoin 独立口、深度 0、出口空才开火；不得复用为注入口  
5. 逐包 φ 全生命周期（含未武装错向空转）；禁止 Σage  
6. 多节点同拍偏转相关、对向镜像灌满  
7. Warm-up 至 age 分布稳态；满 12+2 + 点对点 + 全集；减箱 ≠ 全信封  

## 5. Calibration / PASS lines for this analytical artifact

| Check | Rule |
|-------|------|
| 槽守恒 | 每个真值表原子 `occupied ≤ 2`；非法第三槽行必须 FAIL |
| 双忙 hole | 所有扫描点 `p_hole_dual == 0`；否则机制失败 |
| 分列 | 每流量类一行；alltoall **永不**折进不对称聚合 |
| 消融 | 打印 deflect-off；不对称类 T_off_arm ≥ T_aodi 才可归因 |
| 卡区间 | 0.70–0.95× / 0.95–1.05× 标 **card-claim**，非测得 |
| φ | 探针用剩余跳，不用 Σage；ρ_pref→1 打 freeze 旗 |
| 端点 | 对向 util + completions 与 hole 桶同表；禁 inject-success-only |
| 灵敏度 | (ρ_pref,ρ_opp,c) 与 (η_use, κ_mig) 两对最敏感参数出表 |

## 6. model.py contract

- stdlib only；`python3 models/P-0198/M-4/model.py`  
- 无外部数据文件；T_off / N_txn / G 钉写在常量区并注释 SOURCE  
- 打印：真值表、双忙 hole≡0 断言、φ 走步（非 Σage）、分流量类（无均值）、分桶 hole、对向 util、completions、deflect-off 消融、灵敏度、魔法缺口  
- 退出码 0（断言失败则非 0）  
- 不向总监/周报投递未审计数字（流程约束；本文件可含模型输出）
