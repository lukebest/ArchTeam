# Tier 0 · P-0103/M-4 · MRDR

- 机制卡: mechanisms/P-0103/M-4.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: `t0/t1` 来自当前 `G mod 9`，H0/H1 来自当前 `A[26:19]`/`A[16:9]` 的 XOR 折叠，bitrev 是接线。纯函数，无状态。
- 完美预测/无限带宽/零延迟: 无预测器、无 FSM。1 拍组合（CSA 深度 ~4 + XOR 深度 3 + 模 3 加），partial-good 再 1 拍 SRAM。不是 0。
- 关键边界（S=3·2^k、partial good、冻结奇数因子、512B/4K）: 卡点名「只做数位反转不够」：`3|δ` 时 trit 冻，反转到高位仍然冻。H0 取 `G[17:10]`（`δ=3072` 时低 10b 冻、该 8b 场以 3 步进且 `gcd(3,256)=1`），专打 DMC 因子 3；H1 取 `G[7:0]` 打小步长 bank trit。解码 `DMC=t0'+3·q[6:0]`、`bank=t1'+3·q[10:7]` 不改 384=3×128、48=3×16。XOR 折叠不是 `Z_3` 同态，不把 `3|δ` 传进 H0。partial-good 只改 `bank_in`，第二次重试用 H0 位，禁止 `+1`，DMC 锁定。512B 粒。H0 直方图 `{2,1,1}` 可能把 min/mean 打到 0.7–0.9，卡未把 0.85 写成已达到。
- 硬件开销 vs 问题约束: 五张里最便宜：每核 ~200 GE + 接线 bitrev，无乘法器、无映射路径 RAM。GOOD_MAP 共享。不增端口/资源个数。在信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: 纯 bit-reversal / mixed-radix digit-reversal 来自 FFT 重排（如 US5473556），不是 DRAM DMC 占用方案；卡已证明「只反转不够」。Zhang MICRO'00 permutation page interleave 与 Intel DRAM XOR decode 是 GF(2) 下「高位 XOR 进 bank 索引」；本卡必须在 `Z_3^2` 上做模 3 加，因为 384 与 48 都带因子 3，GF(2) 矩阵表达不了 trit。Seznec CRT 奇数存储器把奇数模当 bank 号本身，不把 trit 与 11b bitrev 拼成混合进制数位。Norton–Melton 布尔线性变换打 2 幂 stride，不注入 trit。结构是「11b bitrev（2 幂轴）+ 两路不相交 XOR-fold trit 注入（奇数轴）+ 混合进制接线解码」，不是已发表 DRAM map 的换名。
- vs 本批其他卡: 与 M-1 同家族（往奇数坐标注入 2-adic 熵），但代数对象不同：无 CRT 模逆、无 Feistel ROM，两 trit 独立注入 + bitrev 把活的高 2-adic 位翻到 DMC 组 LSB。评估计划要求关掉 TRIT_INJ 的纯反转对照必须失败——这把与「只是 bitrev」划清。与 M-5（3b 切块 CSA，根本不算 `G mod 9`）不同。与 P-0105 五张不重复。

## 判决理由
轴一通过：纯组合、覆盖 `δ=3/24/3072` 的活源点名、partial-good 不跨 DMC、开销在信封内。新颖性 DIFFERENT_APPROACH：混合进制数位置换必须搭配 trit 注入才打得开冻结因子 3，这是可被对照实验证伪的结构命题（关注入则 n_DMC 仍 128）。XOR-fold 满 `Z_3` 不是定理、直方图 2:1 偏置是 T1 要测的量，不是 T0 淘汰点。送入 T1。
