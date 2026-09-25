"""DR3 backtest target table: companion mass estimated from the astrometric orbit (see masses.py)."""
import duckdb

from .masses import estimate_m2
from .paths import INTERIM, PROCESSED, RAW

# gaiadr3.nss_two_body_orbit solutions Gaia listed as false positives (DR3 known issues, checked 2026-09-25):
# WD 0141-675, HIP 64690, 54 Cas, HIP 66074
RETRACTED = [4698424845771339520, 5765846127180770432, 522135261462534528, 1712614124767394816]

SQL = f"""
SELECT n.source_id, n.nss_solution_type, n.a_thiele_innes, n.b_thiele_innes, n.f_thiele_innes,
       n.g_thiele_innes, n.parallax, n.period, n.significance, b.m1, b.m2 AS m2_gaia_msun
FROM '{RAW}/nss/nss_two_body_orbit.parquet' n
LEFT JOIN (SELECT * FROM '{RAW}/dr3_tables/binary_masses.parquet'
           WHERE combination_method LIKE 'Orbital%') b USING (source_id)
WHERE n.nss_solution_type LIKE 'Orbital%'
  AND n.source_id NOT IN ({', '.join(map(str, RETRACTED))})
"""


def build_backtest_target():
    """One row per Orbital* solution with primary mass; adds m2_est_mjup and the two mass flags."""
    d = duckdb.sql(SQL).df()
    d = d[d.m1.notna() & d.a_thiele_innes.notna() & (d.parallax > 0) & (d.period > 0)].copy()
    d["m2_est_mjup"] = estimate_m2(d, d.m1)
    d["is_lt80"] = d.m2_est_mjup < 80
    d["is_lt13"] = d.m2_est_mjup < 13
    d["targeted_search"] = d.nss_solution_type.str.startswith("OrbitalTargetedSearch")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    d.to_parquet(PROCESSED / "dr3_orbit_targets.parquet", index=False)
    return d


if __name__ == "__main__":
    d = build_backtest_target()
    print(len(d), "solutions with m1")
    print(d.groupby("nss_solution_type")[["is_lt13", "is_lt80"]].sum())
