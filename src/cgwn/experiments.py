"""Experiments E1-E6. Every run derives its RNG from (seed + replicate), so results are reproducible."""
from __future__ import annotations

import copy
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc

from cgwn import __version__
from cgwn.config import load_config, set_path
from cgwn.detection import oc_table
from cgwn.simulate import Policy, run_scenario

POLICIES = [
    ("none", Policy("none", False)),
    ("fixed 90 d", Policy("fixed", False, 90)),
    ("fixed 270 d", Policy("fixed", False, 270)),
    ("sensor", Policy("sensor", False)),
    ("none + guard", Policy("none", True)),
    ("sensor + guard", Policy("sensor", True)),
]
KEEP = ["exposure_h", "exposure_frac", "max_hi", "mean_hi", "bed_breakthrough_h", "freshwater_m3", "reuse_frac",
        "replacements", "premature_replacements", "guard_block_h", "energy_kwh_per_m3_reused", "co2_kg", "cost_eur",
        "mass_balance_rel_err"]


def default_policy(cfg) -> Policy:
    return Policy(cfg["default_policy"]["replacement"], cfg["default_policy"]["guard"])


def _row(k: dict, **meta) -> dict:
    return {**meta, **{x: k[x] for x in KEEP}}


def run_baseline(cfg, out: Path) -> None:
    sc = cfg["experiments"]["baseline"]["scenario"]
    rows, kp = [], {}
    for name, pol in (("none", Policy("none", False)), ("sensor + guard", Policy("sensor", True))):
        r = run_scenario(cfg, sc, pol, cfg["seed"], record=True)
        s, d = r.series, r.series["hi"].size // 24
        names = [c["name"] for c in cfg["contaminants"]]
        lim = np.array([c["limit_ug_L"] for c in cfg["contaminants"]])
        cl = s["cl"][: d * 24].reshape(d, 24, -1).mean(axis=1) / lim
        for day in range(d):
            row = {"policy": name, "day": day + 1, "hi_mean": s["hi"][day * 24:(day + 1) * 24].mean(),
                   "tank_m3": s["vt"][day * 24:(day + 1) * 24].mean(), "freshwater_m3": s["fw"][day * 24:(day + 1) * 24].sum(),
                   "et_m3": s["et"][day * 24:(day + 1) * 24].sum()}
            row.update({f"ratio_{nm}": cl[day, i] for i, nm in enumerate(names)})
            row.update({f"load_{bn}": s["smax"][day * 24:(day + 1) * 24, j].max() for j, bn in enumerate(s["bed_names"])})
            rows.append(row)
        kp[name] = {k: r.kpis[k] for k in KEEP}
    pd.DataFrame(rows).to_csv(out / "baseline_daily.csv", index=False)
    (out / "baseline_kpis.json").write_text(json.dumps({"scenario": sc, **kp}, indent=2))


def run_bleed(cfg, out: Path) -> None:
    e, rows = cfg["experiments"]["bleed_tradeoff"], []
    for ratio in e["ratios"]:
        c2 = set_path(cfg, "loop.bleed_ratio", ratio)
        for rep in range(e["replicates"]):
            k = run_scenario(c2, e["scenario"], default_policy(cfg), cfg["seed"] + rep).kpis
            rows.append(_row(k, bleed_ratio=ratio, replicate=rep, conc_factor=1 + 1 / ratio))
        print(f"  [bleed] ratio {ratio} done", flush=True)
    pd.DataFrame(rows).to_csv(out / "bleed_tradeoff.csv", index=False)


def run_policies(cfg, out: Path) -> None:
    e, rows = cfg["experiments"]["policy_comparison"], []
    for sc in e["scenarios"]:
        for rep in range(e["replicates"]):
            for name, pol in POLICIES:
                k = run_scenario(cfg, sc, pol, cfg["seed"] + rep).kpis
                rows.append(_row(k, scenario=sc, policy=name, replicate=rep))
        print(f"  [policies] {sc} done", flush=True)
    pd.DataFrame(rows).to_csv(out / "policy_comparison.csv", index=False)


def run_detector(cfg, out: Path) -> None:
    e = cfg["experiments"]["detector"]
    rows = oc_table(e["h_values"], e["shifts"], e["reps"], e["t_max"], e["k"], np.random.default_rng(cfg["seed"]))
    pd.DataFrame(rows).to_csv(out / "detector_oc.csv", index=False)


