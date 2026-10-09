# Tier 0 SUMMARY · P-0198

| id | name | 判决 | 可行性 | 新颖性 | 质量 | one-line reason |
| --- | --- | --- | --- | --- | --- | --- |
| P-0198/M-1 | CBC Circulating Bubble Calendar | PASS_T1 | PASS | DIFFERENT_APPROACH | ISCA_WORTHY | 无缓冲环上日历制造可窃取循环气泡；异于有缓冲 Bubble FC / Prevention Slot |
| P-0198/M-2 | CSR Collective Spine via RBRG | PASS_T1 | PASS | DIFFERENT_APPROACH | ISCA_WORTHY | 集合重映射 RBRG 脊骨+有界 latch；近亲 SHARP/FANIN 但 bufferless CHI 双路径可发表 |
| P-0198/M-3 | DPH Direction-Partitioned Highway | REJECT | PASS | FUNCTIONAL_EQUIVALENT | INCREMENTAL | 永久 CW/CCW 角色=class-based 双资源绑定薄特化 |
| P-0198/M-4 | AODI Age-Bounded Opposite-Ring Deflection Inject | PASS_T1 | PASS | DIFFERENT_APPROACH | INCREMENTAL | 同通道对向 2×2 造 1 拍注入洞；BLESS 近亲但环注入洞对象成立 |
| P-0198/M-5 | CRRF Channel–Ring Rebind Fabric | PASS_T1 | PASS | DIFFERENT_APPROACH | ISCA_WORTHY | SYNC epoch 时分 Snp→ghost Dat；CHI 四环重绑非通用 TDM 复述 |

T1 集合: M-1 CBC, M-2 CSR, M-4 AODI, M-5 CRRF。
REJECT: M-3 DPH。无 KNOWN_CONFIRM / EXACT_MATCH。

路径:
- t0-reviews/P-0198/M-1/tier0.md
- t0-reviews/P-0198/M-2/tier0.md
- t0-reviews/P-0198/M-3/tier0.md
- t0-reviews/P-0198/M-4/tier0.md
- t0-reviews/P-0198/M-5/tier0.md

跨批: 先验 T0（P-0101..0106）为 DRAM interleave / 鸽笼放置域；本批为 bufferless CHI 环 NoC。无结构孪生、无 EXACT_MATCH。known_mechanisms.md 薄索引无 NoC bubble/deflection/collective 条目命中。

Close calls（请门卫确认）:
1. **M-2 CSR vs FUNCTIONAL_EQUIVALENT(SHARP/FANIN)**: 本判 DIFFERENT_APPROACH/PASS_T1，理由是 RBRG 位点 + bufferless 守门 + CAM 满回退 RING_P2P 的双路径对象。若门卫把「凡硬件集合树」一律等价，应改 REJECT / INCREMENTAL。512b×≤8 latch 已按「非 highway 队列」放行——若审计发现实现滑成多 flit FIFO，可行性应改 FAIL。
2. **M-4 AODI vs FUNCTIONAL_EQUIVALENT(BLESS/CHIPPER)**: 本判 DIFFERENT_APPROACH + INCREMENTAL → PASS_T1。若门卫门槛「凡偏转即 BLESS 等价」，改 REJECT。
3. **M-1 CBC vs Prevention Slot / slotted ring**: 本判 ISCA_WORTHY；若认为日历造空槽与 Prevention Slot 功能等价，可降 FUNCTIONAL_EQUIVALENT/REJECT，或降质量为 INCREMENTAL 仍 PASS_T1。
4. **M-3**: 可行性无争议；新颖性淘汰。不建议放行除非与 CBC/AODI 合并卡重提。
5. **M-5 Snp killer**: 可行性 PASS 依赖「报告 Snp 变差、duty 可证伪」；若产品约束要求 Snp 延迟硬上界且 7:1 不可配，T1 可能证伪机制而非 T0 淘汰。
