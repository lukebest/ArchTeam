# T2 insight · P-0198/M-2 CSR（Rendezvous–Grant）

## 模型结构

三层，严格分离；**不是** M-1 CBC 空槽再分配，也不是 M-4/M-5 的结论：

1. **精确不变式**：`occupancy(CAM_i, Dat_beats)==0`，`RBRG_reject_retention_depth==0`，`concurrent_live_cam≤N_cam=4`。会合状态只有 header/credit（4×39 b = 156 b）。payload 不进桥；折叠加在端点已有 RF/cache，不建成 highway FIFO。
2. **日程 + 损失系统**：COLLECT → GRANT flit 开窗 → 静态 order 表内注入。CAM 满走 Erlang-B（无队列，立即 RING_P2P）；COLLECT 超时走迟到份额。`cam_overflow_fallback` / `collect_timeout_fallback` / `spine_grant` 质量守恒，是 endpoints 不是脚注。
3. **相对 makespan**：仅对 fan-in 主导的已坍类 `{gather, reduce, allgather, allreduce}` 启用 H-FANIN-BOUND：`r_sched=(1−f_fanin)+f_fanin·(W_grant/N_src)`，再混回退路径 `r_fb=1`。alltoall **树/残差分列**。broadcast 与均匀读/写 **不算** H-FANIN-BOUND 绝对值。

对照物：`github:lukebest/bufferless-ring-noc` 的 `tests/soc_sim`；T_off 钉问题 YAML + `docs/srcfc_ca_model/data.json` 的 `off`（与 M-1 参考同一张表，只借钉、不借 CBC 方程）。机制卡正文在 PR #53 tip，**可能尚未合 main**。T1 条件已合 main（PR #61）。

锁定的驻留模型（H_inject_gate）：GRANT 前 payload 注入≡0（端点持有）；环上出现该 txn 的 Dat 拍只在 GRANT 之后。禁止与「COLLECT 期提前 orbit」混用。

## 假设（全部具名）

| ID | 含义 | 风险 |
|----|------|------|
| H-CAM-DAT0 / H-RETENTION0 | 不变式，不是拟合 | 违例 = 机制失败（复活 latch / 环面队列） |
| H_inject_gate | GRANT 前 I_payload≡0 | 关掉则 tax_orbit 对消扇入项，r→~1 |
| H-FF-NOTIFY | FORCE_FALLBACK 端点可见 | 假则半集合永等 GRANT |
| H-CAM-LOAD | a=λ·τ_hold | outstanding 256/512 把 a 推高即 overflow 主导 |
| H-CAM-RELEASE | GRANT_SENT 后释 CAM | 窗内仍占 CAM 则 a 更大 |
| H-COLLECT / H-TIMEOUT-WINDOW | τ_collect=N_src·T_hdr；迟到份额 | 头被环堵才亮超时 |
| H-FANIN-BOUND | 已坍 gather 系由 Ω(N) 扇入主导 | 非坍塌类禁用 |
| H-GRANT-TAX | κ_grant≥0 | GRANT 公民抢 Dat 槽 |
| H-A2A-SPLIT / H-A2A-LOAD | 树/残差分列；分段抬 a | 残差与 overflow 可吞掉树收益 |
| H-REL-SCALE | T_hat=T_off·r | 绝对 ns 不是硅 |
| H-SPINE-OFF | 消融回基线量级 | 无差异则不可归因 |

默认数值（模型扫描用，非测得）：`a_fanin=2`，`a_a2a=5`，`f_fanin=0.60`，`W_grant=1`，`κ_grant=0.04`，`T_hdr=15`（τ_collect=180 < timeout=255），`H_inject_gate=true`，`H-FF-NOTIFY=true`。

## 默认假设下的预测（模型输出，非测得）

