# T1 综合 · P-0103/M-5 B3CSH

- 裁决：过线，进入 Tier 2 / #eval
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）。Archi 可行性 2、评估可信度 1，但结论仍是有条件通过，按规则计过线票。

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 2 | 4 | 4 | 4 | 4 |
| 新颖性 | 3 | 4 | 4 | 4 | 4 |
| 预期收益 | 2 | 4 | 3 | 3 | 3 |
| 评估可信度 | 1 | 3 | 3 | 4 | 3 |
| 系统可组合性 | 2 | 2 | 3 | 3 | 2.5 |

## 一致点

- 切口是 3b 切块 + Z_3 CSA，不算 `G mod 9`，和 M-1/M-4 不是同一代数对象；无 `core_id`、只改 interleave。
- 点名 δ 上至少一块 3b 满跑是库内必生成项；翻转计数 C0..C7 必须打印，不能用类比过关。
- 真正进 DMC 的奇数位是卡写的 `dmc_odd=(d0+d1+d2) mod 3`，不是 CSA 重量 1 的 `d0`。四份都要求评估按装配式抄，禁止用 d0 冒充。
- GOOD / select-k 是共享一份；`k mod N_good` 之后禁止再 mod 3。H100 10 MC 不能复现 9 轴塌缩。

## 分歧点

- 可行性 / 评估可信度：Archi 2 / 1（写成的 DMC 装配在 2MiB 丢一半控制器；「d0 满则和满」「min/mean 0.9–1.0」与装配式矛盾）vs Sys/Bench 可行性 4、Sim 评估可信度 4。低分不改「有条件通过」。
- 预期收益：Sys 4（单活块 ⇒ d0 满 Z_3 是组合事实）vs Archi 2（点名 δ 上 min/mean ~0.19–0.43，2MiB 直接 192）。
- 系统可组合性：Archi/Sys 2（1R×1 喂不了 120 核；select-k 改 mask 重排该 DMC 全部行）vs Bench/Sim 3。

## 单一视角会漏的盲点

- Archi + Sim：`Σ trit = d0+3·d1+9·d2`，故 `Σ mod 3 = d0`；卡却用 `dmc_odd=(d0+d1+d2) mod 3`，进位 digit 被折回 Z_3。只听 Sys 的「单活块 ⇒ d0 满」会漏掉装配式把树重新对齐到 `G mod 3`。
- Archi：`p_mix[0]=G[10]⊕G[11]` 在 S=2MiB（G[11:0] 冻）双端死亡，2-adic 7b 秩从 7 掉到 6，n_DMC=192。
- Sys：select-k 在 N_good 一变时重排该 DMC **全部**行，不是局部跳死槽；在线 RAS 若不清空/迁移整个 DMC，写回与 DMA 会把脏数据打到新 bank。
- Sim / Bench：只报 n_DMC、不报 `corr(dmc_odd, G mod 3)` / Cramér-V，切块树可能仍在输出与 3-adic 赋值同构的东西；随机 gather 会掩盖相位/stride 折叠。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. 按 §2.2 抄 `dmc_odd=(d0+d1+d2) mod 3`，禁止用 d0 冒充；S∈{1536B,4608B,12KiB,1.5MiB,2MiB} 任一 S 上 n_DMC < 384，或 2MiB 上 `|{p_mix[0]}|=1`，则声明作废（Archi）。
2. δ=9（S=4608B）：C0、C1 翻转计数符合点名，且 Cramér-V(`dmc_odd`, `G mod 3`) < 0.3；同一 trace 上 `G mod 3` 当 DMC trit 的 mapper n_DMC≈128。相关若 ≥0.8，评估层失败（Sim）。
3. 退役 1 个 bank（N_good: 48→47）后，该 DMC 上已经驻留的地址里 bank 变化比例是 ~1（全洗牌）还是 ~1/48（仅死槽）；按这个运维模型报，不能混称「运行时 live-set」（Sys）。
4. 每个 S 打印 C0..C7 翻转计数，并加随机 gather；主评测 `team-interleave-microbench`；H100 不当 ×3 代理（Bench）。
