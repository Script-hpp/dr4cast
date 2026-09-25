"""Ranking metrics from MANIFEST.md: P@10, P@30, P@100, Recall@100, absolute hits; every metric in two variants.

- all:  hits among all positives
- new:  known planet hosts (training labels) are removed from the list and from the positives
"""
import numpy as np
import pandas as pd

KS = (10, 30, 100, 1000)
G_CLASSES = [(-np.inf, 10, "G<10"), (10, 13, "10-13"), (13, 16, "13-16"), (16, 19, "16-19"), (19, np.inf, "G>=19")]


def _metrics(y_sorted: np.ndarray, n_pos: int) -> dict:
    out = {f"P@{k}": y_sorted[:k].mean() if len(y_sorted) else np.nan for k in KS}
    out["hits@100"] = int(y_sorted[:100].sum())
    out["hits@1000"] = int(y_sorted[:1000].sum())
    out["Recall@100"] = y_sorted[:100].sum() / n_pos if n_pos else np.nan
    out["n_pos"] = n_pos
    return out


def evaluate(df: pd.DataFrame, score: str, y: str = "y", known: str = "known_planet") -> pd.DataFrame:
    """`df` needs columns `score`, boolean `y`, boolean `known`. Returns one row per variant."""
    rows = {}
    for variant, d in (("all", df), ("new", df[~df[known]])):
        d = d.sort_values(score, ascending=False, kind="stable")
        rows[variant] = _metrics(d[y].to_numpy(bool), int(d[y].sum()))
    return pd.DataFrame(rows).T


def evaluate_by_brightness(df: pd.DataFrame, score: str, mag: str = "phot_g_mean_mag", **kw) -> pd.DataFrame:
    """Same metrics with the list formed inside each brightness class (variant 'new')."""
    rows = {}
    for lo, hi, name in G_CLASSES:
        d = df[(df[mag] >= lo) & (df[mag] < hi)]
        rows[name] = evaluate(d, score, **kw).loc["new"]
    return pd.DataFrame(rows).T


def evaluate_curve(df: pd.DataFrame, score: str, y: str = "y", known: str = "known_planet") -> pd.DataFrame:
    """Supplementary metrics that stay informative when P@100 is zero: ROC-AUC, average precision,
    recall within the top 1 %, 5 %, 10 % of the population, and the best target rank."""
    from sklearn.metrics import average_precision_score, roc_auc_score

    rows = {}
    for variant, d in (("all", df), ("new", df[~df[known]])):
        d = d.sort_values(score, ascending=False, kind="stable")
        yy = d[y].to_numpy(bool)
        n = len(d)
        r = {"AUC": roc_auc_score(yy, d[score]), "AP": average_precision_score(yy, d[score])}
        for pct in (1, 5, 10):
            r[f"Recall@{pct}%"] = yy[: n * pct // 100].sum() / max(yy.sum(), 1)
        r["best_rank"] = int(np.flatnonzero(yy)[0]) + 1 if yy.any() else -1
        rows[variant] = r
    return pd.DataFrame(rows).T
