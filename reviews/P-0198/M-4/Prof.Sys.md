# T1 · Prof. Sys · P-0198/M-4 · AODI（T1-return-1）

## 结论

通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 2×2 真值表钉死双忙 `inject-hole≡0`；Rejoin 与 deflect 解耦；无第三槽、无队列。 |
| 新颖性 | 3 | BLESS 家族在环对向上的特化；系统接口几乎为零。 |
| 预期收益 | 3 | 增益窗口诚实收窄到不对称占用；双忙/alltoall 饱和 ≈0，不再硬吹 0.50–0.85×。 |
| 评估可信度 | 4 | 双忙 hole==0 断言、deflect-off、对向 util、分桶 hole 均可硬测。 |
| 系统可组合性 | 4 | 无编程面、无 epoch、不跨 CHI 通道；与 OS/运行时/一致性对齐最好。Rejoin 仍纯硬件。 |

## 退回项审计（T1-return-1）

对照 T0 rerun PR #55：原致命点全部 CLOSED，判决 PASS_T1（新颖性 FE/INCREMENTAL 不改本系统结论）。

1. **双忙端口表 / `inject-hole≡0`**：`busy T ∧ busy U ∧ inject pending` → 仅直通或 swap，禁止注入；声称仍能注入 = 非法第三槽。双忙增益 ≈0 写进预期。**判定：CLOSED**。
2. **AGE_MAX + 独立 Rejoin**：`age≥AGE_MAX` ⇒ 不再偏转；错向包仅当首选向出口空才 1 拍 U-turn；进度 φ 为逐包剩余跳数，禁止 Σ age 假进度。**判定：CLOSED**——活锁叙事从全局 age 和改成逐包 φ。
3. **评估列**：deflect-off、对向 util、completions；禁只报 inject-success；双忙 hole>0 → 机制失败。**判定：CLOSED**。

## 最强反对

偏转与 rejoin 把拥塞**迁到对向环**，软件完全看不见。多租户同机时，租户 A 的注入偏转或错向占槽等待，可以抬高租户 B 在对向上的完成时间；没有 cgroup/QoS，也没有 per-VM「禁止偏转」开关。AGE_MAX+φ 防活锁，不防跨租户伤害。评估若只报全局 makespan、不报 per-source / 分租户完成时间，会把迁移伤害平均掉。Rejoin「首选向长期不空则在错向占槽等」合法且 bufferless，但在多作业叠加时会拉长尾延迟——必须进分位数，不能只报均值。

## 评估层必须验证的一个假设

双方向同时高载（alltoall 或双向均匀写）下：全程断言双忙周期 `inject-hole==0`；对向方向完成事务数相对 deflect-off 不下降、无静默丢包；不对称负载下分流量类 makespan 仍改善。若双忙区 hole>0，或对向完成数掉而总 makespan「看起来更好」，记机制失败。

## 系统视角

- 软件可见性：零。无 CSR、无 epoch、无 opcode 表。应用/OS/集合库都不用改。
- 编程模型：无。本批相对 CSR/CRRF 最大的系统加分；修订未加编程面。
- 协议/一致性：禁止跨 Req/Rsp/Snp/Dat 偏转，通道语义保持。被偏转/错向等待只改延迟与抖动，不改 CHI 消息类型。目录/一致性仍按原通道走。
- 多芯片：机制在节点本地 2×2 + rejoin；RBRG 不参与。12+2 满包络下每环对独立，不要求跨 die 同步。
- 多租户：共享偏转/占槽副作用（见最强反对）；无映射表互踩。可与 CBC/CSR 正交，叠加后更难点清责任——评估须能单独关掉 AODI。
