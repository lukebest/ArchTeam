# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-09-22 (Asia/Shanghai 06:18) — arXiv cs.AR new list for Mon 2026-09-21 (weekend Sat/Sun still no separate batch; prior content coverage through Fri 2026-09-18).

## 2026-09-22 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `cardan-moe-hybrid-vq-lr-multengine` | [2609.21137](insights/2609.21137.md) | Hybrid VQ + shared low-rank expert weights; multi-engine STA dataflow overlaps DMA with expert-common/private phases |
| `comet-cache-ec-rdma-tracking` | [2609.21774](insights/2609.21774.md) | FPGA NIC cache-based loss tracking for multi-path erasure-coded RDMA; state scales with inter-path jitter not end-to-end BDP |

## Rejected this scan (not indexed as mechanisms)

- 2609.21264 XDNA FlashAttention programming / IRON+MLIR-AIR case study (compiler/tools; no new microarch)
- 2609.21697 Integrating ALS into approximate HLS (EDA/synthesis)
- Cross skipped: 2609.21157 (agents+HLS chip design), 2609.19639 (quantum architecture blueprint)
- Replacements skipped: 2512.10089 Chipstitch, 2601.01158 FLAMENCO, 2609.09800 HBFSim, 2609.11288 Bio-inspired AIMC Part 2, 2609.18022 VeriBugBench, 2609.18792 HCL MXFP4, 2609.19206 Epic, 2503.15770 metalens depth (non-AR primary content)

## Conference lists

ISCA 2026 / MICRO 2026 / HPCA 2026 / ASPLOS 2026 public program pages checked — no fresh 24h accepted-paper or program delta (ISCA 2026 already held Jun–Jul 2026; MICRO 2026 author notify Jul 7 / camera-ready ~Sep 11; HPCA/ASPLOS programs long-static). No conference-only picks.

## 2026-09-20 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `meshkv-noc-kv-fabric` | [2609.19207](insights/2609.19207.md) | Affine KV home striping + verified-dup multicast + credit-aligned prefetch/matmul/softmax overlap on lightweight NoC |
| `mix-inverted-microscaling` | [2609.19683](insights/2609.19683.md) | Micro-inverted scaling (per-element exponents, shared mantissa) + MiX-MX dual-format; shifter-based PE |
| `positmac-multispec-quire` | [2609.19859](insights/2609.19859.md) | Rebalanced Posit32/64 MAC pipeline; Booth-4×KS multiply; Multispeculative Adder for quire accumulate |

## Rejected this scan (not indexed as mechanisms)

- 2609.19169 SiliconBench (bench)
- 2609.19189 CovR (verification/RL tool)
- 2609.19206 Epic (ISC programming/compiler stack, no new microarch)
- 2609.19998/19999 PFAL waveform evaluation
- 2609.20315 FE parametric fault spectral detection (test method)
- Cross skipped
- Replacements skipped

## Conference lists

ISCA 2026 / HPCA / ASPLOS public pages checked — no fresh 24h program delta. MICRO 2026 full public accepted list still not published (MiX notes MICRO 2026 accept on arXiv, not a conference-list delta). No conference-only picks.

## 2026-09-18 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `reqap-mixedprec-swar-msb` | [2609.17555](insights/2609.17555.md) | Sensitivity mixed-precision + compile-time heterogeneous SWAR packing into fixed registers; MSB replicas in slack + majority vote |
| `ward-vit-split-modes` | [2609.17556](insights/2609.17556.md) | Channel-wise dual isolated ViT subnets; FP/LP/HR/AD mode scheduling on FPGA accelerator; reliability-scoped continual learning |
| `hbflex-full-hbf-kv` | [2609.18675](insights/2609.18675.md) | Full-HBF LLM mem: plane-aware KV place/schedule + windowed writeback + lifetime pack/deferred GC; base-die SRAM |

## Rejected this scan (not indexed as mechanisms)

- 2609.17569 Lyapunov functional-stability analysis (theory; no new microarch)
- 2609.17730 FAME (FPGA approx-multiplier evaluation platform + retraining; tool)
- 2609.17922 LoRD RTL-Trojan gate-level localization heuristics (detection method)
- 2609.18022 VeriBugBench (RTL debug benchmark construction framework)
- 2609.18662 Automated GPU ISA encoding synthesis (EDA/encoding DSE tool)
- 2609.18792 HCL QoR study on fixed MXFP4 microarch (language comparison; no new microarch)
- 2609.18846 Locus (elliptic-curve PADD hardware generation/DSE framework)
- 2609.18946 Rect3D (3D-IC rectilinear floorplanning CAD)
- Cross skipped: 2609.17562, 2609.17786, 2609.17903, 2609.18994, 2609.19111
- Replacements skipped: 2607.08427, 2609.17057, 2604.19855, 2609.09990

