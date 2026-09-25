import numpy as np
import pyarrow as pa
from astropy.table import MaskedColumn, Table

from gaia_wobble.download import to_arrow


def test_source_id_survives_above_2_53():
    ids = np.array([137339207152687744 + 1, 4295806720038242560 + 3, 2**62 + 1], dtype="int64")
    t = Table({"source_id": ids, "ruwe": MaskedColumn([1.0, 0.0, 2.0], mask=[False, True, False])})
    out = to_arrow(t)
    assert out.schema.field("source_id").type == pa.int64()
    assert out["source_id"].to_pylist() == ids.tolist()
    assert out["ruwe"].null_count == 1
