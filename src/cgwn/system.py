"""Build runtime arrays (limits, partitioning, beds) from the configuration."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BedSpec:
    name: str
    idx: np.ndarray  # indices into the contaminant vector
    w: np.ndarray  # capacity units per ug of each contaminant (molar: 1/M, mass: 1)
    a: np.ndarray  # affinity weights
    cap: float  # capacity in the same units
    K: float  # Thomas steepness at reference conditions
    mass_kg: float
    media_eur_kg: float
    disposal_eur_kg: float
    labour_eur: float


@dataclass
class System:
    cfg: dict
    names: list
    limits: np.ndarray
    kup: np.ndarray
    phi: np.ndarray
    is_metal: np.ndarray
    beds: list
    crop: dict
    site: dict
    loop: dict
    tank: dict
    sens: dict
    costs: dict
    treat: dict

    @property
    def n(self) -> int:
        return len(self.names)


def build_system(cfg: dict) -> System:
    cs = cfg["contaminants"]
    names = [c["name"] for c in cs]
    beds = []
    for bname, b in cfg["treatment"]["beds"].items():
        idx = np.array([i for i, c in enumerate(cs) if c["bed"] == bname], int)
        if len(idx) == 0:
            continue
        if b["basis"] == "molar":
            w = np.array([1.0 / cs[i]["molar_mass"] for i in idx])
        else:
            w = np.ones(len(idx))
        beds.append(
            BedSpec(bname, idx, w, np.array([float(cs[i]["affinity"]) for i in idx]),
                    b["q_tot"] * b["mass_kg"] * 1000.0, float(b["K"]), b["mass_kg"], b["media_eur_kg"],
                    b["disposal_eur_kg"], b["labour_eur"])
        )
    return System(
        cfg, names, np.array([c["limit_ug_L"] for c in cs], float), np.array([c["uptake_frac"] for c in cs], float),
        np.array([c["particulate_frac"] for c in cs], float), np.array([c["kind"] == "metal" for c in cs]), beds,
        cfg["crop"], cfg["site"], cfg["loop"], cfg["tank"], cfg["sensors"], cfg["costs"], cfg["treatment"],
    )
