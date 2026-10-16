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

## 2026-10-07 additions (cs.AR new list Tue 2026-10-06)

| Slug | Paper | One-line structure |
|---|---|---|
| `terracotta-programmable-dram-mc` | [2610.06475](insights/2610.06475.md) | One-time standardized DDR5 custom-command envelope in reserved encodings (operation type / target locality / payload; vendor-defined semantics, no new pins) + post-silicon programmable memory controller built from state / trigger / update / action primitives; deploys PuD, maintenance, SALP, latency-reduction techniques by configuration and composes them (MASA + ChargeCache); >96% of custom benefit, 0.03% area / 0.56% TDP claims (Ramulator 2.0 + DRAMPower; ETH/SAFARI) |

### Rejected this scan (not indexed)

- 2610.03971 LLM-based HLS repair benchmark: **EDA / LLM benchmark**
- 2610.04808 Alkaid: **compiler / HLS-RTL generator** for ultra-low-latency kernels; no new microarchitecture
- 2610.05037 SparseCraft: **agentic DSE loop** over Gemmini RTL; methodology/tooling, generated design not a stated new mechanism
- 2610.05062 VLA workload characterization: **characterization study**; no mechanism
- 2610.05112 Asynchronous-circuit HLS ASIC flow: **EDA flow**
- 2610.06148 RL-based workload-aware PDN optimization: **physical design / EDA**

Cross (policy skip): 2610.03934 SGAnalog / 2610.04396 JASPER / 2610.04957 Trinity / 2610.05380 VHDL-REPOBENCH / 2610.05554 RetainZ / 2610.05559 Cut BCE / 2610.06138 graph sparsification FPGA. Replacement (policy skip): 2604.07387 / 2605.24022 / 2608.24637 / 2609.06270 / 2609.14643 / 2609.22743 TEMPO / 2508.12021 / 2604.21566 / 2609.39131.

Conference lists: ISCA 2026 / MICRO 2026 (micro59) / ASPLOS 2026 returned "One moment, please" anti-bot pages; HPCA 2026 returned a 186-byte stub. No confirmed 24h delta.
