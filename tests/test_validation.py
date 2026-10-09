import json

import numpy as np
import pytest

from cgwn.validation import fit_thomas, selftest, t_at, thomas_curve, validate


def test_fit_recovers_parameters_from_noisy_curve():
    rng = np.random.default_rng(1)
    c0, Q, m, q0, kth = 20.0, 5.0, 10.0, 25.0, 0.3
    t = np.linspace(5, 7500, 40)
    y = thomas_curve(t, q0, kth, c0, Q, m) + rng.normal(0, 0.02, len(t))
    q_fit, k_fit, _ = fit_thomas(t, y, c0, Q, m)
    assert q_fit == pytest.approx(q0, rel=0.05) and k_fit == pytest.approx(kth, rel=0.15)


def test_t_at_inverts_the_curve():
    for p in (0.1, 0.5, 0.9):
        t = t_at(p, 25.0, 0.3, 20.0, 5.0, 10.0)
        assert float(thomas_curve(np.array([t]), 25.0, 0.3, 20.0, 5.0, 10.0)[0]) == pytest.approx(p, abs=1e-9)


def test_selftest_writes_outputs_and_fits_well(tmp_path):
    res = selftest(tmp_path)
    assert res["r2"] > 0.99 and abs(res["t50_rel_error_pct"]) < 5
    assert (tmp_path / "validation_result.json").exists() and (tmp_path / "validation_curve.png").exists()


def test_validate_reads_user_files(tmp_path):
    selftest(tmp_path)
    res = validate(tmp_path / "selftest_points.csv", tmp_path / "selftest_conditions.yaml", tmp_path / "again")
    assert json.loads((tmp_path / "again" / "validation_result.json").read_text())["q0_fit_mg_per_g"] == pytest.approx(
        res["q0_fit_mg_per_g"])
