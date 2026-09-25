"""Photocentre orbit from Gaia's Thiele-Innes elements (docs/simulation_plan.md): offsets in mas relative to the barycentre."""
import numpy as np

DAYS_PER_YEAR = 365.25
J2010 = 2010.0  # `t_periastron` of the DR3 NSS tables is given in days since J2010.0 (BJD - 2455197.5); checked against the control case


def kepler_E(M: np.ndarray, e: float, iters: int = 60) -> np.ndarray:
    """Eccentric anomaly by Newton's method (vectorised over M); safe up to e = 0.99."""
    M = np.mod(M, 2 * np.pi)
    E = M + e * np.sin(M) if e < 0.8 else np.full_like(M, np.pi)
    for _ in range(iters):
        f = E - e * np.sin(E) - M
        E = E - f / (1 - e * np.cos(E))
    return E


def thiele_innes_offsets(t_jyr, A, B, F, G, e, P_days, tperi_days):
    """Offsets (d_alpha*, d_delta) in mas at times `t_jyr` (Julian years). Gaia convention:
    d_alpha* = B X + G Y, d_delta = A X + F Y with X = cos E - e, Y = sqrt(1 - e^2) sin E."""
    t_days = (np.asarray(t_jyr, float) - J2010) * DAYS_PER_YEAR
    E = kepler_E(2 * np.pi * (t_days - tperi_days) / P_days, e)
    X, Y = np.cos(E) - e, np.sqrt(1 - e * e) * np.sin(E)
    return B * X + G * Y, A * X + F * Y
