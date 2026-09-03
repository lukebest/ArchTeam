# T1 · Prof. Sys · P-0103/M-1 · MRFI

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 单边 Feistel + CRT 是当前地址的纯函数；100% good 1 拍，partial-good 2 拍，因果清楚。 |
| 新颖性 | 4 | 对象是「2-adic 活熵注入冻结的 Z_9」，不是 Seznec 整数模、也不是 Intel XOR。 |
| 预期收益 | 4 | 若 F 在 S=3·2^k 上拉满 Z_3，n_DMC 128→384 直接打掉 X_rel=3。 |
| 评估可信度 | 3 | 1.5MiB 只剩 6b 熵、1/3 图案再相关、共享 1R 冲突，三条都可能把占用账打穿。 |
| 系统可组合性 | 3 | 应用不用改图；但 GOOD_MAP 120 核共享 1R，加上 RAS 更新要全局 drain，已经不是「只改接线」。 |

## 最强反对

GOOD_MAP 是 384×48b、**整机一份 1R**。Partial-good 一旦打开，映射从每核组合译码变成带端口仲裁的共享查找。120×128 outstanding 打在一条 1R 上，恢复出来的 384 DMC 占用会被这条 SRAM 口吃掉。位图若在有飞行请求时改写，同一 PA 会被两个核译到不同 bank，这是静默一致性错误，不是 ECC 能遮的。三次 XOR 仍可能停在死 bank（卡自报 ~1.7e-3），系统侧必须当 UE/poison，不能当「死命中为 0」。

## 评估层必须验证的一个假设

Partial-good 打开时，GOOD_MAP 1R 在 120 核满 outstanding 下**不是**发行瓶颈：mapper 等待周期占比应低到不把 n_DMC 恢复带来的 BW 吃回去。若 1R 饱和，本卡的占用论证在真实发行路径上不成立。

## 系统视角

- 软件可见性：PA→(die,HA,pipe,bank) 对 OS 仍透明，无编程模型改动。必须保证 IOMMU 之后、GPU/DMA 与 CPU 走同一份 MRFI+mask，否则别名。
- 多租户：没有 per-tenant 图，不会互踩映射表。共享的是 1R 口和 XOR 重试造成的 bank 叠压；带宽租户会拖慢所有人的译码。
- Partial-good / 固件：mask 写入是 RAS 事务，必须 fence+drain（含 DMA/ATS），不能热补。重试只改 bank、锁 DMC，home/目录可活；但残留死命中要进 OS poison 路径。
- 多芯片：GOOD_MAP×1 跨 2 die 的放置与仲裁没写。若放在一侧，另一侧多一跳；若复制两份，必须同时写。多节点各包一份，CXL 设备要自己实现同一函数。
- 协议：同一 A 在 mask 冻结期映射不变，和缓存写回、原子、拷贝引擎兼容。mask 变更窗口不兼容。
