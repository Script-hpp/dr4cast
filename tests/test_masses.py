import numpy as np

from gaia_wobble.masses import M_JUP, photocentre_a0_mas, solve_m2


def test_thiele_innes_circular_face_on():
    # face-on circular orbit of semi-major axis a: A = a, B = 0, F = 0, G = a  ->  a0 = a
    assert np.isclose(photocentre_a0_mas(2.0, 0.0, 0.0, 2.0), 2.0)


def test_jupiter_around_sun():
    # Sun's reflex orbit due to Jupiter: a1 = 5.2 AU * m2/(m1+m2), P = 11.86 yr
    m2 = 9.55e-4
    a1 = 5.2 * m2 / (1 + m2)
    est = solve_m2(np.array([a1]), np.array([11.86 * 365.25]), np.array([1.0]))[0]
    assert abs(est / m2 - 1) < 0.02
