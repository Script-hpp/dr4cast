"""Additional benchmarks for the backtest (MANIFEST 0.18): rule-based baseline, logistic regression, HGCA list,
neighbour-filter variants and region-bootstrap confidence intervals. Rules were fixed in the manifest before the first run."""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

from .ablation import PHYSICS
from .download import PIX_SPAN
from .evaluate_bet import MS_MAX, backtest_population
from .model_a import NEG_RATIO, N_FOLDS, SEED, region_folds
from .neighbour_test import neighbours
from .paths import PREDICTIONS, PROCESSED

POOL = 3000
TAU_GRID = [2, 3, 4, 5, 6, 8]


def load_full() -> pd.DataFrame:
    pop = backtest_population()
    f = duckdb.sql(f"""SELECT source_id, ra, dec, {', '.join(c for c in PHYSICS if c != 'ms_offset')}, ms_offset, hg_sig_gaia, has_hgca
                       FROM '{PROCESSED}/features_dr2.parquet'""").df().drop(columns=["ruwe_z"])
    pop = pop.merge(f, on="source_id")
    pop["p13"] = pop.source_id.map(pd.read_parquet(PROCESSED / "amplitude_dr2.parquet").set_index("source_id").p13)
    pop["p_a"] = pop.source_id.map(pd.read_parquet(PROCESSED / "oof_physics_dr2.parquet").set_index("source_id").score)
    return pop


def logreg_oof(pop: pd.DataFrame, target: str = "y80") -> np.ndarray:
    folds, oof = region_folds(pop.source_id), np.zeros(len(pop))
    X = pop[PHYSICS].to_numpy(float)
    y = pop[target].to_numpy(bool)
    for k in range(N_FOLDS):
        rng = np.random.default_rng(SEED + k)
        tr = np.flatnonzero(folds != k)
        pos, neg = tr[y[tr]], tr[~y[tr]]
        tr = np.concatenate([pos, rng.choice(neg, min(len(neg), NEG_RATIO * len(pos)), replace=False)])
        med = np.nanmedian(X[tr], axis=0)
        lo, hi = np.nanpercentile(X[tr], 0.5, axis=0), np.nanpercentile(X[tr], 99.5, axis=0)
        prep = lambda a: np.clip(np.where(np.isnan(a), med, a), lo, hi)
        Xtr = prep(X[tr])
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        m = LogisticRegression(C=0.1, class_weight="balanced", max_iter=1000).fit((Xtr - mu) / sd, y[tr])
        te = folds == k
        oof[te] = m.predict_proba((prep(X[te]) - mu) / sd)[:, 1]
    return oof


def add_scores(pop: pd.DataFrame) -> pd.DataFrame:
    pop = pop.copy()
    pop["logreg"] = logreg_oof(pop)
    pop["model_a"] = pop.p_a
    pop["model_a_list2"] = np.where(pop.ms_offset < MS_MAX, pop.p_a * pop.p13, np.nan)
    pop["rule_based_raw"] = np.where(pop.wobble_ratio < 1, pop.ruwe_z, np.nan)   # tau applied later
    pop["hgca"] = np.where(pop.has_hgca, pop.hg_sig_gaia, np.nan)
    pop["baseline_ruwe"], pop["baseline_ruwe_z"] = pop.ruwe, pop.ruwe_z
    return pop


METHODS = ["model_a", "model_a_list2", "logreg", "rule_based", "baseline_ruwe_z", "baseline_ruwe", "hgca"]


def score_of(pop: pd.DataFrame, method: str, tau: float) -> pd.Series:
    if method == "rule_based":
        return pop.rule_based_raw.where(pop.rule_based_raw > tau)
    return pop[{"model_a": "model_a", "model_a_list2": "model_a_list2", "logreg": "logreg", "hgca": "hgca",
                "baseline_ruwe_z": "baseline_ruwe_z", "baseline_ruwe": "baseline_ruwe"}[method]]


def pool_ids(pop: pd.DataFrame, tau: float) -> pd.DataFrame:
    parts = []
    for m in METHODS:
        s = score_of(pop, m, tau)
        idx = s.dropna().sort_values(ascending=False, kind="stable").head(POOL).index
        parts.append(pop.loc[idx, ["source_id", "ra", "dec"]])
    return pd.concat(parts).drop_duplicates("source_id")


def top_hits(pop: pd.DataFrame, score: pd.Series, nb: pd.Series, target: str, k: int, nb_filter: bool, new: bool = True) -> int:
    d = pop.assign(s=score)
    d = d[d.s.notna()]
    if new:
        d = d[~d.known_planet]
    if nb_filter:
        d = d[~(d.source_id.map(nb).fillna(0) > 0)]
    d = d.sort_values(["s", "source_id"], ascending=[False, True], kind="stable").head(k)
    return int(d[target].sum())


