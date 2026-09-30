# Tier 0 · P-0198/M-6 · 环槽相位日历（TDMA 注入窗）

- 机制卡: mechanisms/P-0198/M-6.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 成立但上界清楚。过路优先下本地注入只是残差 `I≤1−O`；静态 `CAL[Φ]` 把同环多源的许可错开，减少「同一空槽被多个 NI 同时抢」的相关碰撞，并把最坏相位等待钉在 `P∈{8,16}`。这只重排空槽残差的时间位置，不增加槽、不提高 `μ`。卡内 Amdahl 式上界（只切 `f·α`）与「全 1 位图 = off、不可分则禁止写因果」是自洽的。轻载卖掉空波会加最多约 `P` 拍，卡已要求单报，不把重载收益外推到全信封。
- 完美预测/无限带宽/零延迟: 未触犯。`Φ` 自由运行 + 上电对齐，明文禁止用占用预言校正相位。日历是 `die_id % P` 的静态 CSR，不是按报文/集合完成时刻排程。不把带宽当成无限：空波被故意放过，均匀读崩塌区不承诺拉回峰值。决策是当拍 `permit AND NOT slot_occupied`，零额外环路延迟或至多 1 拍预译码。
- 约束边界（bufferless 单槽、无 flit 队列、CHI 四环、RBRG、DV200 12+2、点对点+全集集合、有限 outstanding）: 守住。每环每方向独立日历，过路绝对优先，失败停在「既有 CHI 口 1-flit header staging」，不新开织物队列、不在环上堆 flit。四环复制而非把通道揉成一条。跨环对齐明确推给别的机制，本卡不假装单环相位能解 RBRG。评估要求 12+2、点对点与全集集合分开报 makespan/完成数/collapse，并承认 0.85 是每类 pass bar。未把平均 hop 或峰值 goodput 当成 endpoint。
- 硬件开销 vs 问题约束: 匹配。8 个 4b `Φ` + 每 NI 16b `CAL`，上界约 1792 bit CSR，无 SRAM/CAM，`<3 kGE` 量级，不占 highway 槽、不加链路位宽。开销不是可行性问题。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 功能等价于「只允许在预分配时隙注入、其余时隙即使为空也放过」的时隙环/TDM 注入表，而不是空槽环的随到随注。Pierce, "Network for Block Switching of Data," BSTJ 1972 的 slotted ring，以及 Cambridge Ring 的 empty-slot（谁遇到空槽谁填）是近邻；本卡比 empty-slot 更严，等于给每个 NI 一张周期许可位图。Goossens, Dielissen, Rădulescu, "Æthereal Network on Chip," IEEE Design & Test 2005：每槽每口至多一次传输的 slot table，NI 按表注入。Millberg, Nilsson, Thid, Jantsch, "Guaranteed Bandwidth using Looped Containers in Temporally Disjoint Networks within the Nostrum NoC," DATE 2004：bufferless 网络上的 TDM/TDN。Wassel 等, SurfNoC, ISCA 2013 的 wave schedule 同样是时间分片而非新带宽。本卡不做 Æthereal/Nostrum 那种端到端时隙预留，只做本地注入许可，这是范围缩小，不是另一条路。LLM 两类流量只是这张静态表的负载，没有新的结构自由度。
- vs 本批其他卡: 与 M-7（方向二选一）、M-10（空槽出现后的本地打分）正交：M-6 在槽空时仍可能禁止注入，M-10 在槽空且有 ready 时一定选出赢家（work-conserving）。与 M-8 的 `CPHASE`/`RBEN`、M-9 的 `EΦ`+窗长同属静态周期门，但 M-6 门在 NI 注入许可，M-8/M-9 门在 RBRG；位图错开的是同环多源，不是桥的占空比或集合类。不能并成一张卡，也没有超出该族的新机制。

## 判决理由
可行性通过：无预言机、无新 flit 队列、无无限带宽，因果限于碰撞去相关，评估消融写得诚实。新颖性不过：它就是 bufferless 环上的静态 TDMA 注入窗，文献里的 slot table / temporally disjoint slot 已覆盖同一功能。对本题的崩塌与集合尾部，卡自己把收益压在 8%–25% 且置信度中偏低，结构增量不足以单独开 Tier 1。REJECT / INCREMENTAL / 不进 T1。
