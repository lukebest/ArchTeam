# P-0198/M-2 CSR — Tier 3 cycle-level sim

Rendezvous–Grant collective spine on DV200 bufferless CHI+RBRG.
**Own tree only.** Do not mix with M-1 CBC (T3 淘汰, PR #62/#64) or M-5 CRRF.

```bash
python3 sims/P-0198/M-2/sweep.py --mode smoke --seed 20260903
python3 -m pytest sims/P-0198/M-2/tests
```

Seed **20260903**. T2 files are draft PR #66 (not landed here).
Signed pins: PR #68. card-claim bands are **NOT measured**.
