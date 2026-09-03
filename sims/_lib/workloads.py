"""Synthetic team-interleave-microbench stand-in.

No in-repo trace exists. Addresses are an arithmetic progression
    phys[i] = base + i * stride
with W=2^33, grain=512 B, issued I = first min(K, Q_tot, n_pts) points.
SEED default matches T2 (20260903).
"""

from __future__ import annotations

from typing import Iterator

W = 1 << 33
GRAIN = 512
Q_TOT = 120 * 128
SEED = 20260903

SNS_STRIDES = (
    ("2MiB", 2 * 1024 * 1024),
    ("1MiB", 1024 * 1024),
    ("512KiB", 512 * 1024),
    ("4608B", 4608),
    ("512B", 512),
)

AFFINE_DOC = (
    ("512B", 512),
    ("3x512B", 3 * 512),
    ("9x512B", 9 * 512),
    ("512KiB", 512 * 1024),
    ("1MiB", 1024 * 1024),
    ("2MiB", 2 * 1024 * 1024),
)

GRAIN_BASES = (0, GRAIN, 2 * GRAIN, 3 * GRAIN, 7 * GRAIN, 15 * GRAIN, 31 * GRAIN, 63 * GRAIN)
ALIGNED_2MIB = (0, 2 * 1024 * 1024, 4 * 1024 * 1024, 6 * 1024 * 1024)


def k_of(base: int, stride: int) -> int:
    if stride <= 0:
        raise ValueError("stride must be > 0")
    if base >= W:
        return 0
    return (W - 1 - base) // stride + 1


def issued_count(base: int, stride: int, n_pts: int | None = None) -> int:
    n = min(k_of(base, stride), Q_TOT)
    if n_pts is not None:
        n = min(n, n_pts)
    return n


def ap_addrs(base: int, stride: int, n: int) -> list[int]:
    return [base + i * stride for i in range(n)]


def iter_ap(base: int, stride: int, n: int) -> Iterator[int]:
    for i in range(n):
        yield base + i * stride
