"""Feature and target tables for DR2 (backtest) and DR3 (bet).

`COMMON` columns are computed identically for both releases: Model A trains on DR2 and is applied to DR3,
so it may only use columns that exist in both. DR3-only columns (ipd_*, NSS flag, ...) are stored in
features_dr3 but are not part of `COMMON`.
"""
import duckdb

from .paths import PROCESSED, RAW

COMMON = [
    "parallax", "parallax_error", "parallax_over_error", "pm_total", "dist_pc", "phot_g_mean_mag", "bp_rp", "abs_g",
    "phot_g_n_obs", "astrometric_excess_noise", "astrometric_excess_noise_sig", "astrometric_chi2_al",
    "astrometric_n_obs_al", "astrometric_n_good_obs_al", "chi2_per_dof", "visibility_periods_used",
    "ruwe", "ruwe_expected", "ruwe_excess", "ruwe_z",
    "hg_dpm_gaia", "hg_sig_gaia", "hg_dpm_hip", "hg_sig_hip", "has_hgca",
]
DR3_ONLY = ["ipd_gof_harmonic_amplitude", "ipd_frac_multi_peak", "ipd_frac_odd_win", "non_single_star"]

_HGCA = """
SELECT source_id,
  sqrt((pmra_gaia - pmra_hg)^2 + (pmdec_gaia - pmdec_hg)^2) AS hg_dpm_gaia,
  sqrt(((pmra_gaia - pmra_hg) / sqrt(pmra_gaia_error^2 + pmra_hg_error^2))^2
     + ((pmdec_gaia - pmdec_hg) / sqrt(pmdec_gaia_error^2 + pmdec_hg_error^2))^2) AS hg_sig_gaia,
  sqrt((pmra_hip - pmra_hg)^2 + (pmdec_hip - pmdec_hg)^2) AS hg_dpm_hip,
  sqrt(((pmra_hip - pmra_hg) / sqrt(pmra_hip_error^2 + pmra_hg_error^2))^2
     + ((pmdec_hip - pmdec_hg) / sqrt(pmdec_hip_error^2 + pmdec_hg_error^2))^2) AS hg_sig_hip
FROM (SELECT * FROM '{path}' QUALIFY row_number() OVER (PARTITION BY source_id ORDER BY hip_id) = 1)
"""  # duplicated ids (4 in the DR2 edition): keep the row with the smallest HIP number


def _features(release: str, hgca: str, extra: str) -> None:
    ruwe_glob = f"{RAW}/{'dr2' if release == 'dr2' else 'dr3'}_nearby/*.parquet"
    duckdb.sql(f"""
    COPY (
      SELECT g.source_id, g.ra, g.dec, g.parallax, g.parallax_error,
        g.parallax / g.parallax_error AS parallax_over_error,
        sqrt(g.pmra^2 + g.pmdec^2) AS pm_total, 1000 / g.parallax AS dist_pc,
        g.phot_g_mean_mag, g.bp_rp, g.phot_g_mean_mag + 5 * log10(g.parallax) - 10 AS abs_g,
        g.phot_g_n_obs, g.astrometric_excess_noise, g.astrometric_excess_noise_sig, g.astrometric_chi2_al,
        g.astrometric_n_obs_al, g.astrometric_n_good_obs_al,
        g.astrometric_chi2_al / nullif(g.astrometric_n_good_obs_al - 5, 0) AS chi2_per_dof,
        g.visibility_periods_used,
        r.ruwe, r.ruwe_expected, r.ruwe_excess, r.ruwe_z, r.calib_level,
        h.hg_dpm_gaia, h.hg_sig_gaia, h.hg_dpm_hip, h.hg_sig_hip, h.source_id IS NOT NULL AS has_hgca{extra}
      FROM '{ruwe_glob}' g
      JOIN '{PROCESSED}/ruwe_features_{release}.parquet' r USING (source_id)
      LEFT JOIN ({_HGCA.format(path=hgca)}) h USING (source_id)
    ) TO '{PROCESSED}/features_{release}.parquet' (FORMAT parquet)""")


def build_features() -> None:
    _features("dr2", f"{RAW}/hgca/hgca_dr2.parquet", "")
    _features("dr3", f"{RAW}/hgca/hgca_edr3.parquet",
              ", " + ", ".join(f"g.{c}" for c in DR3_ONLY))


def build_targets_dr2() -> None:
    """Outcome per DR2 star, from the DR3 orbit solution linked to it via dr2_neighbourhood (smallest angular distance).

    y_lt80 / y_lt13: linked `Orbital` solution with estimated m2 below the limit.
    excluded: label unknown, kept out of training and evaluation as positive AND negative:
      linked Orbital solution without m1 (no mass estimate), or OrbitalTargetedSearch* / OrbitalAlternative* solution.
    """
    duckdb.sql(f"""
    COPY (
      WITH lk AS (
        SELECT dr3_source_id, arg_min(dr2_source_id, angular_distance) AS source_id
        FROM '{RAW}/dr2_links/orbit_solutions.parquet' GROUP BY 1),
      sol AS (
        SELECT n.source_id AS dr3_source_id, n.nss_solution_type AS typ, t.m2_est_mjup
        FROM '{RAW}/nss/nss_two_body_orbit.parquet' n
        LEFT JOIN '{PROCESSED}/dr3_orbit_targets.parquet' t USING (source_id)
        WHERE n.nss_solution_type LIKE 'Orbital%'),
      j AS (SELECT lk.source_id, sol.* FROM sol JOIN lk USING (dr3_source_id))
      SELECT source_id,
        bool_or(typ = 'Orbital' AND m2_est_mjup < 80) AS y_lt80,
        bool_or(typ = 'Orbital' AND m2_est_mjup < 13) AS y_lt13,
        bool_or(typ <> 'Orbital') AS targeted_or_alt,
        bool_or(typ = 'Orbital' AND m2_est_mjup IS NULL) AS orbital_no_mass,
        bool_or(typ <> 'Orbital' OR m2_est_mjup IS NULL) AS excluded
      FROM j GROUP BY source_id
    ) TO '{PROCESSED}/targets_dr2.parquet' (FORMAT parquet)""")


if __name__ == "__main__":
    build_features()
    build_targets_dr2()
