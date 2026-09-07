# Known mechanisms (literature-intelligence index)

Novelty-check index for design-verification. Slugs may name mechanisms; problem clues elsewhere must not.

Last scan: 2026-09-08 (Asia/Shanghai 06:00 routine) — arXiv cs.AR new list for Monday, 7 September 2026.

## 2026-09-08 additions

| Slug | Paper | One-line structure |
|---|---|---|
| `cim-timedomain-analog-softmax` | [2609.04266](insights/2609.04266.md) | 128-way CIM attention softmax: shared falling ramp + comparator score→time + RC-decay exp sampling + in-circuit normalize; T set by SR and τ, not weak-inversion MOS |
| `flexposit-fractional-bitserial-systolic` | [2609.04724](insights/2609.04724.md) | Bit-serial systolic LLM array with SerialPosit/per-column decode, unified PEs, GPCU fractional precision (~4–8b) under channel-wise scale regularity |
| `tetrisq-phonon-barrier-qec-tiling` | [2609.05226](insights/2609.05226.md) | Planar-mesh qubit tiling with permeable substrate phonon barriers + interleaved rotated surface-code patches to break radiation spatial correlation |

## Rejected this scan (not indexed as mechanisms)

Mon 2026-09-07 new/cross: Budgeting Bytes (roofline/measurement, no new microarch), MonoMoE (GPU software megakernel), HCST (software training under variation), KV low-rank attention adaptation (algorithm/adapter), Huawei τ thermal note (position/commentary), passive-cooling DVFS scheduler (software on Pi 5), EOSQR approx square-rooter (incremental approx arithmetic unit), TreeFI (statistical FI tool), APEX-RBD (mixed-precision DSE framework), proton irradiation characterization of Tensil (measurement, no new mechanism), QuantumEvo BDD ordering (LLM heuristic/tool). Replacements skipped (incl. 2609.04040 already selected 2026-09-05).

## Conference lists

ISCA 2026 program already concluded (Jun 27–Jul 1); no 24h list delta. MICRO 2026 (Athens, Oct 31–Nov 4): author notify Jul 7, camera-ready Sep 11 — public accepted-papers program still not posted. HPCA 2027 notify Nov 6, 2026. ASPLOS 2027 September cycle deadline Sep 9, notify Dec 21. No conference-only picks this run.

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
