import numpy as np
import pytest

pytest.importorskip("astromet")
pytest.importorskip("gaiascanlaw")

from gaia_wobble.simulation.observe import simulate_star  # noqa: E402
from gaia_wobble.simulation.orbit import kepler_E, thiele_innes_offsets  # noqa: E402


def test_kepler_solution_satisfies_equation():
    M = np.linspace(0, 6.2, 50)
    for e in (0.0, 0.3, 0.9):
        E = kepler_E(M, e)
        assert np.allclose(E - e * np.sin(E), np.mod(M, 2 * np.pi), atol=1e-9)


def test_circular_face_on_orbit_has_constant_radius():
    t = np.linspace(2015.0, 2017.0, 200)
    da, dd = thiele_innes_offsets(t, A=1.0, B=0.0, F=0.0, G=1.0, e=0.0, P_days=400.0, tperi_days=0.0)
    assert np.allclose(np.hypot(da, dd), 1.0, atol=1e-9)


def test_single_star_uwe_is_near_one_and_big_orbit_raises_it():
    ra, dec, n = 210.0, 31.7, 50
    quiet = [simulate_star(ra, dec, 12.0, n, np.random.default_rng(i))["uwe"] for i in range(20)]
    assert 0.9 < np.median(quiet) < 1.15
    orbit = lambda t: thiele_innes_offsets(t, 0.6, 0.0, 0.0, 0.6, 0.3, 400.0, 100.0)  # 0.6 mas photocentre orbit, well above the noise
    wobble = [simulate_star(ra, dec, 12.0, n, np.random.default_rng(i), offsets=orbit)["uwe"] for i in range(20)]
    assert np.median(wobble) > 2 * np.median(quiet)
