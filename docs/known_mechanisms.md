# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-10-01 — arXiv cs.AR new list for Wed 2026-09-30.

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

## 2026-10-01 additions (cs.AR new list Wed 2026-09-30)

| Slug | Paper | One-line structure |
|---|---|---|
| `zephyr-snn-flexible-pe-event-mem` | [2609.37711](insights/2609.37711.md) | SNN audio-denoising accelerator: sparsity-aware flexible/heterogeneous PE array (same Hybrid PE time-multiplexed across matrix-mul / pure-add / element-wise mul + Multi-Frame Deep Filtering) + event-driven weight-read memory (active-neuron index → weight addr; skip inactive DRAM/PE); FPGA validate (PYNQ-Z1); HW-friendly SFSN via QAT as co-design enabler |

### Rejected this scan (not indexed)

- 2609.36111 DDR5/LPDDR UVM closed-loop DV: **pre-silicon verification/EDA framework** (SOMA parse, MR-RAL, PHY init); no new memory-controller microarchitecture mechanism
- 2609.36634 CompressedLUT: **lossless LUT compression algorithm + open-source tool** with add/shift reconstruction decoder datapath; contribution is compression/tool flow, not a new accelerator/fabric/cache primitive
- 2609.37021 Clash HDL low-level opts study: **HDL methodology / area overhead experiment** (bit-serial MAC ×16 configs vs Verilog); no new microarchitecture mechanism
- 2609.37399 MEDEM: multi-engine DL accelerator **design methodology / DSE** (engine abstraction + co-design + combination selection); no new microarchitectural fabric primitive

Cross (policy skip): 2609.36074 GEM-KMeans / 2609.36134 HW-aware functional KAN / 2609.36584 analog training co-design / 2609.36731 CHERI linkage compartmentalization / 2609.36752 cktFormer / 2609.37137 mixed-precision scientific computing. Replacement (policy skip): 2604.16007 MemExplorer / 2605.13210 PoisonCap / 2609.11044 BEACON / 2609.11938 HW-attributed PyTorch profiling / 2609.30998 PipeDRAM (already ingested 2026-09-29) / 2606.23742 analogue NN. Tue 2026-09-29 list (MorphAtt / InterpBytecodeLookahead) not re-screened.
