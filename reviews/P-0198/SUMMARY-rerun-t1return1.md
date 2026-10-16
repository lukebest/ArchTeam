# Tier 0 SUMMARY · P-0198 rerun（T1-return-1 · M-2/M-4/M-5）

Clean-room 重跑：仅读 `_src/problem.yaml`、三张修订卡、`fatal_points.md`（主持 synthesis 退回核）。未读旧 `reviews/P-0198/**`、未读 M-1 或其他未修订卡正文。

## 判决表

| id | shortname | 可行性 | 新颖性 | 质量 | 原致命点 | 进入T1 | 判决 | path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P-0198/M-2 | CSR Rendezvous–Grant | PASS | DIFFERENT_APPROACH | ISCA_WORTHY | 全部CLOSED | YES | PASS_T1 | t0-reviews/P-0198-rerun/M-2/tier0.md |
| P-0198/M-4 | AODI Age-Bounded Deflect | PASS | FUNCTIONAL_EQUIVALENT | INCREMENTAL | 全部CLOSED | YES | PASS_T1 | t0-reviews/P-0198-rerun/M-4/tier0.md |
| P-0198/M-5 | CRRF Channel–Ring Rebind | PASS | DIFFERENT_APPROACH | ISCA_WORTHY | 全部CLOSED | YES | PASS_T1 | t0-reviews/P-0198-rerun/M-5/tier0.md |

T1 集合（本重跑）: **M-2, M-4, M-5**。无 REJECT / KNOWN_CONFIRM。未重审 M-1。

## 致命点矩阵

| 卡 | FP-1 | FP-2 | FP-3 |
| --- | --- | --- | --- |
| M-2 CSR | **CLOSED** — Dat 拍持有≡0，无拒收滞留 | **CLOSED** — N_cam=4 专用，取消 1–2 latch×8 TDM | **CLOSED** — overflow/timeout 计数进 endpoints |
| M-4 AODI | **CLOSED** — 双忙真值表 hole≡0，禁第三槽 | **CLOSED** — Rejoin + 逐包 φ，非 Σ age | **CLOSED** — deflect-off / 对向 util / completions |
| M-5 CRRF | **CLOSED** — Epoch Drain + skew 建模 | **CLOSED** — ghost Dat channel-id + bind_mismatch_redirect | **CLOSED** — Snp 指标+duty 扫描；本地压力；SYNC≠预测 |

无 OPEN。无 PARTIAL 残留到「结构洞」级别；各卡残余均为仿真可杀断言（回退率、φ 循环、drain 税/Snp 1.4×）。

## 主题核验（修订正文）

| 卡 | 预期主题 | 正文核验 |
| --- | --- | --- |
| M-2 | 无 RBRG Dat latch；N_cam=4；CAM Dat≡0；overflow/timeout→RING_P2P | ✓ §0/§2.1–2.2 |
| M-4 | 双忙 hole≡0 端口表 + Rejoin；逐包 φ | ✓ §0/§2.2–2.4 |
| M-5 | Epoch Drain + bind_mismatch_redirect；FSM 仅本地压力 | ✓ §0/§2.2–2.4 |

## 轴一要点（跨卡）
- 三卡均未发明每方向第三 highway 槽，未引入片上 flit 载荷队列（M-2 明确杀掉 RBRG Dat latch；M-4 XB/rejoin 深度 0；M-5 为时间复用非第二永久 Dat 端口）。
- 均禁止完美预测/无限带宽；M-5 额外拔掉 COLL_EP 软件预言主臂。
- Bufferless 信封保持：失败路径为重分类/等待空口/有界 duty stall + 可计数 redirect，而非静默丢或无限侧缓。

## 轴二要点（仅本批三卡互比）
- M-2 ↔ M-4 ↔ M-5 切面正交（会合授权 / 注入几何 / 通道绑定），无 EXACT_MATCH。
- M-4 对文献偏转族为 FUNCTIONAL_EQUIVALENT / INCREMENTAL，仍因致命点闭合与双忙诚实窗口送 T1。
- M-2、M-5 相对 in-network reduce 缓冲与静态 1:1 CHI 绑定为 DIFFERENT_APPROACH。

## Close calls
- **M-4 是否因 FE+INCREMENTAL 拒送 T1**：本重跑优先「致命点全 CLOSED + 可行性 PASS」；偏转族增量性留给 T1 深审。若主持政策对 FE+INCREMENTAL 一律不进 T1，可降为 REJECT——当前按闭合退回核判定 PASS_T1。
- **M-2「payload 在 Dat 环直到 GRANT」措辞**：与「授权窗内注入」并读解释为 payload 不进 RBRG、端点侧持有/窗内注入；不变式 Dat_beats_held@CAM≡0 已钉死。T1 应查 orbit vs 端点持有的 cycle 模型是否一致。
- **M-5 跨 die drain**：本地 sniff 非全局瞬时清空；靠 `epoch_committed` + skew 接受集 + mismatch redirect 闭合正确性。T1 必须看 redirect 稳态是否真能 ≈0。

## 产出文件
- `t0-reviews/P-0198-rerun/M-2/tier0.md`
- `t0-reviews/P-0198-rerun/M-4/tier0.md`
- `t0-reviews/P-0198-rerun/M-5/tier0.md`
- `t0-reviews/P-0198-rerun/SUMMARY.md`
