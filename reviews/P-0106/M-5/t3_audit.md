# T3 audit · P-0106/M-5 AffineRebind

auditor: 评估审计
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 退回

## 判决
占用对拍过线（本卡单独）：smoke 18 行 `flag_gt_30pct=0`，`rel_err_cls=rel_err_n_bank=0`，dead=0，真 α=1 列与卡内搜索并存且 rel-diff=0，XOR_fold6 网表未用 AP gcd 顶替。T3 BW 是 H-DRAM-BB 新度量并带 CI，未签 0.85、无 GB/s。但 **smoke 占用/t2_compare 只跑了 {512B, 2MiB}，缺 T2 钉死的含因子 3 的 Doc S（3×512B、9×512B）网表占用**；`gcd_table.csv` 虽列出这两档，那是 AP sanity，不能代替 XOR_fold6 netlist。规范：缺 mandatory Doc S ⇒ **退回 incomplete**，不是机制 淘汰（已跑行 occupancy 对 T2 无 miss；审计员另用同一 mapper 抽查 3×/9×512B 亦 rel_err=0，不计入交付 sweep）。不修代码。

## 对照 T2 占用
cls_mean / n_bank / dead / flag_gt_30pct; gcd table vs netlist; α identical

- Envelope: 120 core / 384 DMC / 18432 bank（`N_DMC=384`，`N_BANK_PER=48`，`Q_TOT=15360`）。SEED=20260903。
- 交付 smoke 占用（`I=min(K,Q_tot)`，确定性）：S∈{512B, 2MiB} × mask∈{full-good, n=40, 3-biased(n=32)} × {skip-dead, modn-a1, minimax} = 18 行。
- 2MiB 三 mask（与 T2 / 已提交 `results/t2_compare.csv` bit 一致，diff 空）：

| mask | skip-dead cls / n_bank | modn-α=1 cls / n_bank | minimax cls / n_bank | dead | rel_err |
|------|------------------------|-----------------------|----------------------|------|---------|
| full-good | 9.3333 / 3584 | 9.3333 / 3584 | 9.3333 / 3584 | 0 | 0 |
| n=40 | 9.3333 / 3584 | 10.6667 / 4096 | 10.6667 / 4096 | 0 | 0 |
| 3-biased(n=32) | 9.2500 / 3552 | 10.6667 / 4096 | 10.6667 / 4096 | 0 | 0 |

- 512B 同表：full-good 三列皆 9.3333/3584；n=40 skip 9.3333/3584 vs modn 10.6667/4096；3-biased skip 9.2500/3552 vs modn 10.6667/4096；dead=0；rel_err=0。
- `flag_gt_30pct` 全 False。主增益在 skip-dead vs mod n α=1（n=40, 2MiB cls 9.3333→10.6667，n_bank 3584→4096），不是挑 α。
- α：`alpha_search(n)` 对 n∈{32,36,40,42,45,48} 全为 1；minimax α=1；真 `modn-a1` 列 α=1；cls rel-diff = 0.0000 < 5%。未把手工 α=1 标成「已重绑」。
- gcd 表 vs 网表：n=40 S=2MiB `classes_AP=n/gcd(S_g,n)=5`，netlist `cls_mean=10.6667`。两列并打；占用走 `XOR_fold6`+kth-one，**未用 AP 表替换网表**。3-biased 2MiB `classes_AP=1` vs netlist 10.6667，同样合法分列。
- 满好增益 vs no-rebind：n_bank skip=minimax=3584，gain=0。
- 均匀 25%（n=36）smoke 占用未跑（spec 标 optional）；测试断言 `36%3==0`、非 3-adic。3-adic 只来自 3-biased 列。
- **缺档（退回理由）：** occupancy / t2_compare **无 3×512B、无 9×512B**（亦无 512KiB/1MiB）。`sweep.py --mode smoke` 写死 `strides=[AFFINE_DOC[0], AFFINE_DOC[-1]]`。night 模式代码含全 Doc S，但未作为本次交付/重跑产物。

审计员额外抽查（不写入 results/、不改变判决口径）：3×512B / 9×512B 对 T2 `rel_err=0`、dead=0、flag=0。故不是占用 miss→淘汰。

## T3 BW（H-DRAM-BB 新度量，非 T2 差）
bbox; CI; class×3 not BW×3; full-good gain

