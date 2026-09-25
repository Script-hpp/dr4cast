"""Backtest predictions of Model A evaluated against the DR3 target with m1 from `mass_ms` instead of `binary_masses` (no retraining).

Added after the freeze (docs/clarifications_v1.md, addendum d). Same code path as evaluate_bet.backtest_population, but the DR3 orbit
solutions get `m1` from either source. Population restriction: solutions whose star is in the DR3 nearby sample (abs_g needed for `mass_ms`).
"""
import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from . import evaluate_bet as eb
from .primary_masses import mass_ms_strict
from .paths import PROCESSED, RAW

RETRACTED = "4698424845771339520, 5765846127180770432, 522135261462534528, 1712614124767394816"


def population(m1_source: str) -> pd.DataFrame:
    df = duckdb.sql(f"""
        SELECT f.source_id, f.phot_g_mean_mag, f.ruwe, f.ruwe_z, f.ms_offset AS ms_offset_earlier, l.source_id IS NOT NULL AS known_planet
        FROM '{PROCESSED}/features_dr2.parquet' f
        LEFT JOIN (SELECT DISTINCT source_id FROM '{PROCESSED}/labels_backtest_dr2.parquet') l USING (source_id)
        WHERE f.parallax_over_error >= 10""").df()
    links = eb.resolve_links(pd.read_parquet(RAW / "dr2_links" / "orbit_solutions.parquet"), "dr3_source_id", "dr2_source_id")
    sol = duckdb.sql(f"""
        SELECT n.source_id, n.nss_solution_type, n.a_thiele_innes, n.b_thiele_innes, n.f_thiele_innes, n.g_thiele_innes, n.parallax, n.period,
               b.m1 AS m1_bm, f.abs_g, f.ms_offset
        FROM '{RAW}/nss/nss_two_body_orbit.parquet' n
        JOIN '{PROCESSED}/features_dr3.parquet' f USING (source_id)
        LEFT JOIN (SELECT source_id, any_value(m1) m1 FROM '{RAW}/dr3_tables/binary_masses.parquet' WHERE combination_method LIKE 'Orbital%' GROUP BY 1) b USING (source_id)
        WHERE n.nss_solution_type LIKE 'Orbital%' AND n.source_id NOT IN ({RETRACTED})""").df()
    sol["m1"] = sol.m1_bm if m1_source == "binary_masses" else mass_ms_strict(sol.abs_g.to_numpy(float))
    o = eb.outcomes_from_solutions(sol, sol[["source_id", "ms_offset"]].drop_duplicates("source_id")).rename(columns={"source_id": "dr3_source_id"})
    o = o.merge(links, on="dr3_source_id", how="inner").rename(columns={"dr2_source_id": "source_id"})
    flags = ["y80", "y13", "y13_ms", "y80_ms", "excluded"]
    o = o.groupby("source_id")[flags].max().reset_index()
    pop = df.merge(o, on="source_id", how="left")
    for c in flags:
        pop[c] = pop[c].fillna(False).astype(bool)
    pop = pop[~pop.excluded].reset_index(drop=True)
    pop["model_a"] = pop.source_id.map(pd.read_parquet(PROCESSED / "oof_physics_dr2.parquet").set_index("source_id").score)
    return pop


def metrics(pop: pd.DataFrame, score: str, target: str) -> dict:
    d = pop[pop[score].notna()].sort_values([score, "source_id"], ascending=[False, True], kind="stable")
    y = d[target].to_numpy(bool)
    return {"n_pos": int(y.sum()), "hits@100": int(y[:100].sum()), "hits@1000": int(y[:1000].sum()),
            "AUC": roc_auc_score(y, d[score]) if y.any() else np.nan, "AP": average_precision_score(y, d[score]) if y.any() else np.nan}


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    rows = []
    for src in ("binary_masses", "mass_ms"):
        pop = population(src)
        pop = pop[pop.model_a.notna()].reset_index(drop=True)  # same stars for the model and the baseline: those with an out-of-fold score
        pop["ruwe_z_s"] = pop.ruwe_z
        for score, name in (("model_a", "Model A (frozen, not retrained)"), ("ruwe_z_s", "ruwe_z baseline")):
            for tgt in ("y80", "y13", "y13_ms"):
                rows.append({"m1": src, "score": name, "target": tgt, "population": len(pop), **metrics(pop, score, tgt)})
    print(pd.DataFrame(rows).round(4).to_string(index=False))
