# Tier 0 · P-0198/M-17 · Decode-epoch 单拍 highway 对换

- 机制卡: mechanisms/P-0198/M-17.md（PR #87 head `65f1268`，该提交中文件名为 `M-12.md`，按标题映射）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc `main@63163ca`（私有仓，认证访问）

## 卡摘要
flit 头带 3b `EP`（发行时的 decode 步号），每 die 有硬件递进的 `CUR`。当 highway 过路 flit 的步号比本地 staging 头「更新」（预取/未来步）而 staging 是当前或更老步时，单拍把 highway 寄存器与 staging 寄存器对换：临界 flit 上环，过路 flit 停进本地 staging，之后按普通注入规则再上环。

## 轴一 可行性
- 被换下的 flit 无合法归宿。被换下的是**别的源发往别的目的的在途 flit**，它被放进本节点本地设备的注入 staging。这等于用本地 NI 的注入缓冲暂存过路流量，即在节点上缓存在途 flit。信封禁止织物内 flit 队列；M-9 因同一理由被判 FAIL（skid 跨拍驻留即队列）。卡的不变式「`highway_valid + staging_valid ≤ 2`」只数了寄存器个数，没有改变「过路 flit 离环驻留」这一事实。
- 队头阻塞: 库里 NI 不是 1-flit staging，而是 shareBuffer/输出缓冲 + 每方向候选（`popCandidate`，AIC `shareBufferDepth` 9–13）。外来 flit 占住候选位后，本地后续 flit 全被堵，本地设备的当前步请求反被推迟。
- 活锁 / 饥饿: 被换下的 flit 在下一节点仍可能遇到「更紧急的 staging」再被换下，卡没有对换次数上界、没有年龄保护。被停进 staging 的 flit 按普通注入等空槽，重载下等待无界（只有基线 i-tag 兜底，卡未提）。
- 步号语义: `CUR` 按每 die `inflight(CUR)==0` 递进，各 die 允许相差 1。flit 在别的 die 被比较时用的是那个 die 的 `CUR`，同一 flit 在不同节点的 `rank` 可能不同，「更老 straggler」与「预取」会被互相误判。
- 负载前提: tests/soc_sim 流量（`TrafficGen.h` 的 `core.plans` 分 phase）没有「当前步与下一步预取重叠」这一形态，需平台新增；卡也承认无预取时 `f_s≈0`。

## 接口落点核查（bufferless-ring-noc main@63163ca）
| 卡声称的钩子 | 实际位置 | 结论 |
| --- | --- | --- |
| `--cc-scheme epoch-swap` | `run_soc.py:329` / `CongestionCtrl.h`（NI 组级速率控制） | 开关可加，对换逻辑不在这里 |
| 「NI 注入/过路模块加 highway↔staging mux」 | `src/TCsHighWay.cpp` `arbitration`/`tryLocalToWay`/`sendFlitToWay`；NI 候选在 `src/TNetworkInterfaceBase.cpp` | 哈希锁定库，结构改动 |
| flit 控制加 3b `EP` | `include/chi_ring_common.h` NetworkFlit | 库内 |
| AIC outstanding 加 3b 标签与 `CUR` | 平台 `tests/soc_sim/platform/TrafficGen.h`/`Endpoint.h`/`CHIPort.h` | 平台层，可行 |
- RTL：不触 RTL（仓内无 RTL 源）；对换本身需改哈希锁定库，只能开新分支。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| MinBD 侧缓冲（Fallin 等, NOCS 2012） | FUNCTIONAL_EQUIVALENT | 无缓冲偏转路由中把在途 flit 拉进节点小缓冲、稍后再注入；本卡用注入 staging 当侧缓冲，按优先级触发 |
| SWAP（Parasar 等, MICRO 2019） | 近亲 | 相邻位置的包对换 |
| M-10 age/class arbitration | 同族 | 按类（步号）给优先级；卡称在「槽已占用」时生效以区分，但优先级键仍是类 |
| 库内 L1 swap（RBRG/D2D 口） | 近亲 | 库里已有「swap 状态下可覆盖无效占位」的机制，但不碰有效过路 |
| 最短方向 / TDM | 非等价 | — |

## 指标核对
即使对换成立，被换下 flit 的驻留与本地队头阻塞也计入 `T_step`；跨 die 步号偏斜使「临界」判定不可靠。不能证明缩短推理尾。

## 判决理由
可行性 FAIL：对换把在途过路 flit 停进本地注入 staging，就是用节点缓冲吸收过路流量（与 M-9 同一理由），并造成本地队头阻塞，且对换次数无上界。新颖性 FUNCTIONAL_EQUIVALENT（MinBD 侧缓冲 + 类优先）。REJECT / FLAWED。
