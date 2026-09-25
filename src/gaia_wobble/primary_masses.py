"""Primary masses for the DR4 evaluation (docs/clarifications_v1.md, addendum on m1). Added after the freeze; evaluate_bet.py is unchanged.

Official rule: m1 = `mass_ms` from the Mamajek main-sequence table (data/mamajek_mg_mass.csv), computed with the later release's
photometry and parallax by the same formula as the feature (absolute G = G + 5 log10(parallax / mas) - 10). Stars outside the table's
range of absolute G have no m1; their orbit solutions get no mass estimate and count as label unknown (excluded), as before for a missing m1.
`stellar_mass_ms` in physics_features.py clips at the table ends; this module does not.
"""
import duckdb
import numpy as np
import pandas as pd

from .physics_features import MASS_TABLE, stellar_mass_ms


def mass_ms_strict(abs_g: np.ndarray) -> np.ndarray:
    """Main-sequence mass from absolute G; NaN where the table does not cover the star (no clipping to the end values)."""
    a = np.asarray(abs_g, float)
    m = stellar_mass_ms(a)
    m[~np.isfinite(a) | (a < MASS_TABLE[0, 0]) | (a > MASS_TABLE[-1, 0])] = np.nan
    return m


def build_primary_masses(features_path, out_path) -> int:
    """features table of the later release (needs `source_id`, `abs_g`) -> Parquet (source_id, m1) as expected by evaluate_bet.check_dr4_schema."""
    f = duckdb.sql(f"SELECT source_id, abs_g FROM '{features_path}'").df()
    out = pd.DataFrame({"source_id": f.source_id.astype("int64"), "m1": mass_ms_strict(f.abs_g.to_numpy(float))})
    out.to_parquet(out_path, index=False)
    return int(out.m1.notna().sum())