- 假设 H-DRAM-BB；decode_lat=2，csr_ports=1，β=0，open-page；cycle `|I|=256`（smoke reduced bbox，已标注）；warmup 10%；trials n=3，SEED+i。
- 每格 `mean ± 95% CI`。确定性 → 半宽 0。无 GB/s。μ_d UNKNOWN。**0.85 是问题合格线，不是测得均值；reduced-bbox 不能签全 envelope 0.85。**
- 2MiB n=40：skip-dead `0.477178 ± 0.000000 (n=3)`；modn-a1 / minimax `0.500000 ± 0.000000 (n=3)`。
- 2MiB full-good 三策略皆 `0.477178 ± 0.000000 (n=3)`（gain vs no-rebind ≈0）。
- 2MiB 3-biased：skip `0.477178`；modn-a1/minimax `0.500000`。
- 512B 全部 smoke 格 `0.500000 ± 0.000000 (n=3)`。
- 2-cycle decode × 1 CSR 口把吞吐钉在 0.5 txn/cyc。类数增益 ×1.14（10.6667/9.3333）**不是** BW ×3（0.500/0.477≈×1.05，且贴天花板）。cycle 格 `cls_mean` 在 |I|=256 时塌到 ~1.0–1.33，与全量占用不可混比。
- cycle `dead=0`，`repair_done=True`。cycle S 同样只有 512B/2MiB（night 过滤名单含 3x512B，但 smoke strides 没有它）。

## spec/sim 一致
XOR_fold6 / kth-one / REPAIR-before-RUN / no silent G%384

- H-FOLD6 PIN：`g[i]=XOR G[i+6k]`（`i+6k≤55`），与 T2 `model.py` 对拍；`xor_fold6(0x123456789ABCDEF)=61`；测试 `test_xor_fold6_pin_matches_t2` 过。抽头未改。
- H-UP-DMC 声明：9b XOR-fold 后 `x if x<384 else x-384`，不是静默 `G%384`。
- `slot=(α·g+β) mod n` 真变模；kth-one 48 线前缀第 slot 个 live bit，非随机挑 bank。
- CSR：minimax 走卡内候选 `{1,5,…,47}` + `gcd(α,n)=1` + `score=max_S gcd(α·S_g,n)`；另列真 α=1（`modn-a1`）。
- REPAIR：`run_cycles` 先 `csr.repair` 再发流量；fence+drain 按注释假定（无中途改 CSR）。warmup + DRAM bbox 在驱动里。
- 三 mapper：skip-dead / modn-a1 / minimax 在 smoke；`stack` 已实现、smoke 未跑（T2 亦未跑 stacking，T1 允许跳死）。无跨 DMC。n=0 毒化该 DMC（`bank<0`）。
- 掩码分列：full-good / n=40 uniform / 3-biased。生产像对照 n=40。

## 代码（亲自重跑）
- pytest: `cd /workspace/archteam-audit && .venv/bin/python -m pytest sims/P-0106/M-5/tests -q`
  - rc=0；17 passed；~0.93s；log `runs/t3-P-0106-M-5-pytest.log`
- smoke: `.venv/bin/python sims/P-0106/M-5/sweep.py --mode smoke --seed 20260903 --n-trials 3 --out runs/t3-aff-smoke`
  - rc=0；~4.47s（15:36 Asia/Shanghai）；log `runs/t3-P-0106-M-5-smoke.log`
  - `t2_compare.csv` / `occupancy.csv` / `bw_ci.csv` / `gcd_table.csv` / `cycles.csv` 相对已提交 `sims/P-0106/M-5/results/` **diff 空**。未覆盖 committed `results/`。
- 未改 sim.py / sweep.py / tests / results / spec.md / model.py / 机制卡。

## 修复清单
1. **必须**：把 T2 Doc S 含因子 3 的 **3×512B 与 9×512B** 纳入占用+`t2_compare` 网表列（smoke 扩 strides，或提交 `--mode night` 占用产物）。gcd 表不算覆盖。
2. 建议：cycle BW 同步带上 3×512B（仍标 bbox/CI；不得用类数×3 当 BW×3；不得从 256 点签 0.85）。
3. 不要用 AP `n/gcd` 顶替 XOR_fold6；不要把 α=1 标成 rebound；不要改抽头。审计员不代修。

## 禁止自检
未改 sim/spec/机制卡; 未与 SNS 混结论
