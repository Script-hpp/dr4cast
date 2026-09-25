"""Evaluation of the bet, written and frozen BEFORE the DR4 release (MANIFEST 0.15).

One code path for both the dry run and the real evaluation:
  backtest: DR2 scores  -> DR3 outcomes   (runs today, reproduces the logged numbers)
  bet:      DR3 lists   -> DR4 outcomes   (needs the DR4 tables in data/raw/dr4/, format below)

Targets (per list, each as "all" and "new" hits, MANIFEST):
  y80     orbit solution, estimated companion mass < 80 M_Jup          (list 1)
  y13     ... < 13 M_Jup, no ms_offset condition                       (list 2, additionally reported)
  y13_ms  ... < 13 M_Jup and ms_offset < 0.2 with the later release's values   (list 2, main)
  y80_ms  ... < 80 M_Jup and ms_offset < 0.2                           (reported for reference)
Solution types `OrbitalTargetedSearch*` / `OrbitalAlternative*` and orbits without mass estimate are excluded (label unknown),
targeted searches are counted separately as `y80_targeted`.
Links between releases: only through the neighbourhood table; several candidates are resolved by the smallest angular distance,
ties by the smallest magnitude difference; a star without link has no outcome and is negative.

DR4 input format (data/raw/dr4/), Parquet, same column names as the DR3 tables of the same name (checked by `check_dr4_schema`):
  nss_two_body_orbit.parquet  (source_id, nss_solution_type, a/b/f/g_thiele_innes, parallax, period)
  nss_multiple_orbits.parquet (same columns; may be absent)
  primary_masses.parquet      (source_id, m1) primary masses in M_sun; if DR4 ships masses (`nss_masses`) they are used only as a comparison
  dr3_neighbourhood.parquet   (dr3_source_id, dr4_source_id, angular_distance, magnitude_difference)
  features_dr4.parquet        (source_id, ms_offset, ...) built with `features.py`/`physics_features.py` from the DR4 nearby sample
"""
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from .masses import estimate_m2
from .metrics import evaluate, evaluate_by_brightness, evaluate_curve
from .paths import PREDICTIONS, PROCESSED, RAW

MS_MAX = 0.2
TARGETS = ["y80", "y13", "y13_ms", "y80_ms"]
DR4_FILES = ["nss_two_body_orbit", "primary_masses", "dr3_neighbourhood", "features_dr4"]
DR4_COLUMNS = {
    "nss_two_body_orbit": {"source_id", "nss_solution_type", "a_thiele_innes", "b_thiele_innes", "f_thiele_innes", "g_thiele_innes", "parallax", "period"},
    "primary_masses": {"source_id", "m1"},
    "dr3_neighbourhood": {"dr3_source_id", "dr4_source_id", "angular_distance", "magnitude_difference"},
    "features_dr4": {"source_id", "ms_offset"},
}


def check_dr4_schema(root: Path = RAW / "dr4") -> None:
    for name in DR4_FILES:
        f = root / f"{name}.parquet"
        if not f.exists():
            raise FileNotFoundError(f"{f} missing; see the module docstring for the expected DR4 layout")
        cols = set(duckdb.sql(f"DESCRIBE SELECT * FROM '{f}'").df().column_name)
        if not DR4_COLUMNS[name] <= cols:
            raise ValueError(f"{f}: missing columns {sorted(DR4_COLUMNS[name] - cols)}")


def resolve_links(links: pd.DataFrame, src: str, dst: str) -> pd.DataFrame:
    """One later-release id per source star: smallest angular distance, ties by smallest |magnitude difference|."""
    d = links.assign(_m=links.magnitude_difference.abs())
    d = d.sort_values([src, "angular_distance", "_m", dst], kind="stable").drop_duplicates(src)
    return d[[src, dst]]


