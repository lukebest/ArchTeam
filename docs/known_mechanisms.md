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

## 2026-10-03 additions (cs.AR new list Fri 2026-10-02)

| Slug | Paper | One-line structure |
|---|---|---|
| `shatterquant-block-mp-systolic-vit` | [2610.00207](insights/2610.00207.md) | Systolic Transformer accelerator co-designed with intra-tensor block mixed-precision: bit-width ∈ {1,2,4,8} for weights (8-bit acts) sets PE block height/parallelism; block rescaling + on-accel softmax & piecewise-linear nonlinearities; hardware-aware PTQ (block std/sensitivity); TSMC 16nm @ 1 GHz claim |
| `edgedae-fpga-gpu-dae` | [2610.00311](insights/2610.00311.md) | Heterogeneous edge VLA: Jetson Orin Nano runs perception ViT; Kria KR260 pins entire Diffusion Action Expert (weights/scales/LN/schedules) in BRAM/URAM with QLU (INT8 P=128 / NF4-g16 P=64), 4-way Xorshift128+Box-Muller GRNG, DDPM unit @ 250 MHz; ASP-DAC 2027 |

### Rejected this scan (not indexed)

- 2610.00106 SyntheticHLS: **ML-for-CAD / dataset tool** — LLM iterative mutation loop to synthesize diverse HLS training corpora; no new accelerator microarchitecture
- 2610.01186 From Physical Devices to RTL Models: **position / foundations** essay on abstraction & validation disciplines; no mechanism
- 2610.01603 U-Sonic: **domain open-source IP** — 8-ch ultrasound TX pulser peripheral in 130 nm RISC-V SoC; programmable bursts behind OBI, but no novel CS.AR microarchitecture beyond open pulser packaging
- 2610.01623 Multi-Wire SPI Readout: **communication IP / tool** for wearable US FPGA↔MCU payload path; no new microarchitecture mechanism
- 2610.01867 ZTA-Q: **platform / operator-support extension** of ztachip — TFLite INT8 per-channel post-MAC requantization datapath + accuracy ablation; incremental datapath, not a substantial new accelerator mechanism
- 2610.01918 Timing-Driven Logic Remapping: **EDA tool** — MILP local remapping with physical context after placement; no runtime microarchitecture
- 2610.01975 CONFERM: **CGRA mapper / compiler** — recurrence-aware temporal mapping for multi-context CGRAs; no new hardware fabric
- 2610.02121 Catscan: **visualization / tooling** — open event-stream viewer for CPU performance simulation pipelines

Cross (policy skip): 2610.00281 Vulnerability-Weighted Routing (eess.SY primary) / 2610.00738 Q-MINO quantization-aware training (math.OC primary) / 2610.01477 ALFRED mobile manipulator (cs.RO primary) / 2610.01602 Live-Reconfigurable Multi-Mode Wearable Ultrasound (eess.SP primary). Replacement (policy skip): 2608.24637 Thermal Tuning Stalls in Wafer-Scale Optical Interconnects / 2512.04705 Early-Exit NN co-opt for multi-core. Thu 2026-10-01 list (NDS 2609.38454) not re-screened.
