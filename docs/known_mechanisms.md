# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-09-04 (Asia/Shanghai 06:00 routine) — arXiv cs.AR new list for Thu 2026-09-03.

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

## 2026-09-25 additions (cs.AR new list Thu 2026-09-24)

| Slug | Paper | One-line structure |
|---|---|---|
| `lmcxd-chunk-aware-cxl-ssd-kv` | [2609.26828](insights/2609.26828.md) | CXL-SSD co-designed for LLM prefix KV: chunks as device-visible I/O units, NAND→DRAM progress exposed to serving engine, device DRAM as GPU-readable source buffer + windowed/layerwise prefetch under limited device DRAM |
| `mvp-motion-speculative-vision` | [2609.27706](insights/2609.27706.md) | ISP-embedded MV predictor + motion-domain default path; full backend inference as periodic non-blocking drift correction; optional frontend sampling scale-down under stable motion |

### Rejected this scan (not indexed)

26824 FINN-Tro (security exploit / HW Trojan on FINN dataflow); 26829 AI datacenter HW survey; 26830 four-level LLM-circuit eval/validation tool; 27319 XOR-LLC decompression-latency covert channel; 27437 Mamba kernels mapped onto existing programmable CGLA (diagnostic, no new µarch); 27438 memory-polynomial DPD mapped onto IMAX CGLA (mapping); 27453 BitNet on CGLA via OP_SMA4 (existing CGLA + thin ISA mapping, not new datapath); 28358 MicroQonv (software tensor reorder / channel-batch-first im2col for microscaling, no new µarch); Cross 26970/27162/27300/27456; Replace 2509.21762 Penrose + 2609.22743 TEMPO (already ingested).
