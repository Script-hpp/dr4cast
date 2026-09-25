"""Model A: LightGBM on DR2 features -> DR3 orbit target (< 80 M_Jup), with region-grouped cross-validation.

Out-of-fold scores are produced for every star, so evaluation always uses the full population.
Training details (fixed before the first run): negatives are down-sampled 1:NEG_RATIO inside the training folds,
early stopping on average precision using a held-out region fold, strong regularisation.
"""
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from .download import PIX_SPAN
from .features import COMMON
from .paths import MODELS, PROCESSED

NEG_RATIO = 50
N_FOLDS = 5
SEED = 42
PARAMS = dict(
    objective="binary", learning_rate=0.05, num_leaves=15, min_child_samples=200, subsample=0.8, subsample_freq=1,
    colsample_bytree=0.7, reg_lambda=10.0, n_estimators=2000, random_state=SEED, n_jobs=-1, verbose=-1,
)


def load(min_poe: float | None = 10, release: str = "dr2", features: list[str] = COMMON) -> pd.DataFrame:
    import duckdb

    where = "" if min_poe is None else f"AND f.parallax_over_error >= {min_poe}"
    cols = ", ".join(f"f.{c}" for c in features)
    return duckdb.sql(f"""
        SELECT f.source_id, {cols}, coalesce(t.y_lt80, false) AS y, coalesce(t.y_lt13, false) AS y13,
               l.source_id IS NOT NULL AS known_planet
        FROM '{PROCESSED}/features_{release}.parquet' f
        LEFT JOIN '{PROCESSED}/targets_dr2.parquet' t USING (source_id)
        LEFT JOIN (SELECT DISTINCT source_id FROM '{PROCESSED}/labels_backtest_dr2.parquet') l USING (source_id)
        WHERE coalesce(t.excluded, false) = false {where}
    """).df()


def region_folds(source_id: pd.Series) -> np.ndarray:
    """Level-2 HEALPix pixel of the star (source_id encodes it) -> fold, whole pixels go to one fold."""
    pix = (source_id.to_numpy() // PIX_SPAN).astype(int)
    fold_of_pix = np.random.default_rng(SEED).permutation(192) % N_FOLDS
    return fold_of_pix[pix]


def fit_fold(df: pd.DataFrame, features: list[str], folds: np.ndarray, k: int, label: str = "y"):
    rng = np.random.default_rng(SEED + k)
    train_folds = [f for f in range(N_FOLDS) if f != k]
    val_fold = train_folds[k % len(train_folds)]  # a region held out from training, used for early stopping only
    tr = df[np.isin(folds, [f for f in train_folds if f != val_fold])]
    va = df[folds == val_fold]
    pos, neg = tr[tr[label]], tr[~tr[label]]
    neg = neg.iloc[rng.choice(len(neg), min(len(neg), NEG_RATIO * len(pos)), replace=False)]
    tr = pd.concat([pos, neg])
    model = lgb.LGBMClassifier(**PARAMS)
    model.fit(tr[features], tr[label], eval_set=[(va[features], va[label])], eval_metric="average_precision",
              callbacks=[lgb.early_stopping(100, first_metric_only=True, verbose=False)])
    return model


def cross_val_predict(df: pd.DataFrame, features: list[str] = COMMON, label: str = "y"):
    folds = region_folds(df.source_id)
    oof = np.zeros(len(df))
    models = []
    for k in range(N_FOLDS):
        m = fit_fold(df, features, folds, k, label)
        oof[folds == k] = m.predict_proba(df.loc[folds == k, features])[:, 1]
        models.append(m)
        print(f"fold {k}: trees {m.best_iteration_}, AP on own region {average_precision_score(df.loc[folds == k, label], oof[folds == k]):.4f}")
    return oof, models


if __name__ == "__main__":
    from .metrics import evaluate, evaluate_by_brightness, evaluate_curve

    pd.set_option("display.width", 200)
    df = load(10)
    print(f"{len(df):,} stars, {int(df.y.sum())} positives, features: {len(COMMON)}")
    df["score"], models = cross_val_predict(df)
    df[["source_id", "score"]].to_parquet(PROCESSED / "oof_model_a_dr2.parquet", index=False)
    MODELS.mkdir(parents=True, exist_ok=True)
    for i, m in enumerate(models):
        m.booster_.save_model(str(MODELS / f"model_a_fold{i}.txt"))
    print("\nModel A (target < 80 M_Jup)"); print(evaluate(df, "score").round(3).to_string())
    print(evaluate_curve(df, "score").round(4).to_string())
    print("\nby brightness class (new hits)"); print(evaluate_by_brightness(df, "score").round(3).to_string())
    imp = pd.Series(np.mean([m.booster_.feature_importance("gain") for m in models], axis=0), index=COMMON)
    print("\nfeature gain share"); print((imp / imp.sum()).sort_values(ascending=False).round(3).head(12).to_string())
