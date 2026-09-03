# T2 audit · P-0103/M-5 B3CSH

auditor: 评估审计
batch: A
round: 1
date: 2026-09-03 (Asia/Shanghai)
verdict: 淘汰

## 判决
诚实重跑 exit 0。dmc_odd=(d0+d1+d2) mod 3 未用 d0 冒充（d0!=odd 计数过万）；CSA 整数恒等式在断言里；GF2 秩算出=11；C0..C7 翻转与点名 δ 对齐；δ=9 V=0.0000<0.3；CTRL G-mod-3 n_DMC=128；N_good=32/36 分表且无二次 mod 3。但 T1/spec kill-line 1：S∈{1536B,4608B,12KiB,1.5MiB,2MiB} 任一 n_DMC<384 或 2MiB |{p_mix[0]}|=1 则作废。重跑：1.5MiB n_DMC=305、2MiB n_DMC=192 且 |{p_mix[0]}|=1（已声明、未藏成 384）。点名 δ 上 min/mean=0.15/0.30/0.05/0.22，远低于 0.85。机制阈值失败 → 淘汰。

## 收益阈值
- 合格线: min/mean 0.85（CONSTRAINT，不是均值）；主结果=相对占用
- 重跑关键数（引自 runs 日志，勿编造）: GF2_11 rank=11；B3CSH 1536B n_DMC=384 min/mean=0.1500；4608B n_DMC=384 min/mean=0.3000 V=0.0000 CTRL=128；12KiB n_DMC=384 min/mean=0.0500；1.5MiB n_DMC=305 min/mean=0.2234；2MiB n_DMC=192 min/mean=0.1875 |{p_mix[0]}|=1；翻转 1536B C0=15359 match；4608B C0=C1=15359 match；12KiB C0=0 C1=15359 C2=5759 match；1.5MiB C3=5461 match；N_good=32/36 在 4608B 均 n_DMC=384 min/mean=0.3000
- T1 kill-line 逐条:
  1. 抄 dmc_odd；n_DMC<384 或 2MiB p_mix[0] 死亡须声明、作废: FAIL 1.5MiB=305、2MiB=192、|{p_mix[0]}|=1（已声明，故非退回隐瞒）
  2. δ=9 翻转点名 + V<0.3 + CTRL≈128；相关≥0.8 失败: PASS V=0.0000（G mod 3 在 δ=9 为常数，3×3 退化成单列；仍满足 <0.3）CTRL=128
  3. k mod N_good 后再禁 mod 3；32 vs 36 分表: PASS
  4. 每 S 打 C0..C7；主 bench；禁 H100: PASS
  5. GF2 秩计算一次、不声称 11: PASS 算出 11
- 阈值判定: 低于阈值

## 魔法缺口
| CLAIM | 模型可解释 | 缺口 |
| 点名 δ 上 n_DMC 128→384 | 1536/4608/12KiB=384；1.5MiB=305；2MiB=192 | p_mix[0] 双端死亡掉一半 |
| min/mean 0.9–1.0 | 实测 0.05–0.30 | LUT 3,3,2 + 进位相关；远低于 CLAIM |
| 「3 值扩展器」 | 未算谱隙 | 类比 |
- 缺口过大?: 否 + CLAIM 未当输入；p_mix 死亡已声明。淘汰因占用杀线。

## spec
- 变量/公式来源/无膻造: PASS
- 问题: 无。CSA 恒等、ROM 3,3,2、chunk 切位均有源。

## 代码（亲自重跑）
- 命令: python3 models/P-0103/M-5/model.py
- 退出码 / 耗时 / log: 0 / ~0.88s / runs/P-0103-M-5.log
- 与 spec 一致 / 无魔数 / 基线 / 种子 / 灵敏度: PASS
- 问题: 无（不修）。CTRL-g%3 / %31/%192/%248/XOR2 在；无 H100/GB/s。N_good 段有未使用的 r_hash=d0+3*0 死代码，不影响 select-k（实际用 mapper 的 bank）。

## 准则
- 第一性原理 / CLAIM 与占用分列 / 未填硅: PASS

## 修复清单
淘汰原因：1.5MiB n_DMC=305、2MiB n_DMC=192 且 p_mix[0] 冻结；点名 δ min/mean≪0.85。不修代码。

## 禁止自检
未改 spec/model/机制卡；未与他卡混排名；未把未签字数字当周报。
