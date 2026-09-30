# Dr. Sim · T1 · P-0198/M-2 · CSR Rendezvous–Grant

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0198/M-2.md（PR #53 修订卡，Rendezvous–Grant，无 Dat latch）
- T0: reviews/P-0198/M-2/tier0.md（PR #55 T1-return-1 重跑；判决 PASS_T1 = 纸面致命点 CLOSED，**不是** T1 方法学通过）
- 日期: 2026-09-30
- revision: T1-return-1

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | T0 已闭合 latch / TDM-假8 / 静默完整三洞；4 路专用 CAM + 显式 RING_P2P 回退可 cycle 建，残余是 GRANT 窗与 payload 驻留位置必须锁成同一套时序。 |
| 新颖性 | 4 | 评估对象是「RBRG 只会合–授权、fold 退回端点」的双路径，不是桥上 reduce 寄存器堆，也不是 M-4 造洞或 M-5 通道重绑。 |
| 预期收益 | 3 | 扇入从盲目注入抽到 GRANT 窗在物理上说得通，但 N_cam=4 对 outstanding 256/512 很容易让回退主导完成路径，区间随即失效。 |
| 评估可信度 | 3 | `occupancy==0`、两回退 CSR、spine-off 均可操作化；T0 close-call 的「环上 orbit vs 端点持有」若建模不一致，仍能把公路占用洗成脊骨收益。 |
| 系统可组合性 | 3 | 与 AODI（注入几何）/ CRRF（通道绑定）切面正交；GRANT 公民占 Dat 槽，叠用时必须靠独立 spine-off 做归因，禁止混开记功。 |

## 最强反对意见

修订卡同时写了「payload 始终在 Dat 环上直到 GRANT」「折叠在端点 RF/cache」「参与端按静态 order 表在授权窗内注入/交拍」——这三句在 cycle 上不是同一个驻留模型。若仿真把 512 B 多拍在 COLLECT 期间继续当环上公民 orbit，会合阶段已经在消耗 highway 槽，GRANT 只是事后贴标签；若改成端点持有再窗内注入，则「一直在环上」不成立，收益来自端点侧缓冲而非脊骨。T0 已把纸面 Dat latch 判 CLOSED，但**没有**替评估层选定其中一种合法时序。评估若任选一种、或两种混用、或让 GRANT flit 与 payload 抢槽却不计入 Dat 占用，好看的集合 makespan 会记在 CSR 头上，失败模式却是「payload 驻留模型未钉死」。不得用解析树深 O(log 12) 或 Amdahl 扇入式代替实测窗占用。

## 评估层必须验证的一个假设

在全程硬断言 `∀i occupancy(CAM_i, Dat_beats)==0` 且 `RBRG_reject_retention_depth==0`（RBRG **无** Dat latch / 多拍 fold / reject-and-orbit 载荷队列；payload **永不**进桥）、物理并发诚实 `N_cam=4`（禁止 1–2 latch 时分伪装 8 槽）、禁止静默丢弃的前提下：spine-off（集合强制全 RING_P2P）必须使 gather/reduce/allreduce/allgather 的 makespan / collapsed **回到基线量级**；同一 harness 必须把 `cam_overflow_fallback` 与 `collect_timeout_fallback` 作为与分流量类 makespan、completions、collapsed **并列的 endpoints** 逐 run 报告。任一集合类完成路径由回退主导 → 卡上 0.45–0.80× 区间作废、不得过关。断言违例 = 机制失败，该 run 作废。

## 必须 cycle 级建模、不能解析近似

1. 每拍每活跃 CAM 探针 `Dat_beats_held` / `occupancy(CAM_i, Dat_beats)`：必须恒为 0；出现任何 Dat payload 寄存器、多拍 fold RAM 或 highway FIFO 即判定越界，run 作废。
2. `RBRG_reject_retention_depth==0`：拒收 RENDZ 头必须同拍重分类 RING_P2P、头继续在环前进；禁止对 Dat 载荷做 reject-and-orbit 滞留。
3. 物理 CAM 诚实 4 项专用（每项 txn_id+bitmap+state+timeout，独立 FSM/计数器）；探针 `concurrent_live_cam ≤ 4`；禁止用 latch TDM 报出 8 路并发。
4. `cam_overflow_fallback` 与 `collect_timeout_fallback` 每 run 进报表，与 makespan / completions / collapsed 同级；回退路径完成数计入分母，禁止静默丢弃或从完成集剔除。
5. 每 CAM 项 `timeout[7:0]` 每拍递减；到期 → `FORCE_FALLBACK` 释放 CAM、通知相关端改走 RING_P2P；禁止静默永等。CAM 满/busy 拒收头 → 立即溢出计数，不得排队进桥。
6. Classifier（opcode→{RING_P2P, SPINE_RENDZ}）1 组合/1 拍；RENDZ **仅** 1-flit header/credit 短 divert，CAM 匹配/分配 1 拍；普通读写不得误入脊骨。
7. **锁定一种** payload 驻留模型并全程断言：要么端点持有至 GRANT 窗再注入，要么（若允许环上已有 Dat）精确记账 COLLECT 期 highway 占用——二者不得混用；GRANT flit 作为 Dat 环 1-slot 公民，其槽占用必须计入，不得当零成本控制魔法。
8. GRANT 发射：位图对齐静态成员掩码后 `GRANT_PENDING` → 环槽可用时 1 拍注入；参与端按**静态集合类** order 表在授权窗注入/交拍；禁止按到达时刻神谕排程，禁止无限带宽「子瞬时齐」。
9. 端点 fold：每拍到达在已有 RF/cache 端口上 1 拍/运算宽度完成；**禁止**把 fold 延迟藏进 RBRG 或假设零延迟归约。
10. 消融 spine-off：集合全回环后 makespan/collapsed 必须回到公开基线量级（均匀读 ~4403.2 ns / 写 ~4834.6 ns 对照仍近中性）；spine-off 无差异则不得把收益记在 CSR。
11. alltoall 分段 GRANT / 多棵小树的残差环争用必须分桶或分位数单独成列，禁止并进 allreduce 均值；0.85 是 pass bar 不是 measured mean。
12. 包络：DV200 12+2、CHI 四环、512 B、outstanding 256|512、额外 FC 关；满跑均匀读/写 + broadcast/gather/reduce/allgather/allreduce/alltoall。单环、top 子集、只测均匀读或完美预测 = reduced-bbox ≠ full envelope。
