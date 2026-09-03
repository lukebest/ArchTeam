# T2 audit · P-0101/M-3 层次正交放置

auditor: 评估审计
batch: A
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 淘汰

## 判决
诚实重跑 exit 0，spec/代码对齐、无魔数、无硅数字、9vs384 未当加速比。S=2MiB SK=0 八个随机 base：n_DMC=384、die 访次 2560:1536（5:3 接线）、max_HA=0.0078、n_HA_hog=0、bank%=0.1667≤K/N=0.2222。但 T1 kill-line 1 明确：S=512B 顺序流 unique DMC 不得塌到 ≪128（Archi 失败值=1）。issued 窗 |I|=15360 上 M-3 n_DMC=1。这是机制高位 Stage A 的阈值失败，不是代码/spec bug → 淘汰。

## 收益阈值
- 合格线: min/mean 0.85（CONSTRAINT，不是均值）；主结果=相对占用
- 重跑关键数（引自 runs 日志，勿编造）: SEED=20260903；S=512B M-3 n_DMC=1、X_rel=384、min/mean=1.0000、n_HA=1；S=512KiB n_DMC=360 min/mean=0.7500；S=1MiB n_DMC=384 min/mean=0.7500；S=2MiB n_DMC=384、n_bank=3072、min/mean=0.7500、die0/die1=2560/1536、bank%=0.166667≤K/N=0.222222；B-modN n_DMC=9（ratio 384/9=42.67，日志标明非测得加速比）；8 bases 全 n_DMC=384、HA hog 合计 0
- T1 kill-line 逐条:
  1. S=512B unique DMC 不得 ≪128（失败值 1）: FAIL n_DMC=1
  2. SK=0 S=2MiB ≥8 base 无 HA 份额 >1.5×(2/384)=0.007812: PASS max_HA=0.0078、n_HA_hog=0
  3. 主评测 team-interleave-microbench；禁 decode-* / H100 代理: PASS
  4. 四层 issued 探针；bank%≤K/N；9vs384 非加速比: PASS
- 阈值判定: 低于阈值（S=512B 塌成 1 DMC）

## 魔法缺口
| CLAIM | 模型可解释 | 缺口 |
| DMC occ 0.95–1.00 @2MiB | n_DMC=384（占用 1.0）；min/mean=0.75 来自 ENC3 2:1:1 | 占用满射成立，均衡不是 0.95 |
| bank 0.18–0.222 | bank%=0.1667≤0.2222 鸽笼 | 小，在上界内 |
| BW ×20–×42 vs mod-N | 384/9=42.67 占用比，日志标非加速比 | CLAIM 未当测得 BW |
- 缺口过大?: 否 + CLAIM 已分列；淘汰因 512B 杀线，非把 CLAIM 当输入

## spec
- 变量/公式来源/无膻造: PASS
- 问题: 无。H-B4 / H-ENC9 / H-MU-D 已标假设。§8 已写明 512B issued 窗「typically 1」，与 kill-line 1 冲突是机制问题不是漏公式。

## 代码（亲自重跑）
- 命令: python3 models/P-0101/M-3/model.py
- 退出码 / 耗时 / log: 0 / ~0.16s / runs/P-0101-M-3.log
- 与 spec 一致 / 无魔数 / 基线 / 种子 / 灵敏度: PASS
- 问题: 无（不修）。Stage A/B、ENC3、SK=0、B-modN/B-M1/B-low、SEED=20260903、S×8 base 均到位。未印 H100/GB/s/353。

## 准则
- 第一性原理 / CLAIM 与占用分列 / 未填硅: PASS

## 修复清单
淘汰原因：S=512B issued unique DMC=1（Archi 失败值），机制 Stage A 绑 addr[32:24]，Q_tot 窗 7.5MiB 不跨 16MiB 时高位冻结。不修代码。

## 禁止自检
未改 spec/model/机制卡；未与他卡混排名；未把未签字数字当周报。
