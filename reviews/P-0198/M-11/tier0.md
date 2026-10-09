# Tier 0 · P-0198/M-11 · MELB Missed-Eject Local Bounce

- 机制卡: mechanisms/P-0198/M-11.md（PR #84 head `e6a5e2b`）
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc `main@63163ca`

## 卡摘要
目的节点 eject 失败（`at_dst ∧ ¬eject_ok`）且同通道对向本拍空时，把该 flit U-turn 到对向走 2 跳、再 U-turn 回来重试，`BOUNCE_MAX`（默认 2）后回落整圈 orbit。目标是把单次 dest-miss 的重试税从 `C_ring` 砍到 ~2 跳。硬不变式 `inject_from_bounce_hole≡0`，与 M-4 AODI 切开。

## 轴一 可行性
- 因果性: 「尾包 miss 一次 → +C_ring」这条链在基线里是真的：`TCsHighWay::tryWayToLocal` eject 失败分支（`src/TCsHighWay.cpp:574-591`）只做 `eject_failed_times++`，flit 继续沿原方向走。但基线已有两个削这笔税的结构（见轴二）：e-tag（目的口标记/保留，`etagReserveCycle 10`）把重复 miss 压到约一圈；`UturnConnect` U-turn 站把 eject 失败 flit 掉头。MELB 的增量是把 U-turn 点从「专用无设备 CS」挪到「每个 dest 的邻居」，以及 2 跳精确回瞄。收益前提是 dest 忙的持续时间短于 2 跳往返（约 4–6 拍）；若 dest 忙来自 NI 输出缓冲被端点反压占满（DV200 AIC `outputBufferDepth` 9/9/9/14），4–6 拍后大概率仍忙，`BOUNCE_MAX` 被耗光后回到 orbit，净效果是多吃 4 个对向链路拍。卡没有给出 dest-busy 持续时间分布的论证。
- Sink / 死锁 / 活锁: 有 sink：XB 深度 0，回弹只在对向空槽发生，超限回到基线 orbit，不丢不缓存。无环上等待链，不引入死锁。活锁由 `BOUNCE_MAX` 有界，退回基线 orbit，基线本身靠 e-tag 保证最终 eject。注意：U-turn 在带设备的 CS 上执行，会与该 CS 本地 inject/eject 同拍竞争 highway 两个方向槽；库里 `arbitration()` 对 U-turn 站直接 `return`（`:242-247`，注释「uturn node should not connect to other device」），说明原设计刻意把 U-turn 与本地端口隔离。MELB 把二者合到同一 CS，需要新定义同拍优先级（U-turn vs 本地注入 vs 本地 eject），卡只规定了禁注入门，没有规定 U-turn 臂与对向 dest 的 eject 冲突。
- 完美预测/无限带宽: 无预测，局部组合判定。不增槽，零和成立。
- 约束边界: 无队列；同通道；`inject_from_bounce_hole≡0` 可探针。双忙区自报无收益，诚实。
- 硬件开销: 每节点每通道 2×2 + 2b 计数，量级可信。

## RTL / 仿真器改动核查
- bufferless-ring-noc 中没有 RTL 源（无 .v/.sv）。`include/`、`src/` 是导入的 ChiRingFabric ESL 库，按 `provenance/esl-2026-09-15.json` 哈希锁定，代表 RTL 行为；`tests/soc_sim/` 是平台。
- 卡称「允许只加模型：`tests/soc_sim` 里 dest eject 失败分支增加 bounce FSM」不准确：eject 失败分支、U-turn 交换、flit 头字段都在库内（`src/TCsHighWay.cpp:574-591`、`:1303-1404`；`include/chi_ring_common.h:289-290` 已有 `can_uturn`/`uturn_times`）。`tests/soc_sim/platform/` 里没有 highway 层。所以这是**仿真器结构改动**，只能开在 bufferless-ring-noc 新分支；不改 RTL（仓内无 RTL），但会动哈希锁定库，须进 tagext 类 manifest 并默认关闭。
- 零代码对照：`UturnConnect CS <id>`（`src/TRingConfig.cpp:270-275`）可在 DV200 配置里直接打开基线 U-turn 站，用来先量 dest-miss 税是否存在。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| 库内 U-turn 站（`TCsHighWay::tryUTurn/canUTurn/doUTurn`, `UturnConnect`） | FUNCTIONAL_EQUIVALENT | eject 失败置 `can_uturn`；对向槽空或同为失败 flit 时交换 CC/CW，`uturn_times<3` 上限。与 MELB 的「dest-miss → 对向空才掉头 → 有界次数 → 否则 orbit」是同一机制，差别只在掉头站位置（专用 CS vs dest 邻居）与 2 跳回瞄 |
| 库内 e-tag（目的口保留） | 同目标 | 解决「反复 miss 绕多圈」，MELB 解决单圈税，两者叠加时 MELB 的边际只剩第一圈的 `C_ring−2` |
| M-4 AODI | DIFFERENT_APPROACH | 卡的切分成立：AODI 偏转挡路过路 flit 造注入洞，MELB 偏转自身 dest-miss flit 不造洞 |
| M-1 CBC / M-2 CSR / M-5 CRRF | 无关 | 不造气泡、无 GRANT、不借通道 |
| 教科书 deflection（BLESS/CHIPPER，HiRD 桥口 deflect） | 近亲 | 偏转回送是 deflection 家族常规动作 |
| slotted ring / 最短 CW/CCW | 非等价 | 卡自述正确 |

## 指标核对
主指标是推理尾。MELB 改的是已在环上尾 flit 的驻留时间，属于完成侧而不是注入侧，方向对。但前提「dest-miss 是推理尾主项」未证：M-5 T3 的 gather 打平被归因于 dest 弹出主导，dest 弹出主导时瓶颈是 eject 口服务率，回弹只是更快地回来再撞同一扇忙门，不增加 eject 带宽，makespan 由 eject 口串行决定。卡的消融 `bounce-off` 与 H-MISS-TAX 是对的证伪手段，但不足以把一个已存在于库内的机制重新算作新机制。

## 判决理由
可行性 PASS（有 sink、有界、无队列）。新颖性 FUNCTIONAL_EQUIVALENT：被评估的 ChiRingFabric 库已带 eject 失败 U-turn（`UturnConnect`）与 e-tag，MELB 是把 U-turn 站下放到每个 dest 邻居的放置泛化。REJECT。

建议（非 T1 任务）：作为基线诊断，在 DV200 配置打开 `UturnConnect` 并报 `eject_failed_times` 分布与推理尾，零代码即可回答「dest-miss 税是否主导」。若主导且库内 U-turn 站因不能挂设备而覆盖不足，再以「U-turn 站与本地端口共存的同拍仲裁」为新卡重提，并给出 dest-busy 持续时间 vs 2 跳往返的证据。

Close call：若门卫认为「库内特性 ≠ 文献/教科书，不进 dedupe」，本卡可改判 PASS_T1 / DIFFERENT_APPROACH / INCREMENTAL，T1 必验：dest-busy 持续时间分布；U-turn 臂与本地 eject/inject 同拍冲突规则；对向 4 拍额外占用对双向 KV 尾的反噬；与 `UturnConnect`+e-tag 基线同表比较。
