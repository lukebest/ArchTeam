# T1 综合 · P-0103/M-1 MRFI

- 裁决：过线，进入 Tier 2 / #eval
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys 有条件通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 3 | 4 | 4 | 4 | 4 |
| 新颖性 | 3 | 4 | 4 | 4 | 4 |
| 预期收益 | 3 | 4 | 3 | 3 | 3 |
| 评估可信度 | 2 | 3 | 3 | 3 | 3 |
| 系统可组合性 | 3 | 3 | 3 | 4 | 3 |

## 一致点

- 2-adic 活熵注入冻结的 Z_9：四份都认单边 Feistel + CRT 是可接线对象，不是再做一次 `G mod N`，也不是纯 XOR。
- GOOD_MAP 是 384×48b、整机一份 1R：120 核满 outstanding 会把占用恢复吃回发行口；四份都把 1R 争用写成条件，不是「100% good 跳过 SRAM」可当整机故事。
- 含 3/9 的 stride 必须测；只跑 2 的幂会让 MRFI 相对 XOR mapper 看起来无增量。
- H100 10 MC、无 9 轴，不当 ×3 代理；禁止用 `hbm-stride-h100` 的 ×3 档代替 TEAM-SPEC 主评测。

## 分歧点

- 评估可信度：Archi 2（计划写 S=3·2^k 上 n_DMC 回 384，正文只敢保证 1.5MiB 时 t' 盖 3 类；`DMC_trit = r' mod 3` 口号与 `idx/48` RTL 互相矛盾）vs 其余 3。
- 1.5MiB：Archi 算 `idx=p+2048·s(r')` 最多 2×9=18 个桶，不是 384；Sim 要求该 S 的 n_DMC / min/mean **单独成列**，不得与 1536B 平均成「S=3·2^k 上回到 384」。
- 预期收益：Sys 4（F 拉满 Z_3 则 128→384 直接打掉 X_rel=3）vs 其余 3（1.5MiB 与 1/3 图案下收益是期望，不是 384 桶）。

## 单一视角会漏的盲点

- Archi + Sim：卡里并存两套 DMC 定义——`DMC=idx/48`（CRT 后再除）和 `DMC=(r' mod 3)+3·u`（用 Feistel 的 trit 装配）。`idx ≡ r' (mod 9)` 推不出 `⌊idx/48⌋ ≡ r' (mod 3)`。只听 Bench 的「含 3 的步长必须测」会漏掉评估扫错定义。
- Sys：mask 热更新是 RAS 事务，必须 fence+drain（含 DMA/ATS）；飞行中改写会让同一 PA 被两个核译到不同 bank，静默一致性错误。
- Bench：只跑 2 的幂（GF(2) 友好）会让整张卡看起来无增量；STREAM 天花板还能让坏映射过关。
- Archi：`(b ⊕ live5) mod 48` 在 {0..47} 上非单射；1/3 图案下二次重试仍可落在同一坏 trit，然后「停在 b2」是死 bank，不是 1.7e-3 的带宽毛刺。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. 逐点核对 `idx/48` 与 `(r' mod 3)+3·⌊(idx/48)/3⌋` 是否相同；禁止用 `G mod 384` 或 `r' mod 3` 代替装配 DMC（Archi / Sim）。
2. 1.5MiB 的 n_DMC / min/mean **单列**，不得与 1536B 平均成「S=3·2^k 上回到 384」（Sim）。
3. S=4608B（δ_G=9，r 冻结）、100% good、顺序 AP：n_DMC 杀线为 ≤ min(384,K)/3，或 min/mean < 0.85（Archi）。
4. GOOD_MAP 1R 在 120 核满 outstanding 下建模争用；mapper 等待不得把 n_DMC 恢复带来的 BW 吃回去（Sys）。
5. 随机 0/6/12% 与 **1/3 图案** 分表；主评测含因子 3/9 的 stride，并与「只跑 2 的幂」对照同表；H100 不当 ×3 代理（Bench / Sim）。
