# T2 audit · P-0106/M-5 AffineRebind

auditor: 评估审计
batch: A
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 通过

## 判决
诚实重跑 exit 0。g=XOR_fold6 抽头冻结（H-FOLD6），DMC 走声明的 H-UP-DMC 9b XOR-fold 而非静默 G mod 384。α 搜索与 gcd 恒等 identical=True（minimax α 全为 1），真 α=1 列保留。死命中全 0。满好 skip-dead 与 minimax n_bank 同为 3584，增益≈0。主增益在 n=40 的 skip-dead vs modn-α=1（2MiB cls_mean 9.3333→10.6667，rel-diff vs minimax=0.0000<5%）。Doc S 含 3×/9×512B。均匀 25% 标明仍含因子 3、非 3-adic。CLAIM ×1.5–×3 未当测得 BW。过线。

## 收益阈值
- 合格线: min/mean 0.85（CONSTRAINT，不是均值）；主结果=相对占用
- 重跑关键数（引自 runs 日志，勿编造）: SEED 未驱动随机（掩码确定）；XOR_fold6 smoke=61；2MiB n=40 skip-dead cls_mean=9.3333 n_bank=3584 dead=0；modn-α=1 cls_mean=10.6667 n_bank=4096 dead=0；minimax 同 α=1 rel-diff=0.0000；full-good skip=minimax n_bank=3584 dead=0；3-biased skip 9.2500 / a1 10.6667 dead=0；AP sanity n=40 S_g=4096 n/gcd=5（网表 cls_mean=10.67，允许不同并已并打）；3x512B/9x512B 在表；unif-25% n=36 标明非 3-adic；DMC min/mean 2 幂=0.7500（来自 H-UP-DMC，各 mapper 相同；BW 0.85 未计时）
- T1 kill-line 逐条:
  1. RUN 钉 XOR_fold6；死命中或 M=0 失败；类数 vs n/gcd 作 sanity（可合法不同）: PASS dead=0；两表并打
  2. 大 2 幂 (mod n,α=1) vs minimax 差<5%；主增益 skip-dead vs modn-α=1；均匀 25% 非 3-adic: PASS rel-diff=0；增益在模数 48→n；25% 已标签
  3. dead=0；仿真器按卡填 α 且保留 α=1 列: PASS
  4. 三 mask 同表：满好 / n=40 / 1/3 偏；满好增益≈0；禁 H100 row-remap: PASS
  5. 不改 XOR_fold6 抽头: PASS
- 阈值判定: 过线（bank 类数/死命中；绝对 BW 未评估）

## 魔法缺口
| CLAIM | 模型可解释 | 缺口 |
| 大 2 幂类数 ×1.5–×3 vs skip-dead | AP 上 n/gcd=5 vs skip 残余；网表 10.67/9.33=×1.14 | XOR_fold6 域 64 点已较散，重绑增量小于整数 AP CLAIM |
| 3-biased BW 0.7–0.95 | 只报类数+min/mean 访次；BW 未算 | CLAIM 含 0.85，未当测得 |
| α 搜索改善 gcd | 恒等 identical=True | 正确打假 |
- 缺口过大?: 否 + CLAIM 未当输入；余量（×1.14 vs ×1.5–3）来自网表≠AP，已分列

## spec
- 变量/公式来源/无膻造: PASS
- 问题: §4 B-stack（近邻堆积）未跑；T1 允许「跳死或 stacking」，已实现 skip-dead，不退回。

## 代码（亲自重跑）
- 命令: python3 models/P-0106/M-5/model.py
- 退出码 / 耗时 / log: 0 / ~7.85s / runs/P-0106-M-5.log
- 与 spec 一致 / 无魔数 / 基线 / 种子 / 灵敏度: PASS
- 问题: 无（不修）。H-FOLD6/H-UP-DMC 声明；gcd 表标「非替代」；无 H100/GB/s。

## 准则
- 第一性原理 / CLAIM 与占用分列 / 未填硅: PASS

## 修复清单
无（不修代码）

## 禁止自检
未改 spec/model/机制卡；未与他卡混排名；未把未签字数字当周报。
