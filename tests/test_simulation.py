import pytest

from cgwn.simulate import Policy, run_scenario

POLS = [Policy("none", False), Policy("fixed", True, 20), Policy("sensor", True)]


@pytest.mark.parametrize("scenario", ["S1", "S2", "S3", "S4"])
def test_contaminant_mass_balance_closes(cfg, scenario):
    for pol in POLS:
        k = run_scenario(cfg, scenario, pol, 3, days=60).kpis
        assert k["mass_balance_rel_err"] < 1e-9


def test_determinism_and_seed_sensitivity(cfg):
    a = run_scenario(cfg, "S3", POLS[2], 1, days=40).kpis
    b = run_scenario(cfg, "S3", POLS[2], 1, days=40).kpis
    c = run_scenario(cfg, "S3", POLS[2], 2, days=40).kpis
    assert a == b and a != c


def test_tank_volume_and_hazard_index_bounds(cfg):
    r = run_scenario(cfg, "S3", POLS[2], 1, days=60, record=True)
    assert (r.series["vt"] >= -1e-9).all() and (r.series["vt"] <= cfg["tank"]["max_m3"] + 1e-9).all()
    assert (r.series["hi"] >= -1e-9).all()


def test_fixed_policy_replacement_count(cfg):
    k = run_scenario(cfg, "S1", Policy("fixed", False, 15), 1, days=60).kpis
    assert k["replacements"] == 4 * 3  # 4 intervals x 3 beds


def test_clean_source_gives_no_exposure(cfg_copy):
    for sc in cfg_copy["scenarios"].values():
        sc["base"] = {k: 0.0 for k in sc["base"]}
        sc["events"] = {"rate_per_year": 0}
    k = run_scenario(cfg_copy, "S3", Policy("none", False), 1, days=60).kpis
    assert k["max_hi"] == 0.0 and k["exposure_h"] == 0


def test_treatment_is_needed_in_chronic_scenario_and_sensor_policy_helps(cfg):
    none = run_scenario(cfg, "S3", Policy("none", False), 1).kpis
    sens = run_scenario(cfg, "S3", Policy("sensor", True), 1).kpis
    assert none["exposure_h"] > 0
    assert sens["exposure_h"] < none["exposure_h"]


def test_bed_failure_follows_saturation(cfg):
    k = run_scenario(cfg, "S3", Policy("none", False), 1).kpis
    assert k["bed_breakthrough_h"] > 0 and k["exposure_h"] > 0
