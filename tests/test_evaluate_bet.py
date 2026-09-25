import numpy as np
import pandas as pd
import pytest

from gaia_wobble import evaluate_bet as eb
from gaia_wobble.paths import PROCESSED


def test_resolve_links_smallest_distance_then_magnitude():
    links = pd.DataFrame({"a": [1, 1, 1, 2], "b": [10, 11, 12, 20], "angular_distance": [0.5, 0.2, 0.2, 0.1],
                          "magnitude_difference": [0.0, 0.3, -0.1, 0.0]})
    r = eb.resolve_links(links, "a", "b").set_index("a").b
    assert r[1] == 12 and r[2] == 20  # 11 and 12 tie on distance, |-0.1| < |0.3|


def test_outcomes_flags():
    # Thiele-Innes circular face-on orbit: a0 = A. m2 from Kepler with P in days; large a0 -> stellar mass, small a0 -> substellar.
    sol = pd.DataFrame({
        "source_id": [1, 2, 3, 4], "nss_solution_type": ["Orbital", "Orbital", "Orbital", "OrbitalTargetedSearch"],
        "a_thiele_innes": [0.01, 5.0, 0.01, 0.01], "b_thiele_innes": 0.0, "f_thiele_innes": 0.0, "g_thiele_innes": [0.01, 5.0, 0.01, 0.01],
        "parallax": 10.0, "period": 400.0, "m1": [1.0, 1.0, np.nan, 1.0]})
    f = pd.DataFrame({"source_id": [1, 2, 3, 4], "ms_offset": [0.0, 0.0, 0.0, 0.0]})
    o = eb.outcomes_from_solutions(sol, f).set_index("source_id")
    assert o.loc[1, "y13"] and o.loc[1, "y80"] and o.loc[1, "y13_ms"]      # small wobble around a Sun-like star: planetary mass
    assert not o.loc[2, "y80"] and not o.loc[2, "excluded"]                # large wobble: stellar mass, a negative
    assert o.loc[3, "excluded"] and not o.loc[3, "y80"]                    # no primary mass: label unknown
    assert o.loc[4, "excluded"] and o.loc[4, "y80_targeted"]               # targeted search: separate


def test_ms_condition():
    sol = pd.DataFrame({"source_id": [1], "nss_solution_type": ["Orbital"], "a_thiele_innes": 0.01, "b_thiele_innes": 0.0,
                        "f_thiele_innes": 0.0, "g_thiele_innes": 0.01, "parallax": 10.0, "period": 400.0, "m1": 1.0})
    o = eb.outcomes_from_solutions(sol, pd.DataFrame({"source_id": [1], "ms_offset": [0.5]})).iloc[0]
    assert o.y13 and not o.y13_ms and not o.y80_ms


@pytest.mark.skipif(not (PROCESSED / "oof_physics_dr2.parquet").exists(), reason="backtest data not built")
def test_dry_run_reproduces_logged_numbers():
    """The frozen script must give the numbers already in docs/experiment_log.md (physics variant, target < 80 M_Jup)."""
    r = eb.dry_run()
    assert r["targets"] == {"y80": 1304, "y13": 17, "y13_ms": 4, "y80_ms": 430}
    top = r["results"]["list1_score"]["y80"]["top"].loc["all"]
    assert top["hits@1000"] == 93 and abs(top["P@100"] - 0.15) < 1e-9
    assert abs(r["results"]["list1_score"]["y80"]["curve"].loc["all", "AUC"] - 0.9656) < 0.001
    assert abs(r["results"]["baseline_ruwe_z"]["y80"]["curve"].loc["all", "AUC"] - 0.830) < 0.002
    assert abs(r["results"]["baseline_ruwe"]["y80"]["curve"].loc["all", "AUC"] - 0.783) < 0.002
    assert r["results"]["list2_score"]["y80"]["top"].loc["all", "hits@1000"] == 38  # logged in plausibility.py output
