# Tier 0 · P-0198/M-4 · AODI Age-Bounded Opposite Deflect（T1-return-1 重跑）

- 机制卡: mechanisms/P-0198/M-4.md
- 修订: T1-return-1
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: YES
- 原致命点: 全部CLOSED

## 轴一 可行性
- 因果性: 单侧 busy 时 2×2 把挡路 flit 偏到对向，同拍在空向注入（`inject-hole=1`）；双忙禁止注入。`age≥AGE_MAX` 关 `deflect_enable`；错向包经**独立 Rejoin 口**在首选向出口空时 1 拍 U-turn。进度函数 φ=首选向剩余最短跳数（错向则含 rejoin 武装），逐包下降可查。deflect-off 消融要求不对称负载下 makespan 回退。
- 完美预测/无限带宽/零延迟: 无流量预言。不增加每方向物理槽；双忙增益显式 ≈0。偏转/注入组合或可选 1 拍打拍；rejoin 条件开火——非零延迟无限洞。
- 约束边界: 端口真值表钉死 `busy T ∧ busy U ∧ inject pending ⇒ hole≡0`，声称此时仍注入 = 非法第三槽。无静默丢、无侧缓、无 flit 队列；2×2 与 rejoin 深度 0。范围限同 CHI 通道 CW↔CCW。诚实窗口 = **不对称占用**（对齐基线读写不对称）；alltoall 双忙饱和单独报 0.95–1.05×，禁止塞进 0.85 均值。残余：首选向长期不空时错向等待可拉长延迟——bufferless 语义保留，仿真用 φ/到达断言评估，非结构第三槽。
- 硬件开销: 每节点每 CHI 通道一套 2×2 deflect XB + Rejoin enable/空口检测；头 4b age + AGE_MAX 比较；inject-hole 可观测位。相对问题约束可接受；禁止项写进硅片契约。

## 原致命点核对（编号对应 fatal_points.md · M-4 AODI）
1. **CLOSED** — 给出完整 2×2 真值表：双忙仅直通/swap、禁止注入、`inject-hole≡0`；非法第三槽行显式标注不得实现；承认双忙/alltoall 饱和预期增益 ≈0。
2. **CLOSED** — 独立 Rejoin 口与 deflect 解耦；`age≥AGE_MAX` 后只直通+条件 U-turn；定义逐包 φ（非 Σ age），成功 rejoin/首选向前进一步使 φ 严格下降；证明义务列为评估断言。
3. **CLOSED** — 强制 deflect-off 消融列、opposite-ring util、completions、分桶 inject-hole；禁止只报 inject-success；双忙周期 `inject-hole==0`，违例=机制失败。

## 轴二 新颖性
- vs 文献: 对向偏转 + age 界偏转次数 + 空口 U-turn 重入，功能等价于经典 bufferless deflection（BLESS/CHIPPER 族）在双向环上的特化。不对称占用下造洞是已知几何直觉。无新运算原语 → **FUNCTIONAL_EQUIVALENT**；质量 **INCREMENTAL**。
- vs 本批修订卡（仅 M-2/M-4/M-5）: M-2 是 RBRG 会合–授权（不碰注入几何）；M-5 是通道–环时间复用。AODI 只改同通道 CW/CCW 端口仲裁——机制切面不同，非 EXACT_MATCH。

## 判决理由
三致命点均 CLOSED；双忙第三槽洞与 Σ age 假进度已用真值表 + φ/Rejoin 钉死。可行性 PASS。新颖性仅为已知偏转族在本信封的诚实裁剪（FUNCTIONAL_EQUIVALENT / INCREMENTAL），但 T1-return 目标是闭合结构洞并保留可评估增益窗（不对称占用）——残余「首选向长期满则延迟拉长」是 bufferless 可观测断言而非未写端口表。允许 **PASS_T1** 送审；T1 应严打双忙区是否偷洞、φ 是否出现不增循环。
