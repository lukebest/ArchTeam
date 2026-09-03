# models/

Tier 2 first-principles analytical specs and occupancy models.

**This tree is Batch A only.** Each card has its own directory. There is no joint ranking and no `SUMMARY.md`.

| Path | Card | Files |
|------|------|--------|
| `models/P-0101/M-3/` | 层次正交放置 | `spec.md`, `model.py` |
| `models/P-0103/M-1/` | MRFI | `spec.md`, `model.py` |
| `models/P-0103/M-5/` | B3CSH | `spec.md`, `model.py` |
| `models/P-0105/M-4/` | SNS | `spec.md`, `model.py` |
| `models/P-0106/M-5/` | AffineRebind | `spec.md`, `model.py` |

Not in this batch: `P-0103/M-4` CR-MRDR.

Envelope TEAM-SPEC: `team-384dmc-18432bank`. Bench name: `team-interleave-microbench`.

Run (stdlib only): `python3 models/<P>/<M>/model.py`.
