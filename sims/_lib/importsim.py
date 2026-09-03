"""Load a card's sim.py under a unique module name (pytest collects both cards)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_sim(sim_dir: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    path = Path(sim_dir) / "sim.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
