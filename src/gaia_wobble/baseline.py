"""Backtest DR2->DR3 baselines: rank DR2 stars by RUWE-based scores, evaluate against the DR3 orbit target."""
import duckdb
import pandas as pd

from .metrics import evaluate, evaluate_by_brightness, evaluate_curve
from .paths import PROCESSED


def load_backtest(min_poe: float | None) -> pd.DataFrame:
    """DR2 population with target y = y_lt80 (or y_lt13 via column `y13`); excluded (unknown-label) stars are dropped."""
    where = "" if min_poe is None else f"AND f.parallax_over_error >= {min_poe}"
    return duckdb.sql(f"""
        SELECT f.source_id, f.phot_g_mean_mag, f.ruwe, f.ruwe_z, f.ruwe_excess, f.astrometric_excess_noise_sig,
               coalesce(t.y_lt80, false) AS y, coalesce(t.y_lt13, false) AS y13,
               l.source_id IS NOT NULL AS known_planet
        FROM '{PROCESSED}/features_dr2.parquet' f
        LEFT JOIN '{PROCESSED}/targets_dr2.parquet' t USING (source_id)
        LEFT JOIN (SELECT DISTINCT source_id FROM '{PROCESSED}/labels_backtest_dr2.parquet') l USING (source_id)
        WHERE coalesce(t.excluded, false) = false {where}
    """).df()


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    for min_poe in (None, 5, 10):
        df = load_backtest(min_poe)
        print(f"\n=== DR2 filter parallax_over_error >= {min_poe}: {len(df):,} stars, "
              f"{int(df.y.sum())} targets <80 MJ, {int(df.y13.sum())} <13 MJ, {int(df.known_planet.sum())} known hosts")
        for score in ("ruwe", "ruwe_z", "astrometric_excess_noise_sig"):
            print(f"-- score: {score} (target <80 M_Jup)")
            print(evaluate(df, score).round(3).to_string())
            print(evaluate_curve(df, score).round(4).to_string())