def outcomes_from_solutions(sol: pd.DataFrame, features_later: pd.DataFrame) -> pd.DataFrame:
    """`sol`: orbit solutions with m1 (columns of nss_two_body_orbit plus m1) -> one row per later-release star with the target flags."""
    s = sol.copy()
    s["m2"] = np.nan
    ok = s.m1.notna() & (s.parallax > 0) & (s.period > 0) & s.a_thiele_innes.notna()
    s.loc[ok, "m2"] = estimate_m2(s[ok], s.loc[ok, "m1"])
    s["orbital"] = s.nss_solution_type == "Orbital"
    s["targeted"] = s.nss_solution_type.str.startswith("OrbitalTargetedSearch") | s.nss_solution_type.str.startswith("OrbitalAlternative")
    o = pd.DataFrame(index=s.source_id.unique())
    o["y80"] = s[s.orbital & (s.m2 < 80)].groupby("source_id").size().reindex(o.index).fillna(0) > 0
    o["y13"] = s[s.orbital & (s.m2 < 13)].groupby("source_id").size().reindex(o.index).fillna(0) > 0
    o["y80_targeted"] = s[s.targeted].groupby("source_id").size().reindex(o.index).fillna(0) > 0
    o["excluded"] = s[(s.orbital & s.m2.isna()) | s.targeted].groupby("source_id").size().reindex(o.index).fillna(0) > 0
    o = o.join(features_later.set_index("source_id")[["ms_offset"]], how="left")
    o["y13_ms"] = o.y13 & (o.ms_offset < MS_MAX)
    o["y80_ms"] = o.y80 & (o.ms_offset < MS_MAX)
    o.loc[o.y80 | o.y13, "excluded"] = False  # a positive is never excluded
    o.index.name = "source_id"
    return o.reset_index()


def evaluate_scores(pop: pd.DataFrame, score: str, targets: list[str] = TARGETS) -> dict:
    """`pop`: eligible stars with columns `score`, target flags, `known_planet`, `phot_g_mean_mag`. Returns metric frames per target."""
    out = {}
    for t in targets:
        d = pop.assign(y=pop[t])
        out[t] = {"top": evaluate(d, score), "curve": evaluate_curve(d, score), "brightness": evaluate_by_brightness(d, score)}
    return out


def ranked_variants(pop: pd.DataFrame, lists: dict[str, pd.Series], ms_rule_lists: set[str]) -> dict:
    """Metrics for every list/baseline: ranking by its score inside the eligible population (list 2 style ones only ms_offset < MS_MAX)."""
    res = {}
    for name, score in lists.items():
        d = pop.assign(score=score.reindex(pop.index))
        d = d[d.score.notna()]
        if name in ms_rule_lists:
            d = d[d.ms_offset_earlier < MS_MAX]
        res[name] = evaluate_scores(d, "score")
    return res


# ---------------------------------------------------------------- dry run on the backtest (DR2 scores -> DR3 outcomes)

def backtest_population() -> pd.DataFrame:
    """DR2 stars (parallax_over_error >= 10) with DR3 outcomes; the linked DR3 orbit solution decides, ms_offset is the DR3 value."""
    df = duckdb.sql(f"""
        SELECT f.source_id, f.phot_g_mean_mag, f.ruwe, f.ruwe_z, f.ms_offset AS ms_offset_earlier,
               l.source_id IS NOT NULL AS known_planet
        FROM '{PROCESSED}/features_dr2.parquet' f
        LEFT JOIN (SELECT DISTINCT source_id FROM '{PROCESSED}/labels_backtest_dr2.parquet') l USING (source_id)
        WHERE f.parallax_over_error >= 10""").df()
    links = pd.read_parquet(RAW / "dr2_links" / "orbit_solutions.parquet")
    links = resolve_links(links, "dr3_source_id", "dr2_source_id")  # one DR2 star per DR3 solution source (smallest distance)
    sol = duckdb.sql(f"""
        SELECT n.source_id, n.nss_solution_type, n.a_thiele_innes, n.b_thiele_innes, n.f_thiele_innes, n.g_thiele_innes,
               n.parallax, n.period, b.m1
        FROM '{RAW}/nss/nss_two_body_orbit.parquet' n
        LEFT JOIN (SELECT source_id, any_value(m1) AS m1 FROM '{RAW}/dr3_tables/binary_masses.parquet'
                   WHERE combination_method LIKE 'Orbital%' GROUP BY 1) b USING (source_id)
        WHERE n.nss_solution_type LIKE 'Orbital%'
          AND n.source_id NOT IN (4698424845771339520, 5765846127180770432, 522135261462534528, 1712614124767394816)""").df()
    f3 = duckdb.sql(f"SELECT source_id, ms_offset FROM '{PROCESSED}/features_dr3.parquet'").df()
    o = outcomes_from_solutions(sol, f3).rename(columns={"source_id": "dr3_source_id"})
    o = o.merge(links, on="dr3_source_id", how="inner").rename(columns={"dr2_source_id": "source_id"})
    o = o.groupby("source_id")[["y80", "y13", "y13_ms", "y80_ms", "y80_targeted", "excluded"]].max().reset_index()
    pop = df.merge(o, on="source_id", how="left")
    for c in ["y80", "y13", "y13_ms", "y80_ms", "y80_targeted", "excluded"]:
        pop[c] = pop[c].fillna(False).astype(bool)
    return pop[~pop.excluded].reset_index(drop=True)


