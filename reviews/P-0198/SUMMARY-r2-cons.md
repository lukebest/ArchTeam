# Tier 0 SUMMARY · P-0198 round 2 保守架构师（M-16..M-20）

门卫：设计验证。机制卡来源：PR #87 head `65f1268`。该提交中文件名为 `M-11.md`..`M-15.md`（与 PR #84 Jim 卡撞号），按标题映射为 M-16..M-20：

| 新编号 | PR #87 `65f1268` 中文件名 | 标题 |
| --- | --- | --- |
| M-16 | mechanisms/P-0198/M-11.md | RBRG 空槽拼接与本环续行 |
| M-17 | mechanisms/P-0198/M-12.md | Decode-epoch 单拍 highway 对换 |
| M-18 | mechanisms/P-0198/M-13.md | Dat 环选择组播（目的位图） |
| M-19 | mechanisms/P-0198/M-14.md | 邻节点饥饿气泡中继 |
| M-20 | mechanisms/P-0198/M-15.md | Decode-epoch 最长弧先发 |

平台核查：bufferless-ring-noc `main@63163ca`（私有仓，以仓主账号认证访问）。查重规则：被评估 ChiRingFabric 库内已有的特性算作先例，增量须相对真实代码库。未读 T1 persona 评审正文。

| id | name | 判决 | 可行性 | 新颖性 | 质量 | one-line reason |
| --- | --- | --- | --- | --- | --- | --- |
| P-0198/M-16 | RBRG 空槽拼接与本环续行 | REJECT | FAIL | FUNCTIONAL_EQUIVALENT | FLAWED | 基线 RBRG 本来就只写空槽、桥满则源环续行，另有 change-ring 保留槽与 i-tag；卡按不存在的「忙仍切入」立论，改动实为删掉 15 深桥缓冲 |
| P-0198/M-17 | Decode-epoch 单拍 highway 对换 | REJECT | FAIL | FUNCTIONAL_EQUIVALENT | FLAWED | 把在途过路 flit 停进本地注入 staging = 节点缓存过路（同 M-9 理由），队头阻塞、对换次数无界；MinBD 侧缓冲 + 类优先 |
| P-0198/M-18 | Dat 环选择组播（目的位图） | KNOWN_CONFIRM | PASS | EXACT_MATCH | INCREMENTAL | 与库内 Dat 多播及同批 M-14 PSCK 逐项相同；并入平台基线 |
| P-0198/M-19 | 邻节点饥饿气泡中继 | REJECT | PASS | FUNCTIONAL_EQUIVALENT | INCREMENTAL | 因果方向正确（上游饿死下游），但即库内 i-tag 饥饿保留（DV200 已开，阈值 64）的邻居让槽 / 低阈值变体 |
| P-0198/M-20 | Decode-epoch 最长弧先发 | KNOWN_CONFIRM | PASS | FUNCTIONAL_EQUIVALENT | INCREMENTAL | 源内发行序 Jackson/LPT 教科书规则；与 M-12 不同（不跨源让路），收益上界受 hops 差约束 |

T1 集合：无。REJECT：M-16、M-17、M-19。KNOWN_CONFIRM：M-18、M-20。

## 两位架构师交叉查重
| 保守卡 | Jim round 2 卡 | 关系 |
| --- | --- | --- |
| M-18 目的位图组播 | M-14 PSCK | 同一机制，且都等于库内 Dat 多播（EXACT_MATCH） |
| M-20 最长弧先发 | M-12 HSSL | 不同：M-12 跨源推迟近源首拍，被「过路优先、远源在上游」否定；M-20 只在单个注入口内按 hops 排序（Jackson 规则），该否定不适用 |
| M-19 邻节点饥饿中继 | M-12 HSSL | M-19 的因果方向（上游饿死下游）正是 M-12 判决里指出的真实偏置；两卡结论互相印证 |
| M-16 RBRG 拼接 | M-11 MELB | 都在复述库内已有的「失败则沿环续行 / 掉头」路径 |
| M-17 epoch 对换 | M-15 TOSE | 都依赖逐波/逐步的临界标记；M-17 的跨 die 步号偏斜与 M-15 的唯一尾拍标记是同类问题 |
| 全部 | M-9（round 1 保守） | M-16 补上了 M-9 缺的合法拒绝动作，但补法即基线；M-17 重犯 M-9 的「用节点存储吸收过路」 |

## 接口落点核查（卡作者未能读仓，钩子按接口描述写成）
- 仓内无 RTL 源（无 .v/.sv），本批无卡触 RTL。`include/`+`src/` 为哈希锁定 ChiRingFabric ESL 库（`provenance/esl-2026-09-15.json`），改动即仿真器结构改动，只能开新分支。
- 各卡声称的 `tests/soc_sim --cc-scheme <name>` 开关真实存在（`run_soc.py:329`），但其后端 `platform/CongestionCtrl.h` 只做 NI 组级速率/赤字控制，不能承载逐拍逐槽逻辑。
- 需要动库：M-16（RBRG = `TNetworkInterfaceRbrg`，出桥注入在 `TCsHighWay::sendFlitToWay`；卡写的「grant 条件」「skid」不存在）、M-17（`TCsHighWay` 仲裁 + NetworkFlit 头）、M-19（`TCsHighWay` 注入决策 + CS 邻接）。
- 只需平台：M-18（库内多播由 `TBridge.cpp:527` 的 `ctrl.m_isCoalesceSucc` 激活；卡写的「加 DMASK 头、NI 加 copy-forward」库里已有）、M-20（`TrafficGen.h`/`Endpoint.h` 发行与回复顺序）。

## 平台基线建议（汇总，非 T1 任务）
1. 为 broadcast / allgather 扇出半边打开库内 Dat 多播（M-14/M-18 合并）。
2. 扫 `itagThreshold` 8/16/32（`gen_config.py` i-tag 参数），量化饥饿尾（M-19）。
3. 增加 FCFS / LPT / SPT 发行序对照臂（M-20），区分源端排队尾与环上争用尾。
4. 打开 `UturnConnect` 并报 `eject_failed_times`（见 SUMMARY-r2.md，M-11）。

## Close calls
1. **M-20 判 KNOWN_CONFIRM 而非 PASS_T1**：机制可行且与 M-12 不同，但它是教科书单机排序规则，且只需平台层改动。若门卫希望保留一张「推理步 issue-order」卡进 T1，可改 PASS_T1 / INCREMENTAL，T1 必验：hops 差占推理步尾的比例上界、SPT 反臂、跨源争用下收益是否保留。
2. **M-19 判 REJECT**：因果正确，淘汰只因库内 i-tag。若 i-tag 阈值扫描显示低阈值仍留明显饥饿尾，本卡值得以增量形式重提。
