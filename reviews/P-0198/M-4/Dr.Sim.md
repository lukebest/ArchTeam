# Dr. Sim · T1 · P-0198/M-4 · AODI Age-Bounded Opposite Deflect

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0198/M-4.md（PR #53 修订卡，dual-busy hole≡0 + Rejoin + 逐包 φ）
- T0: reviews/P-0198/M-4/tier0.md（PR #55 T1-return-1 重跑；判决 PASS_T1 = 纸面致命点 CLOSED，**不是** T1 方法学通过）
- 日期: 2026-09-30
- revision: T1-return-1

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 2×2 真值表 + 独立 Rejoin + AGE_MAX 截止可按拍实现；双忙不造洞已写成硅片契约，仿真失败条件清楚。 |
| 新颖性 | 3 | 评估切面是双向环同通道 CW↔CCW 的诚实造洞，相对 BLESS/CHIPPER 族是增量特化，不是新运算原语；与 M-2/M-5 正交但文献增量。 |
| 预期收益 | 3 | 窗口只在不对称占用；双忙/alltoall 饱和预期增益 ≈0——若把该区平均进 0.85 bar，收益叙事立即作假。 |
| 评估可信度 | 3 | `inject-hole` 分桶与 deflect-off 可操作；T0 残余「φ 不增循环 / 双忙偷洞」取决于同拍采样与逐包探针，错一次就能洗出第三槽。 |
| 系统可组合性 | 3 | 范围限同 CHI 通道方向对，可与 CSR/CRRF 共存；但对向利用率是别人的公路，叠用必须单独 deflect-off，禁止把对向拥塞外溢记成「注入成功」。 |

## 最强反对意见

纸面真值表已经钉死「双忙禁止注入」，仿真仍极易在实现层偷第三槽：把 swap 写成「两路直通 **并且** 本地注入」、把 Rejoin U-turn 口复用成额外注入端口、或让 `inject-hole` 与 busy 掩码**不同拍**采样后做或规约。另一条假证明是用全环 Σ age / 平均 age 当进度——age 总和上涨不能推出每个包的 φ 在下降；错向环上堵在「首选向出口长期不空」的包可以无限占槽等待，T0 已承认这会拉长延迟。若报表只给 inject-success 或不对称读侧 makespan，对向利用率上升与写侧/alltoall 饱和会被洗掉：inject-success 是 proxy，completions / 分流量类 makespan / collapsed 才是 endpoint。双忙区增益必须单独报 ≈0，不得塞进均值过关。

## 评估层必须验证的一个假设

硬断言：任意 `busy T ∧ busy U`（inject pending 与否）周期 `inject-hole≡0`；仿真若在双忙下观测到 `hole>0` → **机制失败**（非法第三槽），该 run 作废。同一 harness 必须含 deflect-off 消融列：不对称占用下 makespan 应回退到基线量级，无差异则不得把收益记在 AODI。进度只许逐包 φ（已在首选向：剩余最短跳；错向：rejoin 武装后的 1+首选向剩余跳），禁止用 Σ age 或平均 age 代理。强制报告 opposite-ring util、分流量类 completions、按**单忙/双忙桶**拆开的 inject-hole 计数。alltoall / 双忙饱和区预期增益 ≈0，**不得**平均进 0.85 pass bar。

## 必须 cycle 级建模、不能解析近似

1. 2×2 端口表按拍求值：单侧 busy+inject pending → 偏转并同拍注入且 `inject-hole=1`；双侧 busy → 仅直通或合法 swap，**禁止注入**，`inject-hole=0`。
2. `inject-hole` 必须与 busy 掩码、偏转提交**同拍**采样；计数按单忙桶 / 双忙桶拆分。双忙桶 hole 总和必须为 0，否则 fail。
3. 被偏转 flit 仅在偏转**提交**时 `age++`；`age≥AGE_MAX` ⇒ 该 flit `deflect_enable=0`，此后只直通，不得再被偏转造洞。
4. Rejoin 为与 deflect **解耦**的独立口：仅当 flit 在错向且首选向出口空时 1 拍 U-turn；深度 0，不得排队，不得顺便注入。
5. 逐包 φ 探针：每次成功 rejoin 或在首选向前进一步，φ 严格下降；检测 φ 不增循环 / 单包活锁。禁止用全环 Σ age、平均 age、平均剩余跳作为进度列。
6. 首选向长期不空时，错向等待必须保持 bufferless（继续占错向槽、无侧缓队列）；延迟可拉长，但必须出现在该包完成时间里，不得当「仍在前进」。
7. 消融 deflect-off（主开关关偏转；rejoin 可另列）：不对称读/写窗口的 makespan 应回退；缺此列不得归因。
8. 强制指标：分流量类 makespan、completions、collapsed、opposite-ring util、deflect 次数、分桶 inject-hole。禁止只报 inject-success。
9. 范围断言：偏转仅同一 CHI 通道 CW↔CCW；跨 Req/Rsp/Snp/Dat 偏转 = 机制越界。
10. 负载分列：均匀读/写（不对称窗口，预期 0.70–0.95×）与 alltoall 双忙饱和（预期 0.95–1.05×）必须分开；后者不得并进 0.85 均值。均匀读峰值后崩塌报 goodput 曲线，不单报注入成功数。
11. 无静默丢、无侧缓、无 flit 队列；2×2 与 rejoin 深度恒 0。出现第三逻辑槽或双忙注入即 fail。
12. 包络：DV200 12+2、CHI 四环、512 B、公开 outstanding、额外 FC 关；点对点 + 全集集合。单环/子集/只测均匀读 = reduced-bbox ≠ full envelope。禁完美预测与无限带宽。
