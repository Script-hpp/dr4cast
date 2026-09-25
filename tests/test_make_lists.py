import pandas as pd
import pytest

from gaia_wobble import make_lists as ml
from gaia_wobble.paths import MODELS, PROCESSED

pytestmark = pytest.mark.skipif(not (MODELS / "ablation_physics_fold0.txt").exists() or not (PROCESSED / "amplitude_dr3.parquet").exists(),
                                reason="models or features not built")


def test_lists_are_byte_identical(tmp_path):
    pop = ml.score_population()
    none = lambda pool: pd.Series(0, index=pool.index)
    m1 = ml.build_lists(tmp_path / "a", "2026-01-01", "abc", tmp_path / "nb_a.parquet", pop=pop, neighbour_fn=none)
    m2 = ml.build_lists(tmp_path / "b", "2026-01-01", "abc", tmp_path / "nb_b.parquet", pop=pop, neighbour_fn=none)
    assert m1 == m2
    for name in m1["lists"]:
        assert (tmp_path / "a" / f"{name}.csv").read_bytes() == (tmp_path / "b" / f"{name}.csv").read_bytes()
        assert m1["lists"][name]["rows"] == ml.LIST_SIZE


def test_rules(tmp_path):
    pop = ml.score_population()
    none = lambda pool: pd.Series(0, index=pool.index)
    ml.build_lists(tmp_path, "d", "c", tmp_path / "nb.parquet", pop=pop, neighbour_fn=none)
    for name in ("list1_substellar", "list2_planets"):
        d = pd.read_csv(tmp_path / f"{name}.csv", comment="#")
        assert d.rank_new.is_monotonic_increasing and d.rank_new.iloc[0] == 1 and d.source_id.is_unique
        assert not d.known_dr3_orbit80.any() and not d.known_planet.any()
    d2 = pd.read_csv(tmp_path / "list2_planets.csv", comment="#")
    assert (d2.ms_offset < ml.MS_OFFSET_MAX).all()
