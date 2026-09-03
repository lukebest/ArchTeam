# T2 · LIMINAL · P-0103/M-4 CR-MRDR（G[23] 现稿）

独立分析模型。只评这一张。不是周报数字。

## 0. Identity

| 项 | 值 |
| --- | --- |
| 卡 | P-0103/M-4 Cut-Resilient Mixed-Radix Digit Reversal |
| 稿 | `mechanisms/P-0103/M-4.md` 现稿，高抽头 **G[23]** |
| 作废 | 冻结窗 MRDR；G[21] 稿；其上全部 T0/T1 数字与任何旧 T2 |
| 批次 | **Batch B，仅本卡。** 不与 Batch A（P-0101/M-3、P-0103/M-1、P-0103/M-5、P-0105/M-4、P-0106/M-5）混写结论 |
| 实现 | `models/P-0103/M-4/model.py`（stdlib，三臂同一 mapper 开关） |
| 信封 | 384 DMC / 18432 bank / 2×192 DMC/die × 96 HA / 512B grain / W=8GiB / 128 outstanding/core |
| 未知 | 时钟、μ_d、DRAM 类型。**禁止填 H100。绝对 GB/s = 假设，默认不报。禁止 ±15% vs silicon**（无公开硅测） |

本文件写 **CONSTRAINT / CLAIM / 未证严 / 假设**。消融 6/3 与 `die=DMC[8]` 是约束，不是已测收益。

## 1. Variables

符号只从信封、卡 §2.2、Little (1961) 来。不引入拟合参数。

