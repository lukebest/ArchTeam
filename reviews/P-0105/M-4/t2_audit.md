# T2 audit · P-0105/M-4 SNS

auditor: 评估审计
batch: A
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 通过

## 判决
诚实重跑 exit 0。S-box 整数多项式 checksum 通过，非 AES/GF(256)。covering 11/10/CV=0.0442 标为 COVERING_BOUND、非黄金。S=2MiB：SNS n_DMC=384、跨 512B-grain 与 2MiB-aligned 两族 base 的 n_DMC rel_diff=0.0000<5%；ABL-sbox 相位变 DMC id（粒内 (0)(1)(2)…(287)，计数恒为 1）；ABL-shear 保持 384。bank 每 DMC=6、bank%8 kinds=1 已报。4608B 单列。无 H100/GB/s。绝对 BW 条款未计时、标为未评估 CONSTRAINT。过线。

## 收益阈值
- 合格线: min/mean 0.85（CONSTRAINT，不是均值）；主结果=相对占用
- 重跑关键数（引自 runs 日志，勿编造）: S(0..15) checksum OK；COVERING_BOUND max=11 min=10 CV=0.0442；SEED=20260903；S=2MiB SNS n_DMC=384 n_bank=2304 min/mean=0.9375 bks/DMC=6-6 bank%8=1；B-mod384 n_DMC=3；ABL-sbox n_DMC=1；S=1MiB/512KiB/512B SNS n_DMC=384 min/mean=0.9375/0.9000/0.9000；4608B SNS n_DMC=384 min/mean=0.7000（单列）；grain 族 SNS n_DMC 全 384 rel_diff=0.0000；aligned 族同；ABL-sbox ids 随 grain 相位变、aligned 上全 (0,)
- T1 kill-line 逐条:
  1. ROM 锁定；S=2MiB 两族 base n_DMC=384 且占用相对差<5%；只赢 min/mean 输绝对 BW=失败（BW 未算）: PASS n_DMC=384 rel_diff=0；BW 条款 unevaluated
  2. bank 直方图 / bank%8；6b 窗趋向 6 bank/DMC: PASS min=max=6、bank%8=1
  3. 消融 shear-only；sbox-only 必须随相位变: PASS shear=384；sbox 计数=1 但 grain 相位 DMC id 变（隔离剪切）
  4. 512B-grain 与 2MiB-aligned 分表；S 含 2MiB/1MiB/512KiB/4608B/512B；4608B 单独: PASS
  5. covering 11/10/CV 非黄金: PASS
  6. team-interleave-microbench；禁 decode/H100: PASS
- 阈值判定: 过线（占用；绝对 BW 未评估）

## 魔法缺口
| CLAIM | 模型可解释 | 缺口 |
| maxload=11 min=10 CV≈0.044 @2MiB | 均匀 raw covering 下界；模型标 COVERING_BOUND；SNS min/mean=0.9375 与 10/10.667 一致 | 未当黄金去贴 ROM |
| 跨 base rel-diff=0 | 测得 0.0000 | 无 |
| 4608B CV≈0.13–0.14 | 本模型报 min/mean=0.7000 单列，未报 CV | 口径不同，已隔离 |
- 缺口过大?: 否 + covering 已贴标签、未当输入

## spec
- 变量/公式来源/无膻造: PASS
- 问题: 无。12b 剪切网表、fold384、整数 S(u) 有源。跨 base 占用向量相对差只报了 n_DMC 而非 visit-share；n_DMC 恒 384 时剪切置换使直方图同类，不构成退回。

## 代码（亲自重跑）
- 命令: python3 models/P-0105/M-4/model.py
- 退出码 / 耗时 / log: 0 / ~0.47s / runs/P-0105-M-4.log
- 与 spec 一致 / 无魔数 / 基线 / 种子 / 灵敏度: PASS
- 问题: grain extra 随机 base 与固定表有重复（0x400/0x600/0xe00），不影响 rel_diff=0。无 H100。0.85 未当均值。

## 准则
- 第一性原理 / CLAIM 与占用分列 / 未填硅: PASS

## 修复清单
无（不修代码）

## 禁止自检
未改 spec/model/机制卡；未与他卡混排名；未把未签字数字当周报。
