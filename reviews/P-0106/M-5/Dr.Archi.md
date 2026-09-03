# Dr. Archi · T1 微架构评审 · P-0106/M-5 AffineRebind

## 结论
有条件通过

硅上可综合的对象不是标题里的「α 重绑」，而是每 DMC 一份 18b CSR + 48b live mask：RUN 路径 `g=XOR_fold6(G) → (α·g+β) mod n → kth_one(M,slot)`，2-cycle、禁跨 DMC、禁 `core_id`，与 384/18432 信封合。作者把定义域写成 `Z/nZ` 双射、把可变 `mod n` 塞进「6b×6b 乘加 1 cycle <0.3kGE」、又用互素 α 的常函数搜索包装 3-adic 收益——三处对不上网表。T1 只在冷配置原子提交、`(M,n)` 一致且 `n>0`、评估走真实 XOR 折路径、`mod n` 单独闭合时序时接受；簇退役把整 DMC 打到 `n=0` 仍进译码器，或用整数 AP 的 gcd 表冒充硅行为，按致命缺陷退回。

## 五维打分
| 维 | 分 | 一句话理由 |
|---|---|---|
| 可行性 | 3 | 48b kth-one + 18b CSR 可造；可变 12b `mod n` 时序、`n=0`/撕裂/kth-one 越界 FSM 未闭合。 |
| 新颖性 | 2 | 译码器=M-2；互素约束下 α 搜索是常函数，多出来的只是固件写 `n`。 |
| 预期收益 | 3 | 均匀退役时 `mod n` 相对 `mod 48` 类数增益真实；作者自报 0.7～0.95，已咬穿 0.85 线。 |
| 评估可信度 | 2 | gcd 表建在整数 AP 上，硅上 `g` 是 XOR_fold6；drain/实例数/DMC 因子 3 未进模型。 |
| 系统可组合性 | 3 | 守住禁 `core_id`、禁跨 DMC；N' occupancy ledger、CDC 影子寄存器、384 的因子 3 没接上。 |

## 最强反对意见
`slot=(α·g+β) mod n` 的定义域是 XOR_fold6 的 6b（64 点），不是卡 §3 宣称的 `Z/nZ`。`α∈(Z/nZ)*` 上的双射、文档步长类数 `n/gcd(S_g,n)`、以及「乘加 → 12b 再 mod n、1 cycle、<0.3kGE」全部建立在这张错图上：真正昂贵且不定时的是可变模 `n∈[1,48]` 余数器，被藏进 6×6 乘法器；同时 `gcd(α,n)=1 ⇒ gcd(α·S_g,n)=gcd(S_g,n)` 对任意文档 stride 成立，α 的 16 元 minimax 搜索是常函数，3-adic 收益只能来自「模数从 48 改到 n」，不能来自「重绑 XOR/仿射参数」。§1 举例 `bank≡G (mod 48)` 的整数剩余类与 §2 的 XOR 折不是同一条数据路径——评估若打印 gcd 表而不走 XOR_fold6 网表，就是在验证一个硅里不存在的代数。

## 评估层必须验证的一个假设
结构：384 套 `(α,β,n)` CSR + 48b mask，RUN 网表 `g=XOR_fold6(G); slot=(α·g+β) mod n; bank=kth_one(M,slot)`（禁止用整数 `g` 的 AP 公式替代）。指标：退役率 {0, 6.25, 12.5, 25}% × {均匀, 按 3 残类偏退役} 上，文档步长 `{512B, 3×512B, 9×512B, 512KiB, 1MiB, 2MiB}` 的每 DMC 碰撞类数、以及 base+stride 扫描的 min/mean BW。失败判据：任一 degenerate 命中 `M=0` 的 bank，或每 DMC 类数相对 `n/gcd(S_g,n)` 偏差 ≥2，或 min 或 mean BW 跌出 0.85。

