# Tier 0 · P-0198/M-12 · HSSL Hop-Slack Staggered Launch

- 机制卡: mechanisms/P-0198/M-12.md（PR #84 head `e6a5e2b`）
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc `main@63163ca`

## 卡摘要
每波推理 KV / collective 由 leader 在 Rsp 上发一条 LAUNCH（`t0`、`H_max`、`wave_id`）；源 i 的本波首拍注入被推迟到 `t0_local + γ·(H_max − hops_i)`，远源先发、近源后发，后续拍不限。声称根因是「近源吃掉早期空槽，远源开工迟到」。

## 轴一 可行性
- 因果性: 失败。无缓冲环上过路 flit 恒优先于本地注入。同一波汇向同一 dest（gather / KV 拉取）时，沿最短方向的远源 F 位于近源 N 的**上游**：F 的 flit 经过 N，挡的是 N 的注入；N 的 flit 只往下游走，不会经过 F，除非 eject 失败后绕整圈。因此单环段上「近源挤占远源的早期空槽」不成立，真实偏置方向相反：上游（远）源天然先占槽，下游（近）源被饿，这正是经典环不公平问题。库里对此已有 i-tag（注入饥饿后保留槽，`TCsHighWay::tryItagProcess`，`src/TCsHighWay.cpp:894`）。HSSL 推迟近源，只会进一步压低近源与下游段利用率。
  卡唯一可能成立的情形是跨环：远源经 RBRG 汇入、近源恰在 RBRG 汇入点上游，此时近源 flit 经过 RBRG 节点会挡 RBRG 注入。但这时决定谁挡谁的是**相对汇入点的上下游位置**，不是 `hops(src,dest)`。Hop ROM 用错了键，修正后变成「RBRG 汇入口按源位置给优先」，与 M-9 RBRG 门控 / M-2 会合授权同族。
  broadcast / allgather 扇出半边只有一个源，不存在近远源争槽，HSSL 无对象。
- 注入侧收益: 门只改「谁先开工」，属注入侧调度。按沿用淘汰规则，注入侧动作只有在 last-completion 缩短时才计分；根据上述因果分析，单环段上它会推迟真实尾（近源被饿的那部分）而不是提前。
- Sink / 死锁 / 活锁: 门挡的是 NI 内尚未上环的 flit，fail-wait 有 sink（端点 outstanding 槽），超时回退 no-CC，无死锁。LAUNCH 走 Rsp 一条，开销小。
- 完美预测: `t0` 用 Rsp 到达本地拍，非神谕；可接受。但 γ 需要对每个流量形态扫描，最佳 γ 依赖负载，接近于离线调参。
- 约束边界: 无队列，不改槽；合规。

## RTL / 仿真器改动核查
- 卡的改动点（NI 注入门、hop 查表、wave_id/release 状态）可以全部放在 `tests/soc_sim/platform/`（`Endpoint.h` / `TrafficGen.h` / `CongestionCtrl.h` 已是 `--cc-scheme` 源端策略的挂点），不需要动哈希锁定的 `include/`/`src/` 库。LAUNCH 可建模为平台层发起的 Rsp 事务。卡「默认只加模型」的说法成立。不触 RTL（仓内无 RTL 源）。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| M-6 TDMA inject calendar | FUNCTIONAL_EQUIVALENT（同族） | 按源静态偏移释放 = 每波一次的静态时隙偏移；卡用「非周期」区分，但仍是按拓扑位置排定注入先后的静态调度 |
| 源端流控（`--cc-scheme srcfc` 等） | 同类 | 首拍延迟门 = 带位置权重的源端节流 |
| 环公平性（MetaRing SAT、库内 i-tag） | 方向相反 | 经典问题是上游饿死下游；HSSL 假定的偏置方向与之相反 |
| M-9 RBRG gate / M-2 CSR | 跨环修正后同族 | 若改用汇入点位置为键，即 RBRG 汇入口优先级 |
| 教科书 farthest-first / longest-path-first 列表调度 | FUNCTIONAL_EQUIVALENT | 「最远任务先发」是列表调度常规启发式 |

## 指标核对
不缩短推理 makespan：单环段上推迟的是本来就被饿的下游源；扇出类无作用；跨环情形键错。卡自带「dest-eject 串行主导则淘汰」，T3 已有该方向证据（M-5 gather 打平）。

## 判决理由
可行性 FAIL：根因方向与无缓冲环过路优先的事实相反，机制在主情形下无因果或负因果；跨环情形用错了排序键。新颖性 FUNCTIONAL_EQUIVALENT（静态注入偏移 / 最远先发 / 源端节流族）。注入侧调度且不缩短完成时间，按沿用淘汰规则不计分。REJECT / FLAWED。

若重提：须先用 cycle 数据（各源首拍注入失败次数 vs 其相对 dest/RBRG 的上下游位置）证明「下游源阻塞上游源」确实存在，并把键改成汇入点位置；那时需与 M-9/M-2 重新查重。
