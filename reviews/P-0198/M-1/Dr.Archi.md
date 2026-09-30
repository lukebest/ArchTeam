# Dr. Archi · T1 微架构评审 · P-0198/M-1 CBC

## 结论
有条件通过

硅上 CBC 未发明 flit 队列或第三 highway 槽：气泡是空槽 1b tag + 4b age，每方向每拍仍 1 槽，CHI 四环各 FSM、插入可做成与环拍对齐的同拍/前置寄存路径。作者把「标签化已有 empty + steal 准入」说成「制造空槽几何」——在 DV200 扇入饱和时 payload 占满槽，日历 mandatory 无法从载荷槽变出 empty；机制有效当且仅当 eject（或 epoch 切换前残留）提供的 raw-empty 到达率足够被 tag/steal 转化。T0 PASS_T1 只说明未触 HARD 红线，不等于硅上收益闭合。

## 五维打分
| 维 | 分 | 一句话理由 |
|---|---|---|
| 可行性 | 3 | FSM/仲裁/面积可闭合，但空槽供给与 epoch 对齐是硬前提；「制造」叙事超卖。 |
| 新颖性 | 4 | bufferless 单槽上可窃取循环气泡 + 流量类 epoch 日历，异于有缓冲 Bubble FC / Prevention Slot。 |
| 预期收益 | 2 | 集合 0.55–0.85× makespan 偏乐观：饱和下只重分已有 empty，P2P duty 过密可砸读峰值后 goodput。 |
| 评估可信度 | 3 | HARD-1/消融与分流量类端点写清，但无 cycle 级空槽到达率数据；T0≠测得。 |
| 系统可组合性 | 3 | 四环独立、RBRG 不持状态可共存；单份 64×8 对 8 路 FSM 的端口/相位未钉死。 |

## 最强反对意见
CBC 不能在 payload 已占满的单槽 highway 上凭空 mint empty——日历只把 eligible raw-empty 写成 bubble tag；扇入坍塌若 eject 空槽到达率低于注入需求，mandatory duty 零和再分配无效，inject-fail 主导的 makespan 不会按卡内区间下落。

## 评估层必须验证的一个假设
**H-CBC-empty-supply**：在 DV200 `tests/soc_sim`、12+2、额外流控关闭、已坍塌 gather（或 alltoall）负载下，对单一 CHI 数据环单方向统计稳态「每拍 raw-empty 到达率」ρ_empty 与「bubble-steal 成功注入率」ρ_steal；若 calendar-on 相对 calendar-off 的 ρ_empty 提升 <5% **且** 端点 inject-success 提升 <10%（同 outstanding/事务数），则判定「制造空槽→缩短 makespan」因果失败，CBC 降级为无几何增益的优先级准入（卡 §3 Little/零和叙事不成立）。

## 微架构要点
- **表/缓冲**：每节点 1× 日历 64×8（高 4b duty 0–15，低 4b 相位）；非 flit 队列、无按地址高位冻结目的（HARD-2 字面合规，§3）。Bubble tag 1b + age 4b 骑在空槽编码上，深度仍为 0 缓冲——**未**发明队列/第三槽。容量与 ~0.002–0.005 mm²/top、~1–3 mW（§5）在 5–7nm 量级自洽；但卡写「每节点 1 份」日历而对「每方向×CHI 四环」共最多 8 个 Bubble FSM（§2）——同拍 8 读若真多口 SRAM，面积下限被低估；若 flop 阵列或 epoch 前置寄存共享 duty，须在实现注明，**否则端口关系属发明性省略**。
- **端口/延迟 vs 环拍**：公路槽同拍到达必须同拍决断（bufferless，错过即飘走）。§2 时序：查表「1 组合或 1 拍 SRAM」、FSM 1 拍、仲裁同拍。硅闭合路径只能是：epoch 计数器预取 duty 寄存，highway 上 bubble/empty 译码→steal/keep 纯组合对准 NIC 注入；**禁止**把「机制总插入 1–2 拍」解读为每跳加 1–2 拍（12 跳环会炸一圈延迟）。Transit 载荷路径必须保持基线切片；仅空槽路径做 age++（§2 步骤 4）。过路 flit 仍赢槽——与信封一致。
- **FSM / 反压**：IDLE/WATCH/EMIT/HOLD（§2），W=8 未见气泡则 EMIT 将 eligible empty→bubble。无下游 flit 队列可反压；唯一「反压」是不 steal 时 bubble keep，把空槽留给下游。死锁：bufferless 单槽无持有链，结构死锁弱。活锁：age≥15 强制退化为 raw empty（§2/T0）破气泡聚团；但 collective > P2P > keep（§2）在长扇入 epoch 可饿死 P2P——须 epoch 有界，否则是策略活锁而非结构死锁。
- **仲裁**：2 输入 payload-steal / bubble-keep + 1b 策略锁（§2）——端口级可实现；未定义与「过路赢」冲突时的时序（过路已占槽则本拍无 empty，仲裁空转）——正确，但再次证明机制不增加槽。
- **信封拟合**：bufferless 双向环每向 1 槽、CHI Req/Rsp/Snp/Dat 独立 FSM、RBRG 不承载 CBC 状态（T0）、12+2、禁完美预测/无限带宽——卡 §2–4 字面对齐。日历绑流量类 epoch（P2P duty≈1/16–1/8；扇入 1/4–1/2），**非**消息级到达预测（§2），过 HARD 预测红线。
- **气泡 vs 队列**：气泡=空槽编码对象，可循环、可偷、可变质；**不是**侧存 flit。作者掩盖点：文案「空槽必须被制造并循环」（§1）在硅上实为「空槽必须先存在才能被标记并准入控制」；制造叙事依赖 eject/相位空隙，卡未给 ρ_empty 下界。
- **日历 epoch vs 预测**：拓扑类/集合类静态编程（§2）可接受；未写节点间 epoch 对齐介质与切换延迟——若软件晚于扇入窗，duty 错相，气泡出现在错误邻域。属有界假设，非消息预测。
- **Age 活锁**：AGE_MAX=15 强制释放，防永久 keep；短环上 age 增速快，高 duty 时气泡寿命短，扇入「保留份额」可能自行塌回 raw empty 被错误优先级抢光——密度与 age 上限未联立约束（§2 与 §4 预期区间之间的发明性间隙）。
- **P2P duty 副作用**：稀疏不足则集合无泡；过密则均匀读峰值后 ~5761 B/ns→坍塌被气泡份额加重（§3 HARD-1、§4 0.95–1.10×）。必须分流量类报 makespan/collapsed/读峰值后 goodput，禁均值过关叙事（§4）。
- **引用**：结构与时序 §2；因果/HARD-1/HARD-2 §3；评估与消融 §4；面积 §5。T0 仅 PASS_T1 / 提醒 P2P duty 风险——本 T1 不以 T0 为硅通过。