## 微架构要点
- **仿射 CSR**（卡表）：384×(6b α + 6b β + 6b n)=6912b=864B，repair 1W / 译码 1R。6b 够 `n≤48`、`α∈[1,47]`；`β=dmc[5:0]` 对 384 DMC 只有 64 个不同值，6 个 DMC 撞同一 β——「错位」是弱声明，不是 384 路相位。若译码在 DMC 内，真实对象是每 DMC 18b flop，864B 只是求和记账；若 120 核各持一份全表，复制为 120×864B，卡未写。1R 在「120×128=15360 outstanding 打一张中心表」下不够，必须是 per-core 或 per-DMC 私有 1R。
- **live mask**（卡：复用 M-1，不依赖 M-3 SRAM）：384×48b=2.25KB=18432b，恰好 1 bit × 系统 bank。这是 valid bit，不是 N' occupancy ledger；P-0106 点名「不能复用满好 18432 分账」——本卡零字交代谁在 `n` 改变后重建 per-bank credit/scoreboard。1R、48b 并行读给 kth-one；SRAM 384×48 或 per-DMC 48 flop 均可，但「共享前缀树」未说共享域：384 DMC 共用一棵则译码串行化，与 1 req/beat 矛盾。
- **6b×6b 乘加 + `mod n`**（卡：组合 1 cycle，`α·g+β`→12b 再 mod n，<0.3kGE）：乘法本身 <0.3kGE 成立。`n` 运行时可取 1..48 非 2 幂，12b 可变余数是独立单元（恢复除法 ~6 级，1–2kGE，1GHz MC 或可 1 cycle，2GHz+ 往往要拆级）。卡把余数器面积/时序吃进乘加，**发明了「乘加=仿射 mod n」**。`g` 为 6b 则值域 0..63，`n=40` 时 64 点打到 40 槽，槽占用差 1；即便 `g` 是满好 0..47，48→`n` 也只是 floor/ceil 均衡，**不是** `Z/nZ` 双射。25% 均匀 `n=36`：12 槽双倍预像、24 槽单倍，2:1 失衡卡未报。
- **kth-one**（卡：共享前缀树，1 cycle，48b→6b）：`slot∈[0,n)` 找第 slot 个 1，到活 bank 的双射成立，死命中 0 当且仅当 `n=popcount(M)` 且 `slot<n`。`n>popcount` 或撕裂时 kth-one 无第 k 个 1——前缀树返回值未定义，可把请求打进退役 bank（官方 falsify 第二枝）或卡住 FSM。
- **RUN FSM / 节拍**：卡「与 M-2 相同 2 cycle（乘余 + kth-one）」。可流水成吞吐 1/beat、延迟 2（stage0：并行读 18b CSR+48b mask 并做乘余；stage1：kth-one），前提是 `mod n` 真落在 stage0。DMC 选择不重绑，译码可放 MC 时钟域，不进核侧临界路径；2 cycle vs DRAM tRCD 可忽略，128 outstanding 覆盖延迟不是问题。背压：1R 结构在 dual-issue MC 上不够，卡按单端口写死。
- **REPAIR FSM / 128 outstanding 原子性**：卡序 fence→drain→写 mask→`n=popcount`→固件搜 α→写 `(α,β,n)`→release。P-0106 写明 live-set 是**运行时集**，卡实现是**离线固件**。120 核 ×128 outstanding 的 drain 是全系统停发，成本是 DRAM 排空（百 ns–μs），不是卡写的「<10k cycle 可忽略」。未关上门限：一笔卡死 outstanding → fence 死锁；未关新请求 → livelock。boot-only 则 128 原子性真空，但与「runtime set」题面冲突。CSR 在 CPU/APB 慢钟、译码在 MC 快钟：66b `(M,α,β,n)` 无影子寄存器则撕裂，`n≠popcount` 即上述 kth-one 未定义。
- **`n=0` / 跨 DMC（本题硬约束）**：卡「`n=0` 标 DMC 不可用」，未写译码器输出。禁跨 DMC 借 bank ⇒ 该 DMC 的地址切片（8GiB/384≈21.3MiB）无处去。25% 簇退役 = 4608 bank ≈ 96 个 DMC 全死：AffineRebind 对这些地址要么打退役 bank、要么挂死。均匀 25% `n=36` 才是卡 §3 的 9 类故事；簇态下本机制收益为零。这不是评估口味，是 THE constraint。
- **α 搜索（卡候选 16 个奇数、`gcd(α,n)=1`、文档步长 minimax）**：整数 AP 上该目标函数对所有互素 α 为常数。仿真器「禁止手工 α=1」是流程约束，不是硅增益。`3|n` 时禁 `3|α` 已被互素蕴含；`3∤n` 时因子 3 从分母消失——题面 3-adic 命题只在 **g 为整数剩余类** 时成立，XOR_fold6 下 S 的进位/位翻转会改碰撞集，卡未给一门级模型。
- **逆映射**：正向 `slot↔` 活 bank 可逆；`g=XOR_fold6` 有损，响应路径若只携带物理 bank 则不必逆。探针/目录走同一正向即可。卡「可逆」只覆盖活集上的 kth-one 段，不覆盖地址重建。
- **384/18432 / 3-adic / core_id**：不改 DMC 图，384=128×3 的大 2 幂步长可先把 BW 钉在 128/384≈0.33，**intra-DMC 重绑救不了 DMC 级因子 3**。禁 `core_id` 守住。满好 `48=16×3`、`S_g=2^k(k≥4)` → 每 DMC 3 类；改 `mod n` 后 `n=36` → `gcd(2^k,36)=4` → 9 类（卡 §3，相对不重绑 ×3）——此句只在整数 `g` 上成立，标为与 XOR 路径的**发明关系**。作者预期「3 残类偏退役有重绑回到 0.7～0.95」、置信度中：0.7 已低于官方 0.85。
- **面积/功耗自洽**：864B flop 卡用 6GE/bit≈41kGE（偏乐观，DFF 常 8–12GE）。mask 2.25KB 若 SRAM 则量级匹配；若 flop 则 ~180kGE，未披露。384 份 kth-one 前缀树才是面积项，卡写成「共享」以躲开 384×。功耗 0.3～0.6mW 只像单实例 1R；×384 MC 则上百 mW。无 13.5KB LUT 这句成立，也是唯一干净的开销命题。
