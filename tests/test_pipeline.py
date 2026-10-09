import pandas as pd
import yaml

from cgwn.config import load_config
from cgwn.experiments import run_all
from cgwn.plotting import make_all
from cgwn.provenance import export_parameters
from cgwn.summary import summarize


def test_end_to_end_smoke(tmp_path):
    base = load_config("configs/default.yaml")
    small = {"horizon_days": 20,
             "experiments": {"bleed_tradeoff": {"ratios": [0.2], "replicates": 1},
                             "policy_comparison": {"scenarios": ["S3"], "replicates": 1},
                             "detector": {"h_values": [4, 6], "shifts": [2], "reps": 100, "t_max": 1500},
                             "sensitivity": {"horizon_days": 15, "N": 4},
                             "pfas_robustness": {"draws": 2, "seeds": 1, "days": 20}}}
    cfg_path = tmp_path / "cfg.yaml"
    merged = base | {k: v for k, v in small.items() if k != "experiments"}
    merged["experiments"] = {**base["experiments"], **{k: {**base["experiments"][k], **v} for k, v in small["experiments"].items()}}
    cfg_path.write_text(yaml.safe_dump(merged))
    out = tmp_path / "res"
    run_all(cfg_path, out)
    for f in ("baseline_daily.csv", "bleed_tradeoff.csv", "policy_comparison.csv", "detector_oc.csv", "sensitivity_sobol.csv",
              "pfas_robustness.csv", "run_metadata.json"):
        assert (out / f).exists()
    assert len(make_all(out, tmp_path / "fig")) == 6
    assert "E6" in summarize(out)


def test_parameter_table_has_provenance(cfg, tmp_path):
    df = export_parameters(cfg, tmp_path / "p.csv")
    assert list(df.columns) == ["key", "value", "status", "note"]
    assert (df[df.key.str.endswith("limit_ug_L")].status == "to verify").all()
    assert pd.read_csv(tmp_path / "p.csv").shape[0] == len(df)
