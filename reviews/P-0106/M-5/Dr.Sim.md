# Dr. Sim · T1 · P-0106/M-5 · AffineRebind

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0106/M-5.md
- T0: reviews/P-0106/M-5/tier0.md
- 日期: 2026-09-03

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | repair 后仿射+kth-one 是纯函数；CSR 布局和选 α 算法写清了，能原样填表。 |
| 新颖性 | 3 | 可评估命题是「哈希域随 n_live 改」；minimax 选 α 在互素约束下对 gcd 是常函数。 |
| 预期收益 | 3 | 类数增益来自 mod 48→mod n，不是来自挑到了更好的 α。25% 均匀退役后 n=36 仍含 3，打不中题面。 |
| 评估可信度 | 3 | 要求 gcd 表和 3 残类偏退役是对的；XOR_fold6 的位源未指定，α 搜索容易被写成有效干预。 |
| 系统可组合性 | 4 | fence+drain 后写 CSR，不跨 DMC，无 core_id。 |

## 最强反对意见

`gcd(α,n)=1` ⇒ `gcd(α·S_g, n)=gcd(S_g, n)` 对任意 S_g 成立。文档 2 幂步长上，16 个候选 α 的 score 全相同。把 BW 增益记在「重绑算法选出了好 α」是给空操作发奖。真对照是 **模数 48 vs n_live**，α 两边都取 1。

## 评估层必须验证的一个假设

在 2 幂大步长上：`(mod n_live, α=1)` 与 `(mod n_live, 卡内 minimax α)` 的占用/BW 差 <5%；主增益出现在 `(mod 48 + 跳死)` vs `(mod n_live, α=1)`。并且：**均匀 25% 退役不得当作 3-adic 测试**（多数 DMC 的 n=36 仍被 3 整除）；3-adic 只认「按 3 残类偏退役」那一列。

## 必须 cycle 级建模、不能解析近似

1. 384×(α,β,n) CSR 864B，1R/核路径。仿真器 **按卡内算法** 填 α（候选集、`gcd(α,n)=1`、`score=max_S gcd(α·S_g,n)`）。禁止手工写 α=1 再贴「已重绑」标签——但报告里必须另有一列真 α=1 作为对照。
2. `slot=(α·g+β) mod n`，6b×6b 乘加 + 真 `mod n`（n 随 DMC 变，禁止仍 mod 48 再 mask）。
3. **XOR_fold6(G) 必须在模型里钉死位源**（卡未指定）。钉死之后冻结，禁止按结果改抽头。
4. kth-one 按 48 线前缀 popcount 选第 slot 个 live bit，1 cycle。禁止「随机挑一个活 bank」解析近似。图案 mask 下 kth-one 与 slot 的相位要对着看。
5. **gcd 表**（评估脚本，但是表必须来自同一 CSR）：每个退役率 × 每个文档 S × 每个 DMC，打印 `n, α, gcd, 类数=n/gcd`。这是解析可算的 sanity，**不能代替** cycle 级 BW。
6. 退役分布分列、禁止平均：均匀 6.25/12.5/25% **vs** 按 3 残类偏退役（刻意丢掉或保留因子 3）。均匀列验证死命中=0；3-adic 结论只许来自偏退役列。
7. 基线三路必须可运行：满好多项式 + mask 不重绑（α=1, mod 48, 跳死或 stacking）；mod n_live + α=1；全算法。缺中间那路就把模数更换和选 α 混成一笔。
8. 死命中 = 0 硬断言（任何退役率）。跨 DMC = 0。可逆：活集上对拍。
9. REPAIR 在 traffic 前完成（fence+drain）。run 中途改 CSR 必须重新 drain，否则 outstanding 打到旧 bank 图。
10. Warm-up + DRAM 时序 + 128 outstanding。类数 ×3 不是 BW ×3。
