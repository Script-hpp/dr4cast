"""SHAP for Model A variants: which features drive the score, and in which direction (evaluation only)."""
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap

from .ablation import VARIANTS
from .model_a import load, region_folds
from .paths import MODELS


def shap_summary(name: str, n_neg: int = 40000, seed: int = 0) -> pd.DataFrame:
    feats = VARIANTS[name]
    df = load(10)
    folds = region_folds(df.source_id)
    rng = np.random.default_rng(seed)
    sample = pd.concat([df[df.y], df[~df.y].iloc[rng.choice((~df.y).sum(), n_neg, replace=False)]])
    sfold = folds[sample.index]
    vals = np.zeros((len(sample), len(feats)))
    for k in range(5):  # each star is explained by the model that did not train on its region
        booster = lgb.Booster(model_file=str(MODELS / f"ablation_{name}_fold{k}.txt"))
        idx = sfold == k
        v = shap.TreeExplainer(booster).shap_values(sample.loc[idx, feats])
        vals[idx] = v[1] if isinstance(v, list) else v
    pos = sample.y.to_numpy()
    out = pd.DataFrame({
        "mean_abs_shap": np.abs(vals).mean(0),
        "mean_shap_targets": vals[pos].mean(0),
        "corr_value_shap": [np.corrcoef(sample[f].fillna(sample[f].median()), vals[:, i])[0, 1] for i, f in enumerate(feats)],
    }, index=feats)
    out["share"] = out.mean_abs_shap / out.mean_abs_shap.sum()
    return out.sort_values("share", ascending=False)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    for name in sys.argv[1:] or ["full", "physics"]:
        print(f"\n### SHAP {name}"); print(shap_summary(name).round(3).head(12).to_string())
