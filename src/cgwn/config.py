"""YAML configuration with inheritance (``extends:``) and dotted-path overrides."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


def deep_update(base: dict, upd: dict) -> dict:
    out = dict(base)
    for k, v in upd.items():
        out[k] = deep_update(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    parent = cfg.pop("extends", None)
    return deep_update(load_config(path.parent / parent), cfg) if parent else cfg


def set_path(cfg: dict, dotted: str, value) -> dict:
    """Return a deep copy of cfg with ``a.b.c`` set to value."""
    out = copy.deepcopy(cfg)
    node = out
    keys = dotted.split(".")
    for k in keys[:-1]:
        node = node[k]
    node[keys[-1]] = value
    return out


def get_path(cfg: dict, dotted: str):
    node = cfg
    for k in dotted.split("."):
        node = node[k]
    return node
