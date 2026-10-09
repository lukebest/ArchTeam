# Tier 0 · P-0221/M-9 · 弹出孔前送

- 机制卡: mechanisms/P-0221/M-9.md（PR #104 head `4b8f7f6`）
- 题卡: problems/P-0221.yaml（main@c7522df）
- 作者: 保守架构师
- 判决: REJECT
- 可行性: PASS（物理可落；而且在设备口零代码即可得到）
- 新颖性: EXACT_MATCH（库内端口参数 `insertAfterRemoval=false` 的仲裁顺序）
- 质量: INCREMENTAL
- 进入 Tier 1: NO
- 核查基准: 模型 `main@63163ca`；平台 `89f9c88`

## 卡摘要
每个（CS, 子环, 方向）一个 1-bit `EHOLE`。本 CS 成功弹出一个 flit 的那一拍，禁止本地注入（覆盖 `insertAfterRemoval=true`），把空出来的槽原样向下游送出。i-tag / leaf-tag 预留仍优先。Snp 关闭。宣称 dest 段 `ρ ≤ 1−λ_eject`，dest+1 必见孔，中游要等绕回（≤ 一圈）。

## 轴一 可行性
1. **这个行为库里已经有，是一个端口配置开关。** `TCsHighWay::arbitration()`（`:217-264`）：
   - `m_canInsertAfterRemove || m_directConnect` 为真时：先 `tryWayToLocal`（弹出），再 `tryItagProcess`，再 `tryLocalToWay`（注入）——弹出空出的槽当拍被本地吃掉（`:249-259`）。
   - 为假时：先 `tryItagProcess`、`tryLocalToWay`，**最后**才 `tryWayToLocal`（`:260-264`）。注入时槽还被待弹出的 flit 占着，注入不了；弹出后槽为空，`xfer` 原样送往下游。
   这就是 M-9 E1 臂的行为。`insertAfterRemoval` 是端口 TOML 参数（`TPortConfig.cpp:94`，模型默认 false `:205`），按 CS 取各端口的 OR（`TCsConfig.cpp:87`，经 `TNetworkInterfaceBase.cpp:40` 传播）。DV200 生成配置对 AIC/COC/HA/SLLC/3DIO/ChangeRing 都设为 true（`gen_config.py:134,144,156,177,198,212`）。
2. **唯一的非零差异在 RBRG 口。** 开了 L1 swap 的端口必须 `insertAfterRemoval=true`（`TPortConfig.cpp:60-61` assert），ChangeRing 端口开 L1 swap（`gen_config.py:212-214`），所以 RBRG 所在 CS 不能直接把开关拨成 false。M-9 在那里「保持弹出先于注入的顺序、只挡当拍注入」，可以绕开这个 assert——但 RBRG 换环 flit 的着陆口正是 M-7 讨论的位置，增量很窄，卡没有把这一点作为主张。设备口（AIC/HA/3DIO，`l1SwapEn=False`）完全等价。
3. 效果的上界分析本身成立：dest 段少占 `λ_eject`，孔在 `L_link` 拍后到 dest+1；中游要绕回，最坏一圈（42 / 72–76 / 132–152 拍）。卡对「途中会被吃掉、不保证远端」的自陈诚实。但这仍是「不在 dest 当拍再注」的局部规则，对「上游合计填满下游」不给段级上界，题面闭合条件不满足。
4. 代价：dest 同时是源时（HA 回读数据、allreduce 中间 rank），每次弹出丢一个注入机会，注入率下降。卡 §4 已列。
5. Sink / 死锁：被挡头留在 head，弹出失败保持基线绕圈（`TCsHighWay.cpp:574-577`）✅。

## 物理假设逐项核查（容量 / 位宽 / 环数 / 缓冲深度）
| # | 假设 | 卡声称 | 实际 | 判定 |
|---|---|---|---|---|
| 1 | `insertAfterRemoval` 默认 | true，`gen_config.py:134,157,198`；`TNetworkInterfaceBase.cpp:40` | 生成配置为 true：`:134`、`:156`（卡写 157，差 1）、`:198`；**模型默认 false**（`TPortConfig.cpp:205`） | ⚠️ 「默认」需区分生成值与模型默认 |
| 2 | 仲裁顺序 | 先弹出再注入，`:217-264` | 仅在 `insertAfterRemoval/directConnect` 为真时；为假时顺序相反 | ⚠️ 漏掉了反向分支 |
| 3 | 弹出失败 | 绕环，`:574-577` | `eject_failed_times++`、`can_uturn=true` ✅ | ✅ |
| 4 | 每向槽 | 1 | ✅ | ✅ |
| 5 | 一圈 / `L_link` | 42 / 72–76 / 132,148,152；2/3/4 | ✅ | ✅ |
| 6 | Dat / Snp 子环 | 2 / 1 | ✅ | ✅ |
| 7 | soc_sim 不生成 `UturnConnect` | 平台事实 3.36 | main ✅；**89f9c88 已加 `uturn` 开关**（`gen_config.py:326-330,384-389`，默认关） | ⚠️ 平台分支已变 |
| 8 | 新增 flit 位 | 0 | EHOLE 本地；不加 invalid 占位、不加 TTL | ✅ 属实 |
| 9 | 新增存储 | 1 bit | ✅；用库内开关则 0 | ✅ |
| 10 | 反向占用 | 0 | ✅ | ✅ |
| 11 | CHI 字段 | SNP 无 Data、DataID 2 b | ✅ 与本卡无关 | ✅ |

## 接口落点与行号核查
| 卡引用 | 实际 | 结论 |
|---|---|---|
| `TCsHighWay.cpp` `tryWayToLocal` 后置 EHOLE，`tryLocalToWay` AND `!EHOLE` | 设备口无需改代码：把端口 TOML `insertAfterRemoval` 置 false（平台层 `gen_config.py`，main 可改）；RBRG 口需改库（新分支） | ⚠️ |
| `gen_config.py:134,157,198` | main/89f9c88 均 `:134`、`:156`、`:198` | ⚠️ 157→156 |
| `--cc-scheme eject-hole` | 不需要；配置开关即可 | — |
| RTL | 无 | ✅ |

## 先例裁定
- **与库内 `insertAfterRemoval=false`：EXACT_MATCH**（设备口行为逐拍相同）。
- 与 i-tag 预留槽：不等价（不打标、不绑定）。
- 与库内 FC：不等价（无速率、无反馈）。
- 与动态 leaf-tag：不等价（不放 invalid 占位）。

## 轴二 新颖性
| 对照 | 关系 | 说明 |
|---|---|---|
| **库内端口参数 `insertAfterRemoval=false`** | **EXACT_MATCH** | 同一仲裁顺序 |
| 教科书 slotted ring「源/宿释放的槽不得被释放者立即重用」 | FUNCTIONAL_EQUIVALENT | 同类防独占规则 |
| P-0221 M-6 | 同族 | M-6 在注入后让孔，M-9 在弹出后让孔 |
- 显式标注：不是 token / credit / window。

## 指标核对
值得做的是**零代码对照**：把设备口 `insertAfterRemoval` 置 false 跑一次 B\*，看沿环等待梯度与最差节点。若有效，它是基线调参，不是新机制。

## 判决理由
REJECT（EXACT_MATCH）。M-9 的弹出当拍不注入，就是库内 `insertAfterRemoval=false` 时 `arbitration()` 的现成顺序；只在开 L1 swap 的 RBRG 口有窄增量，卡没有主张。建议把该开关纳入基线扫描。