| 符号 | 定义 | 源 |
| --- | --- | --- |
| \(A\) | 字节地址 | 信封 |
| \(G=A[63:9]\) | 512B 粒块地址。\(G=A/2^{9}\) | P-0103.yaml；512B\(=2^{9}\) |
| \(N_{\mathrm{DMC}}=384=2^{7}\cdot 3\) | 逻辑控制器数 | 信封 |
| \(N_{\mathrm{bank}}=18432=2^{11}\cdot 9\) | bank 数 | 信封 |
| \(N_{\mathrm{die}}=2\)，每 die 192 DMC，每 die 96 HA，每 HA 2 pipe | 物理装箱 | 信封 2×Die2 |
| \(W=8\,\mathrm{GiB}\) | 共享工作集 | 信封 |
| \(K_{\mathrm{core}}=120\)，\(O=128\) | 核数 × 每核 outstanding | 信封 |
| \(N_{\mathrm{inflight}}=K_{\mathrm{core}}\cdot O=15360\) | 闭环 token | Little 的 \(L\) 上界 |
| \(\delta=S/512\) | 粒步长（整数） | \(S\) 被 512B 整除 |
| \(d[i]\) | 11 个二进制数位，\(i=0..10\) | 卡 LIVE_DIGIT |
| \(q[j]=d[10-j]\) | 11 位倒序 | 卡 DIGIT_REV |
| \(q[6:0]\) | 组索引，7b，像的目标基数 128 | 卡；\(\{d[10],\ldots,d[4]\}\) |
| \(t_0,t_1\in\{0,1,2\}\) | 无权重 7 项 \(\mathrm{mod}\,3\)，**不是** \(G\bmod 9\) | 卡 TRIT_SRC |
| \(H_0,H_1\in\{0,1,2\}\) | 8b XOR 折成 2b，再 \((v{=}3)?0:v\) | 卡；直方图 \(\{2,1,1\}\) |
| \(t_0'=(t_0+H_0)\bmod 3\)（TRIT_INJ 开） | trit 平移 | 卡 TRIT_INJ |
| \(\mathrm{DMC}=t_0'+3\cdot q[6:0]\in[0,383]\) | 逻辑号 | 卡 DIGIT_DEC |
| \(\mathrm{die}=\mathrm{DMC}[8]\) | **主列**。切 256+128 | 卡 §2.2 **按字实现** |
| \(\mathrm{HA}=\mathrm{DMC}[7:1]\in[0,127]\) | 主列 | 卡 |
| \(\mathrm{pipe}=\mathrm{DMC}[0]\) | 主列 | 卡 |
| \(\mathrm{die_{env}}=\lfloor\mathrm{DMC}/192\rfloor\) | **只对照**。禁止替换主列 | T1 Archi/Sim/Sys |
| \(n_{\mathrm{DMC}}=\lvert\{\mathrm{DMC}(G_k)\}\rvert\) | AP 上计桶，不是秩 | Sim T1 |
| \(\lvert q[6:0]\rvert=\lvert\{q[6:0](G_k)\}\rvert\) | 同上 | Sim T1 |
| \(\mu_d\) | 每 DMC 服务率 | **UNKNOWN** |
| \(\mathrm{BW_{peak}}\) | 峰值带宽 | **假设**。本模型不数值化 |

顺序 AP：\(G_{k+1}=G_k+\delta\)，\(G\in[0,W/512)\)。S 集合永不平均：

\[
S\in\{512\mathrm{B},\,1\mathrm{KiB},\,1536\mathrm{B},\,3\mathrm{KiB},\,4608\mathrm{B},\,12\mathrm{KiB},\,1.5\mathrm{MiB},\,2\mathrm{MiB}\}.
\]

基线（同 AP，只换映射）：`%31` / `%192` / `%248` / 纯 2 幂 XOR。本 `model.py` 只闭合 CR-MRDR 三臂；基线是评测约束，不是本文件的拟合对象。

## 2. Bit-exact mapper

高抽头是 **G[23] 不是 G[21]**。\(i+11\in\{11,\ldots,21\}\)，永不等于 23（G[21] 稿在 \(i=10\) 上 \(G[10+11]=G[21]\)，高抽头被异或消掉）。

```
G      = A[63:9]
d[i]   = G[i] ⊕ G[i+11] ⊕ G[23]          // i=0..10；消融臂改 d[i]=G[i]
q[j]   = d[10−j]                         // j=0..10
q[6:0] = {d[10], d[9], d[8], d[7], d[6], d[5], d[4]}
         // 这 7 个数位即组索引。整数权重：q[j] 的 bit j 为 2^j，LSB=q[0]=d[10]
t0     = (G[0]+G[3]+G[6]+G[10]+G[13]+G[16]+G[19])  mod 3
t1     = (G[1]+G[4]+G[7]+G[11]+G[14]+G[17]+G[20])  mod 3
H0_2   = { ⊕ G[19:16] , ⊕ G[15:12] }     // 2b，0..3
H1_2   = { ⊕ G[11:8]  , ⊕ G[7:4]  }
H0     = (H0_2==3) ? 0 : H0_2            // 直方图 {2,1,1}
H1     = (H1_2==3) ? 0 : H1_2
t0'    = TRIT_INJ ? (t0+H0) mod 3 : t0
t1'    = TRIT_INJ ? (t1+H1) mod 3 : t1
DMC    = t0' + 3 · q[6:0]                // 0..383
bank_in= t1' + 3 · q[10:7]               // 0..47
die    = DMC[8]                          // PRIMARY. 256+128. 禁止改成 /192
HA     = DMC[7:1]
pipe   = DMC[0]
die_env= DMC / 192                       // CONTRAST ONLY
```

`model.py` 的 `map_address` 按上式接线。主列永远 `die=(DMC>>8)&1`。

### 2.1 Floorplan — 按字实现，禁止默默修正

信封：\(2\times 192=384\)，每 die 96 HA × 2 pipe。

主列 `DMC[8]`：\(\mathrm{DMC}\in[0,255]\) → die0（256 个号），\(\mathrm{DMC}\in[256,383]\) → die1（128 个号）。不是 192+192。

`HA=DMC[7:1]` 产生 \([0,127]\)。信封 HA 域是每 die \([0,95]\)。任一请求 `HA≥96` = **装箱失败**。任一 die 上出现的逻辑 DMC 数 \(\neq 192\) = **装箱失败**。

对照列 `die_env=DMC/192` 在 \(n_{\mathrm{DMC}}=384\) 且均匀时应打出 192+192。对照列不得写进主结果。

若 die0/die1 **发行比** \(\ge 1.5\)，则 \(n_{\mathrm{DMC}}=384\) **不得记为 BW 成功**（Sim T1）。256:128 的切法在均匀 DMC 上发行比恰好 \(2\ge 1.5\)。这是接线后果，不是评测没扫到。M-1 卡写过「不要 DMC[8]，那会切成 256+128」——现稿用的就是那一刀。本模型不把它改成 `/192`。

必须打印 die0/die1 发行比（主列）与 die_env 发行比（对照）。

### 2.2 GOOD_MAP / XOR_RETRY（cycle 约束，本脚本不报 BW）

- 384×48b，**1R 共享**。100% good **跳过 SRAM** 与 partial-good 冲突 **分列**。
- 掩码读一次进触发器；三次探针禁止三次读 SRAM。
- `b1 = b0 ⊕ {0, live5}`，`live5=G[23:19]`。`≥48` 则 **−48**（禁止 −32）。
- 第三探 miss = **NACK**，DMC 不变。禁止 `+1`，禁止跨 DMC。
- NACK 占发行口，单独列。`{2,1,1}` 三类流量、1R 冲突，各单独列。

本 `model.py` 闭合组合映射占用。1R / NACK 是 T1 分列约束，不是本脚本的 GB/s 通道。

## 3. Per-stride live-tap table

\(\delta=S/512\)。2 幂因子冻住 \(G\) 的低位；奇数因子冻住 \(G\bmod 3^{k}\) 不等于冻住 XOR 数位。

| \(S\) | \(\delta\) | \(G\) 冻 | 行走 | 组索引活源（现电路） |
| --- | --- | --- | --- | --- |
| 512B | 1 | 无 | 全 | 低/中/高三抽头 |
| 1KiB | \(2\) | \(G[0]\) | \(G[1+]\) | 同上，少 G[0] |
| 1536B | 3 | \(G\bmod 3\)（整数） | 各位仍翻 | 低抽头 + 无权重 trit；**不是** \(G\bmod 9\) 冻 |
| 3KiB | 6 | \(G[0]\) 与 \(G\bmod 3\) | \(G[1+]\) | 低/中仍走 |
| 4608B | 9 | \(G\bmod 9\) | 加 9 仍翻比特 | **\(G\bmod 9\) 冻 \(\neq\) XOR 数位冻**。分列，不并进 1536B |
| 12KiB | 24 | \(G[2:0]\) | \(G[3+]\) | H1 高半仍走 |
| **1.5MiB** | \(3072=3\cdot 2^{10}\) | \(G[9:0]\) | \(U:=G\gg 10\)，每步 \(+3\) | 见下表。卡主张 \(\lvert q\rvert=128\) |
| **2MiB** | \(4096=2^{12}\) | \(G[11:0]\) | \(G[12+]\) | 见下表。卡主张 \(\lvert q\rvert=128\) |

杀手步长组 bit（卡 §2.2 表；现电路，不是消融）：

| 组 bit | 数位 | 1.5MiB 活抽头 | 2MiB 活抽头 |
| --- | --- | --- | --- |
| \(q[0]=d[10]\) | \(G[10]\oplus G[21]\oplus G[23]\) | 三个都在 \(G[10+]\) | \(G[21],G[23]\)（\(G[10]\) 冻） |
| \(q[1]=d[9]\) | \(G[9]\oplus G[20]\oplus G[23]\) | \(G[20],G[23]\) | \(G[20],G[23]\) |
| \(q[2]=d[8]\) | \(G[8]\oplus G[19]\oplus G[23]\) | \(G[19],G[23]\) | \(G[19],G[23]\) |
| \(q[3]=d[7]\) | \(G[7]\oplus G[18]\oplus G[23]\) | \(G[18],G[23]\) | \(G[18],G[23]\) |
| \(q[4]=d[6]\) | \(G[6]\oplus G[17]\oplus G[23]\) | \(G[17],G[23]\) | \(G[17],G[23]\) |
| \(q[5]=d[5]\) | \(G[5]\oplus G[16]\oplus G[23]\) | \(G[16],G[23]\) | \(G[16],G[23]\) |
| \(q[6]=d[4]\) | \(G[4]\oplus G[15]\oplus G[23]\) | \(G[15],G[23]\) | \(G[15],G[23]\) |

整数 \(q[6:0]=\sum_{j=0}^{6} q[j]\,2^{j}\)，与 `DMC=t0'+3·q[6:0]` 的位权一致。表里「组 bit」按 \(q[j]=d[10-j]\) 接线，不按把 \(d[10]\) 接到 MSB 的另一种拼法改电路。

消融 \(d[i]=G[i]\)：1.5MiB 上 \(q[6:0]\) 只剩 \(G[10]\) 行走 → \(\lvert q\rvert=2\)；2MiB 上 \(G[11:0]\) 全冻 → \(\lvert q\rvert=1\)。再乘满 trit 得 **6** 与 **3**。这是 Archi 旧拓扑上界，也是消融臂必须打回的数。

## 4. Ablation matrix — CONSTRAINTS，不是结果

同一 `map_address`，两个开关：`live_digit`、`trit_inj`。禁止另写一份旧卡。

1.5MiB 与 2MiB **永不平均**。两列。

| 臂 | LIVE_DIGIT | TRIT_INJ | 1.5MiB 约束 | 2MiB 约束 | 失败语义 |
| --- | --- | --- | --- | --- | --- |
| ablation | `d[i]=G[i]` | 开 | **必须** \(n_{\mathrm{DMC}}=6\) | **必须** \(n_{\mathrm{DMC}}=3\) | 回不去 ⇒ 没打到 Archi 电路，**后续数字作废**（`model.py` assert） |
| trit_off | 现电路 | 关 | \(\lvert q\rvert=128\) 且 \(n_{\mathrm{DMC}}\approx 128\) 不是 384 | 同左，分列 | 关注入仍到 384 ⇒ trit 在偷占 6→384。\(t_0\) 含 \(G[10],G[13],G[16],G[19]\)，杀手步长上这些位行走，故 \(t_0\) 不是 \(G\bmod 3\) 那样冻死——是否停在 128 **只许 AP 计数，不许默认为 128** |
| current | 现电路 | 开 | \(\lvert q[6:0]\rvert=128\) **且** \(n_{\mathrm{DMC}}=384\) | 同左，分列 | \(n_{\mathrm{DMC}}<128\) = **组索引失败**；\(128\le n_{\mathrm{DMC}}<384\) = **trit 失败，不是「没失败」** |

Trit **只乘在已经满的 128 组上**。禁止把 trit 写成占用从 6 到 384 的理由。

## 5. Algebra

### 5.1 为什么卡主张 \(\lvert q\rvert=128\)：中抽头上的 2-adic，不是 trit

**源（2-adic 乘法可逆）。** \(\gcd(3,2^{m})=1\) 对一切 \(m\)，故 \(\times 3\) 是 \(\mathbb{Z}/2^{m}\mathbb{Z}\) 上的双射。Hensel / 奇数单位。因此 \(U_{k+1}=U_k+3\) 的轨道在任何 \(m\) 位窗上满 \(2^{m}\) 点（窗长足够时）。

**1.5MiB。** \(\delta=3\cdot 2^{10}\)，\(G[9:0]\) 冻，\(U:=G\gg 10\) 每步 \(+3\)。中抽头 \(\{G[15],\ldots,G[21]\}=U[5..11]\) 落在行走段。公共 \(G[23]=U[13]\) 进全部 7 个组 bit，**不替代**中抽头移位。卡主张：中抽头的 2-adic 计数给出 \(\lvert q[6:0]\rvert=128\)，不是 2。

**2MiB。** \(\delta=2^{12}\)，\(G[11:0]\) 冻，\(V:=G\gg 12\) 每步 \(+1\)（2-adic 计数器，满 \(2^{m}\) 是恒等式）。中抽头全在 \(G[12+]\)。卡主张 \(\lvert q\rvert=128\)，不是 1。

**Trit 只提供因子 3。** \(\mathrm{DMC}=t_0'+3\cdot q[6:0]\)。若 \(\lvert q\rvert=128\) 且 \(\{t_0'\}=\mathbb{Z}_{3}\) 且两类坐标不塌成函数相关，则 \(n_{\mathrm{DMC}}=384=128\times 3\)。关 TRIT_INJ 后卡预期停在 \(\approx 128\)：因子 3 不再由 \(H_0\) 注入。**禁止**写「trit 把 6 拉成 384」。6→384 拆掉的是「2 个组」，是 LIVE_DIGIT，不是 TRIT_INJ。

### 5.2 未证严

1. **GF(2) 秩。** 11 个 3 抽头对 24b \(G\) 的秩未算，不声称 18432 双射。公共 \(G[23]\) 进入全部 7 个组 bit。**秩不降 \(\neq\) \(+3\) AP 上像的基数是 128。** 禁止用秩代替 AP 上计 \(\lvert\{q[6:0]\}\rvert\)（Sim T1）。`model.py` 只计数。
2. **H 折叠不是 \(\mathbb{Z}_{3}\) 同态。** \(H_0(x+3)-H_0(x)\) 不恒 0，也不恒为满射。\(\{2,1,1\}\) 来自 2b 值域 \(0..3\) 把 3 折回 0 的组合计数（4 个原像 → 类权重 2,1,1），**不是**「满 trit ⇒ 均匀」。
3. **\(G[23]\) 相关。** 11 个数位共享同一高抽头。必须打印 \(\mathrm{corr}(q[i],G[23])\) 与 \(q\) 各 bit 两两 Pearson。不把「不降秩」写成已测满 128。

### 5.3 整数取模对照（P-0103，不是本卡的发明）

\(f(G)=G\bmod N\) 是环同态。AP 像 \(\lvert\mathrm{im}\rvert=N/\gcd(\delta,N)\)（标准陪集计数；卡 M-1 §1 同式）。\(3\mid\delta\) 时 \(N=384\) 丢掉因子 3 → 像 \(\le 128\)，\(X_{\mathrm{rel}}=3\)。本卡不是再做一个 \(\bmod 384\)。

## 6. Little / roofline

**Little (1961) \(L=\lambda W\)。** 闭环 \(N_{\mathrm{inflight}}=15360\) token。每 DMC 驻留

\[
L_{\mathrm{DMC}}=\frac{15360}{n_{\mathrm{DMC}}}.
\]

| \(n_{\mathrm{DMC}}\) | \(L_{\mathrm{DMC}}\) | 源 |
| --- | --- | --- |
| 384 | \(15360/384=40\) | 信封满占用 |
| 128 | \(15360/128=120\) | 整数取模 \(3\mid\delta\) 上界；trit_off 目标 |
| 6 | \(15360/6=2560\) | 冻结窗 / 消融 1.5MiB |
| 3 | \(15360/3=5120\) | 冻结窗 / 消融 2MiB |

这是占用压力，**不是**测得带宽。

**Roofline（Williams, Waterman, Patterson, CACM 2009 的墙形式）。** 本机 \(\mu_d\) 未知，故

\[
\mathrm{BW}\le n_{\mathrm{DMC}}\cdot \mu_d,\qquad \mu_d=\text{UNKNOWN},\qquad \mathrm{BW_{peak}}=\text{假设}.
\]

本模型 **默认不报绝对 GB/s**。占用屋顶是 \(n_{\mathrm{DMC}}/384\) 与 min/mean 两列，与 BW 0.85 **分列**。禁止用 H100 的 10 MC 当 ×3 代理（Bench T1）。禁止「平均 BW / 打满 18432」当合格。

1 拍 mapper 相对 128 outstanding：延迟被 outstanding 盖住（卡 §3）。2 GHz 是卡上 STA **目标**，不是本信封的已知时钟——不写入数值 BW。

## 7. \(X_{\mathrm{rel}}\)：占用比，不是测得 BW

P-0103：整数取模在 \(3\mid\delta\) 上 \(X_{\mathrm{rel}}=3\)，对应 384→128。

| 对照 | 占用比 | 不是 |
| --- | --- | --- |
| vs mod-N 像 128 | \(384/128=3\) | 不是测得 BW ×3 |
| vs 旧电路 / 消融 6 | \(384/6=64\) | 不是测得 BW ×64 |
| vs 消融 3 | \(384/3=128\) | 不是测得 BW ×128 |

MAGIC-GAP **CLAIM**（占用，待三臂计数，不是周报）：

- 1.5MiB：\(6\to 384\)（组索引 2→128，再 × trit 3）。
- 2MiB：\(3\to 384\)（组索引 1→128，再 × trit 3）。

两行分列。任一行失败不得用另一行或 2 幂平均稀释（Bench T1）。

## 8. \(\{2,1,1\}\) 可使 min/mean \(\sim 0.7\) 即使 \(n_{\mathrm{DMC}}=384\)

**源（组合，不是拟合）。** \(H0_2\) 均匀于 \(\{0,1,2,3\}\) 时，折后权重 \((2,1,1)\)。三类占用比 \(2:1:1\)，

\[
\frac{\min}{\mathrm{mean}}=\frac{1}{(2+1+1)/3}=\frac{3}{4}=0.75.
\]

卡写 \(\sim 0.7\)。条件：\(t_0\) 冻、只靠 \(H_0\)，且 \(H0_2\) 在该 AP 上接近均匀——后一项 **未证严**（折叠非同态）。因此：

- 占用 min/mean 与 BW 0.85 **分列**。
- \(n_{\mathrm{DMC}}=384\) 不证明 min/mean≥0.85，更不证明 BW≥0.85。
- 三类流量单独打印。禁止用「满 3 类」冒充均匀。

T1 Archi 在同窗口报过占用 min/mean 0.70/0.75/0.68。那是 T1 组合仿真，**不是本 T2 的已测数字**，不写入结果表。本模型只保留 \(\{2,1,1\}\Rightarrow 3/4\) 这条组合上界。

## 9. Sensitivity

| 开关 | 开 | 关 | 打印 |
| --- | --- | --- | --- |
| \(G[23]\) | W=8GiB，位翻转 | W=4GiB，\(G[23]\) 冻；120 核同相位 | 两杀手上 \(\lvert q\rvert\) 是否仍 128（Sys T1） |
| TRIT_INJ | \(t'=t+H\) | \(t'=t\) | \(\lvert q\rvert\) 仍 128、\(n_{\mathrm{DMC}}\approx 128\)；若关仍 384 则 trit 偷占 |

满 128 若暗含 \(G[23]\) 翻转，公共抽头会把全机打成同一相位。≤4GiB 是常见作业，必须单独走，不得只报 8GiB。

## 10. T1 kill-lines（照抄综合，不当已测）

来源：`reviews/P-0103/M-4/tier1_synthesis.md`「必须带进 T2 的条件」+ Sim 分列。**约束，不是本文件的结果。**

1. 消融 `d[i]=G[i]`：1.5MiB → \(n_{\mathrm{DMC}}=6\)，2MiB → \(n_{\mathrm{DMC}}=3\)。回不去则后续数字作废。
2. 现稿、TRIT_INJ 开：两杀手 \(\lvert q[6:0]\rvert=128\) 且 \(n_{\mathrm{DMC}}=384\)。失败 \(<128\)。1.5MiB 与 2MiB 分两行。
3. 关 TRIT_INJ：\(\lvert q\rvert\) 仍 128，\(n_{\mathrm{DMC}}\approx 128\)。若关注入也到 384，trit 又在偷占 6→384。
4. 按卡实现 `die=DMC[8]`（禁止默默改成 `/192`），打印两 die 发行比；`HA≥96` 或单 die \(\neq 192\) 为装箱失败。另打一行 `die=DMC/192` 只作对照。die 比 \(\ge 1.5\) 则 \(n_{\mathrm{DMC}}=384\) 不得记 BW 成功。
5. ≤4GiB 工作集、\(G[23]\) 冻结、120 核同相位时 \(\lvert q\rvert\) 是否仍 128。
6. 占用 min/mean 与 BW 0.85 分列；\(\{2,1,1\}\) 三类流量、1R 冲突、NACK 占发行口分列。禁止 H100 ×3 代理，禁止平均 BW / 打满 18432 过关。
7. 禁止用 GF(2) 秩代替 AP 上 \(\lvert q[6:0]\rvert\)。打印 \(\mathrm{corr}(q[i],G[23])\) 与两两相关。
8. S 集合分列不平均。4608B 上 \(G\bmod 9\) 冻 \(\neq\) XOR 数位冻。
9. GOOD_MAP 1R；100% good 跳过 vs partial-good 冲突分列；XOR 重试 \(\ge 48\) 则 −48（禁止 −32）；`live5=G[23:19]`；第三 miss = NACK，DMC 不变。禁止 +1，禁止跨 DMC。

## 11. 本模型打印 / 不打印

**打印：** 三臂 × 两杀手的 \(\lvert q[6:0]\rvert\)、\(n_{\mathrm{DMC}}\)、`die=DMC[8]` 发行比与每 die 唯一 DMC、对照 `die_env`、trit 类流量、HA≥96、装箱失败、4GiB 敏感、相关、Little 驻留、占用 CLAIM。消融 6/3 **assert**。

**不打印：** 绝对 GB/s、H100 数、±15% 硅、周报、Batch A 对照结论、把 `die` 改写成 `/192` 的「修正」主列。

**合格不是：** 平均 BW、打满 18432、\(n_{\mathrm{DMC}}=384\) 同时 die 比 ≥1.5 还记 BW 成功。
