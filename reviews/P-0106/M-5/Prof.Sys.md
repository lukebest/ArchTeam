# T1 · Prof. Sys · P-0106/M-5 · AffineRebind

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 运行时是 6b 仿射 + kth-one；α 搜索在 REPAIR+fence，不是每请求神谕。 |
| 新颖性 | 3 | 译码器是教科书仿射+select；新颖在把 n_live 的因子分解当交织一等公民。 |
| 预期收益 | 4 | 对准本题：丢掉奇数因子后 gcd 变，不重绑会按 48 的 3-adic 再被 mask 砍。 |
| 评估可信度 | 4 | gcd 表可打印、可证伪；明确禁止手工 α=1 冒充已重绑。 |
| 系统可组合性 | 3 | 上电/配置时重绑可组合；把 live-set 说成运行时集合则过了，在线 RAS 没有数据面。 |

## 最强反对

`(α,β,n)` 一改，该 DMC 上**每一个** PA 的 bank 像都变（仿射换模数，不是跳死槽）。卡给 REPAIR `<10k` cycle：2 GHz 约 5 µs，够 drain 发行口，不够搬该 DMC 上的数据（8GiB/384≈21MB）。所以这是 **boot/config 的 fuse-map 替换**，不是 OS 运行中的 bank 退役。P-0106 题面写「live set 是运行时集合」；本卡的系统接口只闭合了「上电前算一次」。若产品把它当热 RAS，写回/DMA/GPU 会在新旧仿射之间撕裂。

## 评估层必须验证的一个假设

REPAIR 窗口里存在非 CPU 代理（DMA 或模拟的 posted write）时，fence+drain 之后死命中=0、且**没有**一条在 fence 前发出、在 CSR 提交后写回的请求。若有绕过，本卡在真实 I/O 子系统上不可组合。顺带打印：重绑前后同一批 PA 的 bank 变化比例（预期 ~1，不是 ~1/n）。

## 系统视角

- 软件可见性：PA 空洞不打穿，OS 仍看见满容量 8GiB，并行度却随 n_live 降。若无 RAS 遥测，内核/hypervisor 的 BW QoS 会按 48 bank 记账。需要一条只读 sysfs/CSR（n_live per DMC），不是编程模型改动，是可观测性。
- 编程模型：应用无 API。α 按固件文档步长集搜，不看租户真实 stride；多租户混合步长时「最优 α」对谁都不优。禁止 `core_id` 是对的，避免 per-thread 图。
- 多租户：CSR 按 DMC 全局一份，VM 不能自带 α。一次 repair 影响该 DMC 上所有租户。不能做 per-VM partial-good。
- Partial-good / 固件协同：**这张卡的全部系统税都在这里。** 必须有明确状态机：fence → 停 CPU+DMA+ATS → 写 mask → 按文档算法填 (α,β,n) → release。仿真器与产品固件必须同一算法。热路径若要保数据，还缺 copy engine，本卡没有。
- 多芯片：只重绑 bank-in-DMC，不改 DMC/HA，目录 home 稳定，这是相对改 DMC 图的优点。两 die 可独立 repair 各自 DMC，但每颗 DMC 的 CSR 与 mask 必须同事务。多节点/CXL 设备各自固件，主机 OS 只能看见容量/带宽，看不见 α。
- 协议：config-time 冻结后与一致性、原子、拷贝兼容。在线改 CSR 不兼容，除非先把该 DMC 从可写域摘掉。
