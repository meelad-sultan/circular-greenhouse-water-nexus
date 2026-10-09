"""Validation hook: fit the Thomas model to a PUBLISHED breakthrough curve and report agreement.

Input: CSV of digitised points (columns ``t`` and ``c_over_c0``) and a conditions YAML
(``c0_mg_per_L``, ``flow_mL_per_min``, ``bed_mass_g``, ``time_unit`` = min | h).
Model (Thomas): C/C0 = 1 / (1 + exp( kTh/Q * (q0*m - C0*Q*t) )), kTh in mL/(min*mg), q0 in mg/g.
Equivalent bed steepness used by the simulator: K = kTh * q0 * m / Q.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import least_squares


def thomas_curve(t_min, q0, kth, c0_mg_L, flow, mass_g):
    c0 = c0_mg_L / 1000.0  # mg/mL
    e = (kth / flow) * (q0 * mass_g - c0 * flow * np.asarray(t_min, float))
    return 1.0 / (1.0 + np.exp(np.clip(e, -60, 60)))


def t_at(p: float, q0, kth, c0_mg_L, flow, mass_g) -> float:
    """Time (min) at which the Thomas model reaches C/C0 = p."""
    c0 = c0_mg_L / 1000.0
    return float((q0 * mass_g - (flow / kth) * np.log(1.0 / p - 1.0)) / (c0 * flow))


def t_at_obs(t, y, p: float) -> float:
    t, y = np.asarray(t, float), np.asarray(y, float)
    order = np.argsort(t)
    t, y = t[order], np.maximum.accumulate(y[order])
    return float(np.interp(p, y, t)) if y.min() <= p <= y.max() else float("nan")


def fit_thomas(t_min, y, c0_mg_L, flow, mass_g):
    t, y = np.asarray(t_min, float), np.asarray(y, float)
    q_exp = flow * (c0_mg_L / 1000.0) * np.trapezoid(1 - y, t) / mass_g if len(t) > 1 else 10.0
    best = None
    for q_start in (max(q_exp, 1e-3), 3 * max(q_exp, 1e-3), 0.3 * max(q_exp, 1e-3)):
        for k_start in (1e-4, 1e-3, 1e-2, 1e-1, 1.0):
            def res(lp):
                lp = np.clip(lp, -20.0, 20.0)
                return thomas_curve(t, np.exp(lp[0]), np.exp(lp[1]), c0_mg_L, flow, mass_g) - y
            sol = least_squares(res, np.log([q_start, k_start]), method="lm")
            if best is None or sol.cost < best.cost:
                best = sol
    return float(np.exp(best.x[0])), float(np.exp(best.x[1])), q_exp


def validate(points_csv, conditions_yaml, out_dir) -> dict:
    cond = yaml.safe_load(Path(conditions_yaml).read_text(encoding="utf-8"))
    df = pd.read_csv(points_csv)
    scale = 60.0 if cond.get("time_unit", "min") == "h" else 1.0
    t, y = df["t"].to_numpy(float) * scale, df["c_over_c0"].to_numpy(float)
    c0, Q, m = cond["c0_mg_per_L"], cond["flow_mL_per_min"], cond["bed_mass_g"]
    q0, kth, q_exp = fit_thomas(t, y, c0, Q, m)
    pred = thomas_curve(t, q0, kth, c0, Q, m)
    ss_res, ss_tot = float(((y - pred) ** 2).sum()), float(((y - y.mean()) ** 2).sum())
    res = {"q0_fit_mg_per_g": q0, "kTh_fit_mL_per_min_per_mg": kth, "q_exp_from_curve_mg_per_g": float(q_exp),
           "K_equivalent_for_simulator": kth * q0 * m / Q, "rmse": float(np.sqrt(ss_res / len(y))),
           "r2": 1 - ss_res / ss_tot if ss_tot > 0 else float("nan"),
           "t10_obs_min": t_at_obs(t, y, 0.10), "t10_model_min": t_at(0.10, q0, kth, c0, Q, m),
           "t50_obs_min": t_at_obs(t, y, 0.50), "t50_model_min": t_at(0.50, q0, kth, c0, Q, m),
           "source": cond.get("source", "UNSPECIFIED: add the citation to the conditions file")}
    for p in ("t10", "t50"):
        o, mo = res[f"{p}_obs_min"], res[f"{p}_model_min"]
        res[f"{p}_rel_error_pct"] = 100 * (mo - o) / o if o == o and o != 0 else float("nan")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "validation_result.json").write_text(json.dumps(res, indent=2))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tt = np.linspace(0, t.max() * 1.1, 300)
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.plot(t / 60 if scale == 60 else t, y, "o", label="published points (digitised)")
    ax.plot(tt / 60 if scale == 60 else tt, thomas_curve(tt, q0, kth, c0, Q, m), "-", label="Thomas fit")
    ax.set_xlabel(f"time ({cond.get('time_unit', 'min')})")
    ax.set_ylabel("C / C0")
    ax.set_title(f"R2 = {res['r2']:.3f}, t50 error = {res['t50_rel_error_pct']:.1f}%", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "validation_curve.png", dpi=160)
    plt.close(fig)
    return res


def selftest(out_dir, seed: int = 0) -> dict:
    """Round trip on synthetic data with known parameters: shows the hook works (it validates nothing real)."""
    rng = np.random.default_rng(seed)
    c0, Q, m, q0, kth = 20.0, 5.0, 10.0, 25.0, 0.3  # K = kth*q0*m/Q = 15 (sharp curve)
    t = np.linspace(5, 3 * q0 * m / (c0 / 1000 * Q), 40)
    y = np.clip(thomas_curve(t, q0, kth, c0, Q, m) + rng.normal(0, 0.02, len(t)), 0, 1.2)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"t": t, "c_over_c0": y}).to_csv(out / "selftest_points.csv", index=False)
    (out / "selftest_conditions.yaml").write_text(yaml.safe_dump({"c0_mg_per_L": c0, "flow_mL_per_min": Q, "bed_mass_g": m,
                                                                   "time_unit": "min", "source": "SYNTHETIC SELF-TEST"}))
    res = validate(out / "selftest_points.csv", out / "selftest_conditions.yaml", out)
    res["true_q0"], res["true_kTh"] = q0, kth
    return res
