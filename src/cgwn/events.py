"""Source-water scenarios: baseline concentrations plus random pollution events."""
from __future__ import annotations

import numpy as np


def make_source(cfg: dict, scenario: str, hours: int, rng: np.random.Generator):
    """Return (c_src [hours x n] in ug/L, tss [hours] in mg/L) for a scenario."""
    sc = cfg["scenarios"][scenario]
    names = [c["name"] for c in cfg["contaminants"]]
    base = np.array([sc["base"].get(nm, 0.0) for nm in names], float) * sc.get("scale", 1.0)
    c = np.tile(base, (hours, 1))
    tss = np.full(hours, float(sc["tss"]))
    ev = sc.get("events", {})
    rate = ev.get("rate_per_year", 0.0)
    n_ev = rng.poisson(rate * hours / 8760.0) if rate > 0 else 0
    pool = [names.index(p) for p in ev.get("pool", [])]
    for _ in range(n_ev):
        start = int(rng.integers(0, hours))
        dur = max(2, int(rng.lognormal(np.log(ev.get("dur_median_h", 12)), ev.get("dur_sigma", 0.5))))
        lo, hi = ev.get("n_affected", [1, 1])
        k = min(int(rng.integers(lo, hi + 1)), len(pool))
        hit = rng.choice(pool, size=k, replace=False)
        mult = np.maximum(1.5, rng.lognormal(np.log(ev.get("mult_median", 10.0)), ev.get("mult_sigma", 0.6), size=k))
        sl = slice(start, min(hours, start + dur))
        for j, m in zip(hit, mult, strict=True):
            c[sl, j] = np.maximum(c[sl, j], base[j] * m)
        tss[sl] = np.maximum(tss[sl], tss[sl] * ev.get("tss_mult", 1.0))
    return c, tss
