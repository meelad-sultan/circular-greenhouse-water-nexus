"""Markdown summary tables from a results directory (used to build the README)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    rows = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    rows += ["| " + " | ".join(str(v) for v in r.values) + " |" for _, r in df.iterrows()]
    return "\n".join(rows)


def _iqr(s: pd.Series, nd=0) -> str:
    return f"{s.median():.{nd}f} [{s.quantile(.25):.{nd}f}, {s.quantile(.75):.{nd}f}]"


def summarize(res: str | Path) -> str:
    res, out = Path(res), []
    kp = json.loads((res / "baseline_kpis.json").read_text())
    sc = kp.pop("scenario")
    out.append(f"#### E1: one simulated year, scenario {sc} (single seed)\n")
    rows = [{"policy": p, "hours HI>1": f'{v["exposure_h"]:.0f}', "max HI": f'{v["max_hi"]:.2f}', "replacements": f'{v["replacements"]:.0f}',
             "cost (EUR)": f'{v["cost_eur"]:.0f}', "reuse fraction": f'{v["reuse_frac"]:.3f}'} for p, v in kp.items()]
    out.append(md(pd.DataFrame(rows)))
    b = pd.read_csv(res / "bleed_tradeoff.csv")
    out.append("\n#### E2: bleed trade-off (mean over replicates; scenario S3, sensor + guard)\n")
    g = b.groupby("bleed_ratio")
    t = pd.DataFrame({"bleed ratio": g.size().index, "conc. factor 1+1/b": g.conc_factor.first().round(1).values,
                      "hours HI>1": g.exposure_h.mean().round(0).values, "max HI": g.max_hi.mean().round(2).values,
                      "reuse fraction": g.reuse_frac.mean().round(3).values, "freshwater m3": g.freshwater_m3.mean().round(0).values,
                      "replacements": g.replacements.mean().round(1).values, "cost EUR": g.cost_eur.mean().round(0).values})
    out.append(md(t))
    p = pd.read_csv(res / "policy_comparison.csv")
    out.append("\n#### E3: replacement and guard policies (median [IQR] over replicates, identical weather/events per replicate)\n")
    rows = []
    for (sc_, pol), g in p.groupby(["scenario", "policy"], sort=False):
        rows.append({"scenario": sc_, "policy": pol, "hours HI>1": _iqr(g.exposure_h), "max HI": _iqr(g.max_hi, 2),
                     "replacements": _iqr(g.replacements), "premature": _iqr(g.premature_replacements),
                     "cost EUR": _iqr(g.cost_eur)})
    out.append(md(pd.DataFrame(rows)))
    lines = []
    for sc_, g in p.groupby("scenario", sort=False):
        a = g[g.policy == "sensor + guard"].set_index("replicate")
        f = g[g.policy == "fixed 90 d"].set_index("replicate")
        lines.append(f"- {sc_}: sensor + guard vs fixed 90 d: exposure lower or equal in {(a.exposure_h <= f.exposure_h).mean():.0%} "
                     f"of replicates, cost lower in {(a.cost_eur < f.cost_eur).mean():.0%}, median cost difference "
                     f"{(a.cost_eur - f.cost_eur).median():+.0f} EUR")
    out.append("\nPaired comparison:\n" + "\n".join(lines))
    d = pd.read_csv(res / "detector_oc.csv")
    out.append("\n#### E4: CUSUM operating characteristics (k = 0.5; hours, standardised iid normal data)\n")
    d = d.assign(arl_sim=d.arl_sim.where((d.shift_sd > 0) | (d.censored_frac < 0.05)))  # censored in-control runs are biased
    w = d.pivot(index="h", columns="shift_sd", values="arl_sim").round(1).fillna("censored")
    w.columns = [f"sim shift {c:g}sd" if c else "sim in-control ARL0" for c in w.columns]
    w["ARL0 Siegmund approx."] = d[d.shift_sd == 0].set_index("h").arl_siegmund.round(0)
    w["in-control runs censored"] = d[d.shift_sd == 0].set_index("h").censored_frac.round(2)
    out.append(md(w.reset_index()))
    s = pd.read_csv(res / "sensitivity_sobol.csv")
    out.append("\n#### E5: Sobol sensitivity (S1 = first-order, ST = total effect; +/- 95% bootstrap CI)\n")
    rows = []
    for o, g in s.groupby("output", sort=False):
        for _, r in g.sort_values("ST", ascending=False).head(4).iterrows():
            rows.append({"output": o, "parameter": r.parameter, "S1": f"{r.S1:.2f} +/- {r.S1_conf:.2f}", "ST": f"{r.ST:.2f} +/- {r.ST_conf:.2f}"})
    out.append(md(pd.DataFrame(rows)))
    f = pd.read_csv(res / "pfas_robustness.csv")
    piv = f.pivot(index="draw", columns="policy", values="exposure_h")
    pc = f.pivot(index="draw", columns="policy", values="cost_eur")
    out.append("\n#### E6: PFAS robustness (EXPLORATORY; scenario S4, wide parameter ranges)\n")
    out.append(f"- Parameter draws: {len(piv)} (Latin hypercube over PFAS capacity, affinity ratio, lab interval, lab delay)\n"
               f"- Sensor-based (lab-sampling) policy has exposure <= fixed 90 d in {(piv['sensor'] <= piv['fixed 90 d']).mean():.0%} of draws "
               f"and <= no replacement in {(piv['sensor'] <= piv['none']).mean():.0%}\n"
               f"- Median hours with HI > 1: none {piv['none'].median():.0f}, fixed 90 d {piv['fixed 90 d'].median():.0f}, sensor {piv['sensor'].median():.0f}\n"
               f"- Median cost (EUR): none {pc['none'].median():.0f}, fixed 90 d {pc['fixed 90 d'].median():.0f}, sensor {pc['sensor'].median():.0f}")
    return "\n".join(out)
