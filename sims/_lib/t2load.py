"""Load frozen T2 occupancy models as libraries. Never writes those files."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load_model(rel: str, name: str):
    path = REPO / rel
    if not path.is_file():
        raise FileNotFoundError(f"frozen T2 model missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_sns_t2():
    return load_model("models/P-0105/M-4/model.py", "t2_p0105_m4")


def load_affine_t2():
    return load_model("models/P-0106/M-5/model.py", "t2_p0106_m5")
