# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-09-23 (Asia/Shanghai) — arXiv cs.AR new list for Tue 2026-09-22 (15 papers; 4 mechanism selected).

## 2026-09-04 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `atlas-hierarchical-gaussian-offload` | [2609.02352](insights/2609.02352.md) | Block-partitioned city-scale 3DGS working set: disk→GPU on-demand + async residency; temporal LoD walk; stereo reuse; left-eye→right-eye line buffer |
| `nova-fefet-nat-training` | [2609.01948](insights/2609.01948.md) | FeFET-calibrated eNVM training crossbar with bidirectional (W / Wᵀ) peripherals; NAT steers weights to stable conductance regions under NL/C2C/D2D |

## Rejected this scan (not indexed as mechanisms)

Thu 2026-09-03 new/cross/replace: RunSoC 2.0 (DSE tool), BBYT (EDA timing proxy), FORGE (MCU TTA software), GadIR (quantum compiler IR), dictionary HDL repair (EDA), photonic MoE prefill quantification (no new microarch), space-robotics DPU deployment, H3DNAS (ONNX compression), replacements.

## Conference lists

ISCA 2026 / MICRO 2025 / HPCA 2026 / ASPLOS 2026 public programs checked; no fresh list delta in the past 24h (static accepted-paper programs). No conference-only picks this run.

## Prior (ArchZero PR #11; not yet mirrored here)

See lukebest/ArchZero draft PR for 2609.01084, 2608.30509, 2609.00857, 2609.00450 if importing the earlier index.

## 2026-09-23 additions (cs.AR new list Tue 2026-09-22)

| Slug | Paper | One-line structure |
|---|---|---|
| `tempo-ordering-tags` | [2609.22743](insights/2609.22743.md) | Per-instruction ordering tags; RC constraints enforced via ROB retirement predicates + merge-buffer tag-ordered store visibility (no drain-serialize / excess load squash) |
| `splash-hbm-hbf-kv` | [2609.23816](insights/2609.23816.md) | Virtualize KV across HBM+HBF behind custom base dies; sparse attention retrieval co-designed with flash page granularity and plane-parallel reads |
| `spectra-reconfig-tiles` | [2609.24847](insights/2609.24847.md) | Runtime-reconfigurable tiles: systolic↔vector-lane PE mode per kernel; dynamic tile count / partition / NoC pattern for speculative-decode phases |
| `kercolle-cta-admission` | [2609.22335](insights/2609.22335.md) | CTA dispatcher tags (TC/ALU/MEM) + per-SM util counters + two-phase admission to break VLM-grid HOL blocking for VLA phase overlap |

### Rejected this scan (not indexed)

22347 VRM position; 22343 PQC NTT on Vortex GPGPU (IP/DSE); 22590 UniCASE format+ECC; 22636 Presage agent prefetch tooling; 22765 VeriSelector LLM data selection; 23116 StreamNTT toolchain bench; 23444 WaveletECO agent EDA; 24270 die-scaling GPU sched characterization; 24288 regenerative-SA CIM (ISCAS circuits); 24757 FINN vehicle NPU case; 24904 multi-kW 3D power delivery; all cross/replacement.
