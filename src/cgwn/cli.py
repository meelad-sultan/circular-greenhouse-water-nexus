"""Command line: python -m cgwn <run|figures|summary|validate|params>."""
from __future__ import annotations

import argparse
import json


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="cgwn", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the experiments")
    r.add_argument("--config", default="configs/default.yaml")
    r.add_argument("--out", default="results/metrics")
    r.add_argument("--only", nargs="+", choices=["baseline", "bleed", "policies", "detector", "sensitivity", "pfas"])
    f = sub.add_parser("figures", help="make figures")
    f.add_argument("--results", default="results/metrics")
    f.add_argument("--out", default="results/figures")
    s = sub.add_parser("summary", help="print markdown tables")
    s.add_argument("--results", default="results/metrics")
    v = sub.add_parser("validate", help="fit the Thomas model to a published breakthrough curve")
    v.add_argument("--points")
    v.add_argument("--conditions")
    v.add_argument("--out", default="validation/outputs")
    v.add_argument("--selftest", action="store_true", help="synthetic round-trip check of the hook")
    p = sub.add_parser("params", help="export the parameter provenance table")
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--out", default="data/parameters.csv")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        from cgwn.experiments import run_all

        run_all(a.config, a.out, a.only)
    elif a.cmd == "figures":
        from cgwn.plotting import make_all

        for path in make_all(a.results, a.out):
            print("wrote", path)
    elif a.cmd == "summary":
        from cgwn.summary import summarize

        print(summarize(a.results))
    elif a.cmd == "validate":
        from cgwn.validation import selftest, validate

        res = selftest(a.out) if a.selftest else validate(a.points, a.conditions, a.out)
        print(json.dumps(res, indent=2))
    else:
        from cgwn.config import load_config
        from cgwn.provenance import export_parameters

        print(len(export_parameters(load_config(a.config), a.out)), "parameters ->", a.out)
