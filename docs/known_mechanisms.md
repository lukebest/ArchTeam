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

## 2026-09-30 additions (cs.AR new list Tue 2026-09-29)

| Slug | Paper | One-line structure |
|---|---|---|
| `morphatt-svit-cascaded-mhsa` | [2609.33207](insights/2609.33207.md) | Digital SViT MHSA accelerator: cascaded SpikeQKV (3-way Q/K/V pipelines + SpikeGen/RepConv/Head Separator) → SpikeAtten (QKV reorder O(N²D)→O(ND²)) → RepConv; specialized inter-module QKV/Data buffers cut global on-chip memory congestion; LIF τ=2 → right-shift |
| `interp-bytecode-lookahead-dispatch` | [2609.34263](insights/2609.34263.md) | ~1.3 KB bytecode lookahead engine ahead of pipeline: SW metadata table (Length/Type/HandlerPCLo) + BR.DISP supplies interpreter dispatch targets via BTQ; sequential bytecodes advance vPC by Length; control-transfer bytecodes reuse BPU indexed by vPC with separate BGHR; ~50 LoC CPython |

### Rejected this scan (not indexed)

- 2609.33184 SpecStream: long-context speculative-decoding **serving system** (KV offload streaming + Draft/Target co-schedule on GPU); no new microarchitecture primitive
- 2609.33619 S-ALSA: MRAM **circuit/device** sense-amp + balanced 4T-2MTJ bit-cell (ISVLSI); not microarchitecture mechanism
- 2609.34351 PolyCIM: **polyhedral compiler/mapping** for digital CIM array utilization; no new CIM microarchitecture
- 2609.34452 C2FPlace: **EDA macro placement** (evolutionary search); pure physical-design tool
- 2609.34612 SPIMOE: hetero SRAM-PIM/HBM-PIM **system co-design/framework** (AFD + routing/scheduling algos) on existing PIM substrates; no new microarchitectural fabric primitive
- 2609.34657 Torch-PIM: **compiler/PGO tool** for host-vs-PIM offload in PyTorch lowering; tool paper
- 2609.35254 MEGATRON: 28 nm PCM CiM + RISC-V NPU **chip tapeout/demo** (TOPS/W, density); measurement vehicle, no new mechanism claim in p.1–3
- 2609.35478 Analog UT damage detector: **NDT/SHM analog sensing** application (NDTonline); out of core arch mechanism scope

Cross (policy skip): 32031 MTJ-CMOS neuron / 32237 Apple M6 FFT-SAR / 33997 QBX quantum compiler / 34785 BEHAVE HW-design agents / 35053 TCitH/Mirath ASIC / 35508 Argus bottleneck localization. Replacement (policy skip): 2510.01730 / 2510.05632 / 2511.10909 / 2605.13210 / 2609.21137 / 2609.10515. Mon 2026-09-28 list (PipeDRAM) not re-screened.
