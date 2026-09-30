# models/

Tier 2 first-principles analytical specs and occupancy models.

Each card has its own directory. There is no joint ranking and no `SUMMARY.md`. Later cards are **not** mixed into Batch A ranking.

## Batch A

**This section is Batch A only.** Do not fold P-0198 or other later cards into Batch A ranking.

| Path | Card | Files |
|------|------|--------|
| `models/P-0101/M-3/` | 层次正交放置 | `spec.md`, `model.py` |
| `models/P-0103/M-1/` | MRFI | `spec.md`, `model.py` |
| `models/P-0103/M-5/` | B3CSH | `spec.md`, `model.py` |
| `models/P-0105/M-4/` | SNS | `spec.md`, `model.py` |
| `models/P-0106/M-5/` | AffineRebind | `spec.md`, `model.py` |

Not in this batch: `P-0103/M-4` CR-MRDR.

Envelope and loads: **负载基线 TEAM-SPEC / 问题 YAML** (table is off-repo / shared disk; not a GitHub path). Bench: `team-interleave-microbench`.

## P-0198 new cards (not Batch A)

New cards. Not mixed with Batch A ranking.

| Path | Card | Files |
|------|------|--------|
| `models/P-0198/M-5/` | CRRF (Channel–Ring Rebind Fabric) | `spec.md`, `model.py`, `insight.md` |

Envelope: DV200 `tests/soc_sim` / `lukebest/bufferless-ring-noc` (**not** team-384dmc, **not** `team-interleave-microbench`).

Run (stdlib only): `python3 models/<P>/<M>/model.py`.
