# T2 insight · P-0198/M-4 AODI

## 模型结构

三层，严格分离（**不**借用 M-1 气泡 / M-2 脊骨 / M-5 重绑 的结论或公式）：

1. **精确 2×2 槽守恒**：每节点每 CHI 通道每拍 2 个公路槽。真值表穷举：单侧空 + pending ⇒ 合法偏转造洞 `inject-hole=1`；**双忙 ⇒ `inject-hole≡0`**（硬断言；hole>0 = 机制失败）。无第三槽、无静默丢/缓。
2. **不对称占用窗**：Frechet 联合给出 `P(pref_only)` vs `P(dual)`。合法洞只来自 `pref busy ∧ opp empty`。alltoall 取 `c=+1` 把 `P(pref_only)` 压到 0 → 增益 **≈0**，**单独成行**，禁止折进 0.50–0.85× / 0.70–0.95×。
3. **相对 makespan + 受害税**：H-INJ-DOM 给 `T_inj = p_off/p_on`；H-VICTIM 把被偏转包的 `1+E[wait_rejoin]` 混入 `T_mix`。进度是逐包 φ（重入武装后首选向剩余跳），**不是** Σage。

对照物：`github:lukebest/bufferless-ring-noc` 的 `tests/soc_sim`；T_off 钉与兄弟 P-0198 解析模型同一组（问题 YAML + `docs/srcfc_ca_model/data.json` 的 `off`）。

## 假设（全部具名）

| ID | 含义 | 风险 |
|----|------|------|
| H-RHO-CLASS | 分流量类 (ρ_pref, ρ_opp, c) | 非实测；扫错会开关增益窗 |
| H-CORR | Frechet 相关；alltoall c=+1 | 若 alltoall 实际 c≪1，模型会**低估**残洞（仍不得宣传双忙加速） |
| H-USE | η_use 吃洞效率 | η→1 时纯 H-INJ-DOM 过度乐观 |
| H-AGE | λ_age=P(age<AGE_MAX) | AGE_MAX 只界偏转次数，不提供抢占 |
| H-REJOIN | 几何等空口；无抢占 | ρ_pref→1 ⇒ φ 冻结（Archi） |
| H-INJ-DOM | 已坍 / 占用受限类 T∝1/p_inj | 未坍类与峰值后崩塌禁用绝对值 |
| H-VICTIM | 偏转受害混入 T_mix | H、等待分布是尺度假设 |
| H-OPEN / H-MIGRATE | 对向回填 κ_mig | κ→1 镜像灌满，窗关到双忙 |
| H-SWAP | 双忙只许直通 | 未计 age 的无限 swap 会假活锁 |

## 默认假设下的预测（模型输出，非测得）

跑 `python3 models/P-0198/M-4/model.py` 看当期数字。定性（默认 η_use=0.25、κ_mig=0、λ_age=0.90）：

- **不对称类**（均匀读/写、broadcast、gather/reduce）：`P(pref_only)>0` ⇒ `hole_asym>0`、`hole_dual=0`。纯 `T_inj` 往往 **低于** 卡下沿 0.70（注入机会被算满）；`T_mix` 把 Rejoin 等待税加回后才可能落入 **card-claim 0.70–0.95×**。卡区间不是模型输出。
- **混合类**（allgather/allreduce）：窗更窄；对向本底更高。
- **alltoall 双忙饱和（单独行）**：`c=+1` ⇒ `P(pref_only)≈0` ⇒ `T_inj=T_mix≈1`，增益 **≈0**。deflect-off 与 AODI-on 无差。**禁止**把该行折进任何 0.50–0.85× 叙事。
- **消融**：不对称类 deflect-off 的 T ≥ AODI-on（归因必要非充分）。双忙类两臂都 ≈1。
- **对向 util / 完成数**：开环 κ_mig=0 时 `ρ_opp` 不升，等功完成数 = 公开 N_txn（仅均匀读写 46080）或 n/a。闭环 κ_mig 升高则对向占用上升、`C_opp_rel` 下降——不得用首选向 inject-success 洗掉。
- **φ**：一次偏转 + 成功 rejoin 后 φ 严格降到 0；首选向永满则 freeze 旗=真。Σage 在该走步里只是 1，不能当到达证明。

## 灵敏度（两个最敏感）

1. **(ρ_pref, ρ_opp, c)**：直接开关 `P(pref_only)`。双忙饱和（高 ρ + c=+1）把洞关死。
2. **η_use × κ_mig**：η 定吃洞量；κ 把洞回填成对向满载。κ→1 时不对称窗塌回增益 ≈0。

λ_age / AGE_MAX 是二阶（能偏转的过路份额）；H 只缩放受害税。

## 魔法缺口（卡宣称 − 模型能解释）

1. **双忙 / alltoall 仍写 0.50–0.85×**：模型拒绝。该区增益 ≈0，单独行 0.95–1.05× card-claim，且 card-claim ≠ 测得。
2. **纯注入缩放进 0.70–0.95×**：`T_inj` 常过低；要靠 H-USE≪1 与 H-VICTIM。若 cycle 级受害很轻而仍只有小增益，说明多节点镜像（κ_mig）才是真限制。
3. **均匀读峰值后数量级崩塌**：2 槽守恒解释不了 5761→2.8–3.4e3 B/ns；必须 `tests/soc_sim` 曲线，禁 inject-success 替代。
4. **φ 在首选向永满时闭合**：Rejoin 无抢占 ⇒ 条件进度，不是活锁定理。不得用 Σage 补洞。
5. **同拍 / 异拍偷第三槽**：解析把双忙 hole 钉死为 0；实现若 swap⊕inject 或 hole 与 busy 错拍，cycle 级会 captcha 失败——本文件不能替代该断言。
6. **RBRG 对侧 / 跨通道**：范围外。Dat 满不救 Req。

## 交给评估审计 / 后续 cycle

- 路径：`models/P-0198/M-4/{spec.md,model.py,insight.md}`
- 跑：`python3 models/P-0198/M-4/model.py`（须 exit 0）
- 审计焦点：
  - 双忙 `inject-hole≡0`（违例=机制失败）
  - φ 是逐包剩余跳，不是 Σage
  - deflect-off 分列；对向 util + completions，禁 inject-success-only
  - hole 分不对称 / 双忙桶
  - alltoall 单独行，无假双忙加速、无 0.50–0.85× 折算
- 信封：DV200 `tests/soc_sim` / bufferless-ring-noc；**不是** team-384dmc / interleave microbench
- 先例：T1-return-1 综合 PR #61（main）；机制卡 PR #53 tip（main 无卡正文）
- Tier 3 必须按 Dr.Sim 列表建同拍 2×2 / 分桶 hole / 逐包 φ；禁止用本文件的平均 ρ 冒充测得 makespan
