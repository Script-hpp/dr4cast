"""Guard against the silent float conversion of Gaia source ids (they have up to 19 digits; float64 keeps about 16)."""
import duckdb
import pytest

from gaia_wobble.paths import DATA_DIR, PROCESSED, RAW

pytestmark = pytest.mark.skipif(not (PROCESSED / "features_dr3.parquet").exists(), reason="data not built")


def _id_columns(path):
    cols = duckdb.sql(f"DESCRIBE SELECT * FROM '{path}'").df()
    return [(r.column_name, r.column_type) for r in cols.itertuples() if r.column_name.endswith("source_id")]


def test_every_source_id_column_is_bigint():
    bad = []
    for f in sorted(DATA_DIR.glob("*/*.parquet")) + sorted(DATA_DIR.glob("*/*/*.parquet"))[:400]:
        for name, typ in _id_columns(f):
            if typ != "BIGINT":
                bad.append((str(f.relative_to(DATA_DIR)), name, typ))
    assert not bad, bad


@pytest.mark.parametrize("release", ["dr2", "dr3"])
def test_feature_ids_equal_source_ids(release):
    """The ids of the feature table are exactly the ids of the downloaded catalogue (no rounding, none lost or invented)."""
    a = f"'{PROCESSED}/features_{release}.parquet'"
    b = f"'{RAW}/{release}_nearby/*.parquet'"
    only_a = duckdb.sql(f"SELECT count(*) FROM (SELECT source_id FROM {a} EXCEPT SELECT source_id FROM {b})").fetchone()[0]
    only_b = duckdb.sql(f"SELECT count(*) FROM (SELECT source_id FROM {b} EXCEPT SELECT source_id FROM {a})").fetchone()[0]
    assert only_a == 0 and only_b == 0


def test_known_ids_survive():
    """Two ids that need all 19 digits must be present unchanged."""
    ids = duckdb.sql(f"SELECT source_id FROM '{PROCESSED}/features_dr3.parquet' WHERE source_id IN (1457486023639239296, 2074815898041643520)").df().source_id.tolist()
    assert sorted(ids) == [1457486023639239296, 2074815898041643520]
