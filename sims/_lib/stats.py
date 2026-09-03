"""Mean ± 95% CI over seeded trials. Deterministic series yield width 0."""

from __future__ import annotations

import math
from typing import Iterable


def mean(xs: Iterable[float]) -> float:
    vals = list(xs)
    if not vals:
        return float("nan")
    return sum(vals) / len(vals)


def stdev(xs: Iterable[float]) -> float:
    vals = list(xs)
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (n - 1))


def ci95(xs: Iterable[float]) -> tuple[float, float, float]:
    """Return (mean, halfwidth, n). Uses normal 1.96 * s / sqrt(n); n<2 → halfwidth 0."""
    vals = [float(x) for x in xs]
    n = len(vals)
    if n == 0:
        return float("nan"), float("nan"), 0
    m = sum(vals) / n
    if n == 1:
        return m, 0.0, 1
    hw = 1.96 * stdev(vals) / math.sqrt(n)
    return m, hw, n


def fmt_ci(xs: Iterable[float], digits: int = 4) -> str:
    m, hw, n = ci95(xs)
    if n == 0 or m != m:
        return "nan"
    return f"{m:.{digits}f} ± {hw:.{digits}f} (n={n})"


def rel_err(t3: float, t2: float) -> float:
    if t2 == 0:
        return 0.0 if t3 == 0 else float("inf")
    return abs(t3 - t2) / abs(t2)
