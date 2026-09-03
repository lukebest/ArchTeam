# T2 audit · P-0103/M-1 MRFI

auditor: 评估审计
batch: A
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 淘汰

## 判决
诚实重跑 exit 0，CRT/ROM/XOR 重试按卡接线，1.5MiB 单列、3/9 与 2 幂同表、partial-good 分表、无 +1、无 H100。S=4608B 100% good：n_DMC=384（过 n_DMC 杀线 min(384,K)/3=128）但 min/mean=0.7500<0.85，日志 kill_mm=True。DMC_div 与 DMC_asm 逐点不等（4608B mismatch=10270/15360）。1.5MiB n_DMC=18 非 384。阈值失败 → 淘汰。

## 收益阈值
- 合格线: min/mean 0.85（CONSTRAINT，不是均值）；主结果=相对占用
- 重跑关键数（引自 runs 日志，勿编造）: SEED=20260903；MRFI 100% good：512B n_DMC=384 min/mean=0.9000 mismatch=10243；1536B n_DMC=384 min/mean=0.6500 mismatch=10239；4608B n_DMC=384 min/mean=0.7500 mismatch=10270；12KiB n_DMC=384 min/mean=0.8250；1.5MiB n_DMC=18 min/mean=0.9260 mismatch=3641；2MiB n_DMC=9 min/mean=0.9976；B-%192 在 3-adic 上 n_DMC=64/32/64/8/1；partial-good 4608B dead_hits=0
- T1 kill-line 逐条:
  1. 逐点 DMC_div==DMC_asm；禁 G%384 / r'%3 替代: FAIL 各 S mismatch 过半（512B 10243 … 4608B 10270）；占用走 DMC_div 未偷换 G%384
  2. 1.5MiB 单列不得与 1536B 平均: PASS 分列（18 vs 384）
  3. S=4608B：n_DMC≤128 或 min/mean<0.85 则杀: FAIL min/mean=0.7500（kill_n_DMC=False, kill_mm=True）
  4. XOR 重试≤2 禁 +1；GOOD_MAP 1R 点名: PASS（+1 未实现；争用只命名未计时）
  5. 随机 0/6/12% 与 1/3 分表；3/9 与 2 幂同表: PASS
- 阈值判定: 低于阈值

## 魔法缺口
| CLAIM | 模型可解释 | 缺口 |
| 3·2^k 上 n_DMC 128→384 | 1536B/3KiB/4608B/12KiB 的 DMC_div=384；1.5MiB=18 | 1.5MiB 未覆盖；装配 DMC 与 idx/48 不一致 |
| min/mean 0.9–1.0 | 4608B=0.75；1536B=0.65 | ROM/装配偏置，低于 0.85 |
- 缺口过大?: 否（CLAIM 未当输入/未当测得 BW）+ 淘汰因 kill-line 数字，非魔法输入

## spec
- 变量/公式来源/无膻造: PASS
- 问题: 卡内两套 DMC 定义并存是机制缺陷，spec 已要求逐点打印；无膻造关系。

## 代码（亲自重跑）
- 命令: python3 models/P-0103/M-1/model.py
- 退出码 / 耗时 / log: 0 / ~0.27s / runs/P-0103-M-1.log
- 与 spec 一致 / 无魔数 / 基线 / 种子 / 灵敏度: PASS
- 问题: 无（不修）。B-%31/%192/%248/XOR2 在；SEED=20260903；0.85 只作杀线比较不是均值；无 H100/GB/s。

## 准则
- 第一性原理 / CLAIM 与占用分列 / 未填硅: PASS

## 修复清单
淘汰原因：S=4608B min/mean=0.7500<0.85；DMC_div≠DMC_asm（mismatch≈2/3）；1.5MiB n_DMC=18。不修代码。

## 禁止自检
未改 spec/model/机制卡；未与他卡混排名；未把未签字数字当周报。
