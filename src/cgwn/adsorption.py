"""Fixed-bed adsorption with Thomas-type breakthrough and affinity-weighted competition.

Single contaminant: ``C/C0 = 1 / (1 + exp(K (1 - S)))`` with ``S = fed / (q0 * m)``, which equals the
Thomas model for constant flow and feed (``K = kTh q0 m / Q``).

Several contaminants share one capacity pool (cation bed, PFAS bed). With affinity weights ``a_i`` the
common affinity-weighted loading is ``L = sum_j a_j fed_j / cap`` and contaminant i has
``S_i = L / a_i``: a higher-affinity species breaks through later. This is a STYLISED competition rule
(not a mechanistic multi-component isotherm); it reduces exactly to Thomas for one species, and mass is
conserved by construction (adsorbed = fed - effluent).
"""
from __future__ import annotations

import numpy as np


def thomas_fraction(S, K):
    """Effluent/influent concentration ratio as a function of loading fraction S."""
    return 1.0 / (1.0 + np.exp(np.clip(K * (1.0 - np.asarray(S, float)), -60.0, 60.0)))


class Bed:
    def __init__(self, spec):
        self.spec = spec
        self.fed = np.zeros(len(spec.idx))

    def loading(self) -> np.ndarray:
        lam = float((self.spec.a * self.fed).sum() / self.spec.cap)
        return lam / self.spec.a

    def f(self) -> np.ndarray:
        return thomas_fraction(self.loading(), self.spec.K)

    def smax(self) -> float:
        return float(self.loading().max())

    def apply(self, mass_ug: np.ndarray) -> np.ndarray:
        """Take feed mass (ug per contaminant of this bed), return effluent mass; update loading."""
        out = mass_ug * self.f()
        self.fed += mass_ug * self.spec.w
        return out

    def reset(self) -> None:
        self.fed[:] = 0.0
