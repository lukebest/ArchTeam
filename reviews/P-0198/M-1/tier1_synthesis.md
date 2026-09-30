# T1 综合 · P-0198/M-1 CBC（环上循环气泡日历）

- 裁决：过线，进入 Tier 2 / #eval
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 3 | 4 | 4 | 4 | 4 |
| 新颖性 | 4 | 3 | 4 | 4 | 4 |
| 预期收益 | 2 | 3 | 3 | 3 | 3 |
| 评估可信度 | 3 | 4 | 3 | 3 | 3 |
| 系统可组合性 | 3 | 2 | 3 | 4 | 3 |

## 一致点

- 气泡是空槽编码 + tag/age，不增 highway 深度、不发明 flit 队列；类 epoch 日历 ≠ 消息级到达预测。
- 必须分流量类报 makespan/collapsed；calendar-off 消融与 P2P duty 过密对均匀读峰值后 goodput 的副作用是硬条件。
- 相对有缓冲 Bubble FC / Prevention Slot 有结构差，可进入评估层拷问。

## 分歧点

- 预期收益：Archi 2（饱和下只重分已有 empty，「制造」叙事超卖）vs 其余 3。
- 系统可组合性：Sys 2（epoch/日历谁写、多租户 steal 优先级未闭合；RBRG 对侧气泡语义消失）vs Sim 4 / Archi·Bench 3。
- 新颖性：Sys 3 vs Archi/Bench/Sim 4。

## 单一视角会漏的盲点

- Archi：扇入饱和时日历不能凭空 mint empty——须测 ρ_empty / ρ_steal；否则降级为优先级准入。
- Sys：双租户下 collective-steal 可合法吃掉另一租户的 P2P 注入洞；缺 ABI。
- Bench/Sim：只报集合均值或 harness 神谕对齐 epoch，会让 calendar-off 洗不掉虚胖。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. H-CBC-empty-supply：已坍 gather/alltoall 下测 ρ_empty 与 ρ_steal；calendar-on 相对 off 的 ρ_empty 提升 <5% 且 inject-success <10% ⇒ 因果失败（Archi）。
2. 分流量类 makespan/collapsed；P2P epoch duty≤1/8 时均匀读峰值后 goodput 不得再掉一个数量级；固定高 duty 对照单列；calendar-off 须使已坍集合变差（Bench / Sim）。
3. 双租户叠载：A 扇入高 duty 不得把 B 均匀读再压进 2.8–3.4 TB/s 崩塌带，B makespan 恶化 <10%（Sys）。
4. epoch 边界不得由 harness 神谕注入；禁止只报注入成功率代理（Sim）。
5. 日历对最多 8 路 FSM 的端口/共享读路径须在实现钉死（Archi）。
