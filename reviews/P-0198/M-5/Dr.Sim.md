# Dr. Sim · T1 · P-0198/M-5 · CRRF

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0198/M-5.md
- T0: reviews/P-0198/M-5/tier0.md
- 日期: 2026-09-30

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 3 | 4×4 绑定 + Req-SYNC epoch 可建，但 CHI 通道语义在 ghost Dat 上的正确性与对齐误差是硬风险。 |
| 新颖性 | 4 | 评估对象是 bufferless CHI 四环上「Snp 环时分为 ghost Dat」，不是通用 TDM 虚电路复述。 |
| 预期收益 | 3 | Dat 侧重集合 0.45–0.80× 有 Amdahl 空间；Snp 1.0–1.4× 风险带可使「全类过线」叙事直接破产。 |
| 评估可信度 | 2 | 7:1 若当默认不扫、Snp 指标可刷掉、或把「近 2× Dat 槽」解析上界写成测得，数字必然虚胖。 |
| 系统可组合性 | 3 | Req/Rsp 保持 1:1 降低一致性风险；与 CSR/CBC 叠用时 ghost 路径与脊骨 attribution 须分开消融。 |

## 最强反对意见

Dat/集合 makespan 大幅改善时，Snp 注入被 DAT_EPOCH stall、完成数下降或 makespan 失控——若 harness 不强制报告 Snp 通道端点（或把 Snp 并进总平均），CRRF 会看起来像白捡第二条 Dat 环，实际是偷了正确性通道的时隙。

## 评估层必须验证的一个假设

在 rebind-off（固定 1:1）对照与 duty∈{3:1,7:1,15:1} 扫描下：COLL_EP 启用时 Dat 侧重集合/均匀读抗坍指标相对 rebind-off **改善**；同时 **Snp 通道 makespan 与完成事务数必须分列强制上报**——若任一 duty 下 Snp 完成数下降或 makespan 落入卡内 1.0–1.4× 风险带之外失控，则该 duty 的 Dat 收益不得单独写成机制胜利；7:1 是可证伪假设，不是默认过关点。

## 必须 cycle 级建模、不能解析近似

1. Rebind FSM 三态 IDLE/P2P/COLL_EP：由软件/运行时类提示或本地计数阈值切换；**非**消息级到达神谕；切态时刻可探针。
2. Req 环 SYNC flit + 每节点 2b epoch 计数：采样边沿锁存；对齐误差 ≤ 环周链路延迟必须 cycle 建模，禁止假设零 skew 全球同时切换。
3. NIC 与 RBRG 各一份 4×4 one-hot Channel↔ring 交叉：组合 + 1 拍流水防毛刺；绑定切换与 epoch 边沿对齐。
4. Flit channel-id 2b 与当前绑定核对：不匹配不得注入该环；错绑 run 计数，禁止静默洗到「有效 Dat」。
5. DAT_EPOCH 下 Snp 环硬件运 ghost Dat；SNP_EPOCH 运 Snp；Snp 注入器在 DAT_EPOCH **stall、无队列**——须探针 Snp stall 周期分布与最长等待。
6. Ghost Dat vs 主 Dat 负载均衡（轮转或目的 LSB）：512B issued-window 下两物理环目的/槽分布探针；HARD-2——若坍成单一目的或单槽，该配置作废。
7. 消融 rebind-off：固定 1:1，Dat 侧集合/读坍应恶化；并确认 off 路径 **无** 残留 ghost 偷分（HARD-1）。
8. Duty 扫描 {3:1,7:1,15:1}：每档分列 Dat 类 makespan、Snp makespan、完成数、collapsed；禁止只报 7:1 或把三档平均成「CRRF 加速比」。
9. 流量分列：均匀读/写 + 全集集合；P2P 态 vs COLL_EP 切换场景单独成列；均匀读峰值后 goodput 是否仍坍至 2.8–3.4 TB/s。
10. 基线：DV200 12+2、512B、outstanding 512/256、额外 FC 关；满包络；Warm-up 至 SYNC 对齐稳态后再采；禁止把「Dat 有效槽接近 2×」的解析 Amdahl 式直接写成测得 makespan；0.85 约束若用则对 Snp **同样适用**，不得用 Dat 均值过线冒充全类。
