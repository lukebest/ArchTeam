# T1 综合 · P-0106/M-5 AffineRebind

- 裁决：过线，进入 Tier 2 / #eval
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 3 | 4 | 4 | 4 | 4 |
| 新颖性 | 2 | 3 | 3 | 3 | 3 |
| 预期收益 | 3 | 4 | 3 | 3 | 3 |
| 评估可信度 | 2 | 4 | 3 | 3 | 3 |
| 系统可组合性 | 3 | 3 | 3 | 4 | 3 |

## 一致点

- 增益是模数从 48 改到 n，不是 α 搜索。`gcd(α,n)=1` ⇒ `gcd(α·S_g,n)=gcd(S_g,n)` 对任意文档 stride 成立，互素约束下 16 元 minimax 是常函数。四份都把「选了哪个 α」从合格项里拿掉。
- RUN 路径是 384 套 `(α,β,n)` CSR + 48b mask：`g=XOR_fold6(G) → (α·g+β) mod n → kth_one(M,slot)`；禁跨 DMC、禁 `core_id`，不改 384/18432。
- 满好 / 100% good 上相对不重绑增益必须 ≈0；收益记在「模数跟随 n」的 gcd 表。
- 评估必须走真实 XOR 折路径，不能用整数 AP 的 gcd 表冒充硅行为；H100 row remap 不是 per-DMC bank LUT 代理。

## 分歧点

- 新颖性：Archi 2（译码器=M-2；互素约束下 α 搜索是常函数，多出来的只是固件写 `n`）vs 其余 3（可评估命题是哈希域随 n_live 改）。
- 评估可信度：Archi 2（gcd 表建在整数 AP 上，硅上 `g` 是 XOR_fold6）vs Sys 4（gcd 表可打印、可证伪）。
- 预期收益：Sys 4（丢掉奇数因子后 gcd 变）vs 其余 3（作者自报 0.7～0.95 已咬穿 0.85；25% 均匀 n=36 仍含 3）。
- 系统可组合性：Sim 4（fence+drain 后写 CSR）vs 其余 3（上电/配置可组合，热 RAS 没有数据面）。

## 单一视角会漏的盲点

- Archi + Sim：`slot=(α·g+β) mod n` 的定义域是 XOR_fold6 的 6b（64 点），不是卡宣称的 `Z/nZ`。评估若打印整数 AP 的 gcd 表而不走 XOR_fold6 网表，就是在验证一个硅里不存在的代数。
- Sys：`(α,β,n)` 一改，该 DMC 上每一个 PA 的 bank 像都变；REPAIR `<10k` cycle 够 drain 发行口，不够搬 21MB。这是 boot/config 的 fuse-map 替换，不是 OS 运行中的 bank 退役。题面写「live set 是运行时集合」，系统接口只闭合了「上电前算一次」。
- Archi：簇退役把整 DMC 打到 `n=0` 仍进译码器——禁跨 DMC 借 bank ⇒ 该切片无处去；25% 簇退役 ≈96 个 DMC 全死，收益为零。
- Bench：H100 row remap 是坏行替换，不是 per-DMC bank LUT；库只给 n=40 一条规则，没有生产退役分布。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. RUN 网表钉死 `g=XOR_fold6(G)`；禁止用整数 `g` 的 AP 公式替代。失败：任一 degenerate 命中 `M=0` 的 bank，或每 DMC 类数相对 `n/gcd(S_g,n)` 偏差 ≥2，或 min/mean BW 跌出 0.85（Archi）。
2. 2 幂大步长上：`(mod n_live, α=1)` 与 `(mod n_live, 卡内 minimax α)` 的占用/BW 差 <5%；主增益出现在 `(mod 48 + 跳死)` vs `(mod n_live, α=1)`。均匀 25% 退役不得当作 3-adic 测试（Sim）。
3. REPAIR 窗口里存在非 CPU 代理时，fence+drain 之后死命中=0、且没有一条在 fence 前发出、在 CSR 提交后写回的请求；重绑前后同一批 PA 的 bank 变化比例预期 ~1（Sys）。
4. `team-interleave-microbench` 三组 mask 同表：LUT 满好、n=40 均匀、1/3 残类偏退役；满好上相对 M-2 增益 ≈0；禁止用 H100 row remap 当硅校准（Bench）。