- 不变式由构造成立：四项 CAM Dat 占用全 0，拒收滞留 0。
- 完成守恒：a=2 时 `f_ov≈0.095`、`f_to=0`、`f_grant≈0.905`；a=5（alltoall 分段）`f_ov≈0.398`；a=8 `f_ov≈0.575` **主导** → 卡区间 INVALID。
- gather/reduce/allgather/allreduce：`T_hat/T_off≈0.539`（T_hat 约 289.3 / 289.3 / 898.7 / 533.5 ns）。落在卡宣称 **0.45–0.80×** 数字带内——**仅当** 门控开、a 不大、f_fanin 够大。列标 **card-claim / ok** 不是 pass。
- alltoall：**TREE** r≈0.693（T_tree≈2840.5 ns），**RESIDUAL** r=1（T_res=4098.0 ns），伴生 mix≈0.816。残差必须单列；不得与 gather 系平均。分段 a=5 已有实质 overflow（Sys 10% 预算探针 `flag_sys_fb=true`），卡 0.60–0.95× 偏乐观。
- broadcast / 均匀读/写：H-FANIN-BOUND 为 `n/a`；card-claim 0.75–0.98× / 0.95–1.05× 只对照。分类器把均匀读写送 RING_P2P，CAM 到达为 0。
- **H_inject_gate OFF**：tax_orbit=0.55，gather 系 r≈1.036，回到基线量级（略差于 1，因 GRANT 税仍在）。提前 orbit 探针按设计取消脊骨归因。
- 拥塞头间距 T_hdr=28：`f_to≈0.218`（尚未单独主导）。H-FF-NOTIFY 默认 true；若 false 且 f_to>0 → orphan / 半集合等 GRANT，区间作废。
- **spine-off**：已坍类 T_hat_off=T_off；on 优于 off（HARD 探针 True）。无此差异不得把收益记在 CSR。均匀读写两臂都是 RING_P2P。

## 灵敏度（两个最敏感）

1. **a（及隐含的 outstanding / 分段数）**：直接定 `f_overflow`。a=8 过 0.5 主导线，卡带作废。N_cam 是硅常量 4，不是本卡旋钮；提到 8 只是反事实。
2. **f_fanin / W_grant**：在 GRANT 路径仍占优时定 r_ok。f_fanin→0.30 则 r≈0.79（仍像「有点用」）；f_fanin→0.90 则 r≈0.29（低于卡下沿，需几乎全程扇入失败才成立）。W_grant=1 是静态 order 表的诚实默认；W_grant=N_src 只剩 κ_grant 税，r≈1.04。

τ_collect 在默认 T_hdr 下低于 255，超时不是默认热路径；超时敏感来自环堵把头间距拉长，而不是 timeout 寄存器本身。

## 魔法缺口（卡宣称 − 模型能解释）

1. **0.45–0.80× 全集 gather 系**：默认点能进带，但依赖 H_inject_gate + 中等 a + f_fanin≳0.5。缺一门控或 outstanding 把 a 抬到 ~8，带就失效或叙事回到 RING_P2P。不得把卡区间当模型输出或测得。
2. **「payload 留在 Dat 环直到 GRANT」 vs 端点持有**：本解析按 T1 条件锁定门控注入。若 cycle 级允许 COLLECT 期 orbit，模型说明收益对消——这是 Archi/Sim 盲点，不是解析能「平均掉」的。
3. **alltoall 0.60–0.95×**：树臂在 a=5 已 r≈0.69 且 overflow≈0.40；残差列仍是 1.0。只报 mix/均值会假装比残差诚实值更好。
4. **FORCE_FALLBACK 通知路径**：解析只把它标成 H-FF-NOTIFY 探针。结构表若无回退公民/双端同源超时，T3 必须补，不能用本文件的 `flag_orphan=false` 当已测。
5. **绝对 ns**：289.3 ns 等只是 T_off×r。无硅 ±15%；无 cycle FSM。

## 交给评估审计 / 后续 cycle

- 路径：`models/P-0198/M-2/{spec.md,model.py,insight.md}`；索引在 `models/README.md` 的 **P-0198 (new cards — not Batch A)**
- 跑：`python3 models/P-0198/M-2/model.py`（stdlib；须 exit 0）
- 信封：DV200 `tests/soc_sim` / `lukebest/bufferless-ring-noc`。禁止 team-384dmc / decode-* / STREAM / team-interleave-microbench
- 卡源：机制 PR #53（正文可能不在 main）；T1 PR #61
- 审计焦点：
  - CAM Dat≡0 与拒收滞留≡0（不是「≤1 拍」旧稿）
  - 回退两计数是 endpoints；任一类主导完成路径 → 卡带 INVALID，不签 pass
  - H_inject_gate 与 FORCE_FALLBACK 可观测（具名假设/探针）
  - 分流量类、alltoall 残差，禁止平均过关
  - spine-off 回到基线量级才可归因
  - 0.45–0.80× 等只标 card-claim
- 移交：**评估审计**。Tier 3 必须按 Dr.Sim 列表建 cycle FSM，禁止用本文件的平均 a / 平均 r 冒充测得 makespan
