"""Export every numeric parameter with a provenance status (the honesty table)."""
from __future__ import annotations

import pandas as pd

LIMIT_NOTE = {
    "Cd": "FAO-style irrigation guideline (0.01 mg/L) as cited in secondary sources; verify jurisdiction",
    "Ni": "FAO-style irrigation guideline (0.2 mg/L) as cited in secondary sources; verify jurisdiction",
    "Pb": "conservative placeholder; guideline values vary widely by jurisdiction; verify",
    "As": "conservative placeholder; guideline values vary by jurisdiction; verify",
    "PFAS_long": "exploratory placeholder; no harmonised irrigation limit assumed; verify",
    "PFAS_short": "exploratory placeholder; no harmonised irrigation limit assumed; verify",
}


def _flatten(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            yield from _flatten(v, key + ".")
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            yield key, v


def export_parameters(cfg: dict, path) -> pd.DataFrame:
    rows = []
    for c in cfg["contaminants"]:
        for k, v in c.items():
            if isinstance(v, (int, float)):
                status, note = "illustrative", "set in configs/default.yaml"
                if k == "molar_mass":
                    status, note = "standard value", "atomic mass; PFAS classes are lumped (mass basis)"
                if k == "limit_ug_L":
                    status, note = "to verify", LIMIT_NOTE[c["name"]]
                if k == "affinity":
                    note = "relative affinity within the bed (higher = breaks through later); ranking illustrative"
                rows.append({"key": f"contaminants.{c['name']}.{k}", "value": v, "status": status, "note": note})
    for key, v in _flatten({k: cfg[k] for k in ("site", "crop", "loop", "tank", "treatment", "sensors", "costs", "policy_defaults")}):
        note = "assumption" if key.startswith(("sensors", "policy")) else "illustrative; calibrate to your system"
        rows.append({"key": key, "value": v, "status": "illustrative", "note": note})
    for sc, d in cfg["scenarios"].items():
        for key, v in _flatten({sc: d}):
            rows.append({"key": f"scenarios.{key}", "value": v, "status": "scenario assumption",
                         "note": "S3 values are PLACEHOLDERS: replace with ranges from your own measurements" if sc == "S3"
                         else ("exploratory" if sc == "S4" else "illustrative")})
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return df
