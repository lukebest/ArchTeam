# Prof. Bench T1 — P-0198/M-5 CRRF（T1-return-1）

## 结论
有条件通过
T0-rerun（PR #55）致命点全 CLOSED；Drain/Barrier、失配重定向与「Snp≤1.4× + duty∈{3:1,7:1,15:1}」硬杀假设堵住了只报 Dat 甜区；相位改本地压力计数后，负载条件变成——drain 税与 Snp floor 是否仍让 Dat 侧净赢，15:1 是否必须被扫描暴露。

## 五维打分（1–5）
| 维 | 分 | 一句话 |
|---|---|---|
| 可行性 | 4 | Epoch Drain + skew 接受集；ghost Dat 禁当 Snp；`bind_mismatch_redirect` 禁静默丢。 |
| 新颖性 | 4 | 带屏障的 Channel–Ring 时分复用；杀软件 COLL_EP 主臂后更干净。 |
| 预期收益 | 3 | Dat 侧 0.55–0.85×（扣 drain）；Snp≤1.4× 为硬杀；15:1 可能伤 Snp。 |
| 评估可信度 | 3 | Snp makespan/completions 与 duty 扫描已强制（较初稿可信）；库仍无 NoC 包。 |
| 系统可组合性 | 3 | 与 CSR 正交层；无 hint 也须能 drain/flip；duty floor 防 Snp 饿死。 |

## 最强反对意见
杀手仍在 Snp。若只跑 7:1 甜区、省略 15:1，或用 runtime hint 人为躲过 Snp 退化，Dat 改善会写成全故事。修订已禁止软件主臂并钉杀假设——评估层若跳过 duty 扫描或 Snp 列，评审作废。

## 评估层必须验证的一个假设
COLL_EP/STEADY 由本地压力计数驱动（无 hint 主路径）时，对 duty∈{3:1,7:1,15:1} 同表报告 Dat 侧 makespan/collapsed **与** Snp makespan、Snp completions。任一 duty 下 Snp makespan >1.4× rebind-off → 该点失败。`bind_mismatch_redirect` 稳态目标 ==0。 T0 close call：跨 die 本地 sniff 非全局清空，稳态 redirect 须真能 ≈0，否则 drain/skew 未闭合。rebind-off 须使 Dat 侧变差。禁止只报 Dat 均值。

## 负载特征核对
- 机制依赖：Dat 饱和且 Snp pending 低才抬 Dat duty；SNP duty floor；drain 死时间进模型。
- 库里：无专用包。主评测 = 均匀读/写 + 全集集合 + **强制 Snp 类指标**。禁止 decode / 仅 Dat 代理。
- 反例：省略 Snp 列；只报 7:1；runtime hint 当正确性依赖；减箱；skew 未 cycle 建模。
