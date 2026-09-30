# Tier 0 · P-0198/M-3 · DPH Direction-Partitioned Highway

- 机制卡: mechanisms/P-0198/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: Classifier + Direction Lock 把 class 永久绑到首选方向（默认 CW≈P2P Dat、CCW≈集合）；仅几何需要反向时经 RBRG 1 拍 U-turn；age 限止 U-turn 活锁。因果链「去跨形态 HOL → 同形态空槽可见率上升」在零和单槽下成立。Lock-off 消融应使跨形态冲突回归。卡诚实承认 alltoall 双方向皆忙为 killer，不宣称双向空闲。
- 完美预测/无限带宽/零延迟: Lock 表按 class/子类静态可配，「非运行时预测」。不增槽、不加队列。U-turn +1 拍，非零延迟神谕。
- 约束边界: 纯路由规则 + 组合交叉；bufferless 保持；CHI 每通道对各自 CW/CCW；DV200 12+2 与全集（含 alltoall）在计划内。不把 endpoints 偷换成利用率代理。
- 硬件开销 vs 问题约束: ~0.001–0.004 mm²/节点，可忽略级。开销不违信封。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 双向环本身标准；按交通类把流固定到不同物理/虚拟资源是教科书级 **class-based / asymmetric resource partitioning**——CPU–GPU NoC 上 request/reply 的 VC 分区（如 T-VCP / adaptive VC partitioning，ISCAS 与后续 Supercomputing 类工作）、以及双环上 CW/CCW 分表路由（开源 double-ring 路由表生成等）都是「类 → 资源」绑定。DPH 把绑定对象换成 bufferless 双向环的两个方向，并加 RBRG U-turn + age——是同一对象的薄特化，**FUNCTIONAL_EQUIVALENT**，非新可命名结构。异于 BLESS 式偏转（M-4）与日历气泡（M-1）：那些改注入几何；本卡只改永久角色表。
- vs 本批其他卡: 卡自称异于 CBC（无日历）与 AODI（非临时偏转）——正交叙述成立，但正交 ≠ 新颖。相对 M-1/M-4，DPH 是三者中结构最薄的「表驱动方向偏好」。相对 M-2/M-5 无机制重复。跨批 DRAM 无孪生。

## 判决理由
轴一通过：无预测、无队列、alltoall killer 诚实。淘汰原因在新颖性：永久 CW/CCW 角色分区是 class-based 双资源绑定的 FUNCTIONAL_EQUIVALENT，质量 INCREMENTAL，不足以进 T1。工程上或可与 CBC/AODI 组合，但单独不成顶会对象。