## Conference lists

ISCA 2026 program page static — no 24h delta. MICRO 2026 full public accepted-paper list still not published. HPCA 2027 notify ~2026-11-06. ASPLOS 2027 Sep cycle notify ~2026-12-21. No conference-only picks.

## 2026-09-17 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `wmha-diffusion-vliw-dualdot` | [2609.16244](insights/2609.16244.md) | VLIW 4-engine sequencer (systolic + vector + dual DMA); weight-stationary 16×16 dual-dot (FP8/BF16); single-pass online-softmax attention |
| `scalelut-parallel-lut-sr` | [2609.16508](insights/2609.16508.md) | Fully parallel configurable LUT SR: YUV + power-of-two kernels/rotation ensemble; deep pipeline / massively parallel lookup; zero-DSP FPGA |
| `cgra-config-mac-trunc` | [2609.16600](insights/2609.16600.md) | Edge CGRA PE: same multiplier+adder as single-cycle ADD/MUL/MAC + 4-mode dynamic truncation readout |
| `optiprime-he-mpc-dataflow` | [2609.16898](insights/2609.16898.md) | HE-MPC private inference: denser-output conv HE protocol + lightweight plaintext compression + reuse-centric intermediate-ciphertext dataflow |
| `budgeted-express-mesh` | [2609.17057](insights/2609.17057.md) | Budgeted traffic-aware express links + committed top-K routing from delayed congestion/reservation + XY escape VC |

## Rejected this scan (not indexed as mechanisms)

- 2609.16003 DT-RAID (storage middleware / software-defined tiered RAID — no new microarch)
- 2609.16085 INT8 portability measurement study
- 2609.16358 EBL (FPGA harmonic-estimation framework / app mapping)
- 2609.16363 FSNIC (SmartNIC IDS integrating P4 + existing LogicNets; integration, thin new microarch)
- 2609.16367 FINNAS (FINN-guided NAS/pruning tool)
- 2609.16729 SpecLens (LLM Verilog codegen / EDA)
- 2609.16742 Carry-Through Checksum (ABFT algorithm on embedded GPU, not microarch)
- Cross skipped: 2609.16787 Nested BSP/vN, 2609.17123 CFET thermal AI agent, 2609.17399 SCHERI
- Replacements skipped: 2604.05012, 2609.13285, 2609.14845, 2511.06605

## Conference lists

ISCA 2026 program final — no 24h delta. MICRO 2026 full public accepted list still not published (some MICRO 2026 accepts appear on arXiv, e.g. OptiPrime, but that is not a conference-list delta). HPCA 2027 notify ~2026-11-06. ASPLOS 2027 Sep cycle notify ~2026-12-21. No conference-only picks.

## 2026-09-16 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `arborist-fmt-motion-accel` | [2609.13420](insights/2609.13420.md) | FMT*-family substrate: inter-tree toolbox, KD-tree NN, multi-bank parallel query, look-ahead engine + in-order commit |
| `bss2-chiplet-unified-in` | [2609.13563](insights/2609.13563.md) | Routing-chiplet 2D mesh; spike + secured non-event multiplexed on wide parallel D2D; class-aware reliability |
| `neuroflex-element-ann-snn` | [2609.14092](insights/2609.14092.md) | Dual ANN/SNN sparse PEs; lossless element-level mode assign; shared bitmap FiberCache; offline cost scheduler |

## Rejected this scan (not indexed as mechanisms)

- 2609.13153 DVFSLM (mobile SLM runtime DVFS governor / estimators — no new microarch)
- 2609.13161 PDD (cross-datacenter PD disaggregation serving system)
- 2609.13166 NPU Hardware Evaluation v1.0 (white-paper bench / evaluation)
- 2609.13285 Grouped Value Attention (attention/KV algorithm + planned kernels; no new microarch)
- 2609.13311 SIMT lockstep UVM methodology (verification tool/methodology)
- 2609.14643 BigMoMo (mobile MoE speculative offload runtime)
- 2609.14845 Accurate Models of AMD Matrix Cores (numerical HW models)
- 2609.15311 FlashGPU-sim (GPU simulator)
- 2609.15318 LLM BDD / FV Gherkin workflow (EDA/formal workflow)
- 2609.15636 Trillion-Parameter MoE in a Box (HBF/DRAM provisioning DSE; no new microarch claim)
- Cross-lists skipped (11): WISER, BOOST, in-sensor compression, TCP-SYN FPGA, NAQsim, MDL time-series, FastPair, event-driven GNN processor, memristive STDP synapse, DeepSeek-V4-Flash gfx90a eng, Cnuas twin
- Replacements skipped (8)

