"""Comparison models B and B': same features and protocol as Model A, but trained on NASA planet-host labels.

B : known planet hosts (discovered up to 2017, DR2 id) = 1, everything else = 0.
B': like B, but positives are only hosts whose expected astrometric wobble is measurable, amplitude >= AMP_MIN_MAS;
    other hosts (too small or no mass/period) are dropped from training (neither positive nor negative).
Both are evaluated on their own label and on the backtest target of Model A (DR3 orbit < 80 M_Jup).
"""
import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from .features import COMMON
from .metrics import evaluate, evaluate_curve
from .model_a import cross_val_predict, load, region_folds
from .paths import PROCESSED, RAW

AMP_MIN_MAS = 0.1  # fixed before the first run; roughly the single-epoch precision of Gaia astrometry for bright stars


def host_amplitudes() -> pd.DataFrame:
    """Expected reflex amplitude (mas) per host: (Mp / M*) * a[AU] * parallax, M* from the star's main-sequence mass."""
    from .physics_features import stellar_mass_ms

    h = duckdb.sql(f"""
        SELECT l.source_id, max(pl_bmassj) AS mp_mjup, min(pl_orbper) AS period_d
        FROM '{PROCESSED}/labels_backtest_dr2.parquet' l GROUP BY 1""").df()
    f = duckdb.sql(f"SELECT source_id, abs_g, parallax FROM '{PROCESSED}/features_dr2.parquet'").df()
    h = h.merge(f, on="source_id")
    m_star = stellar_mass_ms(h.abs_g.to_numpy(float))
    a_au = (m_star * (h.period_d / 365.25) ** 2) ** (1 / 3)
    h["amp_mas"] = (h.mp_mjup * 9.5479e-4 / m_star) * a_au * h.parallax
    return h[["source_id", "amp_mas"]]


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    df = load(10)
    amp = host_amplitudes()
    df = df.merge(amp, on="source_id", how="left")
    host = df.known_planet
    df["yB"] = host
    df["yBp"] = host & (df.amp_mas >= AMP_MIN_MAS)
    print(f"{len(df):,} stars; hosts {int(host.sum())}; hosts with amplitude >= {AMP_MIN_MAS} mas {int(df.yBp.sum())}; "
          f"hosts without amplitude {int((host & df.amp_mas.isna()).sum())}")
    rows = {}
    for name, label in (("B", "yB"), ("Bprime", "yBp")):
        d = df if name == "B" else df[~(host & ~df.yBp)]  # B': drop non-measurable hosts
        oof, _ = cross_val_predict(d.assign(y_own=d[label]).rename(columns={"y": "y_target"}), COMMON, "y_own")
        d = d.assign(score=oof)
        d[["source_id", "score"]].to_parquet(PROCESSED / f"oof_model_{name}_dr2.parquet", index=False)
        own = {"AUC_own": roc_auc_score(d[label], d.score), "AP_own": average_precision_score(d[label], d.score),
               "base_own": d[label].mean()}
        t = d.rename(columns={"y": "y_t"})
        m = evaluate(t.assign(y=t.y_t), "score").loc["all"]
        cv = evaluate_curve(t.assign(y=t.y_t), "score").loc["all"]
        rows[name] = {**own, "AUC_target": cv["AUC"], "AP_target": cv["AP"], "P@100": m["P@100"], "P@1000": m["P@1000"],
                      "hits@1000": m["hits@1000"], "Recall@1%": cv["Recall@1%"]}
    print(pd.DataFrame(rows).T.round(4).to_string())
