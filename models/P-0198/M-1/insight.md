# T2 insight · P-0198/M-1 CBC

## 模型结构

三层，严格分离：

1. **精确守恒**：每方向每拍 `ρ_payload+ρ_empty=1`，`ρ_empty=ρ_raw+ρ_bubble`。CBC 只改 tag，**Δρ_empty=0**（Archi H-CBC-empty-supply 的解析形式）。
2. **再分配**：duty `d` 把空槽标成可窃取气泡；位置效率 `η/η0`（假设 H-PLACE）把「扇入邻域可见空槽」从基线抬到日历引导后的水平。单租户下 collective 与 P2P 都能偷泡，一阶收益来自**空槽出现在对的地方**，不是多出来的槽。
3. **相对 makespan**：仅对 inject-fail 主导的已坍集合类启用 H-INJ-DOM：`T∝1/p_inj`，再可选 Amdahl（`f_coll`）。均匀读/写与 broadcast **不算** H-INJ-DOM 绝对值。

对照物：`github:lukebest/bufferless-ring-noc` 的 `tests/soc_sim`；T_off 钉问题 YAML + `docs/srcfc_ca_model/data.json` 的 `off`。

## 假设（全部具名）

| ID | 含义 | 风险 |
|----|------|------|
| H-RHO | 扇入稳态仍有 ρ_empty>0（eject/残留） | 若实测 ρ_empty≈0，日历零和再分配无效 → 因果失败 |
| H-PLACE | η≥η0 刻画气泡被送到汇聚邻域 | 解析代替不了 FSM×环拍；η 不可 >1 |
| H-INJ-DOM | 已坍集合 makespan 由注入机会主导 | 非坍塌类禁用 |
| H-AMDAHL | f_coll 扇入时间占比 | 与拓扑/软件 epoch 对齐绑定（Sys 盲点） |
| H-AGE / H-KEEP | age 寿命与未窃取气泡空转 | 短环上 AGE_MAX=15 可能自行塌回 raw |

## 默认假设下的预测（模型输出，非测得）

- 已坍集合、d∈{1/4,1/2}：`T_hat/T_off ≈ 0.74 / 0.58`（纯 H-INJ-DOM），落在卡宣称 **0.55–0.85×** 区间内——**仅当** η/η0 足够大；灵敏度显示 η→η0 时比回到 ~1。
- Amdahl 同参更保守（~0.82 / ~0.71 量级），卡上沿依赖「几乎全程 inject-fail」。
- calendar-off 相对 CBC 变差：HARD-1 解析探针通过（归因必要非充分）。
- P2P duty≤1/8：本线性 keep 模型下 G_hat 仅轻度下降，**未**再现 YAML 峰值后掉一个数量级——该崩塌来自环拥塞动力学，不在本解析内；固定高 duty 须 cycle 级验证。
- **双租户**：d_A∈{1/4,1/2} 时 B 的 `T_dual/T_solo = 1.33 / 2.0`，**超过** Sys <10% 条件 → 解析支持「不能当整机默认织物 / 缺 ABI」的 T1 警告。

## 灵敏度（两个最敏感）

1. **η/η0**：直接定 S_inj 与相对 makespan。  
2. **f_coll**：把 S_inj 译成端到端；ρ_empty 在线性 H-PLACE 下**不改比值**，只改绝对注入水平（与「不能 mint」一致）。

## 魔法缺口（卡宣称 − 模型能解释）

1. **「制造并循环空槽」文案**：模型否定 mint；若 cycle 级测得 Δρ_empty≈0 且 steal 无抬升，卡 §1/§3 Little 叙事降级为优先级准入（T1 Archi）。
2. **0.55–0.85× 全集已坍类**：解析要 η 显著高于 η0 才进区间；无消息神谕、仅静态拓扑类时 η 可能不够——与 Dr.Sim「神谕对齐虚胖」同向。
3. **均匀读峰值后数量级崩塌的缓解/加重**：本模型的 κ_keep 线性项解释不了 5761→2.8–3.4e3 B/ns；副作用结论必须留给 `tests/soc_sim` cycle 扫描。
4. **RBRG 对侧**：气泡语义消失（Sys）；解析未建模跨环，跨 die 集合收益属缺口。

## 交给评估审计 / 后续 cycle

- 路径：`models/P-0198/M-1/{spec.md,model.py,insight.md}`  
- 跑：`python3 models/P-0198/M-1/model.py`  
- 审计焦点：守恒与不 mint；分流量类分列；假设标签；双租户失败探针；魔法缺口是否写清  
- Tier 3 必须按 Dr.Sim 列表建 FSM，禁止用本文件的平均 ρ 冒充测得 makespan  
