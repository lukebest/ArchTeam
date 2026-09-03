# Tier 0 · P-0106/M-4 · HA 级 valid mask 拦截死 bank

- 机制卡: mechanisms/P-0106/M-4.md
- 判决: REJECT
- 可行性: PASS
- 新颖性: FUNCTIONAL_EQUIVALENT
- 质量: THIN
- 进入 Tier 1: NO

## 轴一 可行性
- 因果性: 译码出的 (pipe,bank) 独热后与 HA 的 96b V 做 AND。spare 来自活集，默认 spare_valid=0 走 ERROR。不在流量下改 V。
- 完美预测/无限带宽/零延迟: 闸门，不是预测器。
- 关键边界: **不是主 interleave**。不跨 DMC 借 bank。重定向只指向该 DMC 活集内预留 spare。库内无 live-set 的 mapper 被挡住。
- 硬件开销: 192×96b=2.25KB，与 M-1 mask 同量级。

## 轴二 新颖性
- vs 文献: valid/ready 闸门 + spare slot 是访问路径安全网，不是映射发明（disabled target 已在库验证套件）。
- vs 本周卡: 不产生新的可逆 live-set 映射。M-1 已经保证死桶命中率 0；本卡是对兄弟 mapper 的兜底。

## 轴三 质量
- 机制完整度: 作为闸门写清楚，默认 ERROR 比静默重定向老实。
- 可证伪性: 陈旧 mapper 打到死 bank 应被拦。
- 深度: 对 P-0106「映射必须在 live set 上可逆」只做拦截，不回答怎么映。THIN。

## 理由
可行性通过。作为机制卡过薄：闸门不是 interleave。不进 Tier 1。