def dry_run() -> dict:
    pop = backtest_population()
    oof = pd.read_parquet(PROCESSED / "oof_physics_dr2.parquet").set_index("source_id").score
    p13 = pd.read_parquet(PROCESSED / "amplitude_dr2.parquet").set_index("source_id").p13
    p = pop.set_index("source_id", drop=False)
    lists = {"list1_score": oof, "list2_score": oof * p13, "baseline_ruwe": p.ruwe, "baseline_ruwe_z": p.ruwe_z}
    return {"population": len(pop), "targets": {t: int(pop[t].sum()) for t in TARGETS},
            "results": ranked_variants(p, lists, ms_rule_lists={"list2_score"})}



# ---------------------------------------------------------------- competitor lists (DR3-based, only for the DR3 -> DR4 evaluation)

def competitor_scores(dr3_ids: pd.Series) -> dict[str, pd.Series]:
    """Scores of the published competitor lists for the stars of our DR3 population (index = DR3 source_id, NaN = not listed).

    Ordering rules (fixed before the release, MANIFEST):
      exodnn   : PredProb1 descending (the published probability); ties by source_id.
      kiefer   : s_RUWE descending (significance of the RUWE anomaly), then Mplmin ascending, then source_id. The catalogue is a set
                 of candidates, not a ranking; this is our documented ordering.
      sahlmann : the 20 candidates (22 in Table 4 minus the two solutions retracted by Gaia) as an unranked set; score 1 for members.
    The lists come from DR3 data, the same input as our lists; they cannot be used in the DR2 -> DR3 backtest.
    """
    root = RAW / "competitors"
    out = {}
    ex = pd.read_parquet(root / "exodnn.parquet").sort_values(["PredProb1", "source_id"], ascending=[False, True])
    out["exodnn"] = ex.set_index("source_id").PredProb1
    ki = pd.read_parquet(root / "kiefer.parquet").sort_values(["s_RUWE", "Mplmin", "source_id"], ascending=[False, True, True])
    ki["score"] = np.arange(len(ki), 0, -1, dtype=float)  # rank score: first row highest
    out["kiefer"] = ki.set_index("source_id").score
    sg = pd.read_parquet(root / "sahlmann_gomez.parquet")
    out["sahlmann"] = pd.Series(1.0, index=sg[~sg.retracted].source_id)
    return {k: v[~v.index.duplicated()].reindex(dr3_ids) for k, v in out.items()}


def competitor_coverage() -> pd.DataFrame:
    """How many stars of each competitor list are in our DR3 population (parallax_over_error >= 10) and how many are already known."""
    f = duckdb.sql(f"SELECT source_id FROM '{PROCESSED}/features_dr3.parquet' WHERE parallax_over_error >= 10").df().source_id
    known = set(duckdb.sql(f"SELECT source_id FROM '{PROCESSED}/dr3_orbit_targets.parquet' WHERE nss_solution_type = 'Orbital' AND m2_est_mjup < 80").df().source_id)
    known |= set(duckdb.sql(f"SELECT source_id FROM '{PROCESSED}/labels_bet_dr3.parquet'").df().source_id)
    rows = {}
    for name, sc in competitor_scores(pd.Series(f.unique())).items():
        listed = sc.dropna()
        full = {"exodnn": 7414, "kiefer": 9698, "sahlmann": 20}[name]
        rows[name] = {"in_list": full, "in_our_population": len(listed), "share": len(listed) / full,
                      "already_known_in_DR3": int(listed.index.isin(known).sum())}
    return pd.DataFrame(rows).T


def to_markdown(res: dict) -> str:
    lines = [f"population {res['population']:,}; targets {res['targets']}"]
    for name, r in res["results"].items():
        for t, m in r.items():
            lines += [f"\n### {name} / {t}", m["top"].round(4).to_string(), m["curve"].round(4).to_string()]
    return "\n".join(lines)


if __name__ == "__main__":
    res = dry_run()
    md = to_markdown(res)
    (PREDICTIONS / "dry_run_backtest.md").write_text(md + "\n")
    pd.set_option("display.width", 200)
    for name in res["results"]:
        print(f"\n=== {name}")
        for t in ("y80", "y13_ms"):
            m = res["results"][name][t]
            print(t, "| new:", m["top"].loc["new"].round(3).to_dict(), "| AUC", round(m["curve"].loc["new", "AUC"], 3))
    print("\npopulation", res["population"], res["targets"])
