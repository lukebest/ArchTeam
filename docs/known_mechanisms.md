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

## 2026-10-08 additions (cs.AR new list Wed 2026-10-07)

| Slug | Paper | One-line structure |
|---|---|---|
| `trail-pte-embedded-delta-tlb-prefetch` | [2610.08483](insights/2610.08483.md) | Temporal TLB prefetcher storing a few signed inter-region deltas (e.g., 4×18-bit + 2-bit confidence per 32 KB region) in unused bits of leaf PTEs; 64-entry per-PC table pairs consecutive page-table walks from the same instruction to record deltas into the source region's PTE block; payload arrives with the PTW's cache block at no extra memory access and drives pre-walks into L2 TLB/prefetch buffer + cache hierarchy; OS-managed mirror table fallback when no free bits (MICRO 2026; ETH/SAFARI; Virtuoso+Sniper) |
| `svrf-scalarized-vector-regfile` | [2610.07078](insights/2610.07078.md) | Dedicated scalar register file inside a long-vector VPU: rename-stage redirection of scalar-semantics vector results (broadcast/scalar move, scalar-indexed gather, reductions) to narrow storage with on-demand lane broadcast, avoiding full-width physical vector register allocation; ISA-compatible RVV 1.0, VLEN up to 16384 bit, RTL to physical implementation (BSC) |
| `dynacore-shape-adaptive-systolic` | [2610.07443](insights/2610.07443.md) | Systolic array whose minimum efficient tile m×n×k is reshaped at runtime: asymmetric width/height trade at fixed PE count (32×32 → 1×1024 per core) for weight-delivery-heavy decode, Split-K folding partial sums over existing array links via tick–tock forward/accumulate, phase-disaggregated quantization (prefill W8A8 / decode W4A16) on an inner-product mixed-precision datapath with precision-invariant output width, per-batch MEU scheduler from offline profiles (Duke) |

### Rejected this scan (not indexed)

- 2610.06905 ElecSafety: **LLM safety benchmark** for MCU boards; no mechanism
- 2610.06937 FAPO: **FPGA technology-mapping / EDA**
- 2610.07029 ReRAM PIM fault-vulnerability study: **fault-injection characterization** (TR 2025 reprint); no new mechanism
- 2610.07094 Enterprise GenAI inference-compute framework: **sizing / methodology**
- 2610.07191 Agentic DSE for HW config + mapping: **DSE tooling**
- 2610.07301 Banded SpMM FPGA pipeline for Longformer: **narrow FPGA datapath** (implicit-index row storage + adder trees) at 100 MHz; below mechanism bar for this scan
- 2610.07600 Clock-tree realizability via Benders cuts: **EDA / optimization**
- 2610.07668 CACHEFORGE: **LLM-driven policy-search framework** (ChampSim loop); framework, not a stated hardware mechanism
- 2610.07685 CHiRP: **archival repost of MICRO 2020** TLB replacement paper; not new
- 2610.08186 gem5-CIMD: **simulation framework**
- 2610.08190 Degradation-balanced manycore scheduling: **OS scheduling policy**, no new microarchitecture
- 2610.08373 ECO: **configuration search / Bayesian optimization** for AFD serving
- 2610.08378 Lachesis: **software placement layer** (HBM vs HBF by KV lifetime); system paper without new microarchitecture
- 2610.08502 X-OPM: **power-modeling methodology**
- 2610.08688 RISC-V edge-transformer ISE framework: **ISE derivation flow**; single AGU custom instruction, not a new structure

Cross (policy skip): 2610.07489 / 07593 TRANSIT / 07644 hyperscaler NIC lessons / 07820 / 08301 Zeppelin / 08372 vTen / 08444 ActTune / 08457. Replacement (policy skip): 2605.18612 / 2610.02236 / 2610.06475 Terracotta (already indexed 2026-10-07).

Conference lists: ISCA 2026 / ASPLOS 2026 full programs unchanged vs 2026-10-06 (md5 129a94cb / 8cba7b89); MICRO 2026 (micro59) program changed only in logistics, one title wording ("L2 Partition Locality" → "L2 Domain Locality") and Trail's author line — no new papers; HPCA 2026 186-byte stub. Trail (2610.08483) matches a MICRO 2026 program entry.
