# Dr. Archi · T1 微架构评审 · P-0198/M-2 CSR（T1-return-1）

## 结论
有条件通过
原三项致命点（RBRG Dat latch / 假 8 槽 TDM / 无超时逃逸）在修订卡上被**结构性拆除**而非仅改措辞：无载荷存储、`N_cam=4` 专用、`overflow/timeout→RING_P2P` 计数进 endpoints，硅上可强制 `Dat_beats_held==0`。但卡文把「payload 留在 Dat 环直到 GRANT」与「授权窗内注入」并置，cycle 模型未钉死；再加 FORCE_FALLBACK「通知相关端」无对应公民/端口——这是新洞，不是旧洞回魂。条件不满足则降为致命。

## 五维打分
| 维 | 分 | 一句话理由 |
|---|---|---|
| 可行性 | 3 | Dat≡0 与拒收零滞留可硬；orbit/门控歧义 + 回退通知路径未进结构表，12 top 下 CAM 单端口仍紧 |
| 新颖性 | 4 | 会合状态与 payload 切开、RBRG 只做 Tag+GRANT，相对桥上 in-network reduce 寄存器堆是真切面，非 CBC 换皮 |
| 预期收益 | 2 | `N_cam=4` vs 12 top / 高 outstanding 易使 overflow 主导；GRANT 占 Dat 槽与窗内串行注入税可能吃掉 0.45–0.80× 区间 |
| 评估可信度 | 2 | 预期区间依赖未钉死的注入语义；「通知相关端」像纸面闭合；T0 PASS≠硅证明 |
| 系统可组合性 | 3 | 与 CBC 对象正交可辩；但 GRANT 公民与 P2P/日历气泡抢同一 Dat 槽，端点 fold 默认已有 RF/cache 端口 |

## 最强反对意见
若 COLLECT 期间各源已将 payload 注入 Dat 环做 orbit，则 GRANT 前环上已有 Ω(成员数×多拍) 公民占槽，扇入零和未被移除——spine-on 环占用应 ≥ spine-off；若改为端点持有至见 GRANT 再注入，则 §2.2「留在 Dat 环直到 GRANT」为假叙述，必须改成显式端点门控注入，并证明 512 B×outstanding 持拍只走已有 RF/cache、不发明第三 highway 槽或侧缓 FIFO。

## 评估层必须验证的一个假设
**H_inject_gate（端点门控注入）**：对任意 `SPINE_RENDZ` txn，在该源端点观测到本 txn 的 GRANT flit 之前，该 txn 的 payload Dat 拍**注入计数 ≡ 0**；同时全仿真 `∀i occupancy(CAM_i, Dat_beats)==0` 且 `RBRG_reject_retention_depth==0`。若 GRANT 前已在环上出现该 txn 的 payload 拍，则按「提前 orbit」判机制失败（不得记入 CSR 收益）。

## 微架构要点
- **CAM / 端口（§2.1）**：`N_cam=4`，每项 `txn_id16 + child_bitmap12 + state3 + timeout8 ≈ 39 b`，专用非 TDM；端口声明 1 读匹配 + 1 写分配 / 拍。相对旧「1–2 latch 装 8」——**原致命点 2 真闭合**（面积按 4 路真并发，§5）。**发明性省略**：四环/多 divert 同拍双头抵达时的 CAM 仲裁优先级未给；busy 即 overflow 回退，可活，但 12 top 并发集合下 `cam_overflow_fallback` 预期偏高。
- **Dat≡0 不变式（§0/§2.2/§2.3）**：禁止 RBRG 内任何 Dat payload 寄存器/多拍 fold/reject-and-orbit 滞留队列；断言 `Dat_beats_held==0`、`retention_depth==0`。RENDZ 限定 1-flit header/credit 短 divert——**原致命点 1 在「桥内不持拍」意义上真闭合**，强于旧「≤1 Dat latch」。硅可在 divert mux 按 tag 拒载荷。
- **GRANT 公民（§2.1–2.2）**：位图齐 → `GRANT_PENDING` → 向 Dat 环注 1 拍 GRANT（txn_id+相位），占既有 1-slot/向，**未发明第三槽**。与 payload / RING_P2P 零和抢槽——诚实。窗内按静态 order 表串行注入：扇入从盲目 Ω(N) 变为有界窗口并发，逻辑自洽，但窗长与 GRANT 本身占槽是收益税。
- **timeout / overflow（§0/§2.2）**：每项 `timeout` 到期 → `FORCE_FALLBACK` 释 CAM + `collect_timeout_fallback++`；CAM 满/busy → 头继续前进并立即 `RING_P2P` + `cam_overflow_fallback++`。禁止静默等死/丢弃；两计数进 endpoints——**原致命点 3 的「逃逸存在性」真闭合**。**发明性省略**：结构表无 FALLBACK/Notify flit 端口，却写「通知相关端改走 RING_P2P」——分布式超时与源端本地等待若不同步，会 orphan CAM 项或源永等 GRANT；须双端同源超时上界或显式回退公民，否则纸面闭合。
- **端点 fold（§2.2/§2.3）**：折叠声明在目的/root NIC 的已有 RF/cache，1 拍/运算宽度，不在 RBRG。不发明 highway FIFO——方向正确。**发明性省略**：假定集合 fold 所需 RF/累加端口与写回带宽已存在且不与普通 CHI complete 路径打架；评估须确认不是「默认有归约 ALU」。
- **反压 / bufferless（§1/§2.2）**：RBRG 拒 RENDZ 不造深度>0 滞留；满则重分类而非侧缓。Payload 若不提前 orbit，环反压形态回到「单槽公路 + 端点门控」——与信封一致。若提前 orbit，则反压被自我污染，机制自毁。
- **面积自洽（§5）**：~156 b CAM + 4×(timeout/FSM) + GRANT 装配/仲裁 + 2×32 b CSR；明确为零：512 b Dat latch、fold RAM、highway FIFO。叙事与并发上限一致，无「小存储装大并发」自打脸。
- **与 envelope 拟合（§4）**：DV200 ≤12+2、CHI 四环、禁完美预测/无限 BW；消融 spine-off 须回基线量级；512 B、outstanding 256/512、全集扫描。预期 gather/reduce 等 0.45–0.80× 在 `N_cam=4` 下偏乐观——卡已写「回退主导则区间失效」，评估必须把该杀开关当真，不得只报均值。
- **与 T0**：T0 PASS_T1 /「原致命点全部 CLOSED」只确认声明边界进 T1；本评独立认定旧三点**结构上可闭合**，但 **H_inject_gate** 与 FORCE_FALLBACK 通知路径为 T1 新条件——未钉死前不得无条件通过。

**通过条件（须同时满足，否则改判致命缺陷）**：
1. 实现与断言采用 **端点门控注入**（见 H_inject_gate），禁止 GRANT 前 payload orbit；卡文歧义在实现规范中消除。
2. FORCE_FALLBACK 的端点可见性有具体路径（显式环上回退 flit **或** 源/桥双端同源 timeout 上界 + orphan CAM 有界释放），并进仿真计数。
3. 满信封下若 `cam_overflow_fallback` 或 `collect_timeout_fallback` 主导完成路径，不得宣称集合 makespan 区间达成。
