"""Simulate what Gaia's astrometric fit reports for one star (docs/simulation_plan.md, 'Aufbau der Simulation eines Sterns')."""
import astromet
import gaiascanlaw
import numpy as np

NMEASURE = 9  # single measurements per transit; astrometric_n_obs_al = 9 * transits in the catalogue
_G_MIN, _G_MAX = float(astromet.mags.min()), float(astromet.mags.max())


def sigma_al(G: float, s: float = 1.0) -> float:
    """Single-measurement along-scan error in mas (astromet: Lindegren et al. 2020, Fig. A.1, digitised), scaled by s."""
    return float(s * astromet.sigma_ast(np.clip(G, _G_MIN, _G_MAX)))


def nominal_transits(ra: float, dec: float, window: str = "dr3"):
    """Nominal transit times (Julian years) and scan angles (rad) for one position, astrometric transits only."""
    end = {"dr3": gaiascanlaw.tdr3, "dr4": gaiascanlaw.tdr4}[window]
    return gaiascanlaw.scanlaw(ra, dec, tstart=gaiascanlaw.tstart, tend=end, obstype="astrometry")


def thinned_transits(ra, dec, n_transits: int, rng, window: str = "dr3", nominal=None):
    """Plan rule: thin the nominal DR3 transits to the star's real number; take all if fewer (flag returned).
    DR4: keep the same share (real number / nominal DR3 number) of the nominal DR4 transits."""
    t3, p3 = nominal if nominal is not None else nominal_transits(ra, dec, "dr3")
    short = len(t3) < n_transits
    if window == "dr3":
        keep = np.sort(rng.choice(len(t3), min(n_transits, len(t3)), replace=False))
        return t3[keep], p3[keep], short
    t4, p4 = nominal_transits(ra, dec, "dr4")
    share = min(1.0, n_transits / max(len(t3), 1))
    keep = np.sort(rng.choice(len(t4), int(round(share * len(t4))), replace=False))
    return t4[keep], p4[keep], short


def simulate_star(ra, dec, G, n_transits, rng, offsets=None, s: float = 1.0, window: str = "dr3", nominal=None) -> dict:
    """One noise realisation. `offsets(t) -> (d_alpha*, d_delta)` in mas adds a photocentre orbit; None = single star.
    Returns astromet's fit outputs: uwe, excess_noise, chi2, n_good_obs, vis_periods, n_obs, plus n_transits used and a `short` flag."""
    t, phi, short = thinned_transits(ra, dec, n_transits, rng, window, nominal)
    ts, phis = np.repeat(t, NMEASURE), np.repeat(phi, NMEASURE)
    sig = sigma_al(G, s)
    x = rng.normal(0.0, sig, ts.size)
    if offsets is not None:
        da, dd = offsets(ts)
        x = x + da * np.sin(phis) + dd * np.cos(phis)   # astromet convention: phi = 0 north, pi/2 east
    r = astromet.fit(ts, x, phis, sig, ra, dec, G=G, epoch=2016.0)
    return {"uwe": float(r["uwe"]), "excess_noise": float(r["excess_noise"]), "chi2": float(r["chi2"]), "n_good_obs": int(r["n_good_obs"]),
            "vis_periods": int(r["vis_periods"]), "n_obs": int(r["n_obs"]), "n_transits_used": len(t), "short": bool(short)}
