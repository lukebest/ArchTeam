# Tier 0 · P-0106/M-2 · AKTH

- 机制卡: mechanisms/P-0106/M-2.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `g=XOR_fold6(G)`、`slot=(αg+β) mod n`、`bank=kth_one(M,slot)` 只依赖当前地址与 repair 后 CSR/mask。无运行时 FSM。`n/α/β` 只在 fence 后写。
- 完美预测/无限带宽/零延迟: 无预测。2 cycle 译码（乘余 1 + kth-one 1），不是 0。禁止 48-iter 探针上数据路径——迭代只离线对照，合法。outstanding 128 覆盖。
- 关键边界（live-set 可逆、禁止跨 DMC 借 bank、3-adic、512B/4K）: DMC 上游锁定，不因 dead 改 DMC。`gcd(α,n)=1` ⇒ 仿射是 `Z_n` 双射，再接 kth-one 仍双射到活集；逆 `g=α^{-1}(slot-β) mod n` 存在。死命中 0。哈希域是 `Z_n` 不是「先出 r0∈Z_48 再 % n」：大 2 幂占用类 `n/gcd(S_g,n)`（例 n=40 →5，n=36 →9），好于卡在 48 的 3 类。`gcd(α S_g,n)=gcd(S_g,n)`，互素 α 不额外放大类数。α 取列表中最小互素者，常为 α=1。禁止跨 DMC。粒 512B。
- 硬件开销 vs 问题约束: 2.25KB mask 1R + 864B `(α,β,n)` CSR + 6b×6b 乘余 `~0.3kGE` + 共享 kth-one 树。无 13.5KB LUT、无 48-iter、不增端口、不改 384/18432。只改 interleave。信封内。repair 选 α 在固件，不是每请求神谕。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: `Z_n` 互素仿射再映到不规则活集 = Budnik/Kuck 线性偏斜（IEEE TC 1971）、Harper/Jump skewed storage（IEEE TC 1987）、Knuth multiply-shift，再接 rank-select。Rau ISCA'91 是 GF(2) 多项式不是 `Z_n`。Chipkill / CXL sparing 不是 bank 图重绑。P-0105/AB2A 已是满好 `Z_48/Z_96` 互素 2D 仿射；本卡把模数换成 `n_live` 仍是同一构造。
- vs 本批其他卡: 译码器与 M-5 相同；M-5 用文档 stride 的 minimax gcd 选 α 并强制评估 gcd 表。相对 M-1：直接 `mod n`，能改 3-adic 类数，不是压缩塌缩的 r0。相对 M-3：组合 kth-one vs SRAM，升序 L 即 α=1 的本卡。无 EXACT_MATCH。跨批无主卡重复。

## 判决理由
轴一通过。淘汰结构化原因：与 M-5 同构 RUN 路径，α 策略更弱（最小互素，常为 1），质量 INCREMENTAL / FUNCTIONAL_EQUIVALENT（Rau/Knuth/偏斜家族）。3-adic 域切换的可评测版本在 M-5（gcd 表 + 禁止随便写 α=1）。不进第二张 T1。
