"""Two physically motivated features, computed per release from that release's own photometry/astrometry.

1. `ms_offset`: how much brighter (mag) the star is than the main sequence at its colour. Companion stars add light and lift
   a system above the main sequence; brown dwarfs and planets add none. The main sequence is the median absolute magnitude per
   colour bin of high-quality stars within 100 pc of the same release (dwarfs dominate that volume).
2. `wobble_ratio`: observed astrometric excess noise divided by the largest reflex wobble an 80 M_Jup companion could cause
   at an orbital period equal to the release's observing baseline. Values well above 1 point to a stellar companion.
   The same computation gives the amplitude range needed for list 2 of the bet.

The stellar mass comes from the main-sequence mean sequence of Pecaut & Mamajek (Mamajek's table, version 2022.04.16,
absolute Gaia G vs mass; `data/mamajek_mg_mass.csv`). It is a dwarf sequence: giants, subgiants and unresolved binaries get
a mass that is too small or too large; the result is only an approximate scale for the wobble ratio.
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from .paths import PROCESSED

M_JUP = 9.5479e-4
BASELINE_YEARS = {"dr2": 22 / 12, "dr3": 34 / 12}  # observing baseline of each release
_MASS = pd.read_csv(Path(__file__).parent / "data" / "mamajek_mg_mass.csv", comment="#")
MASS_TABLE = _MASS[["M_G", "Msun"]].to_numpy(float)  # main-sequence M_G -> mass, Mamajek 2022.04.16 (Pecaut & Mamajek 2013)
COLOUR_STEP = 0.1


def stellar_mass_ms(abs_g: np.ndarray) -> np.ndarray:
    return np.interp(abs_g, MASS_TABLE[:, 0], MASS_TABLE[:, 1])


def main_sequence_grid(df: pd.DataFrame) -> pd.Series:
    """Median absolute G per BP-RP bin for well-measured stars within 100 pc; bins with fewer than 50 stars are dropped."""
    d = df[(df.dist_pc < 100) & (df.parallax_over_error >= 20) & df.bp_rp.notna() & df.abs_g.notna()]
    b = np.floor(d.bp_rp.clip(-0.4, 4.4) / COLOUR_STEP).astype(int)
    g = d.groupby(b).abs_g
    med, n = g.median(), g.size()
    return med[n >= 50]


def add_physics_features(release: str) -> None:
    path = PROCESSED / f"features_{release}.parquet"
    df = duckdb.sql(f"SELECT * EXCLUDE (ms_offset, wobble_ratio, mass_ms, a1_max_mas) "
                    f"FROM '{path}'").df() if "ms_offset" in duckdb.sql(f"DESCRIBE SELECT * FROM '{path}'").df().column_name.values \
        else duckdb.sql(f"SELECT * FROM '{path}'").df()
    grid = main_sequence_grid(df)
    bins = np.floor(df.bp_rp.clip(-0.4, 4.4) / COLOUR_STEP)
    ms = bins.map(lambda b: np.nan if np.isnan(b) else grid.get(int(b), np.nan))
    df["ms_offset"] = ms - df.abs_g  # positive = brighter than the main sequence
    m1 = stellar_mass_ms(df.abs_g.to_numpy(float))
    m2 = 80 * M_JUP
    a_au = ((m1 + m2) * BASELINE_YEARS[release] ** 2) ** (1 / 3)
    df["mass_ms"] = m1
    df["a1_max_mas"] = a_au * m2 / (m1 + m2) * df.parallax  # star's reflex semi-major axis, in mas
    df["wobble_ratio"] = df.astrometric_excess_noise / df.a1_max_mas
    df.to_parquet(path, index=False)


if __name__ == "__main__":
    for r in ("dr2", "dr3"):
        add_physics_features(r)
        print(r, "done")
