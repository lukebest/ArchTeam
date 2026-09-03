# Tier 0 · P-0106/M-5 · RBAF

- 机制卡: mechanisms/P-0106/M-5.md
- 判决: PASS_T1
- 可行性: PASS
- 新颖性: DIFFERENT_APPROACH
- 质量: ISCA_WORTHY
- 进入 Tier 1: YES

## 轴一 可行性
- 因果性: 运行时 `slot=(α·g+β) mod n`、`bank=kth_one(M,slot)` 只看当前 `G` 与 repair 后 CSR/mask。α 搜索在 REPAIR+fence 固件（≤16 个候选），不是每请求神谕、不读未来 stride。config-time 重绑，合法。
- 完美预测/无限带宽/零延迟: 无预测。2 cycle 译码，不是 0。repair `<10k` cycle 可忽略。outstanding 128 覆盖。
- 关键边界（live-set 可逆、禁止跨 DMC 借 bank、3-adic、512B/4K）: 不跨 DMC。`α∈(Z/nZ)*` ⇒ 仿射双射，kth-one 再到活集，死命中 0，可逆。哈希域是退役后的 `Z_n`：对比「满好多项式仍 mod 48 + 跳死/stacking」（每 DMC ≤3 类再被 mask 砍）与「mod n 后类数 `n/gcd(S_g,n)`」。`3∤n` 时因子 3 从分母消失，必须按新因子分解算 gcd——这是题面「丢掉奇数因子会改变与 δ 的 gcd」。卡写明 `S=2^m` 时 `gcd(α·S_g,n)=gcd(S_g,n)`：互素 α 之间 gcd 相同，minimax 搜索在整数 AP 模型下是常函数。T1 必须打印 gcd 表，把收益记在「模数跟随 n_live」而不是「选了哪个单位 α」。禁止 `3|α` 在 `3|n` 时已被互素约束蕴含。粒 512B。clustered / 1/3 图案是评估风险不是 T0 淘汰。
- 硬件开销 vs 问题约束: 864B CSR + 2.25KB mask 1R + 6b 乘加，无 13.5KB LUT，不增端口，不改 384/18432。只改 interleave。信封内。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: DRAM sparing / 列修 fuse-map / CXL bank-row-cacheline sparing 是同 DPA 换备用颗粒，不改交织模数。Chipkill-Correct（Dell/IBM）在 ECC 层。OS page retirement / hwpoison 丢掉页，不在活 bank 上重绑可逆图。BIOS 写 DRAM scramble seed 不随 `n_live` 的因子分解走。Rau ISCA'91、Intel XOR decode、P-0105/AB2A 都是**满好** N 上的哈希/仿射。结构命题是「partial-good 的 N' 因子分解是交织参数的一等公民：repair 时把 (α,n) 绑到活集，否则 3-adic 类按 48 的 16×3 塌再被 mask 砍」。不是 EXACT_MATCH。偏置：相对 Chipkill/退役/valid-mask 是 DIFFERENT_APPROACH；译码器构件仍是教科书仿射+select，ISCA 论证靠 gcd×N' 交互而不是新门级对象。
- vs 本批其他卡: 译码器=M-2；多出的是强制按文档 stride 重算 α、CSR 布局、以及「有重绑 vs 仍 mod 48」对照。M-1 两段式压缩塌缩 r0，不能代表该命题。M-3 是 LUT 实现变体。M-4 闸门与本卡相反。跨批：P-0103 打满好 384 的因子 3（GOOD_MAP 是副作用 select-k，禁止再 mod 3）；P-0105/AB2A 满好互素仿射且坏 bank 不进系数。无 EXACT_MATCH。

## 判决理由
轴一通过：config-time 重绑、活集可逆、不跨 DMC、开销在信封内。新颖性不是选 α 的常值搜索，而是把哈希域从冻结的 48 改到随退役变化的 n_live，并给出可证伪的 gcd 表——这是 P-0106 点名的 3-adic×partial-good 交互，足够支撑顶会一节论证。非 EXACT_MATCH。偏置送 T1（不与 M-2 双开）。T1 必须按卡内算法填 CSR（禁止手工 α=1 冒充已重绑），并证明收益相对 M-1 两段式 / 相对仍 mod 48+跳死。
