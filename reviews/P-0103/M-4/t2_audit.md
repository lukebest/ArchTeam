# T2 audit · P-0103/M-4 CR-MRDR

auditor: 评估审计
batch: B
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 淘汰

## 判决

**淘汰。** Batch B 单独收口，未读、未引 Batch A 任何模型输出，不写联合结论。

亲自重跑 `python3 models/P-0103/M-4/model.py`（exit 0，~58s，log 见下）。消融臂按 AP **计出** 1.5MiB `n_DMC=6`、2MiB `n_DMC=3`（assert 通过），后续占用数字因此有效。现电路 + TRIT_INJ 开，两杀手分列均 `|q[6:0]|=128` 且 `n_DMC=384`。主列 `die=(DMC>>8)&1` 未改成 `/192`；对照列存在且未替换主列。高抽头 **G[23] 不是 G[21]**。W=4GiB（G[23] 冻）两杀手 `|q|` 仍 128。S 分列未平均。无 H100、无绝对 GB/s、无对硅 ±15%。stdlib、确定 AP、无 RNG 种子。

淘汰触发是 **T1 杀线 3 被实跑打穿**，不是伪影 bug、不是消融没打回：

- TRIT_INJ **关**：1.5MiB `|q|=128` 但 **`n_DMC=384`（须 ≈128）**。模型自己打出 `VOID: trit-off still 384; trit is stealing 6→384`。Sim T1 / spec §4：关注入仍到 384 ⇒ trit 在偷占 6→384。诚实错过 T1 杀线 ⇒ 淘汰。
- 同臂 2MiB trit_off `|q|=128`、`n_DMC=320`（既非 ≈128 也非 384）。`t0` 在杀手步长上行走（含 G[10],G[13],G[16],G[19]），H0 不是唯一 ×3；2MiB 上 TRIT_INJ 只补 320→384。

装箱按字实现后 **PACK_FAIL**（HA≥96；uniq8=256:128≠192:192；发行比≈2.0≥1.5）。`n_DMC=384` **不得记 BW 成功** 已触发。此条是接线后果，模型没有默默改成 `/192`，不单独构成伪影退回；主结果本就只许相对占用。占用 6→384 / 3→384 在 current 臂上数字成立，但 trit_off 已证明 ×3 不是 TRIT_INJ 的功劳，MAGIC-GAP 的「trit 不得被写成 6→384」被实跑打穿。

不是退回：消融 6/3 是走出来的，die 主列正确，对照列正确，无魔数 GB/s，无挂死。伪影可修的清单不适用。

## 收益阈值

- 消融 d[i]=G[i] 1.5MiB n_DMC=**6** (须=6) / 2MiB n_DMC=**3** (须=3) — **打回，assert OK。** 6 与 3 由 AP 计数产生，不是当已测收益写进输入。
- 主条件 die=DMC[8] 发行比 die0:die1=**1.5MiB 3644:1818 ratio=2.004**（uniq8=256:128）；**2MiB 2728:1368 ratio=1.994**（uniq8=256:128）。装箱 HA≥96?**是**（1.5MiB current HA≥96:**914**；2MiB:**680**）。uniq8≠192:192 → **PACK_FAIL**。对照 /192 发行比=**1.5MiB 2730:2732 uniq_env=192:192**；**2MiB 2048:2048 uniq_env=192:192**。对照未替换主列。
- current 1.5MiB |q|=**128** n_DMC=**384**；2MiB |q|=**128** n_DMC=**384**（分列，未平均）
- trit_off 1.5MiB n_DMC=**384**（杀线失败）；2MiB n_DMC=**320**（≠≈128）
- W=4GiB |q| 1.5MiB/2MiB=**128 / 128**（n_DMC 亦 384/384；G[23] 冻后组索引仍满）
- die 比≥1.5 时 n_DMC=384 不得记 BW 成功: **触发**（两杀手 current 均标注 `n_DMC=384 NOT BW success (die ratio≥1.5)`）
- 阈值判定: 相对占用 current 两杀手满 384，消融 6/3 闭合；**0.85 是 min/mean BW 合格线，本脚本未发射 BW，未把 0.85 当均值、未对 S 平均**。`{2,1,1}` 组合 min/mean=**0.7500** 与 BW 0.85 分列。占用比 384/6、384/3、384/128 **不是测得 BW**。因 trit_off 1.5MiB 仍 384，杀线 3 失败 → **收益叙事（TRIT_INJ 提供 ×3）作废**，occupancy CLAIM 不得把 trit 写成 6→384 的原因。主结果停在占用；BW 成功本已因 die 比≥1.5 不得记。

## 魔法缺口

CLAIM（占用，非 BW）：1.5MiB 6→384（×64）；2MiB 3→384（×128）。

实跑 current：两行都到 384，消融 6 与 3 闭合，故 **占用数字 6→384 / 3→384 在 LIVE_DIGIT 开时成立**。

trit 是否偷占 6→384：**是（1.5MiB）**。trit_off 与 current 同为 n_DMC=384，×3 来自 `t0` 行走而非 TRIT_INJ/H0。6→384 拆掉的是组索引 2→128（LIVE_DIGIT），因子 3 在关注入时已经满。卡文「H0 吃满再乘 trit」在 1.5MiB 上被 AP 证伪。2MiB trit_off=320，TRIT_INJ 只解释 320→384，仍不是 3→384 的主因。不得把占用比写成测得 BW。

## spec

对照 `models/P-0103/M-4/spec.md` 与卡 `mechanisms/P-0103/M-4.md`（G[23] 现稿）：

