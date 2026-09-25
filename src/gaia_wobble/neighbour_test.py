"""Backtest check: are DR2 stars with a close DR2 neighbour less often real targets? (Gaia DR2 positions only, no leakage.)"""
import duckdb
import numpy as np
import pandas as pd
from astropy.table import Table
from scipy.stats import fisher_exact

from .download import run_async
from .model_a import load
from .paths import PROCESSED

HEIDELBERG = "https://gaia.ari.uni-heidelberg.de/tap"
RADIUS_ARCSEC = 2.0


def neighbours(df: pd.DataFrame, batch: int = 3000) -> pd.Series:
    """Neighbour counts within 2" from Gaia DR2; long uploads hang on the server, so the query runs in batches."""
    parts = []
    for i in range(0, len(df), batch):
        parts.append(_neighbours_batch(df.iloc[i : i + batch]))
        print(f"  neighbours: {min(i + batch, len(df))}/{len(df)}", flush=True)
    return pd.concat(parts)


def _neighbours_batch(df: pd.DataFrame) -> pd.Series:
    t = Table({"source_id": df.source_id.to_numpy("int64"), "ra": df.ra.to_numpy(float), "dec": df.dec.to_numpy(float)})
    q = f"""SELECT u.source_id, count(*) AS n FROM TAP_UPLOAD.ids u
            JOIN gaiadr2.gaia_source g ON 1 = CONTAINS(POINT('ICRS', g.ra, g.dec), CIRCLE('ICRS', u.ra, u.dec, {RADIUS_ARCSEC / 3600}))
            WHERE g.source_id <> u.source_id GROUP BY u.source_id"""
    r = run_async(q, uploads={"ids": t}, url=HEIDELBERG, wall_clock=300).to_pandas().set_index("source_id").n
    return df.source_id.map(r).fillna(0).astype(int)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    df = load(10)
    pos = duckdb.sql(f"SELECT source_id, ra, dec FROM '{PROCESSED}/features_dr2.parquet'").df()
    df = df.merge(pd.read_parquet(PROCESSED / "oof_physics_dr2.parquet"), on="source_id").merge(pos, on="source_id")
    top = df.sort_values("score", ascending=False).head(2000)
    sample = pd.concat([top, df[df.y & ~df.source_id.isin(top.source_id)], df[~df.y].sample(5000, random_state=0)]).drop_duplicates("source_id")
    sample["nb"] = neighbours(sample).to_numpy()
    sample.to_parquet(PROCESSED / "neighbour_test_dr2.parquet", index=False)
    top = sample[sample.source_id.isin(top.source_id)].copy()
    top["has_nb"] = top.nb > 0
    tab = top.groupby("has_nb").agg(n=("y", "size"), hits=("y", "sum"), hit_rate=("y", "mean"))
    print(tab.round(4).to_string())
    a, b = tab.loc[True], tab.loc[False]
    odds, p = fisher_exact([[a.hits, a.n - a.hits], [b.hits, b.n - b.hits]])
    print(f"rate ratio (neighbour / none) = {a.hit_rate / b.hit_rate:.2f}, Fisher p = {p:.4f}")
    print("neighbour share: top 100", round((top.head(100).nb > 0).mean(), 3), "| top 2000", round(top.has_nb.mean(), 3),
          "| all targets", round((sample[sample.y].nb > 0).mean(), 3), "| random negatives", round((sample.sample(frac=1, random_state=0)[~sample.y].nb > 0).mean(), 3))
    for k in (100, 1000):
        t = top.head(k); print(f"top {k}: neighbour share {(t.nb > 0).mean():.3f}, hit rate with nb {t[t.nb > 0].y.mean():.3f} / without {t[t.nb == 0].y.mean():.3f}")
