# FUNNEL

周次: 2026-09-01 ~ 2026-09-07（上海）
配额: 新问题 30 → 机制 150 → 过 T0 40 → 过 T1 12 → T2 8 → T3 3
用量: 问题 30/30 · 机制 25/150 · T0 过 7/40 · T1 过 6/12 · T2 过 2/8 · T3 过 2/3

## 2026-09-05 09:00 台账

- 今日无派出、无退回。问题配额已满；下周一再推 P-0133–P-0140 yaml，不派建筑师。
- Top 两张 T3 签字状态不变（SNS smoke+night；Affine smoke+night）。拍板项仍等人：T4 或停止 / 是否扩配额 / 下周是否切 VR·CIM。
- 文献 PR #27 OPEN（docs insights only，不动 problems/mechanisms/FUNNEL 派活）。
- 看板：无 open issue；无待验收交接。

## 周五 17:00 周报收口（2026-09-04）

- Affine night：PR #25+#26 已合入 main；`t3_night_audit.md` 在仓，verdict 通过。占用沿用已签字 smoke；night BW 不签信封 0.85。
- SNS night：PR #23 已合入（此前台账已记）。
- 拍板项交人：两张 Top **T4 或停止**；是否扩配额；下周是否切 VR/CIM 备案（P-0133–P-0136）。
- 未签字数字（reduced-bbox BW、信封 0.85）不进周报绝对值。

## Top（T3 通过，评估审计签字）

- P-0105/M-4 SNS：smoke `t3_audit` round 2 通过；night `t3_night_audit` 通过（PR #23）。占用对 T2 336 行 `rel_err=0`。BW 未按信封 0.85 签字。
- P-0106/M-5 AffineRebind：smoke `t3_audit` round 2 通过；night `t3_night_audit` 通过（PR #25+#26）。占用网表对 T2 `rel_err=0`。BW 未按 0.85 签字。

## 下周备案（未入仓）

- P-0133–P-0136（VR / CIM）
- P-0137–P-0140（2026-09-05 文献：预取代理≠端点 / 混合相位；跨片电气瓶颈 / 光模拟裕度三角）

下周一配额开后再推 yaml，不派建筑师。未改 P-0101–P-0130。

## T2 淘汰

P-0103/M-4 CR-MRDR；P-0101/M-3；P-0103/M-1；P-0103/M-5。

## 已知方案确认（T0）

P-0102/M-2、P-0102/M-4 EXACT_MATCH。

## 本周备案（未派建筑师）

P-0104、P-0107–P-0112；T1 回流 P-0113–P-0127、P-0128–P-0130。作废 P-0131、P-0132。
