# Dr. Archi · T1 微架构评审 · P-0105/M-4 SNS

## 结论
有条件通过

剪切 `x'=(x+7y) mod 2^12` 加 256×8 整数环 S-box 把 S=2MiB 的 4096 点做成 12 bit 全置换：`raw` 对全部 4096 个相位都是 `{0..4095}` 的双射，`fold384` 后 n_DMC 恒 384、min/max=10/11、CV≈0.044，与 base 无关。没有 `core_id`，请求路径上也没有 4096 项相位表，DMC/HA 轴的 P-0105 被代数钉死。但卡把 bank 轴交给 `x'[9:4] mod 48` 的 6 bit 窗，大步长下每 DMC 只碰 6 个 bank 且锁在单一 `bank%8` 类；位图按 DMC 索引，不可能与 ROM 真并行，1 mapper cycle 不是硅。DMC 相位问题换成了 bank-group 瓶颈——过 T1 的条件是改 bank 窗或用带 tCCD_L 的 cycle 级 DRAM 证过 0.85，并把 mapper 拆拍、写清 48:6 PE 与全坏 DMC 出口。

## 五维打分
| 维 | 分 | 一句话理由 |
|---|---|---|
| 可行性 | 3 | DMC 数据路径可综合（12 bit 剪切 + 256 B ROM + fold384），但 1 cycle 含位图与 6-bank 窗按原样流片不成立。 |
| 新颖性 | 4 | 奇数剪切拧格 + 整数环 `u^5+u^3+u mod 256`（非 AES/GF(256)）再 fold 到非 2 幂 384，确非 Latin/平面导数。 |
| 预期收益 | 3 | 相对 1D 的 3 DMC/5120 是数量级；相对「48 bank 用满」被每 DMC 6 bank 同一剩余类吃掉。 |
| 评估可信度 | 3 | S=2MiB 的 DMC 数字是定理级（置换）而非卡写的「实验 discrepancy」；bank 轴与 DRAM 时序被 §2 主动放弃证明。 |
| 系统可组合性 | 3 | 384/18432/无 `core_id` 干净、不跨 DMC 借 bank；但 `bank_in` 与 partial-good PE、DRAM BG、fold384 的 256 热/128 冷装箱咬合差。 |

## 最强反对意见
`bank_in = x'[9:4] mod 48`（§2）在 P-0105 的硬工况上把 48 轴塌成 6。S=2MiB 时 `x'` 虽是 4096 全置换，送进 bank 的只有 6 bit 再 mod 48：全局 bank 0–15 恒 128 hit、16–47 恒 64 hit（min/mean=0.75<0.85，与 base 无关）；每个 DMC 精确占用 6 个 bank，构成公差 8 的等差，即单一 `bank%8` 剩余类，类内负载可到 1 vs 4。`(DMC,bank)` 对在 base+=512 时 Jaccard=0——占用控制器个数不变，占用哪些 bank 全换。卡明文「gcd 不在这 6 bit 切片上证明」。48<4096 的剩余不是「联合空桶」，而是 DMC 内部 bank-group 锁死；冻结包络禁止跨 DMC 借 bank。occupancy CV≈0.044 不能外推 min/mean R/W BW：6 路同剩余类直接撞 tRRD_L/tCCD_L/tFAW。48:6 PE 若再按固定优先回收，坏 bank 会把整 DMC 的 10–11 hit 倒进 bank 0/1。

## 评估层必须验证的一个假设
结构：§2 的 12 bit 剪切加法器（`(y<<3)-y`）+ 按 `S(u)=u^5+u^3+u mod 256` 装填的 256×8 ROM（前 16 项 `[0,3,42,17,68,183,62,5,8,139,146,89,204,255,166,141]`）+ XOR + 12 bit fold384 + `bank_in=x'[9:4] mod 48`，请求路径禁止 4096 项表、禁止 `core_id`。负载：S=2MiB，8GiB，15360 inflight，只改 base∈{0,512,…,3584}；partial-good 用「每 DMC 随机 3/48」与「整 residue class 失效」两档。度量：每 DMC 占用 bank 数、占用 `bank%8` 种类数、cycle 级 DRAM（tRRD_L/tCCD_L/tFAW）min/mean R/W BW。失败：任一 base 使任 DMC 占用 bank≤6 且该相位 min/mean BW<0.85，或跨 base BW 相对差≥5%。

