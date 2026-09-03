# Tier 0 · P-0106/M-3 · LLUT

- 机制卡: mechanisms/P-0106/M-3.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `slot=H(G) mod n_live`、`bank=L[dmc][slot]` 是当前地址与 repair 编程的 LUT 的纯函数。无运行时 FSM。LUT/`n_live` 只在 fence 后写。
- 完美预测/无限带宽/零延迟: 无预测。1 cycle `mod n` + 1R SRAM，共 1–2 cycle，不是 0。boot 填表 `384×n` 次写（25% 退役约 14k cycle）在配置态，不是每请求神谕。
- 关键边界（live-set 可逆、禁止跨 DMC 借 bank、3-adic、512B/4K）: 上游只选 DMC，LUT 不改 DMC，不跨 DMC 借 bank。编程约束 `L[0..n)` 为 `{0..47}` 无重复子集且不含死 bank ⇒ `Z_n→L_set` 双射；逆是离线 48×6 反表。哨兵 `6'h3F` 拦住越界 slot。升序填时 `bank=kth_one(M, H(G) mod n)`，与 M-2 α=1 重合（卡自证「kth-one 的固化」），不是 M-1 那种压缩上游 48 值 r0。打乱 L 只置换物理 bank 标签，AP 占用**类数**仍是 `n/gcd(step,n)`，不能单靠洗牌放大像。3-adic 未被忽略（模数是 n 不是 48），也没有新的 3-adic 对象。粒 512B。
- 硬件开销 vs 问题约束: 13.5KB LUT **1R1W**（addr=`{dmc,9b+6b}` / data 6b）+ 384×6b CSR。不 2R、不 CAM。相对「只 interleave 组合」多约 11KB SRAM，但仍是信封内允许的 LUT mapper（库已有 LUT 映射；P-0103 GOOD_MAP 18kb 同族）。约 `0.01mm²` @7nm 量级，不增 DMC/bank/die/端口。面积是相对 M-1 的主代价，不是越出冻结拓扑。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于 DRAM **列/行修复译码 LUT**（工厂 fuse-map、Horiguchi 冗余译码：逻辑列号 → 物理列，缺陷列不出现在表里）、cache set/way remap 表（DEFCAM remap match 寄存器；US6671822 缺陷 way 经 mux 改挂到 surrogate）。CXL bank sparing 是同 DPA 换备用颗粒，不是 48×6b 活列表。OS 页退役无此 LUT。升序填时与 rank-select 功能等价，卡自己写了「就是 kth-one 的固化」。
- vs 本批其他卡: 与 M-2 α=1 在升序填下功能等价；与 M-5 同一 `H mod n` 再译码，只是译码器用 SRAM 而非前缀树、且无 gcd 重绑策略。打乱 L 做 3-adic 规避是未规定的可选固件，置信低，不是可证伪的新代数。跨批：不是 P-0101 区分位抽取 / P-0102 滑动窗 / P-0103 Feistel-trit / P-0105 XOR-scheme 的主卡。无 EXACT_MATCH。

## 判决理由
轴一通过：每 DMC 48 项活列表局部可实现、1R、活集可逆、不跨 DMC。LUT 额外 SRAM 仍在只改 interleave 信封内。淘汰结构化原因：新颖性 FUNCTIONAL_EQUIVALENT（列修 LUT / 固化 kth-one），质量 INCREMENTAL。实现变体不进 T1。
