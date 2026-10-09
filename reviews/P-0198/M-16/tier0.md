# Tier 0 · P-0198/M-16 · RBRG 空槽拼接与本环续行

- 机制卡: mechanisms/P-0198/M-16.md（PR #87 head `65f1268`，该提交中文件名为 `M-11.md`，按标题映射）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: FAIL
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: FLAWED
- 进入 Tier 1: NO
- 平台核查: bufferless-ring-noc `main@63163ca`（私有仓，认证访问）

## 卡摘要
RBRG 只在对端环本拍输入为空（`dst_free`）时把过桥 flit 拼进对端环，否则 flit 沿本环续行、下一圈再试；flit 带 3b `REV` 计未拼接次数，`REV≥R` 时可向对端紧邻上游 NI 发 1b `vac_req`，让其跳过一次注入、把空槽让给 RBRG。零 FIFO、零 skid、无窗。

## 轴一 可行性
- 基线描述与代码不符。卡的根因是「RBRG 在对端 `slot_occupied=1` 时仍把 flit 切进去，成为对端外源过路」。库里 RBRG 是一对带输出缓冲的 NI（`TNetworkInterfaceRbrg`，`port_ChangeRing_{cc,cw}.toml`：`outputBufferDepth 15`、`l1SwapEn`、`l2SwapEn`、`ejectCbusyEn`）。进桥：flit 从源环 eject 进 RBRG 缓冲，缓冲满则 eject 失败，flit 沿源环继续走，即卡里的「本环续行」，基线已有（`src/TCsHighWay.cpp:574-591`）。出桥：RBRG 作为对端环上的注入者走 `tryLocalToWay`→`sendFlitToWay`（`src/TCsHighWay.cpp:1041-1118`），只能写空槽、L1 swap 状态下的无效占位、或 change-ring 保留槽，**从不覆盖有效过路 flit**。所以「对端忙仍切入」在基线里不存在，`dst_free` 门是基线注入语义本身。
- 因果: 过桥 flit 最终都要进入对端环，进入后都是对端节点的过路，这个总占用拼接不改变；拼接只改变进入时刻。去掉 15 深桥缓冲后，对端忙时 flit 只能在源环绕圈（每圈占源环 N 个槽拍），源环的外源过路反而增加。卡的收益链（对端 `λ_local` 上升）在基线已成立的前提下没有新增项。
- 结构: 卡的改动点要求「删除忙则 stall / 进 skid 的路径」，库里对应的是 RBRG 输出缓冲与 L1/L2 swap，删除它们是对现有桥结构的删减，不是新增机制，且会让跨环 flit 在源环绕圈。
- Sink / 死锁 / 活锁: 续行有 sink（本环下一跳），无死锁。`REV` 饱和 7 不构成进度保证；进度依赖 `vac_req`，而 `vac_req` 冷却 `S=4` 只是概率性。基线靠 change-ring 保留槽 + i-tag 给 RBRG 注入进度保证。
- 完美预测/无限带宽: 无。

## 接口落点核查（bufferless-ring-noc main@63163ca）
| 卡声称的钩子 | 实际位置 | 结论 |
| --- | --- | --- |
| `tests/soc_sim` 入口 `--cc-scheme vacant-splice` | `run_soc.py:329` 有 `--cc-scheme`，后端是 `tests/soc_sim/platform/CongestionCtrl.h`，按 NI 组做速率/赤字控制，不进入 RBRG 槽逻辑 | 开关可加，但开关后面的逻辑必须进库 |
| 「RBRG 过桥模块 grant 条件改为 `dst_free`」 | RBRG = `include/TNetworkInterfaceRbrg.h` / `src/TNetworkInterfaceRbrg.cpp`；出桥注入在 `src/TCsHighWay.cpp` `tryLocalToWay`/`sendFlitToWay`。没有 grant 概念，空槽注入已是基线 | 钩子名不存在；语义已存在 |
| 「删除忙则 stall/进 skid」 | 实际是 15 深输出缓冲 + L1/L2 swap（`TNetworkInterfaceBase.cpp:321-390`） | 删减现有结构，动哈希锁定库 |
| flit 加 3b `REV` | `include/chi_ring_common.h` NetworkFlit；已有 `eject_failed_times`/`looped_times` 可直接当 REV | 库内；已有等价字段 |
| `vac_req` 接对端上游 NI | 基线等价物：Dat 环 `reservedChangeRingSlot true`（`docs/noc_setup.md:115`）、`canUseResvervedSlot`/`tryRbrgSlotProcess`（`src/TCsHighWay.cpp:1168-1212`）、i-tag | 库内已有 |
- RTL：仓内无 RTL 源，不触 RTL。改动全部落在哈希锁定库 `include/`/`src/`，属仿真器结构改动，只能开新分支。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
| --- | --- | --- |
| 库内 RBRG（eject 进桥缓冲 / 满则源环续行 / 空槽注入对端） | FUNCTIONAL_EQUIVALENT | 「对端空才进、否则本环续行」即基线行为；卡还去掉了缓冲 |
| 库内 change-ring 保留槽 + i-tag | FUNCTIONAL_EQUIVALENT | `vac_req` 让上游空出一槽给 RBRG，就是为换环注入者保留槽 |
| HiRD（Ausavarungnirun 等, SBAC-PAD 2014） | 近亲 | 桥满则绕回；卡自称零 FIFO 区别，但零 FIFO 是倒退 |
| M-9 RBRG gate window | DIFFERENT_APPROACH | 卡给出了合法拒绝动作（续行），补上了 M-9 的洞，但补法即基线 |
| M-2 CSR / M-5 CRRF | 无关 | — |

## 指标核对
相对真实基线，卡的主因果（对端 `λ_local` 上升使 KV straggler 提前）没有新增作用量；去缓冲还会增加源环绕圈占用。不能证明缩短推理 `T_step`。

## 判决理由
可行性 FAIL：卡按一个不存在的基线（RBRG 对端忙仍切入）建立因果，实际库已是「对端空才注入、桥满则源环续行」，且有 change-ring 保留槽与 i-tag 作进度保证；卡的改动是删掉桥缓冲。新颖性 FUNCTIONAL_EQUIVALENT（库内 RBRG 语义 + 保留槽）。REJECT / FLAWED。

若重提：须以真实 RBRG（15 深缓冲、L1/L2 swap、`reservedChangeRingSlot`）为基线，给出 cycle 级证据说明哪一个现有行为造成推理尾，再提增量。
