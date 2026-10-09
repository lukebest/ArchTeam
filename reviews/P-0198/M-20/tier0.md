# Tier 0 · P-0198/M-20 · Decode-epoch 最长弧先发

- 机制卡: mechanisms/P-0198/M-20.md（PR #87 head `65f1268`，该提交中文件名为 `M-15.md`，按标题映射）
- 作者: 保守架构师
- 判决: KNOWN_CONFIRM
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO（可作平台层 issue-order 对照臂）
- 平台核查: bufferless-ring-noc `main@63163ca`（私有仓，认证访问）

## 卡摘要
在 AIC 请求发行口（及 bottom Dat 响应注入口），从当前 decode 步已就绪的至多 4 个候选中选 `hops` 最大者先发（LPT），打平按 txnid。只改发行序，上环后仍按基线过路优先；不改方向。

## 轴一 可行性
- 因果: 单个注入口上一组同步作业，各自有发出后的「尾长」`q_j`（这里是 hops），目标为 `max_j (C_j + q_j)`，按 `q_j` 非增序发行即 Jackson 规则，对单机子问题最优。所以在**同一源内部**重排是有因果的，且与 M-12 的失败点不同：M-12 是跨源推迟近源，被「过路优先、远源在上游」否定；M-20 只在一个源自己的候选之间排序，不涉及跨源让路，过路优先不影响其成立。
- 收益上界: 只排一个注入口内的先后，节省量不超过候选间 hops 差（环上至多约半环，`N≤21` 个 CS、链路 1–3 拍，即几十拍量级）。DV200 基线 makespan 为数千 ns 量级，推理一步内若注入口排队主导，hops 差只占尾部很小一段；卡上 8%–20% 的预期与该上界不相称（按规则视为假设，不作 card-claim）。跨源争用、dest eject 串行、RBRG 换环不在本机制作用范围内。
- 响应侧: bottom HA 的回复顺序在平台 `Endpoint.h` 的 `replies_` 队列，按 hops 挑选可行；但 HBM 时延在平台内为 0（`Endpoint.h:275`），响应侧可排的候选数取决于 HA 同时完成的读数。
- Sink / 死锁 / 活锁: 只改发行序，无新存储，无死锁。长期饥饿：短弧请求可能被持续推后，卡以「当前步过滤 + 4 候选窗」限制，步内有界。
- 依赖: `EP`/`CUR` 与 M-17 共用，M-17 已 REJECT；M-20 可改用平台已有的 phase（`TrafficGen.h` `core.plans.at(phase)`）作步号，不依赖 M-17。

## 接口落点核查（bufferless-ring-noc main@63163ca）
| 卡声称的钩子 | 实际位置 | 结论 |
| --- | --- | --- |
| `--cc-scheme lpt-issue` | `run_soc.py:329` | 可加 |
| AIC 发行/注入挑选（`aic`/`injector`/outstanding 模型） | 平台：`tests/soc_sim/platform/TrafficGen.h`（`plans` 生成与发行）、`Endpoint.h`、`CHIPort.h` | 平台层，存在 |
| bottom Dat 响应注入挑选 | 平台：`Endpoint.h` `replies_`/`PendingReply`（`:31`、`:270`） | 平台层，存在 |
| `hops` 计算 | 平台可调 `m_top->getDistOfRingToTgtPort` 等库接口（只读）或自建 LUT | 只读库接口 |
- RTL：不触 RTL，也不需要改哈希锁定库；全部在 `tests/soc_sim/platform/`。本批唯一无需动库的卡。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| Jackson 规则 / LPT 列表调度（对 `max(C+q)` 目标按尾长非增序） | FUNCTIONAL_EQUIVALENT（教科书） | 卡自己引用 LPT |
| M-12 HSSL（Jim round 2，REJECT） | DIFFERENT_APPROACH | M-12 跨源推迟首拍；M-20 源内重排。M-12 的否定理由不适用于 M-20 |
| Lee 等 MICRO 2010 距离仲裁 | DIFFERENT_APPROACH | 卡的区分成立：发行一次排序 vs 每拍网络仲裁 |
| M-6 TDMA / M-10 age/class | 非等价 | — |
| 最短 CW/CCW（M-7） | 非等价 | 只读 hops，不改方向 |

## 指标核对
作用于推理步的 `max`，是完成侧目标，方向正确；但收益上界受 hops 差约束，且只覆盖源端排队主导的尾。

## 判决理由
可行性 PASS（平台层、无库改动、无新存储）。新颖性：教科书 Jackson/LPT 规则直接应用于注入口发行序，与 M-7 同类，判 KNOWN_CONFIRM，不进 T1。与 M-12 不重复，M-12 的「过路优先」否定不适用。

建议：作为零风险平台对照臂（FCFS vs LPT vs SPT）放进后续 cycle 基线表，用于区分「源端排队尾」与「环上争用尾」；不单独作为机制卡推进。