- 信封 2×Die2、120×128=15360、384 DMC / 18432 bank、512B、W=8GiB：与 YAML 一致。
- 接线：`d[i]=G[i]⊕G[i+11]⊕G[23]`，`q[j]=d[10-j]`，`DMC=t0'+3·q[6:0]`，`die=DMC[8]` 主列，`die_env=DMC/192` 只对照。HIGH_TAP=23，MID_TAP 永不撞 23。
- 三臂同一 `map_address` 开关，不是另写旧卡。消融 `live_digit=False, trit_inj=True`。
- 主结果相对占用；绝对 BW 为 μ_d 假设列且未打印。禁止 H100、禁止 ±15% 硅。
- 未证严保留：GF(2) 秩不代替 `|q|`；H 折叠非 Z_3 同态；`{2,1,1}`⇒min/mean=3/4 只作组合上界。
- spec 把消融 6/3 与 die=DMC[8] 写成 CONSTRAINT。模型 assert 6/3；die 按字切 256+128 并打印 PACK_FAIL。符合「禁止默默修正」。
- trit_off「须停在 ≈128」是杀线；实跑 1.5MiB=384，spec 自己也写了 t0 在杀手上行走、只许计数不许默认 128——计数结果打穿了 CLAIM。

## 代码（亲自重跑）

- 命令：`python3 /workspace/archteam-audit/models/P-0103/M-4/model.py`
- 退出码：**0**
- 墙钟：约 58s（未挂死；>5min 无输出才杀）
- log：`/workspace/archteam-audit/runs/P-0103-M-4.log`（stdout+stderr 全量）
- 与 spec 一致：`die_bit8 = (dmc >> 8) & 1` 为主列；`die_env = dmc // 192` 只对照；ablation assert 6 与 3；无 H100；无绝对 GB/s；无用 `//192` 替换主列。
- 无魔数带宽；Little 驻留为 15360/n_DMC（384→40；消融 6→2560；3→5120；trit_off 2MiB 320→48）。
- 种子：无 RNG。stdlib only（`statistics`, `sys`）。确定顺序 AP `G=0, G+=δ, G<W/512`。
- grep：`HIGH_TAP = 23`；`DIE_BIT = 8`；`assert a15 == 6` / `a2 == 3`；注释与收尾均声明 die 未改成 /192。

关键 log 行（原文）：

```
1.5MiB   current   |q|=128  n_DMC=384  die8 3644:1818    ratio=2.004 uniq8=256:128  die_env 2730:2732    uniq_env=192:192  ... HA≥96:914 PACK_FAIL ... n_DMC=384 NOT BW success (die ratio≥1.5)
1.5MiB   trit_off  |q|=128  n_DMC=384  ... VOID: trit-off reached 384 (trit stealing 6→384)
1.5MiB   ablation  |q|=2    n_DMC=6
2MiB     current   |q|=128  n_DMC=384  die8 2728:1368    ratio=1.994 uniq8=256:128  die_env 2048:2048    uniq_env=192:192  ... HA≥96:680 PACK_FAIL
2MiB     trit_off  |q|=128  n_DMC=320  ... trit-off: |q|=128 but n_DMC=320 not ≈128
2MiB     ablation  |q|=1    n_DMC=3
ASSERT OK: ablation d[i]=G[i] → n_DMC=6 at 1.5MiB, n_DMC=3 at 2MiB
1.5MiB   W=4GiB |q|=128 n_DMC=384  W=8GiB |q|=128 n_DMC=384
2MiB     W=4GiB |q|=128 n_DMC=384  W=8GiB |q|=128 n_DMC=384
         VOID: trit-off still 384; trit is stealing 6→384
```

corr(q[i], G[23])：1.5MiB 上 q[0]=+0.0004、其余 0.0000；2MiB 全 0.0000。两两 Pearson 对角 1、非对角 ~0。未用 GF(2) 秩代替 `|q|`。4608B 单独一行并注明 `G mod 9` 冻 ≠ XOR 数位冻（该行仍 `|q|=128` n_DMC=384）。

## 准则

- 主结果 = 相对占用。通过对硅 ±15%。无 H100。无写死 GB/s。
- 0.85 = min/mean BW **合格线**，不是均值，未对 S 平均。占用 min/mean（组合 0.75）与 BW 0.85 分列。
- n_DMC=384 且 die 比≥1.5 **不得记 BW 成功**：已触发。
- 384/6、384/3、384/128 只作占用比，不是测得 BW。
- 诚实错过 T1 杀线 ⇒ **淘汰**（本卡：trit_off 1.5MiB=384）。伪影 bug 才退回；本轮不是伪影。
- 未改 spec.md / model.py / README.md / 机制卡。未与 Batch A 混结论。6 与 3 不当已测收益写入周报——它们是消融约束的实跑回打。

## 修复清单

不适用（淘汰，非 round-1 退回）。下列是杀线证据，不是「改脚本就能过」的伪影：

1. trit_off 必须在 1.5MiB 与 2MiB 分列停在 `n_DMC≈128`。现 384 与 320。根因是 TRIT_SRC 的 `t0` 在杀手 AP 上已满扫 Z_3，TRIT_INJ 不是 ×3 的来源。改卡才能动这条，不是修 log。
2. 若仍主张 6→384 是 LIVE_DIGIT 而非 trit：叙事要改，且不得再把 TRIT_INJ 写成杀手步长满 384 的必要臂。T1 杀线 3 按现文仍失败。
3. `die=DMC[8]` 装箱失败（256+128、HA≥96）是按字实现的已知后果；禁止改成 `/192` 冒充过线。本模型已正确暴露 PACK_FAIL 与「384 非 BW 成功」。改接线才可能装箱，那是另一张卡。

## 禁止自检

未改 spec/model/机制卡；未与 Batch A 混结论；6 与 3 不当已测数字写入周报。Batch B 单独判决。
