# Prof. Bench T1 — P-0198/M-5 CRRF

## 结论
有条件通过
Dat:Snp 时分重绑打的是「Dat 饱和、Snp 闲」不对称；7:1 duty 可能杀 Snp makespan。必须强制 Snp 类指标与 duty 扫描，禁止只报 Dat/集合改善。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | SYNC 只对齐 epoch ≠ 预测；无 flit 队列；Snp 仅 SNP_EPOCH 注入；rebind-off 可证伪。 |
| 新颖性 | 4 | CHI 四环上 Channel–Ring 时分 ghost Dat，异于通用 TDM 预留与 VC 窃取。 |
| 预期收益 | 3 | Dat 重集合 0.45–0.80× 中置信；Snp 路径 1.0–1.4× 风险带——改善可能被 Snp 代价抵消。 |
| 评估可信度 | 2 | 库无 NoC 包；更关键的是若省略 Snp makespan/完成数，评估不可信。duty∈{3:1,7:1,15:1} 必扫。 |
| 系统可组合性 | 3 | 与 CSR（路径树）正交层；COLL_EP/P2P 态切换依赖运行时类提示，错态会伤 P2P 或 Snp。 |

## 最强反对意见
问题端点含点对点与全集集合，但 CRRF 的杀手在 **Snp 通道**。若评测只扫 Dat 形态集合与均匀读抗坍、不报 Snp makespan/完成数，7:1 假设下的「Dat 加速」会写成全故事——那是 Dat 单通道微基准，不是 CHI 四环代表负载。Snp 无队列、只能 stall 到 SNP_EPOCH，duty 越稀 Snp 越伤。

## 评估层必须验证的一个假设
在满 DV200、COLL_EP 启用下，对 duty∈{3:1,7:1,15:1} 同表报告：Dat 侧集合/均匀读 makespan/collapsed **与** Snp 通道 makespan、完成事务数。若某 duty 下 Dat 改善但 Snp makespan >1.4× 基线或完成数下降，该 duty 不得标为通过点；加密 SNP_EPOCH 或缩短 COLL_EP 须作为敏感性结果单列。rebind-off 须使 Dat 侧恶化。ghost/主 Dat 在 512B 窗下目的分布不得坍成单槽（HARD-2）。

## 负载特征核对
- 机制依赖：集合/读相 Dat 饱和而 Snp 相对闲；粗相位 COLL_EP vs P2P；SYNC 对齐；Snp 仅 SNP_EPOCH。
- 库里：无专用包。主评测 = 均匀读/写 + 全集集合 + **显式 Snp 类流量/指标**（一致性轻负载也须报完成数）。禁止 decode / 仅 Dat 代理。
- 反例：省略 Snp 指标；只报 Dat goodput；固定 7:1 无扫描；减箱；P2P 态误开 COLL_EP；用集合均值掩盖 Snp 恶化。
