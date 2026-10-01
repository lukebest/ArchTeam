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

## 2026-10-02 additions (cs.AR new list Thu 2026-10-01)

| Slug | Paper | One-line structure |
|---|---|---|
| `nds-near-data-strands` | [2609.38454](insights/2609.38454.md) | Transparent NDP offload for unmodified binaries: host-side Strand Analysis Engine (Dispatch-time FSM detects two loop patterns; records templates from OoO host runs) + Loop Orchestration Unit (page-aware map of iterations to bank-local in-order NDCores; non-speculative dependence/placement checks; host pause/resume) + introspective higher-ILP micro-op schedules for weak NDCores; explicit eligibility/fallback; PACT ’26 poster extended |

### Rejected this scan (not indexed)

- 2609.38601 PRISM / structure-augmented LLM for HLS pragma optimization: **ML-for-CAD / EDA tool** (AST+CFG+DFG injected into frozen code LLM for pragma suggestion); no new accelerator/interconnect/cache microarchitecture mechanism

Cross (policy skip): 2609.38734 Exact Diagonal Completion / QAOA placement (quant-ph primary) / 2609.39131 Characterizing HBF for LLM serving (cs.LG primary; system characterization + hierarchical storage scheduling) / 2609.39703 STELLA 16nm spatio-temporal elastic CGRA (eess.SY primary — **mechanism-looking but Cross-list, skip**). Replacement (policy skip): 2508.16738 zkPHIRE (HPCA’26) / 2605.15638 ITHICA (MICRO’26) / 2609.09800 HBFSim / 2609.14595 MDL temporal misalignment diagnostic / 2609.16787 Nested Parallel von Neumann / Nested BSP. Wed 2026-09-30 list (Zephyr 2609.37711) not re-screened.