## 微架构要点
- **表/缓冲**：256×8 组合 ROM = 256 B、1R，固件/离线装填置换多项式，非每请求可编程 offset 表，也不是 4096 项相位 SRAM（§2、§5）。位图 384×48-bit = 2.25 KB、1R，boot 写、运行读。无 outstanding 缓冲（§2）——若拆拍只需 2–3 级流水寄存，128 outstanding/核盖得住。**发明关系**：卡按一份 ROM+一份位图报面积；未写 mapper 是 120 核副本还是 192 HA 副本，副本数未计入。
- **端口与拍数**：ROM 地址是 `x'[11:4]`，必须等 12 bit 剪切加法结束才能读；`z` 再 XOR `y[7:0]` 后才拼 `raw`、才 `fold384`。位图按 DMC 索引，**不能**与 ROM「1R 并行」（§2 时序句是错的）。真路径是串行：`(y<<3)-y`+加 `x` → ROM → XOR → 12 bit `q*384` 折合（`q=0..10`，`384=256+128`）→ SRAM[DMC] → 48:6 PE。5 nm 上 ROM<200 ps 只覆盖中间一截；全链 1 mapper cycle 在 2 GHz+ 不自洽。条件：拆 ≥2 拍，bitmap/PE 放在 DMC 稳定之后。
- **FSM / 反压**：48:6 PE「1-cycle retry 到同 DMC 好 bank」（§2）未画状态机。若组合 find-first，没有 retry 拍，也没有 livelock。若真是 miss 再试，气泡打进 HA 请求反压；全 48 bank 坏时冻结包络禁止跨 DMC 借用——**没有 poison/error 出口即死锁**。PE 替换策略未指定；按 index-0 优先会在 partial-good 下把 11 hit 压进单 bank（结构名：48:6 PE + 2.25 KB 位图）。
- **384/18432 拟合**：`raw∈[0,4095]`，`4096=10×384+256` → 256 个 DMC 得 11、128 个得 10，且因全置换，**热集恒为 DMC 0–255**（对所有 base）。HA 轴若按 2 DMC/HA 装箱则 20/22，CV 同 0.044。**发明关系**：DMC 编号到 2×Die2 ×96 HA ×2 pipe 的物理装箱卡未给出；若线性装箱，die0 全热、die1 半冷，10% 级永久 die 偏，与相位无关但与 floorplan 有关。不改 384/18432/96，不借 bank，符合信封。
- **bank 窗与 3-adic**：`x'[9:4]` 扫 0..63 再 mod 48，`48=16×3`、`64=48+16` → 2:1 静态偏。S=2MiB 的 6 bank 公差 8，是 2-adic 切片而非剪切的 3-adic 保护（`7≢0 (mod 3)` 只保护 `x'` 在 mod 3 上不冻）。fold384 的 `384=2^7×3` 在全置换下不塌；短窗 3-adic 步长（如 4608 B、8192 点）CV≈0.13–0.14 与卡 §3 一致，是 inflight 窗而非 8GiB 渐近。`gcd(4096,384)=128` 的 1D 三 DMC 病被剪切打断，**没有**在 bank 轴上做对偶。
- **core_id / 相位 id**：相位是 `phys_addr[20:9]`，行走是 `phys_addr[32:21]`，映射只看当前地址（§2）。128 outstanding/核独立成立。禁止把核号塞进 ROM 地址或「phase id」。
- **partial-good**：S-box 不参与坏 bank 重映射，位图+PE 保持 384/18432（§2）。S=2MiB 的目标 6 bank 与 base 一起转；随机 3/48 坏时 remap 计数随 base 小幅晃（约 226–288/4096），整 residue class 失效时 48 个 DMC 的全部流量被 PE 重放。不能跨 DMC 借，评估必须含聚类失效，不能只跑 1/16 均匀。
- **面积/功耗**：256 B ROM + 2.25 KB 位图，单份与 5 nm <0.002 mm²、mW 级（§5）量级自洽；120 份仍远小于 120 核。功耗自洽的前提是 ROM 真是表、不是关键路径上的 `u^5` 链（§2、§4 已排除 AES/GF(256)，那只有 154 值、不是置换）。
- **对审讯的直接回答**：不加可编程 offset 大表；ROM 256 项由固件装填、每请求只做 1R；不偷 `core_id`。384 DMC 对任意 base 看到同一 10/11 discrepancy **不需要** 4096 项请求路径结构——剪切+S-box 的 12 bit 置换已经够。T0 的 PASS_T1 只覆盖了这一句；T1 卡住的是同一套硬件上的 6 bit bank 窗和假并行 1 cycle。