def run_sensitivity(cfg, out: Path) -> None:
    from SALib.analyze import sobol as sanalyze
    from SALib.sample import sobol as ssample

    e = cfg["experiments"]["sensitivity"]
    params = e["parameters"]
    problem = {"num_vars": len(params), "names": [p["name"] for p in params], "bounds": [[p["low"], p["high"]] for p in params]}
    X = ssample.sample(problem, e["N"], calc_second_order=False, seed=cfg["seed"])
    outputs = ["exposure_frac", "max_hi", "cost_eur", "reuse_frac"]
    Y = {o: np.zeros(len(X)) for o in outputs}
    pol = default_policy(cfg)
    for i, x in enumerate(X):
        c2 = cfg
        for p, v in zip(params, x, strict=True):
            c2 = set_path(c2, p["path"], float(v))
        k = run_scenario(c2, e["scenario"], pol, cfg["seed"], days=e["horizon_days"]).kpis
        for o in outputs:
            Y[o][i] = k[o]
        if i % 50 == 0:
            print(f"  [sensitivity] {i}/{len(X)}", flush=True)
    rows = []
    for o in outputs:
        if np.ptp(Y[o]) < 1e-12:
            continue
        try:
            si = sanalyze.analyze(problem, Y[o], calc_second_order=False, num_resamples=100, print_to_console=False, seed=cfg["seed"])
        except TypeError:
            si = sanalyze.analyze(problem, Y[o], calc_second_order=False, num_resamples=100, print_to_console=False)
        for j, nm in enumerate(problem["names"]):
            rows.append({"output": o, "parameter": nm, "S1": si["S1"][j], "S1_conf": si["S1_conf"][j],
                         "ST": si["ST"][j], "ST_conf": si["ST_conf"][j], "output_mean": float(Y[o].mean()), "output_sd": float(Y[o].std())})
    pd.DataFrame(rows).to_csv(out / "sensitivity_sobol.csv", index=False)


def run_pfas(cfg, out: Path) -> None:
    e = cfg["experiments"]["pfas_robustness"]
    r = e["ranges"]
    keys = list(r)
    lhs = qmc.LatinHypercube(d=len(keys), seed=cfg["seed"]).random(e["draws"])
    pols = [("none", Policy("none", False)), ("fixed 90 d", Policy("fixed", False, 90)), ("sensor", Policy("sensor", False))]
    rows = []
    for d, u in enumerate(lhs):
        v = {k: r[k][0] + ui * (r[k][1] - r[k][0]) for k, ui in zip(keys, u, strict=True)}
        c2 = copy.deepcopy(cfg)
        c2["treatment"]["beds"]["pfas"]["q_tot"] = v["pfas_q_tot"]
        for c in c2["contaminants"]:
            if c["name"] == "PFAS_long":
                c["affinity"] = v["pfas_affinity_ratio"] * 1.0
        c2["sensors"]["pfas_lab_interval_h"] = int(v["lab_interval_h"])
        c2["sensors"]["pfas_lab_delay_h"] = int(v["lab_delay_h"])
        for name, pol in pols:
            ks = [run_scenario(c2, "S4", pol, cfg["seed"] + s, days=e["days"]).kpis for s in range(e["seeds"])]
            rows.append({"draw": d, **v, "policy": name, **{x: float(np.mean([k[x] for k in ks])) for x in ("exposure_h", "cost_eur", "replacements")}})
        if d % 6 == 0:
            print(f"  [pfas] draw {d}/{e['draws']}", flush=True)
    pd.DataFrame(rows).to_csv(out / "pfas_robustness.csv", index=False)


STEPS = {"baseline": run_baseline, "bleed": run_bleed, "policies": run_policies, "detector": run_detector,
         "sensitivity": run_sensitivity, "pfas": run_pfas}


def run_all(config_path, out_dir, only=None):
    cfg = load_config(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    timings, t0 = {}, time.perf_counter()
    print(f"cgwn {__version__} | config {config_path} | out {out}")
    for name in only or STEPS:
        t1 = time.perf_counter()
        print(f"[{name}] start", flush=True)
        STEPS[name](cfg, out)
        timings[name] = round(time.perf_counter() - t1, 1)
        print(f"[{name}] finished in {timings[name]} s", flush=True)
    import SALib
    import scipy
    meta = {"cgwn_version": __version__, "config_path": str(config_path), "config": cfg, "timings_s": timings,
            "total_s": round(time.perf_counter() - t0, 1), "python": sys.version.split()[0], "platform": platform.platform(),
            "packages": {"numpy": np.__version__, "scipy": scipy.__version__, "pandas": pd.__version__,
                         "SALib": getattr(SALib, "__version__", "unknown")}}
    (out / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    print(f"all done in {meta['total_s']} s -> {out}")
