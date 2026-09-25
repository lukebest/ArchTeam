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

## 2026-09-26 additions (cs.AR new list Fri 2026-09-25)

| Slug | Paper | One-line structure |
|---|---|---|
| `vq-lic-shared-dw-pw-vq` | [2609.29727](insights/2609.29727.md) | Resource-constrained FPGA LIC: reusable INT8 DW/PW engine pair for analysis transform; multi-codebook VQ codeword scoring mapped as dot products onto the same PW MAC array (no separate VQ compute array); RTL cycle-count latency model (read/DW/PW/write) sizes geometry and shared-engine VQ cost; table-driven rANS on PS; reconstruction offloaded to cloud decoder |

### Rejected this scan (not indexed)

28717 HeteroReason (FPGA-GPU system placement + backtracking/step-ahead scheduling for speculative reasoning; p.1–3 no new FPGA datapath/µarch fabric); 28769 Xtrace (GPU intra-kernel tracing tool / binary probe splicing); 28904 NTT-on-CGLA (ML-KEM NTT mapped onto existing programmable CGLA, mapping/eval); 29246 HBF-Sim (HBF simulator / tool, not new µarch); 29563 NDN certified fast-path coverage (offline placement/certificate formulation under HW budget model; no synthesized µarch claim); 29619 CAGE (algorithm-engineering / coverage-selection regimes); 29629 PANEM (heuristic DRAM latency model for simulation); 29965 EZ130 student standard-cell library (education/tapeout narrative); 30099 EAAC (compiler–HW co-design prototyping framework / tooling); 30131 LLM4PDR (LLM-guided word-level PDR verification tool). Cross 29267 MagiCFirm / 29480 quantum BAT / 29648 Albireo / 29681 SPEC RRR skipped; Replace 2608.22110 ANE weight-encoding skipped.
