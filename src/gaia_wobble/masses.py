"""Companion mass estimate for DR3 astrometric orbits (nss_two_body_orbit, type Orbital).

Dark-companion assumption: all light comes from the primary, so the photocentre orbit equals the
primary's orbit around the barycentre, a1 = a0 / parallax. Kepler's third law then gives
    m2^3 / (m1 + m2)^2 = a1^3 / P^2      (a1 in AU, P in years, masses in M_sun)
Because Thiele-Innes elements carry the inclination, this is a true mass, not a minimum mass.
m1 comes from `binary_masses` (Gaia's own primary mass); solutions without m1 get no estimate.
"""
import numpy as np

M_JUP = 9.5479e-4  # M_sun per Jupiter mass


def photocentre_a0_mas(A, B, F, G):
    """Semi-major axis of the photocentre orbit (mas) from Thiele-Innes elements (Halbwachs+ 2023)."""
    u = (A**2 + B**2 + F**2 + G**2) / 2
    v = A * G - B * F
    return np.sqrt(u + np.sqrt(np.maximum(u**2 - v**2, 0)))


def solve_m2(a1_au, period_days, m1):
    """Solve m2^3 = K (m1 + m2)^2 for m2 (M_sun) by bisection; K = a1^3 / P^2."""
    K = a1_au**3 / (period_days / 365.25) ** 2
    lo, hi = np.zeros_like(K), np.full_like(K, 10.0)
    for _ in range(80):
        mid = (lo + hi) / 2
        too_big = mid**3 - K * (m1 + mid) ** 2 > 0
        hi = np.where(too_big, mid, hi)
        lo = np.where(too_big, lo, mid)
    return (lo + hi) / 2


def estimate_m2(nss, m1):
    """`nss`: DataFrame with a/b/f/g_thiele_innes, parallax, period; `m1`: Series (M_sun). Returns m2 in M_Jup."""
    a0 = photocentre_a0_mas(nss.a_thiele_innes, nss.b_thiele_innes, nss.f_thiele_innes, nss.g_thiele_innes)
    a1_au = a0 / nss.parallax
    m2 = solve_m2(a1_au.to_numpy(float), nss.period.to_numpy(float), m1.to_numpy(float))
    return m2 / M_JUP
