# T3 report · P-0106/M-5 AffineRebind

Smoke numbers are filled after `sweep.py --mode smoke`. See `results/`.

## Scope

Cycle-accurate CSR + XOR_fold6 + `mod n` + kth-one + card α search. DRAM is 假设 H-DRAM-BB.
T2 is occupancy-only; like-to-like compare is `cls_mean` / `n_bank` / `dead`.
`t2_audit.md` was not in-tree; Dr.Sim + T2 spec were the must-verify list.

## Seeds / CI

SEED=20260903. Trials `SEED+i`. Every BW cell is `mean ± 95% CI (n=trials)`.

## T2 vs T3 occupancy (smoke)

*(filled after smoke)*

Main gain is **modulus 48 → n_live**, not α. On large 2-power, `modn-a1` vs `minimax` occupancy diff must be <5%.
Uniform 25% (`n=36`) still has factor 3 — not a 3-adic test. 3-adic only from the 3-residue-biased column.
`classes_AP = n/gcd(S_g,n)` is sanity; `cls_mean` is XOR_fold6 netlist.

## Discrepancy

If `|T3−T2|/T2 > 30%`: inspect this simulator first. Do not silently pick T2.

## Cycle BW note

Class-count ×3 is not BW ×3. txns/cycle is H-DRAM-BB, not GB/s. μ_d UNKNOWN.
Dead hits must be 0. REPAIR completes before RUN.
