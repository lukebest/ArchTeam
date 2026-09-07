# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-09-08 (Asia/Shanghai 06:00 routine) — arXiv cs.AR new list for Monday, 7 September 2026.

## 2026-09-08 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `cim-timedomain-analog-softmax` | [2609.04266](insights/2609.04266.md) | 128-element analog softmax peripheral: shared falling ramp + comparator score-to-time + RC-decay exp sampling + in-circuit normalize; T via ramp slope and RC τ, not weak-inversion MOS |
| `flexposit-fractional-bitserial-systolic` | [2609.04724](insights/2609.04724.md) | Unified bit-serial systolic: per-column rescale + SerialPosit decode + unified PEs + GPCU treating weight precision as a fractional ~4–8 bit knob under channel-wise regularity |
| `tetrisq-phonon-barrier-qec-tiling` | [2609.05226](insights/2609.05226.md) | Planar-mesh tiling: permeable substrate phonon barriers on tile edges + spatial interleave of independent rotated-surface-code patches; no extra QEC round/decode time |

## Rejected this scan (not indexed as mechanisms)

Mon 2026-09-07 new/cross: Budgeting Bytes, MonoMoE, HCST, KV low-rank adaptation, Huawei τ note, DVFS scheduler, EOSQR, TreeFI, APEX-RBD, proton Tensil characterization, QuantumEvo; replacements skipped.

## Conference lists

ISCA 2026 concluded; MICRO 2026 public accepted list not posted; HPCA 2027 notify Nov 6; ASPLOS 2027 Sep cycle deadline Sep 9 / notify Dec 21; no conference-only picks.

## 2026-09-05 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `prefetch-confidence-regularity-admission` | [2609.04040](insights/2609.04040.md) | Predictor-agnostic prefetch admission: median prediction-error confidence window + dominant-delta regularity histogram; matched wrap over MLP or stride; gate-closed ≡ no-prefetch |
| `time-encoded-analog-photonic-interposer` | [2609.03125](insights/2609.03125.md) | Chiplet analog photonic interposer: amplitude→timing edge on WDM MRR (implicit ~6-bit, one λ/PE) between IPC sensor and analog accelerator; no digital codeword/SerDes |

## 2026-09-05 rejected (archived)

Fri 2026-09-04 new/cross: LevelSyn (EDA/GNN synthesis), systolic FP32 Givens-QRD MVDR FPGA (app datapath, no new general microarch), RACE-AIMC (statistical selective ensemble, not new HW), FlowTT (GPU TT embedding runtime), LeanGRPO (diffusion RL training), AI-assisted PQC accelerator case study (design-process/crypto methodology), Mesh-Native TCAD GAT surrogate (EDA/ML tool).

## 2026-09-05 Conference lists (archived)

ISCA 2026 / MICRO 2026 / HPCA 2026 / ASPLOS 2026 public programs checked 2026-09-05; no fresh list delta in the past 24h. No conference-only picks this run.

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
