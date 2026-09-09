# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-09-10 (Asia/Shanghai 06:00 routine) — arXiv cs.AR new list for Wed 2026-09-09.

## 2026-09-10 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `interface-aware-kv-nvm-quant` | [2609.05764](insights/2609.05764.md) | Dense on-chip NVM holds 4-bit KV indices behind fixed-range SA references; small static analog crossbar for fixed rotation; attention stays digital; per-vector norm ≈3% metadata |
| `cmd-cgra-cluster-distributed-memory` | [2609.05982](insights/2609.05982.md) | CGRA partitioned into clusters; each cluster shares a multi-bank data memory (banks = cluster size) plus arbiter/coherence; MESI-like coherence controller with varInfoTable; DMA loads at config |
| `wafertrans-iommu-free-va` | [2609.06125](insights/2609.06125.md) | Per-GPU PTE Presence Directory (PPD/cuckoo-style) + Domain Presence Broadcaster; interleaved PTE-PC domains and Local Search Groups so remote VPN→PTE holder is resolved on-wafer without CPU-IOMMU |
| `distance-addressable-memory` | [2609.06270](insights/2609.06270.md) | Distance-Addressable Memory: 1T-1R array + near-array processor computes approximate per-datapoint distances to emit partially ordered responses for post-process pruning/rerank |
| `nova-cim-stochastic-interface` | [2609.07059](insights/2609.07059.md) | Analog crossbar unchanged; column MAC reconstructed by random-reference 1-bit SA + N-cycle popcount instead of multi-bit ADC; row Bernoulli SNG (optional shared LFSR) gates wordlines |
| `2609-07175` | [2609.07175](insights/2609.07175.md) | TBD — full one-line pending follow-up |
| `2609-07907` | [2609.07907](insights/2609.07907.md) | TBD — full one-line pending follow-up |
| `2609-08424` | [2609.08424](insights/2609.08424.md) | TBD — full one-line pending follow-up |
| `2609-08446` | [2609.08446](insights/2609.08446.md) | TBD — full one-line pending follow-up |
| `2609-08682` | [2609.08682](insights/2609.08682.md) | TBD — full one-line pending follow-up |

## Rejected this scan (not indexed as mechanisms)

Wed 2026-09-09 new/cross: 2609.05960 (EDA power), 2609.06157 (3DGS analysis), 2609.06781 (BLINK reliability overlay), 2609.06796 (HT survey), 2609.08232 (EDA routing); cross-list tools; replacements skipped.

## Conference lists

ISCA 2026 final program: no list delta. MICRO 2026 program list not public. HPCA 2027 notify 2026-11-06. ASPLOS 2027 September cycle notify ~2026-12-21. No conference-only picks this run.

## 2026-09-04 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `atlas-hierarchical-gaussian-offload` | [2609.02352](insights/2609.02352.md) | Block-partitioned city-scale 3DGS working set: disk→GPU on-demand + async residency; temporal LoD walk; stereo reuse; left-eye→right-eye line buffer |
| `nova-fefet-nat-training` | [2609.01948](insights/2609.01948.md) | FeFET-calibrated eNVM training crossbar with bidirectional (W / Wᵀ) peripherals; NAT steers weights to stable conductance regions under NL/C2C/D2D |

## 2026-09-04 rejected (archived)

Thu 2026-09-03 new/cross/replace: RunSoC 2.0 (DSE tool), BBYT (EDA timing proxy), FORGE (MCU TTA software), GadIR (quantum compiler IR), dictionary HDL repair (EDA), photonic MoE prefill quantification (no new microarch), space-robotics DPU deployment, H3DNAS (ONNX compression), replacements.

## 2026-09-04 Conference lists (archived)

ISCA 2026 / MICRO 2025 / HPCA 2026 / ASPLOS 2026 public programs checked; no fresh list delta in the past 24h (static accepted-paper programs). No conference-only picks this run.

## Prior (ArchZero PR #11; not yet mirrored here)

See lukebest/ArchZero draft PR for 2609.01084, 2608.30509, 2609.00857, 2609.00450 if importing the earlier index.