## Conference lists

ISCA 2026 program final — no 24h delta. MICRO 2026 full public accepted-paper list still not published (author notifications earlier; camera-ready ~2026-09-11). HPCA 2026 program already public/static; HPCA 2027 notify ~2026-11-06. ASPLOS 2027 Sep cycle notify ~2026-12-21. No conference-only picks this run.

## 2026-09-15 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `vortex-systolic-vq-sparsity` | [2609.12208](insights/2609.12208.md) | Systolic-compatible VQ lookup/vector unit + dual prefill/decode flows; on-the-fly KV VQ; codebook-aligned contextual sparsity |

## Rejected this scan (not indexed as mechanisms)

- 2609.11938 Operator Profiler (hardware-attribution profiling pipeline / tool)
- 2609.11939 Adaptive multi-exit TinyML on GAP9 (CNN early-exit software scheme on existing SoC; COINS; no new microarch)
- Cross 2609.12075 Robion (VLA multi-GPU serving/management system)
- Cross 2609.12923 Hopper SM-utilization dissection (measurement/analysis)
- Replacements skipped: 2604.04750 DeepStack (DSE/model), 2609.06691 Gutenberg

## Conference lists

ISCA 2026 program final — no 24h delta; MICRO 2026 full public accepted list still not out; HPCA 2027 notify 2026-11-06; ASPLOS 2027 Sep cycle notify ~2026-12-21; no conference-only picks.

## 2026-09-13 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `reach-hbm-inner-outer-ecc` | [2609.10861](insights/2609.10861.md) | Controller inner 32 B decide + exceptional long-span known-erasure; differential parity; co-designed endpoint |
| `beacon-pathology-ai-plus-x` | [2609.11044](insights/2609.11044.md) | Systolic AI chiplet + flexible PE datapath/RF; aggregation, load-balance, Euclidean, binning, counters |
| `cheri-d-reincarnate-objid` | [2609.11590](insights/2609.11590.md) | Reincarnate slots under new IDs (quarantine IDs); large-object ID modes; ObjID reverse-map/filter coherence |

## Rejected this scan (not indexed as mechanisms)

- New: 2609.10970 Fengshui (chiplet/accelerator co-design framework)
- New: 2609.11288 Bio-inspired AIMC Part 2 (technical note / TLM demo, no new microarch claim this paper)
- New: 2609.11392 PATTON (PIM runtime/system, no PU microarch changes)
- New: 2609.11906 AccelForge (modeling/co-design framework)
- Cross (not primary new): HermiCache, Entwine, PHAT, Grid-to-Chip power perspective, time-based memristive SNN readout
- Replacements skipped: 2512.07312, 2609.07907, 2509.24425

## Conference lists

ISCA 2026 program page static (no 24h delta). MICRO 2026 public accepted-paper list still not found. HPCA 2027 / ASPLOS 2027 notification windows not producing new public accept lists in past 24h. No conference-only picks.

## 2026-09-11 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `shift-accumulate-attention-pot-k` | [2609.09208](insights/2609.09208.md) | Signed PoT key cache; QK⊤/AV as shift-accumulate; fused CUDA; DS4A ISA gap |
| `dssa-2048-fc-annealer` | [2609.09559](insights/2609.09559.md) | 28nm 2048-spin FC DSSA; flip-only differential updates; 16Mb SRAM; 16:1 RNG |
| `unison-session-kv-nmem` | [2609.09643](insights/2609.09643.md) | Near-memory session KV scheduler; SPEAR eviction + TIDE idle DMA tiering |
| `tri6-two-turn-routing` | [2609.09746](insights/2609.09746.md) | Degree-6 triangular mesh 1-VC / torus 2-VC+dateline; two forbidden turns |
| `amend-gpu-pim-audit-sparse` | [2609.09823](insights/2609.09823.md) | History-margin sparse mask; GPU survivors ∥ PIM audit of omitted KV blocks |
| `sage-semantic-geo-recovery` | [2609.10126](insights/2609.10126.md) | Class-H/M/L semantic replay eligibility + geographic checkpoint intervals |
| `fhe-adaptive-hks-klss-fpga` | [2609.09423](insights/2609.09423.md) | U280 FHE accel; memory-efficient KLSS datapath; runtime HKS↔KLSS select |

