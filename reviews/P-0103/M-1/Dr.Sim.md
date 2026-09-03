# Dr. Sim · T1 · P-0103/M-1 · MRFI

- reviewer: Dr. Sim
- 机制卡: mechanisms/P-0103/M-1.md
- T0: reviews/P-0103/M-1/tier0.md
- 日期: 2026-09-03

## 结论

有条件通过

## 五维打分（1–5）

| 维 | 分 | 一句理由 |
|---|---|---|
| 可行性 | 4 | 单边 Feistel + CRT 是纯函数；1R GOOD_MAP 冲突已点名，能建模。 |
| 新颖性 | 4 | 评估对象清楚：2-adic 宽位注入冻结的 Z_9，不是再做一次 `G mod N`。 |
| 预期收益 | 3 | ×3 占用是 384↔128 的算术；1.5MiB 只剩 6b 熵、ROM 对 trit 6:5:5、CRT 与装配 DMC 可能不是同一函数。 |
| 评估可信度 | 3 | 库内 mod 基线公平；S 平均、随机退役平均、1R 当无限端口，会把 3-adic 失败洗掉。 |
| 系统可组合性 | 4 | 100% good 可跳过 SRAM；不改资源个数。 |

## 最强反对意见

卡里并存两套 DMC 定义：`DMC=idx/48`（CRT 后再除）和 `DMC=(r' mod 3)+3·u`（用 Feistel 的 trit 装配）。`idx ≡ r' (mod 9)` **推不出** `⌊idx/48⌋ ≡ r' (mod 3)`。评估若只扫占用集合、不逐点核对两式，×3 可能写在错误的 DMC 定义上。

## 评估层必须验证的一个假设

对 `S∈{1536B,4608B,1.5MiB}` 的顺序 AP：**`idx/48` 与 `(r' mod 3)+3·⌊(idx/48)/3⌋` 逐点相同**；且 1.5MiB 的 n_DMC / min/mean **单独成列**，不得与 1536B 平均成「S=3·2^k 上回到 384」。

## 必须 cycle 级建模、不能解析近似

1. MOD9_PRE 按 6b CSA（或与全 `G mod 9` 位级一致）；`p_wide=A[24:9]`；4 路 4b XOR-fold；ROM16×4 按卡内直方图锁定（0..6 各 2、7/8 各 1）。
2. `r'=(r+F) mod 9`、CRT 逆元 2、`idx=p'+2048·((2·(r'−p' mod 9)) mod 9)`。打印 `idx/48` vs 装配 trit，禁止只实现其中一个。
3. GOOD_MAP 384×48 **共享 1R**：120 核争用排队。100% good 跳过 SRAM 与 partial-good 走 2 拍必须分列，延迟不得混用。
4. XOR 重试最多 2 次，`live5=p_wide[4:0]`，禁止 `+1` 扫描，禁止改 DMC。
5. 占用探针：n_DMC、n_bank、每 DMC trit 类流量（F mod 3 为 6:5:5，占用满 3 类仍可能偏载）。
6. 3-adic 步长必须分列、禁止平均：`S∈{512B,1KiB,1536B,3KiB,4608B,12KiB,1.5MiB,2MiB}`。
7. partial-good：**随机** 0/6/12% 与 **1/3 图案** 分表。1/3 图案下 XOR 重试再对齐坏 trit 是本卡自己标的中等置信来源，不得并进随机退役均值。
8. 基线实装：ModMapper%31、Mod192Mapper%192、Mod248Mapper%248、仅 2 幂均匀的 XOR mapper。后者是「2 幂已经均匀仍被因子 3 打死」的对照。
9. Warm-up：mapper 无状态，但 DRAM 仍丢 refresh/行缓冲前 10k；min/mean BW 用稳态。outstanding 128 按周期占槽，不许用占用 roofline 代替发行。
