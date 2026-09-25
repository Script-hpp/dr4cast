"""Do the top-ranked stars without a DR3 orbit look like future orbit solutions? Evaluation only, no training.

DR3's `nss_acceleration_astro` holds stars whose motion is curved but whose observing time was too short for a full orbit; they are
likely candidates for an orbit in DR4 (66 instead of 34 months). We map the DR2 ids of the top-K stars (and of two control samples)
to DR3 via dr2_neighbourhood (upload of the DR2 ids, smallest angular distance) and count NSS solution types.
"""
import sys

import duckdb
import numpy as np
import pandas as pd
import pyvo
from astropy.table import Table

from .download import TAP_URL, run_async
from .paths import PROCESSED, RAW

LINK = """SELECT n.dr2_source_id, n.dr3_source_id, n.angular_distance
FROM gaiadr3.dr2_neighbourhood AS n JOIN tap_upload.ids AS u ON u.source_id = n.dr2_source_id"""


def links(dr2_ids: np.ndarray) -> pd.DataFrame:
    t = run_async(LINK, uploads={"ids": Table({"source_id": dr2_ids.astype("int64")})}, wall_clock=900).to_pandas()
    return t.sort_values("angular_distance").drop_duplicates("dr2_source_id")[["dr2_source_id", "dr3_source_id"]]


def nss_types() -> pd.DataFrame:
    return duckdb.sql(f"""
        SELECT source_id AS dr3_source_id, list(DISTINCT nss_solution_type) AS types FROM (
          SELECT source_id, nss_solution_type FROM '{RAW}/nss/nss_two_body_orbit.parquet'
          UNION ALL SELECT source_id, nss_solution_type FROM '{RAW}/nss/nss_acceleration_astro.parquet'
          UNION ALL SELECT source_id, nss_solution_type FROM '{RAW}/nss/nss_non_linear_spectro.parquet') GROUP BY 1""").df()


def summarize(name: str, ids: np.ndarray, nss: pd.DataFrame) -> dict:
    lk = links(ids).merge(nss, on="dr3_source_id", how="left")
    has = lk.types.map(lambda t: t if isinstance(t, (list, np.ndarray)) else [])
    kinds = lambda pred: float(has.map(lambda t: any(pred(x) for x in t)).mean())
    return {"n": len(ids), "linked": len(lk) / len(ids),
            "any_orbit": kinds(lambda x: x.startswith("Orbital")),
            "acceleration": kinds(lambda x: x.startswith("Acceleration")),
            "any_NSS": kinds(lambda x: True)}


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "full"
    oof = pd.read_parquet(PROCESSED / f"oof_{variant}_dr2.parquet")
    f = duckdb.sql(f"SELECT source_id, parallax_over_error, phot_g_mean_mag, ruwe_z FROM '{PROCESSED}/features_dr2.parquet' "
                   "WHERE parallax_over_error >= 10").df()
    t = duckdb.sql(f"SELECT source_id, excluded FROM '{PROCESSED}/targets_dr2.parquet'").df()
    d = oof.merge(f, on="source_id").merge(t, on="source_id", how="left")
    d = d[~d.excluded.fillna(False).astype(bool)]
    d["has_dr3_orbit_row"] = d.source_id.isin(duckdb.sql(f"SELECT dr2 FROM (SELECT arg_min(dr2_source_id, angular_distance) dr2 "
        f"FROM '{RAW}/dr2_links/orbit_solutions.parquet' GROUP BY dr3_source_id)").df().dr2)
    top = d.sort_values("score", ascending=False).head(1000)
    top_noorb = top[~top.has_dr3_orbit_row]
    rest = d[~d.has_dr3_orbit_row & ~d.source_id.isin(top.source_id)]
    rng = np.random.default_rng(0)
    pop = rest.sample(20000, random_state=0)
    # feature-matched control: same quality/brightness/wobble range as the top-1000-without-orbit
    lo, hi = top_noorb[["parallax_over_error", "phot_g_mean_mag", "ruwe_z"]].quantile(.05), top_noorb[["parallax_over_error", "phot_g_mean_mag", "ruwe_z"]].quantile(.95)
    m = rest[(rest.parallax_over_error.between(lo.parallax_over_error, hi.parallax_over_error))
             & (rest.phot_g_mean_mag.between(lo.phot_g_mean_mag, hi.phot_g_mean_mag)) & (rest.ruwe_z.between(lo.ruwe_z, hi.ruwe_z))]
    matched = m.sample(min(20000, len(m)), random_state=0)
    nss = nss_types()
    res = {"top-1000 without DR3 orbit": summarize("top", top_noorb.source_id.to_numpy(), nss),
           "random population (no DR3 orbit)": summarize("pop", pop.source_id.to_numpy(), nss),
           "feature-matched control (no DR3 orbit)": summarize("matched", matched.source_id.to_numpy(), nss)}
    print(pd.DataFrame(res).T.round(4).to_string())
