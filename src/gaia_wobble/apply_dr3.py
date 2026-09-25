"""Apply Model A (physics variant, mean of the five region models) to the DR3 features. Development check, not the frozen list."""
import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd

from .ablation import VARIANTS
from .paths import MODELS, PREDICTIONS, PROCESSED, RAW

VARIANT = "physics"


def score_dr3(min_poe: float = 10) -> pd.DataFrame:
    feats = VARIANTS[VARIANT]
    df = duckdb.sql(f"""
        SELECT source_id, {', '.join(feats)}, phot_g_mean_mag, parallax_over_error, dist_pc, mass_ms
        FROM '{PROCESSED}/features_dr3.parquet' WHERE parallax_over_error >= {min_poe}""").df()
    boosters = [lgb.Booster(model_file=str(MODELS / f"ablation_{VARIANT}_fold{k}.txt")) for k in range(5)]
    df["score"] = np.mean([b.predict(df[feats]) for b in boosters], axis=0)
    return df


def flags(df: pd.DataFrame) -> pd.DataFrame:
    """Mark stars whose outcome is already known in DR3 (see MANIFEST 'Neue Treffer')."""
    orb = duckdb.sql(f"SELECT source_id, nss_solution_type, m2_est_mjup FROM '{PROCESSED}/dr3_orbit_targets.parquet'").df()
    df["known_dr3_orbit80"] = df.source_id.isin(orb[(orb.nss_solution_type == "Orbital") & (orb.m2_est_mjup < 80)].source_id)
    df["known_dr3_orbit_any"] = df.source_id.isin(duckdb.sql(
        f"SELECT source_id FROM '{RAW}/nss/nss_two_body_orbit.parquet' WHERE nss_solution_type LIKE 'Orbital%'").df().source_id)
    df["dr3_acceleration"] = df.source_id.isin(duckdb.sql(f"SELECT source_id FROM '{RAW}/nss/nss_acceleration_astro.parquet'").df().source_id)
    df["known_planet"] = df.source_id.isin(duckdb.sql(f"SELECT source_id FROM '{PROCESSED}/labels_bet_dr3.parquet'").df().source_id)
    return df


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    df = flags(score_dr3())
    PREDICTIONS.mkdir(parents=True, exist_ok=True)
    df[["source_id", "score", "known_dr3_orbit80", "known_dr3_orbit_any", "dr3_acceleration", "known_planet", "ms_offset"]].to_parquet(
        PREDICTIONS / "dev_dr3_scores_model_a_physics.parquet", index=False)
    print(f"{len(df):,} DR3 stars scored")
    top = df.sort_values("score", ascending=False)
    rows = {}
    for k in (100, 1000):
        t = top.head(k)
        new = top[~top.known_dr3_orbit80 & ~top.known_planet].head(k)
        rows[f"top {k}"] = {"known DR3 orbit <80": t.known_dr3_orbit80.mean(), "any DR3 orbit": t.known_dr3_orbit_any.mean(),
                            "acceleration": t.dr3_acceleration.mean(), "known planet": t.known_planet.mean(),
                            "median ms_offset": t.ms_offset.median(), "median G": t.phot_g_mean_mag.median()}
        rows[f"top {k} after excluding known"] = {"known DR3 orbit <80": new.known_dr3_orbit80.mean(), "any DR3 orbit": new.known_dr3_orbit_any.mean(),
                            "acceleration": new.dr3_acceleration.mean(), "known planet": new.known_planet.mean(),
                            "median ms_offset": new.ms_offset.median(), "median G": new.phot_g_mean_mag.median()}
    rows["population"] = {"known DR3 orbit <80": df.known_dr3_orbit80.mean(), "any DR3 orbit": df.known_dr3_orbit_any.mean(),
                          "acceleration": df.dr3_acceleration.mean(), "known planet": df.known_planet.mean(),
                          "median ms_offset": df.ms_offset.median(), "median G": df.phot_g_mean_mag.median()}
    print(pd.DataFrame(rows).T.round(3).to_string())
    print("\nscore distribution (DR3 vs DR2 out-of-fold):")
    dr2 = pd.read_parquet(PROCESSED / "oof_physics_dr2.parquet")
    print(pd.DataFrame({"DR3": df.score.quantile([.5, .9, .99, .999]), "DR2 OOF": dr2.score.quantile([.5, .9, .99, .999])}).round(4).to_string())
    print("share with ms_offset < 0.2 in top 1000 (candidates for list 2):", round((top.head(1000).ms_offset < 0.2).mean(), 3))
