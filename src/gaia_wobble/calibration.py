"""Expected RUWE as a function of G magnitude and BP-RP colour, calibrated per Gaia release.

RUWE of a single, well-behaved star still depends on brightness and colour. The wobble signal is the
deviation from that expectation, so we tabulate robust quantiles per (G bin, colour bin) with
`fit_ruwe_grid` and apply them with `apply_ruwe_grid`.

Robustness: median and 16/84 percentiles, so that the wobbling minority does not move the expectation.
Cells with fewer than MIN_N stars fall back to the G-only bin, which in turn falls back to the global value.
The calibration sample is the release's own nearby-star table (a larger sky sample is planned, see MANIFEST).
"""
import duckdb

from .paths import PROCESSED

G_STEP = 0.25
COLOUR_STEP = 0.2
MIN_N = 100


def _bins(g="phot_g_mean_mag", c="bp_rp"):
    return (
        f"floor({g} / {G_STEP})::INTEGER AS g_bin, "
        f"CASE WHEN {c} IS NULL THEN NULL ELSE floor(greatest(least({c}, 4.4), -0.4) / {COLOUR_STEP})::INTEGER END AS c_bin"
    )


def fit_ruwe_grid(parquet_glob: str, release: str) -> None:
    """Write data/processed/ruwe_grid_<release>.parquet with columns g_bin, c_bin, level, n, med, sig."""
    q = f"""
    CREATE OR REPLACE TABLE s AS
      SELECT ruwe, {_bins()} FROM '{parquet_glob}' WHERE ruwe IS NOT NULL AND phot_g_mean_mag IS NOT NULL;
    COPY (
      SELECT g_bin, c_bin, 'cell' AS level, count(*) n, quantile_cont(ruwe, .5) med,
             (quantile_cont(ruwe, .84) - quantile_cont(ruwe, .16)) / 2 sig
      FROM s GROUP BY g_bin, c_bin HAVING count(*) >= {MIN_N}
      UNION ALL
      SELECT g_bin, NULL, 'g_only', count(*), quantile_cont(ruwe, .5),
             (quantile_cont(ruwe, .84) - quantile_cont(ruwe, .16)) / 2
      FROM s GROUP BY g_bin HAVING count(*) >= {MIN_N}
      UNION ALL
      SELECT NULL, NULL, 'global', count(*), quantile_cont(ruwe, .5),
             (quantile_cont(ruwe, .84) - quantile_cont(ruwe, .16)) / 2
      FROM s
    ) TO '{PROCESSED}/ruwe_grid_{release}.parquet' (FORMAT parquet)
    """
    PROCESSED.mkdir(parents=True, exist_ok=True)
    duckdb.sql(q)


def apply_ruwe_grid(parquet_glob: str, release: str) -> "duckdb.DuckDBPyRelation":
    """Per star: ruwe_expected, ruwe_sigma, ruwe_excess = ruwe - expected, ruwe_z = excess / sigma, calib_level."""
    grid = f"'{PROCESSED}/ruwe_grid_{release}.parquet'"
    return duckdb.sql(f"""
    WITH t AS (SELECT source_id, ruwe, {_bins()} FROM '{parquet_glob}'),
    cell AS (SELECT * FROM {grid} WHERE level = 'cell'),
    gonly AS (SELECT * FROM {grid} WHERE level = 'g_only'),
    gl AS (SELECT * FROM {grid} WHERE level = 'global')
    SELECT t.source_id, t.ruwe,
           coalesce(cell.med, gonly.med, gl.med) AS ruwe_expected,
           coalesce(cell.sig, gonly.sig, gl.sig) AS ruwe_sigma,
           t.ruwe - coalesce(cell.med, gonly.med, gl.med) AS ruwe_excess,
           (t.ruwe - coalesce(cell.med, gonly.med, gl.med)) / coalesce(cell.sig, gonly.sig, gl.sig) AS ruwe_z,
           CASE WHEN cell.med IS NOT NULL THEN 'cell' WHEN gonly.med IS NOT NULL THEN 'g_only' ELSE 'global' END AS calib_level
    FROM t
    LEFT JOIN cell ON t.g_bin = cell.g_bin AND t.c_bin IS NOT DISTINCT FROM cell.c_bin
    LEFT JOIN gonly ON t.g_bin = gonly.g_bin
    CROSS JOIN gl
    """)
