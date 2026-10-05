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

## 2026-10-06 additions (cs.AR new list Mon 2026-10-05)

| Slug | Paper | One-line structure |
|---|---|---|
| `rapid-migration-cell-row-parallel-pum` | [2610.02502](insights/2610.02502.md) | DRAM subarray with periodic dual-port migration cells bridging adjacent bitlines (paired offsets) + edge inversion cells (BLSA complement side); row shift/broadcast/invert → Kogge–Stone prefix add (power-of-two shifts + MAJ) and carry-save multiply on row-major bit-parallel data; compiler co-selects bit-serial vs bit-parallel layout; 5.9× vs SIMDRAM claim |
| `peek-privileged-hped` | [2610.03045](insights/2610.03045.md) | Heterogeneous parallel error detection (OoO big core + little checker cores, RCP segments + load-store log) extended to privileged mode: CSR Extraction Controller for online partial CSR snapshots, shadow registers + context-switching unit for hardware trap repetition, proactive OS-lock contention resolution; Linux 6.7 on U280, 28 nm tape-out; MICRO 2026 |

### Rejected this scan (not indexed)

- 2610.02228 Compression-tree generation: **EDA / datapath generator** (weighted bit heap, delay-aware CSA tree); methodology, not a runtime microarchitecture mechanism
- 2610.02229 FlashAttention on Blackwell: **GPU kernel software** (fixed-shift softmax, persistent scheduling in Triton TLX)
- 2610.02233 Budgeted Cache Repair: **LLM serving algorithm** (KV reuse row recompute); no hardware
- 2610.02235 CORE: **KV-cache compression algorithm**; no hardware
- 2610.02236 GPX: **software compression system** (CPU/GPU codec pipeline)
- 2610.02240 ABFT bfloat16 checksum calibration: **characterization study**; no mechanism
- 2610.02241 Hardware-native joint sparse-quant MoE: **algorithm + GPU kernel** on existing SpTCs; no new microarchitecture
- 2610.02288 AdaptViT: **deployment pipeline** (runtime-configurable binaries) with minor ISA extension; primarily software
- 2610.02401 Backside clock mesh DSE: **physical design DSE** for 2 nm BSPDN; no architecture mechanism
- 2610.03061 MCM GPU divide and conquer: **design-space study** of chiplet count/topology; no new mechanism
- 2610.03219 Repository-level RTL repair: **EDA / LLM tool**

Cross (policy skip): 2610.02333 superconductor retiming (EDA) / 2610.02713 WakeKV (KV residency policy, software) / 2610.03260 distributed quantum multi-compilation / 2610.03562 secure dToF LiDAR SoC (circuit). Replacement (policy skip): 2510.07304 Cocoon / 2605.24461 100 MW AI cluster / 2609.13546 WISER.

Conference lists: ISCA 2026 / MICRO 2026 (micro59) / ASPLOS 2026 program pages byte-identical to 2026-10-04; HPCA 2026 program page reachable (past conference, static). No fresh 24h delta.
