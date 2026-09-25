"""Comparison samples for the reality check, split into calibration and test halves BEFORE any simulation run (docs/simulation_plan.md).

Null sample: 2,100 real candidate stars (list-2 population, DR3, parallax_over_error >= 10, ms_offset < 0.2, no known DR3 orbit < 80 M_Jup,
no known planet host), 700 per brightness class (G < 10, 10-13, 13-16).
Check C: 200 DR3 `Orbital` solutions stratified by estimated companion mass (5 classes), brightness (4 classes) and period (3 classes);
Gaia-4 and Gaia-5 are excluded. Both samples are split 50/50 by star with a fixed seed.
"""
import hashlib
import json

import duckdb
import numpy as np
import pandas as pd

from ..paths import DATA_DIR, PROCESSED, REPO

SEED = 20260926
CONTROL_IDS = [1457486023639239296, 2074815898041643520]  # Gaia-4, Gaia-5
G_CLASSES = [(-np.inf, 10, "G<10"), (10, 13, "10-13"), (13, 16, "13-16"), (16, np.inf, ">=16")]
MASS_EDGES = [0, 50, 150, 400, 1000, np.inf]           # estimated companion mass, M_Jup
PERIOD_EDGES = [0, 200, 500, np.inf]                    # days
OUT = DATA_DIR / "interim" / "simulation"


def g_class(g: pd.Series) -> pd.Series:
    return pd.cut(g, [c[0] for c in G_CLASSES] + [np.inf], labels=[c[2] for c in G_CLASSES], right=False)


def null_sample() -> pd.DataFrame:
    df = duckdb.sql(f"""
        SELECT f.source_id, f.ra, f.dec, f.phot_g_mean_mag, f.bp_rp, f.astrometric_n_obs_al, f.ruwe, f.ruwe_z, f.ruwe_excess,
               f.astrometric_excess_noise, f.chi2_per_dof, f.wobble_ratio
        FROM '{PROCESSED}/features_dr3.parquet' f
        WHERE f.parallax_over_error >= 10 AND f.ms_offset < 0.2 AND f.bp_rp IS NOT NULL AND f.phot_g_mean_mag < 16
          AND f.source_id NOT IN (SELECT source_id FROM '{PROCESSED}/dr3_orbit_targets.parquet')
          AND f.source_id NOT IN (SELECT source_id FROM '{PROCESSED}/labels_bet_dr3.parquet')
          AND f.source_id NOT IN ({', '.join(map(str, CONTROL_IDS))})""").df()
    df["g_class"] = g_class(df.phot_g_mean_mag)
    rng = np.random.default_rng(SEED)
    parts = [d.sample(700, random_state=int(rng.integers(1 << 31))) for _, d in df.groupby("g_class", observed=True)]
    return pd.concat(parts).reset_index(drop=True)


def check_c_sample() -> pd.DataFrame:
    df = duckdb.sql(f"""
        SELECT t.source_id, t.m2_est_mjup, t.m1, t.period, f.ra, f.dec, f.phot_g_mean_mag, f.bp_rp, f.astrometric_n_obs_al, f.ruwe, f.ruwe_z,
               f.ruwe_excess, f.astrometric_excess_noise, f.chi2_per_dof, f.wobble_ratio, f.parallax
        FROM '{PROCESSED}/dr3_orbit_targets.parquet' t JOIN '{PROCESSED}/features_dr3.parquet' f USING (source_id)
        WHERE t.nss_solution_type = 'Orbital' AND f.bp_rp IS NOT NULL
          AND t.source_id NOT IN ({', '.join(map(str, CONTROL_IDS))})""").df()
    df["g_class"] = g_class(df.phot_g_mean_mag)
    df["mass_class"] = pd.cut(df.m2_est_mjup, MASS_EDGES, labels=False, right=False)
    df["period_class"] = pd.cut(df.period, PERIOD_EDGES, labels=False, right=False)
    rng = np.random.default_rng(SEED + 1)
    cells = [(k, d) for k, d in df.groupby(["mass_class", "g_class", "period_class"], observed=True)]
    rng.shuffle(cells)
    quota = {k: 3 for k, _ in cells}
    for k, _ in cells[: 200 - 3 * len(cells)]:
        quota[k] += 1
    take = []
    for k, d in cells:
        take.append(d.sample(min(quota[k], len(d)), random_state=int(rng.integers(1 << 31))))
    s = pd.concat(take)
    if len(s) < 200:  # fill up from the remaining stars of any cell, at random
        rest = df[~df.source_id.isin(s.source_id)]
        s = pd.concat([s, rest.sample(200 - len(s), random_state=int(rng.integers(1 << 31)))])
    return s.head(200).reset_index(drop=True)


def split_half(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    order = np.random.default_rng(seed).permutation(len(df))
    part = np.where(np.isin(np.arange(len(df)), order[: len(df) // 2]), "calibration", "test")
    return df.assign(part=part)


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    null = split_half(null_sample(), SEED + 2)
    c = split_half(check_c_sample(), SEED + 3)
    for name, d in (("null_sample", null), ("check_c_sample", c)):
        assert d.source_id.dtype == "int64" and d.source_id.is_unique
        d.to_parquet(OUT / f"{name}.parquet", index=False)
    info = {}
    for name, d in (("null_sample", null), ("check_c_sample", c)):
        for part in ("calibration", "test"):
            ids = sorted(d[d.part == part].source_id.tolist())
            info[f"{name}_{part}"] = {"n": len(ids), "sha256_of_sorted_ids": hashlib.sha256("\n".join(map(str, ids)).encode()).hexdigest()}
    info["seed"] = SEED
    info["check_c_strata"] = {"mass_edges_mjup": [float(x) if np.isfinite(x) else "inf" for x in MASS_EDGES], "period_edges_days": [float(x) if np.isfinite(x) else "inf" for x in PERIOD_EDGES],
                              "cells_used": int(c.groupby(["mass_class", "g_class", "period_class"], observed=True).ngroups)}
    info["null_by_g_class"] = null.groupby(["g_class", "part"], observed=True).size().unstack().to_dict()
    (REPO / "docs" / "simulation_split.json").write_text(json.dumps(info, indent=2, sort_keys=True, default=str) + "\n")
    return info


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, default=str))
