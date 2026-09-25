"""Download DR3 nearby stars from the Gaia archive in 192 HEALPix chunks -> Parquet.

Uses the Heidelberg ARI TAP mirror by default (ESA archive async jobs were unstable); override with GAIA_TAP_URL.
IDs are kept as int64 end to end: pandas would turn masked int64 into float and round source_ids.
"""
import os
import signal
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from astropy.table import Table
import pyvo

from .paths import RAW

# source_id encodes HEALPix level 12 in its upper bits: id // 2**35 = level-12 index
PIX_SPAN = 2**35 * 4**10  # source_id span of one level-2 pixel
ADQL_DIR = Path(__file__).parent / "adql"
TEMPLATE = (ADQL_DIR / "dr3_nearby.adql").read_text()


def to_arrow(t: Table) -> pa.Table:
    """astropy Table -> Arrow, preserving int64 (no float detour) and masks as nulls."""
    cols = {}
    for name in t.colnames:
        col = t[name]
        data = np.ma.getdata(col)
        mask = np.ma.getmaskarray(col) if np.ma.isMaskedArray(col) or hasattr(col, "mask") else None
        if data.dtype.kind == "O":
            data = data.astype(str)
        cols[name] = pa.array(data, mask=None if mask is None or not mask.any() else mask)
    out = pa.table(cols)
    if "source_id" in out.column_names:
        assert out.schema.field("source_id").type == pa.int64(), "source_id must be int64"
        assert out["source_id"].null_count == 0, "source_id must not contain nulls"
    return out


CHUNK_TIMEOUT = 180  # a normal chunk takes 3-20 s; longer means a hung server job
TAP_URL = os.environ.get("GAIA_TAP_URL", "https://gaia.ari.uni-heidelberg.de/tap")


def _raise_timeout(signum, frame):
    raise TimeoutError("Gaia TAP job exceeded wall-clock limit")


def run_async(query: str, tries: int = 5, wall_clock: int = 900, uploads: dict | None = None, url: str | None = None) -> Table:
    """Run a TAP job; a hung connection is aborted after `wall_clock` seconds and retried."""
    service = pyvo.dal.TAPService(url or TAP_URL)
    signal.signal(signal.SIGALRM, _raise_timeout)
    for i in range(tries):
        signal.alarm(wall_clock)
        try:
            return service.run_async(query, timeout=wall_clock, maxrec=10_000_000, uploads=uploads).to_table()
        except (ConnectionError, OSError, pyvo.DALServiceError) as e:
            wait = 30 * (i + 1)
            print(f"  {type(e).__name__}: {str(e)[:100]}, retry in {wait}s")
            time.sleep(wait)
        finally:
            signal.alarm(0)
    raise RuntimeError("TAP async job failed repeatedly")


def download_chunked(template: str, out_dir: Path) -> None:
    """Run `template` for each of the 192 level-2 HEALPix source_id ranges -> one Parquet per chunk."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for hp in range(192):
        out = out_dir / f"hp2_{hp:03d}.parquet"
        if out.exists():
            continue
        t = run_async(template.format(lo=hp * PIX_SPAN, hi=(hp + 1) * PIX_SPAN), wall_clock=CHUNK_TIMEOUT)
        tab = to_arrow(t)
        ids = tab["source_id"].to_numpy() if "source_id" in tab.column_names else tab["dr2_source_id"].to_numpy()
        assert ((ids >= hp * PIX_SPAN) & (ids < (hp + 1) * PIX_SPAN)).all(), "id outside chunk"
        pq.write_table(tab, out.with_suffix(".tmp"))
        out.with_suffix(".tmp").rename(out)
        print(f"hp {hp:3d}: {tab.num_rows} rows")


def download_dr3_nearby(out_dir: Path = RAW / "dr3_nearby") -> None:
    download_chunked(TEMPLATE, out_dir)


if __name__ == "__main__":
    download_dr3_nearby()
