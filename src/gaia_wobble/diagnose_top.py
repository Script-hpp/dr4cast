"""Diagnose the top of the DR3 ranking: SIMBAD object types and close Gaia neighbours, against a matched control.

Evaluation only (nothing here enters the model). Known cases (DR3 orbit < 80 M_Jup, known planet) are excluded first.
"""
import duckdb
import numpy as np
import pandas as pd
from astropy.table import Table

from .download import run_async
from .paths import PREDICTIONS, PROCESSED

SIMBAD = "https://simbad.cds.unistra.fr/simbad/sim-tap"
HEIDELBERG = "https://gaia.ari.uni-heidelberg.de/tap"


def load(top_n: int = 100, control_n: int = 1000) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = pd.read_parquet(PREDICTIONS / "dev_dr3_scores_model_a_physics.parquet")
    f = duckdb.sql(f"SELECT source_id, ra, dec, parallax_over_error, phot_g_mean_mag, ruwe_z FROM '{PROCESSED}/features_dr3.parquet'").df()
    d = s.merge(f, on="source_id")
    d = d[~d.known_dr3_orbit80 & ~d.known_planet]
    top = d.sort_values("score", ascending=False).head(top_n)
    rest = d[~d.source_id.isin(top.source_id)]
    q = top[["parallax_over_error", "phot_g_mean_mag", "ruwe_z"]].quantile([.05, .95])
    m = rest[rest.parallax_over_error.between(*q.parallax_over_error) & rest.phot_g_mean_mag.between(*q.phot_g_mean_mag)
             & rest.ruwe_z.between(*q.ruwe_z)]
    return top, m.sample(min(control_n, len(m)), random_state=0)


def simbad_types(ids: np.ndarray) -> pd.DataFrame:
    t = Table({"source_id": ids.astype("int64"), "gid": np.array([f"Gaia DR3 {i}" for i in ids])})
    q = """SELECT u.source_id, b.main_id, b.otype FROM TAP_UPLOAD.ids u
           JOIN ident i ON i.id = u.gid JOIN basic b ON b.oid = i.oidref"""
    return run_async(q, uploads={"ids": t}, url=SIMBAD, wall_clock=600).to_pandas().drop_duplicates("source_id")


def close_neighbours(df: pd.DataFrame, radius_arcsec: float = 2.0) -> pd.Series:
    t = Table({"source_id": df.source_id.to_numpy("int64"), "ra": df.ra.to_numpy(float), "dec": df.dec.to_numpy(float)})
    q = f"""SELECT u.source_id, count(*) AS n_neighbours FROM TAP_UPLOAD.ids u
            JOIN gaiadr3.gaia_source g ON 1 = CONTAINS(POINT('ICRS', g.ra, g.dec), CIRCLE('ICRS', u.ra, u.dec, {radius_arcsec / 3600}))
            WHERE g.source_id <> u.source_id GROUP BY u.source_id"""
    r = run_async(q, uploads={"ids": t}, url=HEIDELBERG, wall_clock=900).to_pandas().set_index("source_id").n_neighbours
    return df.source_id.map(r).fillna(0).astype(int)


def summarize(name: str, df: pd.DataFrame) -> dict:
    sb = simbad_types(df.source_id.to_numpy())
    df = df.merge(sb, on="source_id", how="left")
    o = df.otype.fillna("")
    out = {"n": len(df), "in SIMBAD": df.main_id.notna().mean(),
           "binary (SB*, EB*, **, El*)": o.str.contains(r"SB\*|EB\*|\*\*|El\*|\*i\*").mean(),
           "young (Y*O, TT*, Or*)": o.str.contains(r"Y\*O|TT\*|Or\*|pr\*").mean(),
           "white dwarf (WD*)": o.str.contains(r"WD\*").mean(),
           "variable/flare (V*, Fl*, BY*, RS*)": o.str.contains(r"V\*|Fl\*|BY\*|RS\*|Pu\*|\*\*\*").mean()}
    out["neighbour within 2\""] = (close_neighbours(df) > 0).mean()
    return out, df


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    top, ctrl = load()
    res, top_named = summarize("top", top)
    res_c, _ = summarize("control", ctrl)
    print(pd.DataFrame({"top 100 (new)": res, "matched control": res_c}).round(3).to_string())
    print("\nSIMBAD types in the top 100:"); print(top_named.otype.fillna("(not in SIMBAD)").value_counts().head(12).to_string())
    top_named.to_parquet(PREDICTIONS / "dev_top100_simbad.parquet", index=False)
