# Tier 0 · P-0198/M-19 · 邻节点饥饿气泡中继

- 机制卡: mechanisms/P-0198/M-19.md（PR #87 head `65f1268`，该提交中文件名为 `M-14.md`，按标题映射）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc `main@63163ca`（私有仓，认证访问）

## 卡摘要
每 NI 每方向 4b 饥饿计数 `ST`；`ST≥H`（复位 8）时向紧邻上游发 1b `hungry`；上游在本拍槽空、本地有就绪、自己不饿且冷却到期时跳过一次注入，把空槽让给下游。Snp 关闭。

## 轴一 可行性
- 因果成立，且方向正确：无缓冲环上上游填空槽、下游被饿，是经典环不公平（与 M-12 判决中的分析一致：真实偏置是上游饿死下游）。让紧邻上游让一槽，空槽 1 跳后到达饥饿节点，可截断 `W_starve`。
- Sink / 死锁 / 活锁：让出的槽仍在环上；被跳过的本地头留在既有 staging；冷却 `S` 限制捐赠频率；双方都饿时不捐，回到 work-conserving。无死锁、无队列。
- 局限：只接紧邻上游。若空槽在更上游已被第三个节点吃掉，紧邻上游本拍根本看不到空槽，`hungry` 无效。基线 i-tag 通过标记在途 flit、待其离环后槽留给标记者，不依赖邻居恰好有空槽，覆盖面更大。

## 接口落点核查（bufferless-ring-noc main@63163ca）
| 卡声称的钩子 | 实际位置 | 结论 |
| --- | --- | --- |
| `--cc-scheme starve-relay` | `run_soc.py:329`；`CongestionCtrl.h` 是 NI 组级速率/赤字控制，不做逐拍逐槽决策 | 开关可加，逻辑不在这里 |
| NI 加 `ST` 与注入与门 `donate` | 逐拍注入决策在 `src/TCsHighWay.cpp` `tryLocalToWay`/`sendFlitToWay`/`wantItag`；注入失败计数已有（`isInjectFailed`、`updateInjectFailCnt`，`:664-672`、`:851`） | 哈希锁定库，结构改动；`ST` 可复用现有注入失败计数 |
| 每条环向邻接加 1b `hungry` 端口（拓扑文件 / `ni` 邻接表） | 拓扑在 `manyring.csv`/`TRingConfig`；CS 间已有 `setCcCwHighWay` 邻接指针（`src/TCsHighWay.cpp:196`） | 库内 |
| 零代码近似 | i-tag 阈值与策略已可配：`gen_config.py:113-137`（`itagThreshold=64`、`itagPolicy`/`itagMaxTags`/`itagAgeBoost`/`itagWindow`），`run_soc.py --itag-policy` | 可直接扫描 |
- RTL：不触 RTL（仓内无 RTL 源）；`donate` 门需改库，只能开新分支。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| 库内 i-tag（注入饥饿后为该注入者保留槽，`TCsHighWay::wantItag`/`tryItagProcess`，DV200 `itagThreshold=64`） | FUNCTIONAL_EQUIVALENT | 同一目标「把一个空槽送到饥饿注入者面前」；M-19 改为让紧邻上游放弃空槽、阈值 8，是触发点与阈值的变体 |
| 库内 tagext i-tag 策略（`itagPolicy`/`itagAgeBoost`/`itagWindow`，provenance `esl-2026-09-22-tagext.json`） | 同族 | 已有 i-tag 策略扫描基础设施 |
| MetaRing SAT / 环公平性回压 | FUNCTIONAL_EQUIVALENT | 下游饥饿信号让上游暂停注入 |
| M-1 CBC / M-6 TDMA | DIFFERENT_APPROACH | 卡的区分成立：有反馈、非日历、默认 work-conserving |
| M-10 age/class | DIFFERENT_APPROACH | 不在本地多候选间打分 |

## 指标核对
饥饿节点 KV 尾是完成侧 straggler，方向对；但相对已开启的 i-tag 的增量未知，卡把基线写成「work-conserving 注入」，漏掉了 i-tag。

## 判决理由
可行性 PASS，因果方向正确。新颖性 FUNCTIONAL_EQUIVALENT：被评估库已有 i-tag 饥饿保留（DV200 已开，阈值 64）及可配策略，M-19 是同一目标下换成紧邻上游让槽、阈值 8 的变体。按「库内已有特性算作先例，增量须相对真实代码库」规则，REJECT。

建议（零代码）：先用 `gen_config` i-tag 参数把 `itagThreshold` 扫到 8/16/32，报饥饿节点 KV 注入等待 p99 与推理 `T_step`。若 i-tag 在低阈值下仍留有明显饥饿尾，再以「i-tag 失效的具体场景 + 邻居让槽的增量」重提。
