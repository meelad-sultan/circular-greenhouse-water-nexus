"""One-sided CUSUM change detection: run-length simulation and Siegmund approximations."""
from __future__ import annotations

import numpy as np


def siegmund_arl0(h: float, k: float = 0.5) -> float:
    """Approximate in-control average run length (standardised iid normal data, one-sided CUSUM)."""
    b = h + 1.166
    return float((np.exp(2 * k * b) - 2 * k * b - 1) / (2 * k * k))


def siegmund_arl1(h: float, delta: float, k: float = 0.5) -> float:
    """Approximate average run length after a mean shift of delta standard deviations."""
    d, b = delta - k, h + 1.166
    return float(b * b) if abs(d) < 1e-9 else float((np.exp(-2 * d * b) + 2 * d * b - 1) / (2 * d * d))


def first_alarm_times(h_values, shift: float, reps: int, t_max: int, k: float, rng) -> np.ndarray:
    """Simulate CUSUM from S=0 on N(shift, 1) data; return first-alarm hour per h (nan = censored)."""
    h = np.asarray(h_values, float)
    out = np.full((len(h), reps), np.nan)
    S = np.zeros(reps)
    for t in range(1, t_max + 1):
        S = np.maximum(0.0, S + rng.normal(shift, 1.0, reps) - k)
        for i, hv in enumerate(h):
            new = np.isnan(out[i]) & (S > hv)
            out[i, new] = t
        if not np.isnan(out).any():
            break
    return out


def oc_table(h_values, shifts, reps: int, t_max: int, k: float, rng):
    """Rows: h, shift, mean run length (censored runs excluded and counted), Siegmund approximation."""
    rows = []
    for shift in [0.0, *shifts]:
        fa = first_alarm_times(h_values, shift, reps, t_max, k, rng)
        for i, h in enumerate(h_values):
            ok = fa[i][~np.isnan(fa[i])]
            approx = siegmund_arl0(h, k) if shift == 0 else siegmund_arl1(h, shift, k)
            rows.append({"h": h, "shift_sd": shift, "arl_sim": float(ok.mean()) if len(ok) else np.nan,
                         "censored_frac": float(np.isnan(fa[i]).mean()), "arl_siegmund": approx})
    return rows
