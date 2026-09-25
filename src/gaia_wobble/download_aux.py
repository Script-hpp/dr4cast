"""NSS tables (DR3) from the Heidelberg mirror and planet labels from the NASA Exoplanet Archive."""
import pyarrow as pa
import pyarrow.parquet as pq
import pyvo

from pathlib import Path

from .download import ADQL_DIR, TAP_URL, download_chunked, run_async, to_arrow
from .paths import RAW

NSS_TABLES = ["nss_two_body_orbit", "nss_acceleration_astro", "nss_non_linear_spectro", "nss_vim_fl"]
DR3_TABLES_FULL = ["binary_masses"]
SKIP = {"corr_vec", "bit_index"}  # array columns
NASA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP"


def download_nss(out_dir=RAW / "nss") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = pyvo.dal.TAPService(TAP_URL).tables
    for name in NSS_TABLES:
        out = out_dir / f"{name}.parquet"
        if out.exists():
            continue
        cols = [c.name for c in tables[f"gaiadr3.{name}"].columns if c.name not in SKIP]
        tab = to_arrow(run_async(f"SELECT {', '.join(cols)} FROM gaiadr3.{name}"))
        pq.write_table(tab, out.with_suffix(".tmp"))
        out.with_suffix(".tmp").rename(out)
        print(f"{name}: {tab.num_rows} rows")


def download_full_tables(out_dir=RAW / "dr3_tables") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in DR3_TABLES_FULL:
        out = out_dir / f"{name}.parquet"
        if not out.exists():
            tab = to_arrow(run_async(f"SELECT * FROM gaiadr3.{name}"))
            pq.write_table(tab, out)
            print(f"{name}: {tab.num_rows} rows")


def download_dr2() -> None:
    download_chunked((ADQL_DIR / "dr2_nearby.adql").read_text(), RAW / "dr2_nearby")


LINK_QUERY = """SELECT n.dr2_source_id, n.dr3_source_id, n.angular_distance, n.magnitude_difference,
       n.proper_motion_propagation
FROM gaiadr3.dr2_neighbourhood AS n JOIN tap_upload.ids AS u ON u.source_id = n.dr3_source_id"""


def download_dr2_links(out=RAW / "dr2_links" / "orbit_solutions.parquet", batch=20_000) -> None:
    """DR2<->DR3 links (dr2_neighbourhood, the only allowed link) for DR3 sources with an Orbital* NSS solution.

    Only these rows are needed to attach DR3 outcomes to DR2 stars; the full table covers the whole sky.
    The ids are uploaded to the archive (TAP upload) in batches.
    """
    import duckdb
    import numpy as np
    from astropy.table import Table, vstack

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return
    ids = duckdb.sql(
        f"SELECT DISTINCT source_id FROM '{RAW}/nss/nss_two_body_orbit.parquet' "
        "WHERE nss_solution_type LIKE 'Orbital%' ORDER BY source_id"
    ).fetchnumpy()["source_id"].astype("int64")
    parts = []
    for i in range(0, len(ids), batch):
        parts.append(run_async(LINK_QUERY, uploads={"ids": Table({"source_id": ids[i : i + batch]})}, wall_clock=900))
        print(f"links: {i + len(ids[i : i + batch])}/{len(ids)} ids, {sum(len(x) for x in parts)} rows")
    tab = to_arrow(vstack(parts))
    pq.write_table(tab, out)
    print(f"dr2 links: {tab.num_rows} rows")


HGCA_URL = "http://physics.ucsb.edu/~tbrandt/{}.fits"  # Brandt; DR2 edition (2018) and EDR3 edition (2021)


def download_hgca(out_dir=RAW / "hgca") -> None:
    """HGCA FITS -> Parquet. `source_id` is a DR2 id in the DR2 edition (backtest), a DR3 id in the EDR3 edition."""
    import urllib.request

    import numpy as np
    from astropy.io import fits
    from astropy.table import Table

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, out_name in [("HGCA_vDR2", "hgca_dr2"), ("HGCA_vEDR3", "hgca_edr3")]:
        out = out_dir / f"{out_name}.parquet"
        if out.exists():
            continue
        raw = out_dir / f"{name}.fits"
        if not raw.exists():
            urllib.request.urlretrieve(HGCA_URL.format(name), raw)  # follows the http->https redirect
        d = fits.open(raw)[1].data
        cols = {c: np.ascontiguousarray(d[c]).astype(d[c].dtype.newbyteorder("=")) for c in d.columns.names}
        cols["source_id"] = cols.pop("gaia_source_id").astype("int64")
        tab = to_arrow(Table(cols))
        assert tab["source_id"].null_count == 0
        pq.write_table(tab, out)
        print(f"{out_name}: {tab.num_rows} rows")


def download_labels(out=RAW / "labels" / "nasa_pscomppars.parquet") -> None:
    """Confirmed planets; gaia_dr3_id ('Gaia DR3 <id>') is parsed to an int64 source_id."""
    out.parent.mkdir(parents=True, exist_ok=True)
    t = pyvo.dal.TAPService(NASA_TAP).run_sync(
        "SELECT pl_name, hostname, gaia_dr2_id, gaia_dr3_id, pl_bmassj, pl_orbper, "
        "discoverymethod, disc_year, sy_dist, sy_gaiamag FROM pscomppars"
    ).to_table()
    rows = t.to_pandas().astype(object).where(lambda d: d.notna(), None)

    def parse(v):
        return int(str(v).split()[-1]) if v else None

    tab = pa.table({
        "pl_name": rows.pl_name.astype(str).tolist(),
        "hostname": rows.hostname.astype(str).tolist(),
        "dr2_source_id": pa.array([parse(v) for v in rows.gaia_dr2_id], pa.int64()),
        "dr3_source_id": pa.array([parse(v) for v in rows.gaia_dr3_id], pa.int64()),
        "pl_bmassj": pa.array(rows.pl_bmassj.astype(float).tolist(), pa.float64()),
        "pl_orbper": pa.array(rows.pl_orbper.astype(float).tolist(), pa.float64()),
        "discoverymethod": rows.discoverymethod.astype(str).tolist(),
        "disc_year": pa.array([None if v is None else int(v) for v in rows.disc_year], pa.int64()),
        "sy_dist": pa.array(rows.sy_dist.astype(float).tolist(), pa.float64()),
        "sy_gaiamag": pa.array(rows.sy_gaiamag.astype(float).tolist(), pa.float64()),
    })
    pq.write_table(tab, out)
    print(f"labels: {tab.num_rows} planets, {tab['dr3_source_id'].null_count} without DR3 id")


if __name__ == "__main__":
    download_labels()
    download_nss()
    download_full_tables()
    download_hgca()
    download_dr2()
    download_dr2_links()
