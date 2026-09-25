"""Wobble amplitude and companion-mass probability from the single-star astrometric fit (method: see docs/experiment_log.md).

sigma_formal follows Eq. 8 of Kiefer et al. (2025, arXiv 2409.16992): sigma_formal = AEN * (chi2/(N-5) - 1)^(-1/2), median per (G, BP-RP) bin
over sources with significant excess noise. The amplitude estimate inverts it, AEN_est = sigma_formal * sqrt(max(chi2/(N-5) - 1, 0)),
which stays available where the catalogue AEN is zero. a_est = sqrt(2) * AEN_est assumes a circular orbit with period within the baseline.
"""
import duckdb
import numpy as np
import pandas as pd

from .masses import solve_m2
from .paths import PROCESSED

M_JUP = 9.5479e-4
G_STEP, COLOUR_STEP, MIN_N = 0.25, 0.25, 50
PERIODS_YR = np.geomspace(0.5, 5.0, 25)  # log-uniform period grid used for P(m2 < 13 M_Jup)


def _bins(df: pd.DataFrame):
    return np.floor(df.phot_g_mean_mag / G_STEP), np.floor(df.bp_rp.clip(-1, 5) / COLOUR_STEP)


def sigma_formal_grid(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    d = df[(df.astrometric_excess_noise_sig >= 2) & (df.chi2_per_dof > 1) & (df.astrometric_excess_noise > 0)].copy()
    d["sf"] = d.astrometric_excess_noise / np.sqrt(d.chi2_per_dof - 1)
    g, c = _bins(d)
    cell = d.groupby([g, c]).sf.agg(["median", "size"])
    cell = cell[cell["size"] >= MIN_N]["median"]
    gonly = d.groupby(g).sf.agg(["median", "size"])
    gonly = gonly[gonly["size"] >= MIN_N]["median"]
    return cell, gonly


def add_amplitude(df: pd.DataFrame, grid=None) -> pd.DataFrame:
    cell, gonly = grid or sigma_formal_grid(df)
    g, c = _bins(df)
    key = pd.MultiIndex.from_arrays([g, c])
    sf = pd.Series(cell.reindex(key).to_numpy(), index=df.index)
    sf = sf.fillna(pd.Series(gonly.reindex(g).to_numpy(), index=df.index)).fillna(np.nanmedian(cell))
    aen = sf * np.sqrt(np.maximum(df.chi2_per_dof - 1, 0))
    out = df.copy()
    out["sigma_formal_mas"], out["aen_est_mas"], out["amp_est_mas"] = sf, aen, np.sqrt(2) * aen
    return out


def p_below(df: pd.DataFrame, limit_mjup: float = 13.0) -> np.ndarray:
    """Share of the log-uniform period range (0.5-5 yr) for which the implied companion mass is below the limit."""
    a1_au = (df.amp_est_mas / df.parallax).to_numpy(float)
    m1 = df.mass_ms.to_numpy(float)
    below = np.zeros(len(df))
    for p in PERIODS_YR:
        m2 = solve_m2(a1_au, np.full(len(df), p * 365.25), m1)
        below += (m2 < limit_mjup * M_JUP)
    return below / len(PERIODS_YR)


if __name__ == "__main__":
    from scipy.stats import spearmanr

    pd.set_option("display.width", 200)
    cols = "source_id, phot_g_mean_mag, bp_rp, parallax, mass_ms, chi2_per_dof, astrometric_excess_noise, astrometric_excess_noise_sig"
    for release in ("dr2", "dr3"):
        f = duckdb.sql(f"SELECT {cols} FROM '{PROCESSED}/features_{release}.parquet' WHERE chi2_per_dof IS NOT NULL").df()
        f = add_amplitude(f)
        print(release, "sigma_formal median (mas):", round(f.sigma_formal_mas.median(), 3), "| a_est median (mas):", round(f.amp_est_mas.median(), 3))
        f[["source_id", "sigma_formal_mas", "amp_est_mas"]].assign(p13=p_below(f)).to_parquet(PROCESSED / f"amplitude_{release}.parquet", index=False)
    # validation on DR3 Orbital solutions: true photocentre amplitude a0 from Thiele-Innes elements
    from .masses import photocentre_a0_mas

    v = duckdb.sql(f"""SELECT t.source_id, t.a_thiele_innes a, t.b_thiele_innes b, t.f_thiele_innes f, t.g_thiele_innes g, t.period, t.m2_est_mjup,
                      a.amp_est_mas, a.sigma_formal_mas, f.phot_g_mean_mag, f.astrometric_excess_noise
                      FROM '{PROCESSED}/dr3_orbit_targets.parquet' t JOIN '{PROCESSED}/amplitude_dr3.parquet' a USING (source_id)
                      JOIN '{PROCESSED}/features_dr3.parquet' f USING (source_id) WHERE t.nss_solution_type = 'Orbital'""").df()
    v["a0"] = photocentre_a0_mas(v.a, v.b, v.f, v.g)
    v["ratio"] = v.amp_est_mas / v.a0
    v["period_class"] = pd.cut(v.period, [0, 200, 500, 1200, 1e5], labels=["<200 d", "200-500 d", "500-1200 d", ">1200 d"])
    v["g_class"] = pd.cut(v.phot_g_mean_mag, [0, 10, 13, 16, 30], labels=["G<10", "10-13", "13-16", ">16"])
    print(f"\nvalidation on {len(v)} DR3 Orbital solutions: median ratio {v.ratio.median():.2f}, Spearman rho {spearmanr(v.amp_est_mas, v.a0)[0]:.2f}")
    for k in ("period_class", "g_class"):
        print(v.groupby(k, observed=True).apply(lambda d: pd.Series({"n": len(d), "median_ratio": d.ratio.median(), "rho": spearmanr(d.amp_est_mas, d.a0)[0]})).round(2).to_string())
    s = v[v.m2_est_mjup < 80]
    print(f"\nsubstellar subset (<80 M_Jup): n {len(s)}, median ratio {s.ratio.median():.2f}, rho {spearmanr(s.amp_est_mas, s.a0)[0]:.2f}")
