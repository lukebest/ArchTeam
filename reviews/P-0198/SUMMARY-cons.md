# P-0198-cons · Tier 0 SUMMARY（保守架构师 M-6..M-10）

清洁室：只读 `_src/problem.yaml` 与 `_src/M-6.md`..`M-10.md`，只与本批五张卡及公开文献对比。未与本批以外的机制卡或评审对照。未改机制卡。

信封：bufferless 双向环，每方向每拍 1 个 highway 槽，无片上 flit 队列；DV200 / `tests/soc_sim`（≤12 top + 2 bottom）；CHI Req/Rsp/Snp/Dat 四环；RBRG；点对点与全集集合；有限 outstanding 与有限链路延迟。禁止完美预测与无限带宽。Endpoint = 分类 makespan / 完成数 / collapse，不是 hop、注入成功率或均匀读峰值。

| 卡 | 简称 | 判决 | 可行性 | 新颖性 | 质量 | 进 T1 |
|----|------|------|--------|--------|------|-------|
| M-6 | 环槽相位日历（TDMA 注入窗） | REJECT | PASS | FUNCTIONAL_EQUIVALENT | INCREMENTAL | NO |
| M-7 | CW/CCW 最短争用弧方向选择 | KNOWN_CONFIRM | PASS | EXACT_MATCH | INCREMENTAL | NO |
| M-8 | CHI 信道亲和与集合相位钉扎 | REJECT | FAIL | FUNCTIONAL_EQUIVALENT | FLAWED | NO |
| M-9 | RBRG 跨环门控窗（无大缓冲） | REJECT | FAIL | FUNCTIONAL_EQUIVALENT | FLAWED | NO |
| M-10 | 环上年龄/集合进度优先仲裁（注入侧） | REJECT | PASS | FUNCTIONAL_EQUIVALENT | INCREMENTAL | NO |

通过 Tier 1：无。

## 边界裁决

- M-6 是本批里唯一「规格闭合且因果自洽」的新提案，仍不进 T1。它没有报文级预测，1-flit 保持停在既有 CHI staging，也没有把带宽说成无限。否决理由只在新颖性：静态许可位图功能等价于 slotted-ring / Æthereal slot table / Nostrum TDM 的注入窗，空波故意放过是 TDMA 的非 work-conserving 本义，不是新结构。与 M-9/M-8 同族不同点。
- M-7 记 KNOWN_CONFIRM 而不是 REJECT：主规则与双向环最短方向逐字相同，值得冻成已知基线，避免以后再当发明；对径 1 拍空槽打平是最小自适应的标准特例，卡自己把主收益钉在 hop 比较上。名字里的「争用」没有测弧上占用。不进 T1。
- M-8 与 M-9 都在 RBRG 时间门上失败，且失败模式相同：窗关时已经在环上的过桥 flit 没有合法下一跳（不能进队列、不能消失、`bp` 只作用于尚未注入的 NI）。M-9 还把 1-flit skid 停过整个 Hold 窗，构成吸收对端忙的 flit 队列。M-8 另有一处：任意 `AFF.ch` 改挂 CHI 通道在 flit 格式上不合法，推荐 on 表又退回 Dat/Req 字面映射，亲和半张卡没有新隔离域。二者互相重叠（M-8 的 Hold 指向 M-9），都不构成可独立推进的机制。
- M-10 可行性放行：4 槽只存 header、不出 NI，且过路优先；若实现扩成数据 FIFO 则应改判 FAIL。新颖性否决：`Age+K·Class` 等价于本地 oldest-first 加静态 QoS 权重（Abts & Weisser SC'07，QNoC，Das 等 MICRO'09 的 LocalAge/rank 基线）。与 M-6 的差别是 work-conserving，不是新问题解。

## 本批结构观察

五张卡都是局部、静态、无反馈的保守旋钮：注入相位、最短方向、通道/相位标签、桥占空比、本地打分。没有任何一张改变单槽零和，也没有任何一张在不添加队列或不依赖测试台排程的前提下切断跨环正反馈。可行的三张（M-6/M-7/M-10）各自只触及碰撞去相关、弧长或本地赢家，且文献已有功能等价物或精确匹配。
