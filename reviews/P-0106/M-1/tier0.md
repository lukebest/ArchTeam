# Tier 0 · P-0106/M-1 · LPCC

- 机制卡: mechanisms/P-0106/M-1.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: INCREMENTAL
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: `(dmc,r0)` 来自当前地址的上游 mapper；`n=popcount(M_d)`、`r=r0 mod n`、`bank=kth_one(M_d,r)` 都是当前请求与 repair 时写好的 mask 的纯函数。无 stride 状态、不读未来请求。mask 只在 fence 后写。
- 完美预测/无限带宽/零延迟: 无预测器。译码 1R + 1 cycle 前缀树，共 1–2 cycle，不是 0。outstanding 128 盖住 mapper 延迟。未假设无限 DRAM 带宽。
- 关键边界（live-set 可逆、禁止跨 DMC 借 bank、3-adic、512B/4K）: DMC 由上游锁定，压缩只在该 DMC 的 48 槽内，不跨 DMC 借 bank。`ψ: Z_n→L_d` 经 kth-one 是双射，逆为 `rank=popcount(M[bank-1:0])`，活集可逆。死像只落在 `L_d`，死命中 0。两段式：`r0` 仍在上游的 48 值域名里算出，再 `r0 mod n`。若上游 AP 在 `Z_48` 上已塌成 `48/gcd(S_g,48)`（大 2 幂时 =3）个类，取模不能把类数放大到 `n/gcd(S_g,n)`——最多 3 个活槽。卡故意不重绑 α（留给 M-5），3-adic 交互没有被忽略成「仍打到死桶」，但也没有把哈希域改成 `Z_n`。不因此 FAIL：死命中 0、可逆、不跨 DMC 均成立；只是不是点名的 gcd 修复。粒 `G=addr>>9`。clustered 短板 DMC 可能 min/mean <0.85，卡已标诚实区间。
- 硬件开销 vs 问题约束: 384×48b=2.25KB mask **1R**（与 P-0103 GOOD_MAP / P-0105 位图同量级）+ 一份共享前缀树 `~0.5kGE`，不复制 384 份树、不增端口、不改 384/18432、不加 die。只改 interleave。在信封内。负对照「有 mask 无压缩」是 stacking。

## 轴二 新颖性
- vs 文献（引用具体论文/工作）: FUNCTIONAL_EQUIVALENT 于教科书 **rank/select 压缩禁用槽**：Jacobson 静态 rank；并行前缀 popcount 找第 k 个 1；cache 故障优雅降级（Pour *Performance of Graceful Degradation for Cache Faults*，ISVLSI 2007；DEFCAM 故障图；US6918071 way-select 关缺陷 way）。DRAM 列/行修（Horiguchi fuse-map）与 CXL bank/row sparing 是同 DPA 替换备用资源，不是 48→n popcount。OS page retirement / hwpoison 丢页不压活 bank。`r0 mod n` + kth-one 无新代数对象。
- vs 本批其他卡: M-2/M-5 把哈希直接做到 `Z_n`（不是压缩一个已塌的 48 值 r0）。M-3 升序 LUT 固化的是 `H(G) mod n` 的 kth-one，更近 M-2 而不是本卡两段式。M-4 只闸门。跨批：P-0103 GOOD_MAP+select-k、P-0105 2.25KB+48:6 PE 已是同一副作用；P-0101/M-1 预告「退役交给 per-DMC live mask」。无 EXACT_MATCH 主卡。

## 判决理由
轴一通过：因果合法、无神谕、活集可逆、不跨 DMC、开销在信封内。淘汰结构化原因：新颖性 FUNCTIONAL_EQUIVALENT（教科书 popcount/select），质量 INCREMENTAL。两段式不能修复上游在 48 上已塌的 3-adic 类，不是本问题的 gcd 对象。FUNCTIONAL_EQUIVALENT 不进 T1。
