# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-09-10 (Asia/Shanghai 06:00 routine) — arXiv cs.AR new list for Wed 2026-09-09.

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
