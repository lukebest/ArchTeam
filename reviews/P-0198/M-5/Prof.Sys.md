# T1 · Prof. Sys · P-0198/M-5 · CRRF

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 3 | 时分重绑电路可做；但 Snp 无队列只 stall，把一致性流量绑到 epoch，系统风险高于另三张。 |
| 新颖性 | 4 | CHI 四环上 Channel–Ring epoch 重绑，不是通用 TDM 复述。 |
| 预期收益 | 4 | 直接打 Dat 饱和 / Snp 闲的不对称；Amdahl 叙事清楚。 |
| 评估可信度 | 3 | 必须强制 Snp makespan；duty 扫描可证伪；ghost Dat 正确性难一次测净。 |
| 系统可组合性 | 2 | COLL_EP 是整 die/整环织物模式；多租户与一致性延迟同绑一条 SYNC。 |

## 最强反对

CRRF 在 DAT_EPOCH 把 **Snp 环硬件改成 ghost Dat**，Snp 只能等 SNP_EPOCH，且**无队列**。缓存一致性的关键路径（Snp/SnpResp）被推进一个与 LLM 集合相位耦合的全局时间表。Rebind FSM 若由「软件/运行时类提示」切入 COLL_EP，一个租户的 allreduce 相位会抬高**所有**核的 Snp 尾延迟——包括无关 VM。若改由本地计数器自动切，则误判 COLL_EP 时仍锁全环。SYNC 在 Req 环对齐；跨 RBRG 的 epoch 视图一旦歪一拍，channel-id 核对会拒注或（更糟）若实现放松核对就会上错环。这是本批对一致性/多租户伤害面最大的一张，不是「再分配闲带宽」这么轻。

## 评估层必须验证的一个假设

COLL_EP、duty=7:1 下，在混合负载（Dat 向集合 + 后台缓存一致性抖动）中，Snp 类 makespan ≤1.2× 基线，且无 CHI 通道错绑（ghost Dat flit 永不进 Snp 逻辑消费口）。若 Snp 越出 1.2× 或出现错绑，本卡不能进多租户/有目录的 SoC，只能当无 Snp 压力的加速器专环模式。

## 系统视角

- 软件可见性：高。运行时至少要暴露 COLL_EP/P2P 提示，或接受计数器误判。同步错误是全机故障，不是单流性能毛刺。
- 编程模型：新控制面（epoch 表、duty、FSM 态）。与 CBC 的日历类似但更重——改的是通道–环绑定，不是空槽密度。集合库与一致性子系统必须联合回归。
- 协议/一致性：Req/Rsp 不重绑是必要减伤。Snp stall 无队列 ⇒ 一致性 outstanding 在 SNP_EPOCH 饥饿时堆积在端点；端点若也无队列，会反压到核侧 fence/原子。必须在模型里打开「有 Snp 流量」的用例，不能只用纯 Dat 集合刷分。
- 多芯片：NIC 与 RBRG 各一份 4×4，必须共享同一 epoch 视图。12 top + 2 bottom 经 RBRG 传播 SYNC；bottom 间若有第二条时间源，卡未写仲裁。
- 多租户：织物级模式，无 per-tenant bind。一租户 COLL_EP，全员吃 Snp 税。不可与「每 VM 独立 NoC QoS」故事共存，除非禁止自动 COLL_EP、改为整机作业切换。
