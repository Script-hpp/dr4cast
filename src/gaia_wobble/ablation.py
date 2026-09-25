"""Feature ablations of Model A (same protocol as model_a.py, one run each, fixed before looking at results).

variants:
  full          all COMMON features
  no_poe        without parallax_over_error
  no_selection  without every feature that mirrors Gaia's admission rules for orbit solutions
                (parallax precision, brightness, number of observations, visibility periods)
  physics       only wobble and colour-magnitude features
  physics_strict  physics without every feature derived from parallax or distance
                  (wobble_ratio, abs_g, pm_total): tests whether selection information leaks through them
"""
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from .features import COMMON
from .metrics import evaluate, evaluate_curve
from .model_a import cross_val_predict, load, region_folds
from .paths import MODELS, PROCESSED

SELECTION = ["parallax_over_error", "parallax_error", "phot_g_mean_mag", "phot_g_n_obs", "astrometric_n_obs_al",
             "astrometric_n_good_obs_al", "visibility_periods_used"]
PHYSICS = ["ruwe_z", "ruwe_excess", "astrometric_excess_noise_sig", "wobble_ratio", "ms_offset", "chi2_per_dof",
           "bp_rp", "abs_g", "pm_total"]
PHYSICS_STRICT = ["ruwe_z", "ruwe_excess", "astrometric_excess_noise_sig", "chi2_per_dof", "ms_offset", "bp_rp"]
VARIANTS = {
    "full": COMMON,
    "no_poe": [c for c in COMMON if c != "parallax_over_error"],
    "no_selection": [c for c in COMMON if c not in SELECTION],
    "physics": PHYSICS,
    "physics_strict": PHYSICS_STRICT,
}


def run(names: list[str]) -> None:
    pd.set_option("display.width", 200)
    df = load(10)
    folds = region_folds(df.source_id)
    summary = {}
    for name in names:
        feats = VARIANTS[name]
        print(f"\n### {name}: {len(feats)} features", flush=True)
        oof, models = cross_val_predict(df, feats)
        df["score"] = oof
        df[["source_id", "score"]].to_parquet(PROCESSED / f"oof_{name}_dr2.parquet", index=False)
        for i, m in enumerate(models):
            m.booster_.save_model(str(MODELS / f"ablation_{name}_fold{i}.txt"))
        m1, cv = evaluate(df, "score").loc["all"], evaluate_curve(df, "score").loc["all"]
        ap_folds = [average_precision_score(df.y[folds == k], oof[folds == k]) for k in range(5)]
        summary[name] = {**{k: m1[k] for k in ("P@30", "P@100", "P@1000", "hits@1000")}, "AUC": cv["AUC"], "AP": cv["AP"],
                         "Recall@1%": cv["Recall@1%"], "AP_fold_min": min(ap_folds), "AP_fold_max": max(ap_folds)}
    print("\n", pd.DataFrame(summary).T.round(4).to_string())


if __name__ == "__main__":
    run(sys.argv[1:] or list(VARIANTS))
