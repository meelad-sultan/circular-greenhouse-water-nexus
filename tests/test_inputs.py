import numpy as np

from cgwn.climate import et_m3_per_h, synth_climate
from cgwn.events import make_source


def test_climate_shapes_and_determinism(cfg):
    a = synth_climate(cfg["site"], 30, np.random.default_rng(1))
    b = synth_climate(cfg["site"], 30, np.random.default_rng(1))
    assert a.hours == 720
    np.testing.assert_array_equal(a.r_in, b.r_in)
    assert (a.r_in >= 0).all() and (a.vpd >= 0).all() and a.r_in.min() == 0.0


def test_et_nonnegative_and_summer_exceeds_winter(cfg):
    c = synth_climate(cfg["site"], 365, np.random.default_rng(2))
    et = et_m3_per_h(c, cfg["crop"])
    assert (et >= 0).all()
    daily = et.reshape(365, 24).sum(axis=1)
    assert daily[150:240].mean() > daily[330:360].mean()


def test_source_without_events_is_constant(cfg):
    c, tss = make_source(cfg, "S1", 100, np.random.default_rng(0))
    assert c.shape == (100, 6) and np.ptp(c, axis=0).max() == 0.0 and (tss == 15).all()


def test_events_only_increase_concentrations_and_are_reproducible(cfg):
    c1, _ = make_source(cfg, "S2", 8760, np.random.default_rng(5))
    c2, _ = make_source(cfg, "S2", 8760, np.random.default_rng(5))
    base, _ = make_source(cfg, "S1", 8760, np.random.default_rng(5))
    np.testing.assert_array_equal(c1, c2)
    assert (c1 >= base - 1e-12).all() and (c1 > base).any()


def test_scale_multiplies_baseline(cfg_copy):
    cfg_copy["scenarios"]["S1"]["scale"] = 2.0
    c, _ = make_source(cfg_copy, "S1", 10, np.random.default_rng(0))
    assert c[0, 0] == 1.0  # Cd baseline 0.5 x 2
