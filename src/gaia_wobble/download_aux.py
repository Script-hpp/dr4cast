"""NSS tables (DR3) from the Heidelberg mirror and planet labels from the NASA Exoplanet Archive."""
import pyarrow as pa
import pyarrow.parquet as pq
import pyvo

from .download import TAP_URL, run_async, to_arrow
from .paths import RAW

NSS_TABLES = ["nss_two_body_orbit", "nss_acceleration_astro", "nss_non_linear_spectro", "nss_vim_fl"]
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
