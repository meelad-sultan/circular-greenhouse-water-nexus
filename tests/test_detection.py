import numpy as np
import pytest

from cgwn.detection import first_alarm_times, siegmund_arl0, siegmund_arl1


def test_siegmund_reference_values():
    assert siegmund_arl0(5.0) == pytest.approx(937, rel=0.02)  # one-sided; two-sided known value is about 465
    assert siegmund_arl1(5.0, 1.0) == pytest.approx(10.3, rel=0.05)


def test_simulated_in_control_arl_matches_theory():
    fa = first_alarm_times([5.0], 0.0, 1500, 10000, 0.5, np.random.default_rng(3))[0]
    assert np.isnan(fa).mean() < 0.01
    assert np.nanmean(fa) == pytest.approx(siegmund_arl0(5.0), rel=0.10)


def test_delay_decreases_with_shift_and_arl0_increases_with_threshold():
    rng = np.random.default_rng(4)
    d1 = np.nanmean(first_alarm_times([5.0], 1.0, 500, 2000, 0.5, rng)[0])
    d3 = np.nanmean(first_alarm_times([5.0], 3.0, 500, 2000, 0.5, rng)[0])
    assert d3 < d1
    assert siegmund_arl0(8.0) > siegmund_arl0(5.0) > siegmund_arl0(3.0)