## Rejected this scan (not indexed as mechanisms)

- 2609.09344 Academia×Industry AI-native silicon (position)
- 2609.09519 HLSFactory-Agent (dataset/tool)
- 2609.09526 HLS-Eval agentic benchmark (tool)
- 2609.09800 HBFSim (simulation platform/tool)
- 2609.10347 CertiFlash (FTL formal verification framework)
- Cross: 2609.10515 PASCAL (shared-cache analytical model), AutoTrans (EDA assertion translation), chem/SP/security-bench cross-lists
- Replacements skipped

## Conference lists

ISCA 2026 program already final — no 24h delta. MICRO 2026 public accepted-paper list still not published (camera-ready deadline 2026-09-11). HPCA 2027 notification 2026-11-06. ASPLOS 2027 Sep cycle notification ~2026-12-21. No conference-only picks this run.

## 2026-09-10 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `nvm-kv-fixed-range-quant` | [2609.05764](insights/2609.05764.md) | Dense on-chip NVM 4-bit KV + fixed-range SA refs; static rotation crossbar; digital attention; ~3% norm metadata |
| `cmd-cgra-cluster-memory` | [2609.05982](insights/2609.05982.md) | CGRA cluster-local multi-bank DM + coherence controller; mapper/DSE over cluster size |
| `wafertrans-pte-presence` | [2609.06125](insights/2609.06125.md) | Per-GPU PTE presence directory + domain broadcaster; on-wafer IOMMU-free remote translation |
| `dam-distance-addressable-memory` | [2609.06270](insights/2609.06270.md) | 1T-1R + near-array distance processor; post-process pruning via distance-ordered responses |
| `nova-cim-stochastic-readout` | [2609.07059](insights/2609.07059.md) | Analog CIM column MAC via random-reference 1-bit SA + N-cycle popcount (no multi-bit ADC) |
| `hbf-gr-lru-k-admission` | [2609.07175](insights/2609.07175.md) | HBM4+HBF GR serving; admission-controlled LRU-K decouples KV writes from misses |
| `pegasus-multichip-ising` | [2609.07907](insights/2609.07907.md) | 28nm 4-chip 27648-spin degree-15 Pegasus Ising; scheduled C2C boundary packets |
| `penda-nod-pe` | [2609.08424](insights/2609.08424.md) | PE replaces MAC with subtract-square-accumulate; law-of-cosines inner product |
| `flexspim-digital-cim-snn` | [2609.08446](insights/2609.08446.md) | Digital in-column CIM; flexible weight/membrane resolution; layer-wise hybrid WS/OS |
| `hda-moe-3d-nmp` | [2609.08682](insights/2609.08682.md) | Hybrid TP/EP placement + dynamic/adaptive scheduling + hardware-aware gating on 3D NMP |

## Rejected this scan (not indexed as mechanisms)

- 2609.05960 GPU time-based power analysis (EDA/tool)
- 2609.06157 Splats-to-Silicon 3DGS efficiency rethink (analysis, no new microarch)
- 2609.06781 BLINK BN integrity checkpoints (reliability overlay; no new PE/memory fabric)
- 2609.06796 HT threats to MCPNA (threat survey)
- 2609.08232 history-aware RL dense routing (EDA)
- Cross-lists: RAGMark/GMSBench/QROB/TASTE/etc. tools or non-primary mechanisms
- Replacements skipped

## Conference lists

ISCA 2026 program already final — no 24h delta. MICRO 2026 public accepted-paper/program list still not published (camera-ready ~2026-09-11). HPCA 2027 notification 2026-11-06. ASPLOS 2027 Sep cycle: notification ~2026-12-21. No conference-only picks this run.

## 2026-09-04 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `atlas-hierarchical-gaussian-offload` | [2609.02352](insights/2609.02352.md) | Block-partitioned city-scale 3DGS working set: disk→GPU on-demand + async residency; temporal LoD walk; stereo reuse; left-eye→right-eye line buffer |
| `nova-fefet-nat-training` | [2609.01948](insights/2609.01948.md) | FeFET-calibrated eNVM training crossbar with bidirectional (W / Wᵀ) peripherals; NAT steers weights to stable conductance regions under NL/C2C/D2D |

## Prior (ArchZero PR #11; not yet mirrored here)

See lukebest/ArchZero draft PR for 2609.01084, 2608.30509, 2609.00857, 2609.00450 if importing the earlier index.

Also note draft PRs #27/#28 may still hold later Sep-5/Sep-8 insights until merged.
