# Tier 0 · P-0198/M-4 · AODI Age-Bounded Opposite-Ring Deflection Inject

- 机制卡: mechanisms/P-0198/M-4.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: INCREMENTAL
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: 本地有 pending 注入且首选方向被过路 flit T 占用时，若 T.age<AGE_MAX 且同通道对向 2×2 合法，则把 T 偏转到对向一跳，置 inject-hole 1 拍，载荷注入原方向。因果链「挡路 flit 换向 → 1 拍注入洞 → 注入开始前移 → makespan」。deflect-off 须使注入失败与集合 makespan 变差。禁止跨 CHI 通道偏转，避免通道语义破坏。
- 完美预测/无限带宽/零延迟: 无日历、无到达预测；偏转是局部组合决策。不增第三槽、不加 flit 队列。Inject-hole 窗恰 1 周期。Age 界提供进度函数，非无限绕行。
- 约束边界: 2×2 深度 0；仅 Dat-CW↔Dat-CCW（等同通道方向对）。DV200 满包络与全集在计划内。Killer：多源同时偏转 → 拥塞迁到对向——卡要求报对向利用率与完成数，禁止静默丢包。T1 须验证环上周长与 age 下最坏绕行仍有界、且不破坏 CHI 通道独立性。
- 硬件开销 vs 问题约束: ~0.003–0.008 mm²/top、~2–5 mW；无队列。符合 bufferless。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: BLESS（Moscibroda & Mutlu, ISCA 2009）与 CHIPPER（Fallin et al., HPCA 2011）在 **mesh** 上用偏转替代缓冲解决输出口争用；注入规则通常是「存在空闲输出才注入」。Hierarchical Rings with Deflection（Ausavarungnirun et al., 相关 ISCA/期刊层次环工作）把偏转用在层次环桥接。AODI 的对象不同：在 **双向无缓冲环的同通道 CW↔CCW 对** 上，为制造 **首选方向的 1 拍注入洞** 而主动把过路 flit 推到对向，带 AGE_MAX 与 inject-hole latch——不是 mesh 多端口热土豆，也不是「有空口再注入」的被动规则。相对 BLESS 家族为策略/拓扑特化的 DIFFERENT_APPROACH（近亲，非 EXACT_MATCH）。Prevention Slot / Bubble FC 造空位方式不同（日历禁止或缓冲留空），见 M-1。
- vs 本批其他卡: 明确第三条路径：CBC=日历造气泡；DPH=永久方向角色；AODI=按需瞬时偏转洞。与 M-3 正交叙述成立。与 M-5（通道重绑）不同层。与 M-2 无重叠。无 EXACT_MATCH。跨批 DRAM 无孪生。

## 判决理由
轴一通过：局部偏转 ≠ 预测；无队列；age 与同通道约束守住活锁与 CHI 语义。新颖性：在双向 bufferless 环上「对向偏转制造注入洞」相对 BLESS 有真实结构差，但是偏转家族的强 INCREMENTAL，质量标 INCREMENTAL 而非 ISCA_WORTHY。规则允许「DIFFERENT_APPROACH + 强 INCREMENTAL 结构差 → PASS_T1」。进入 T1。T1 必须量化对向拥塞迁移与 age 分布，并与 deflect-off、以及（诊断）相对 CBC 对照，忌只报注入成功率代理。

Close call: 若把门檻提到「凡偏转即 FUNCTIONAL_EQUIVALENT(BLESS)」可改 REJECT；本判决因 **注入洞制造 + 环对向 2×2 + 同通道禁跨** 的具体对象放行。
