# T1 · Prof. Sys · P-0105/M-4 · SNS

## 结论

通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 剪切加法 + 256B ROM + fold384，1 cycle；ROM 按整数置换装填，避开了 AES/GF(256) 假置换。 |
| 新颖性 | 4 | 奇数剪切拧格 + 整数环置换多项式拆线性码，不是 XOR Latin / 互素仿射的换名。 |
| 预期收益 | 4 | 直接打 OS 真实会发生的事：ASLR、不同 malloc base、同相/错相；相位不变是系统收益。 |
| 评估可信度 | 3 | 剪切可证；S-box discrepancy 无 Weil 界，卡内 CV 数字必须当待测，不能当已测。 |
| 系统可组合性 | 4 | 无编程模型、无 per-tenant 表、S-box 不参与重绑；和现有 PA/DMA/一致性模型对齐。 |

## 最强反对

`fold384` 吃 12 bit，`4096 = 10×384 + 256`，永久 256 个 DMC 多一档、128 个少一档。这偏置软件不可见。更糟的是：Linux/NUMA 页着色、部分内核的 cache-color 假设仍是「低位或 XOR hash」。本卡的剪切+S-box 打散的位，和 OS 正在涂的色可能重叠也可能对抗。实验室「扫 base、相对差→0」若在 buddy+ASLR+着色同时打开时复现不了，相位不变只在裸机线性 PA 上成立。

## 评估层必须验证的一个假设

在真实 4K 分配器（buddy + ASLR，再加一档页着色）下，固定 S=2MiB，跨进程起始地址的 min/mean BW 相对差仍 <5%、n_DMC 变化 <10%。若着色位打进 x' 或 z 后方差回来，本卡对「人钉的起始地址症状」在有 OS 时不成立。

## 系统视角

- 软件可见性：应用零改动。ROM 必须进复位镜像、两 die/CPU/GPU/DMA 同一张表；禁止运行时改 S-box（改了就改 PA→DMC，home 漂）。
- 编程模型：无新 API。OS 不必为相位调 base；这是本卡相对本批最能组合的一点。
- 多租户：全机一张 ROM，租户互不改映射。不同 VM 的 GPA→HPA 只是又一次 base 平移，正好落在本卡声称的不变性上——前提是 HPA 仍走同一 shear+SBOX。
- Partial-good：位图 + PE，同 DMC 好 bank，S-box 不参与。改 mask 只挪死槽，比 select-k 轻。仍要 drain 再写位图。
- 多芯片/多节点：包内两 die 必须锁同一 ROM。跨 socket 只要 home 在本 socket 的 MC 里就算完；CXL.mem 设备若用自己的交织，相位不变性在主机侧不可见，不能把主机 ROM 的结论外推到设备。
