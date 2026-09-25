"""Plausibility checks for list 2 (evaluation only): where do known dark companions land, and what does the backtest say?"""
import duckdb
import numpy as np
import pandas as pd

from .ablation import VARIANTS
from .apply_dr3 import score_dr3
from .paths import PROCESSED

CONTROL = {"Gaia-4 b": 1457486023639239296, "Gaia-5 b": 2074815898041643520}


def dr3_control_ranks() -> None:
    """Ranks of the control planets among all DR3 stars for the list-1 and list-2 scores (they are excluded from training and lists)."""
    d = score_dr3(min_poe=10)  # same population and quality filter as the lists (MANIFEST)
    a = pd.read_parquet(PROCESSED / "amplitude_dr3.parquet")[["source_id", "p13"]]
    d = d.merge(a, on="source_id")
    d["score2"] = np.where(d.ms_offset < 0.2, d.score * d.p13, np.nan)
    n_all, n2 = len(d), d.score2.notna().sum()
    for name, sid in CONTROL.items():
        r = d[d.source_id == sid]
        if r.empty:
            print(name, "not in the DR3 feature table"); continue
        r = r.iloc[0]
        r1 = int((d.score > r.score).sum()) + 1
        r2 = int((d.score2 > r.score2).sum()) + 1 if r.score2 == r.score2 else None
        print(f"{name}: poe {r.parallax_over_error:.0f}, G {r.phot_g_mean_mag:.1f}, ms_offset {r.ms_offset:.2f}, p13 {r.p13:.2f} | "
              f"rank list-1 score {r1:,}/{n_all:,} ({100 * r1 / n_all:.1f} %) | rank list-2 score "
              f"{'%s/%s (%.1f %%)' % (f'{r2:,}', f'{n2:,}', 100 * r2 / n2) if r2 else 'excluded by ms_offset >= 0.2'}")


def backtest_list2() -> None:
    """DR2 -> DR3: list-2 style score = OOF P_A * P(m2 < 13), ms_offset < 0.2; how do the 17 targets below 13 M_Jup rank?"""
    df = duckdb.sql(f"""
        SELECT f.source_id, f.ms_offset, coalesce(t.y_lt13, false) y13, coalesce(t.y_lt80, false) y80,
               o.score p_a, a.p13
        FROM '{PROCESSED}/features_dr2.parquet' f
        LEFT JOIN '{PROCESSED}/targets_dr2.parquet' t USING (source_id)
        JOIN '{PROCESSED}/oof_physics_dr2.parquet' o USING (source_id)
        JOIN '{PROCESSED}/amplitude_dr2.parquet' a USING (source_id)
        WHERE coalesce(t.excluded, false) = false""").df()
    d = df[df.ms_offset < 0.2].copy()
    d["score2"] = d.p_a * d.p13
    d["score1"] = d.p_a
    n = len(d)
    print(f"DR2 population with ms_offset < 0.2: {n:,}; targets < 13 M_Jup: {int(d.y13.sum())} of {int(df.y13.sum())}; < 80 M_Jup: {int(d.y80.sum())}")
    for name, col in (("list-1 score", "score1"), ("list-2 score", "score2")):
        s = d.sort_values(col, ascending=False)
        y13, y80 = s.y13.to_numpy(bool), s.y80.to_numpy(bool)
        r13 = np.flatnonzero(y13) + 1
        print(f"{name}: hits<13 in top 100/1000/10000: {y13[:100].sum()}/{y13[:1000].sum()}/{y13[:10000].sum()} | "
              f"median rank of the <13 targets {int(np.median(r13)) if len(r13) else None} of {n:,} | hits<80 in top 100/1000: {y80[:100].sum()}/{y80[:1000].sum()}")


if __name__ == "__main__":
    dr3_control_ranks()
    print()
    backtest_list2()
