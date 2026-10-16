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

## 2026-09-24 additions (cs.AR new list Wed 2026-09-23)

| Slug | Paper | One-line structure |
|---|---|---|
| `hbf-hotcold-agentic-kv` | [2609.25782](insights/2609.25782.md) | Hot–cold KV hierarchy inside GPU memory tier: active decode KV in HBM, paused-session cold pool in co-packaged HBF; base-die D2D eviction/prefetch keeps per-step reads on HBM |
| `dsac-ntc-tpu-clocking` | [2609.26644](insights/2609.26644.md) | Per-MAC HD/MSB/Hybrid predictors → three timing tiers; local dummy-hold under fixed global clock + feedback threshold updates (reclaim NTC slack without global DVFS) |

### Rejected this scan (not indexed)

25022 NPLSD (NPU operator adapt / vision detection port); 25335 GRADE-RTL (LLM RTL eval framework); 25624 fused-upcast GEMM cross-GPU determinism (SW kernel fixed reduction order); 25869 Tessera BSA runtime (logical mask ↔ execution SW runtime); 26374 ESupNNet (soft-error supervised net); 26551 Toki (HBM profiling framework/tool); Cross 25637 SLED-IFV, 25873 AgenticSizing; all replacements.