def region_bootstrap(score: np.ndarray, y: np.ndarray, region: np.ndarray, B: int, seed: int = 0) -> dict:
    ok = ~np.isnan(score)
    score, y, region = score[ok], y[ok], region[ok]
    order = np.argsort(region, kind="stable")
    score, y, region = score[order], y[order], region[order]
    cells, start = np.unique(region, return_index=True)
    bounds = np.append(start, len(region))
    rng = np.random.default_rng(seed)
    res = {"P@100": [], "P@1000": [], "AP": []}
    for _ in range(B):
        pick = rng.integers(0, len(cells), len(cells))
        idx = np.concatenate([np.arange(bounds[c], bounds[c + 1]) for c in pick])
        s, yy = score[idx], y[idx]
        o = np.argsort(-s, kind="stable")
        yo = yy[o]
        res["P@100"].append(yo[:100].mean())
        res["P@1000"].append(yo[:1000].mean())
        r = np.flatnonzero(yo) + 1
        res["AP"].append((np.arange(1, len(r) + 1) / r).mean() if len(r) else np.nan)
    return {k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))) for k, v in res.items()}


def run(B: int = 200) -> dict:
    pd.set_option("display.width", 220)
    pop = add_scores(load_full())
    out = {"population": len(pop), "positives": int(pop.y80.sum())}
    # --- tau for the rule-based baseline: smallest tau with the largest P@1000 (with neighbour filter, target y80, all hits)
    nb_path = PREDICTIONS / "backtest_neighbours_dr2.parquet"
    if nb_path.exists():
        nb = pd.read_parquet(nb_path).set_index("source_id").n
    else:
        pool = pool_ids(pop, min(TAU_GRID))
        nb = pd.Series(neighbours(pool).to_numpy(), index=pool.source_id.to_numpy(), name="n")
        nb.rename_axis("source_id").reset_index().to_parquet(nb_path, index=False)
    p1000 = {t: top_hits(pop, score_of(pop, "rule_based", t), nb, "y80", 1000, True, new=False) for t in TAU_GRID}
    tau = min(t for t in TAU_GRID if p1000[t] == max(p1000.values()))
    out["tau_grid_hits@1000_with_neighbour_filter"], out["tau"] = p1000, tau
    print("tau grid (hits@1000 with neighbour filter):", p1000, "-> tau =", tau, flush=True)
    # --- top-k table, with and without the neighbour filter
    rows = []
    for m in METHODS:
        if m == "hgca":
            continue  # compared on its own subset below
        s = score_of(pop, m, tau)
        for tgt in ("y80", "y13_ms"):
            if tgt == "y13_ms" and m not in ("model_a_list2", "model_a", "logreg", "rule_based"):
                pass
            for nf in (False, True):
                rows.append({"method": m, "target": tgt, "neighbour_filter": nf,
                             "hits@100": top_hits(pop, s, nb, tgt, 100, nf), "hits@1000": top_hits(pop, s, nb, tgt, 1000, nf)})
    tab = pd.DataFrame(rows)
    print(tab.pivot_table(index="method", columns=["target", "neighbour_filter"], values=["hits@100", "hits@1000"]).to_string(), flush=True)
    out["topk"] = rows
    # --- HGCA subset comparison
    h = pop[pop.has_hgca]
    print(f"\nHGCA subset: {len(h):,} stars, {int(h.y80.sum())} of {int(pop.y80.sum())} targets ({h.y80.sum() / pop.y80.sum():.1%})")
    hg = {}
    for m in ("hgca", "model_a", "logreg", "rule_based", "baseline_ruwe_z", "baseline_ruwe"):
        s = score_of(h, m, tau)
        d = h.assign(s=s)
        d = d[d.s.notna()]
        srt = d.sort_values("s", ascending=False, kind="stable")
        hg[m] = {"n_scored": len(d), "hits@100": int(srt.y80.head(100).sum()), "AUC": roc_auc_score(d.y80, d.s) if d.y80.any() and (~d.y80).any() else np.nan,
                 "AP": average_precision_score(d.y80, d.s) if d.y80.any() else np.nan}
    print(pd.DataFrame(hg).T.round(4).to_string(), flush=True)
    out["hgca_subset"] = hg
    # --- bootstrap intervals over HEALPix level-2 cells
    region = (pop.source_id.to_numpy() // PIX_SPAN).astype(int)
    ci = {}
    for m in ("model_a", "model_a_list2", "logreg", "rule_based", "baseline_ruwe_z", "baseline_ruwe"):
        s = score_of(pop, m, tau).to_numpy(float)
        ci[m] = region_bootstrap(s, pop.y80.to_numpy(bool), region, B)
        print(m, {k: tuple(round(x, 4) for x in v) for k, v in ci[m].items()}, flush=True)
    out["bootstrap_95ci"] = ci
    (PREDICTIONS / "benchmarks_backtest.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    return out


if __name__ == "__main__":
    import sys

    run(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
