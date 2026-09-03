# T1 综合 · P-0105/M-4 SNS

- 裁决：过线，进入 Tier 2 / #eval
- 规则：有条件通过计过线票；致命缺陷一票否决
- 票：Dr. Archi 有条件通过 · Prof. Sys 通过 · Prof. Bench 有条件通过 · Dr. Sim 有条件通过（4/4，无致命缺陷）
- 主持不另打分；下表只汇总四份已提交分数（中位数）

## 五维汇总

| 维 | Archi | Sys | Bench | Sim | 中位 |
|---|---|---|---|---|---|
| 可行性 | 3 | 4 | 4 | 4 | 4 |
| 新颖性 | 4 | 4 | 4 | 4 | 4 |
| 预期收益 | 3 | 4 | 3 | 3 | 3 |
| 评估可信度 | 3 | 3 | 3 | 2 | 3 |
| 系统可组合性 | 3 | 4 | 3 | 3 | 3 |

## 一致点

- 剪切 `x'=(x+7y) mod 2^12` + 256×8 整数环 S-box + fold384，无 `core_id`、请求路径无 4096 项相位表；S=2MiB 上 raw 对 4096 相位是双射、n_DMC 恒 384 可以作为基数。
- 合格是跨 base 不变 + 分轴满射，不是平均 BW、不是 2MiB 打满 18432。
- 卡内 CV≈0.044 / maxload=11/10 不得当已测黄金结果；T2 必须重测。
- 主评测必须扫 base 相位；消融（去剪切 / 去 S-box）可组合；H100 校准不能代替 384 桶。

## 分歧点

- 票型：Sys 通过 vs 其余有条件通过。Sys 认相位不变是系统收益、和现有 PA/DMA 对齐；其余把 bank 窗、fold 下界、huge-page 对齐写成条件。
- 评估可信度：Sim 2（§3 把 fold384 的覆盖下界写成了本卡 discrepancy）vs 其余 3。
- 预期收益：Sys 4（直接打 ASLR / 不同 malloc base）vs 其余 3（好相位 / STREAM 上增量小；剪切会打散行缓冲，min/mean 比变好可以伴随绝对 BW 变差）。
- 系统可组合性：Sys 4 vs 其余 3（页着色、huge-page 对齐、6-bank 窗不在 Sys 的通过理由里）。

## 单一视角会漏的盲点

- Sim：`raw ∈ [0,4095]`、`4096=10×384+256`：若 raw 均匀，256 个 DMC 得 11 hit、128 个得 10 hit。这是 fold384 的覆盖下界，与 S-box 无关；§3 把这组数写成机制效果。T2 若对着这组数校准模型，评估从第一天就被做假。
- Archi：`bank_in = x'[9:4] mod 48` 在 S=2MiB 把 48 轴塌成 6；每 DMC 精确占用 6 个 bank，锁在单一 `bank%8` 类。占用控制器个数不变，占用哪些 bank 全换。
- Sys：Linux/NUMA 页着色与本卡剪切+S-box 打散的位可能重叠也可能对抗；实验室「扫 base、相对差→0」在 buddy+ASLR+着色同时打开时可能复现不了。
- Bench：生产 huge page 把 base 钉在 2MiB 对齐；若钉住的是 1D 好相位，SNS 的跨 base 故事对生产为 0。STREAM 天花板同样能藏坏相位。

## 必须带进 T2 的条件（摘自四份，不改写结论）

1. ROM 锁定为 `S(u)=u^5+u^3+u (mod 256)`（前 16 项校验）；S=2MiB 扫页内 base **和** 2MiB 对齐，n_DMC=384 且占用跨 base 相对差 <5%；只赢 min/mean 比、输绝对 BW，记失败（Sim）。
2. 每 DMC 占用 bank 数、占用 `bank%8` 种类数、带 tRRD_L/tCCD_L/tFAW 的 cycle 级 DRAM：任一 base 使任 DMC 占用 bank≤6 且该相位 min/mean BW<0.85，则失败（Archi）。
3. 真实 4K 分配器（buddy + ASLR，再加一档页着色）下，固定 S=2MiB，跨进程起始地址的 min/mean BW 相对差仍 <5%、n_DMC 变化 <10%（Sys）。
4. `team-interleave-microbench` 的 base 扫描拆两套：库默认 512B 粒度相位，以及仅 2MiB 对齐；禁止 decode；H100 不当 384 桶代理（Bench）。
