# FUNNEL

周次: 2026-09-08 ~ 2026-09-14（上海）
配额: 新问题 30 → 机制 150 → 过 T0 40 → 过 T1 12 → T2 8 → T3 3
用量: 问题 8/30 · 机制 0/150 · T0 过 0/40 · T1 过 0/12 · T2 过 0/8 · T3 过 0/3

## 2026-09-07 09:00 台账

- 新周开账。已推入仓 `problems/P-0133.yaml` … `P-0140.yaml`（格式验收通过：CONTEXT/SYMPTOM/CONSTRAINT + generality≥7）。**不派建筑师**（等人拍方向）。
- 今日无退回；无机制/评审/评估派出。看板：无 open issue；无待验收交接。
- 上周 Top 两张 T3 签字状态不变（SNS smoke+night；Affine smoke+night）。拍板项仍等人：T4 或停止 / 是否扩配额 / 是否派建筑师 dig VR·CIM·预取·跨片（P-0133–P-0140）。
- 文献 PR #27 仍 OPEN draft（docs insights only，不动派活）。
- 上周收口用量（对照）：30/30 · 25/150 · 7/40 · 6/12 · 2/8 · 2/3。

## Top（上周 T3 通过，评估审计签字；等人定 T4）

- P-0105/M-4 SNS：smoke `t3_audit` round 2 通过；night `t3_night_audit` 通过（PR #23）。占用对 T2 336 行 `rel_err=0`。BW 未按信封 0.85 签字。
- P-0106/M-5 AffineRebind：smoke `t3_audit` round 2 通过；night `t3_night_audit` 通过（PR #25+#26）。占用网表对 T2 `rel_err=0`。BW 未按 0.85 签字。

## 本周已入仓备案（未派建筑师）

- P-0133–P-0136（VR / CIM）
- P-0137–P-0140（预取代理≠端点 / 混合相位；跨片电气瓶颈 / 光模拟裕度三角）

## 上周备案残留（未改、不派）

P-0104、P-0107–P-0112；T1 回流 P-0113–P-0127、P-0128–P-0130。作废 P-0131、P-0132。

## 周五 17:00 周报收口（2026-09-04）

- Affine night：PR #25+#26 已合入 main；`t3_night_audit.md` 在仓，verdict 通过。
- SNS night：PR #23 已合入。
- 拍板项交人：两张 Top **T4 或停止**；是否扩配额；是否切 VR/CIM 等新方向。

## T2 淘汰（上周）

P-0103/M-4 CR-MRDR；P-0101/M-3；P-0103/M-1；P-0103/M-5。

## 已知方案确认（T0，上周）

P-0102/M-2、P-0102/M-4 EXACT_MATCH。
