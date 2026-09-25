import duckdb
import pytest

from gaia_wobble.features import COMMON, DR3_ONLY
from gaia_wobble.paths import PROCESSED

pytestmark = pytest.mark.skipif(not (PROCESSED / "features_dr3.parquet").exists(), reason="features not built")


@pytest.mark.parametrize("release", ["dr2", "dr3"])
def test_features_shape(release):
    f = f"'{PROCESSED}/features_{release}.parquet'"
    n, u = duckdb.sql(f"SELECT count(*), count(DISTINCT source_id) FROM {f}").fetchone()
    assert n == u > 1_000_000
    cols = {r[0]: r[1] for r in duckdb.sql(f"DESCRIBE SELECT * FROM {f}").fetchall()}
    assert cols["source_id"] == "BIGINT"
    assert set(COMMON) <= set(cols)
    assert (set(DR3_ONLY) <= set(cols)) == (release == "dr3")  # DR2 must not contain DR3-only columns


def test_targets_unique_and_positives_not_excluded():
    t = f"'{PROCESSED}/targets_dr2.parquet'"
    n, u = duckdb.sql(f"SELECT count(*), count(DISTINCT source_id) FROM {t}").fetchone()
    assert n == u
    assert duckdb.sql(f"SELECT count(*) FROM {t} WHERE (y_lt80 OR y_lt13) AND excluded").fetchone()[0] == 0
