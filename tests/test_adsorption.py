import numpy as np
import pytest

from cgwn.adsorption import Bed, thomas_fraction
from cgwn.system import BedSpec
from cgwn.validation import thomas_curve


def spec(a, cap=1000.0, K=20.0, w=None):
    a = np.array(a, float)
    return BedSpec("t", np.arange(len(a)), np.ones(len(a)) if w is None else np.array(w, float), a, cap, K, 1, 1, 1, 1)


def test_single_species_matches_thomas_formula():
    bed = Bed(spec([1.0], cap=500.0, K=12.0))
    fed = 0.0
    for _ in range(80):
        f = bed.f()[0]
        assert f == pytest.approx(float(thomas_fraction(fed / 500.0, 12.0)))
        bed.apply(np.array([10.0]))
        fed += 10.0


def test_consistent_with_validation_module_thomas_curve():
    c0, Q, m, q0, kth = 20.0, 5.0, 10.0, 25.0, 0.3
    K = kth * q0 * m / Q
    t = np.linspace(0, 6000, 25)
    S = c0 / 1000 * Q * t / (q0 * m)
    np.testing.assert_allclose(thomas_curve(t, q0, kth, c0, Q, m), thomas_fraction(S, K), atol=1e-9)


def test_mass_is_conserved_per_step():
    bed = Bed(spec([3.0, 1.0, 10.0], cap=800.0))
    rng = np.random.default_rng(0)
    for _ in range(200):
        m_in = rng.uniform(0, 20, 3)
        m_out = bed.apply(m_in)
        assert (m_out >= -1e-12).all() and (m_out <= m_in + 1e-12).all()


def test_higher_affinity_breaks_through_later():
    bed = Bed(spec([1.0, 10.0], cap=300.0))
    for _ in range(60):
        bed.apply(np.array([5.0, 5.0]))
    f = bed.f()
    assert f[0] > f[1]


def test_reset_restores_fresh_bed():
    bed = Bed(spec([1.0], cap=100.0))
    for _ in range(50):
        bed.apply(np.array([5.0]))
    assert bed.f()[0] > 0.5
    bed.reset()
    assert bed.f()[0] < 1e-6 and bed.smax() == 0.0


def test_single_species_loading_is_fed_over_capacity():
    bed = Bed(spec([7.0], cap=200.0))
    bed.apply(np.array([50.0]))
    assert bed.loading()[0] == pytest.approx(0.25)
