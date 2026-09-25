"""Generate both bet lists in one run from the same state (MANIFEST.md 0.14).

List 1: score = P_A (Model A, physics variant, mean of the five region models).
List 2: score = P_A * P(m2 < 13 M_Jup), only stars with ms_offset < MS_OFFSET_MAX.
Both: population DR3 with parallax_over_error >= 10; known cases stay in the file but are marked; the ranking of the main metric
(`rank_new`) skips stars with a known DR3 orbit < 80 M_Jup, a known planet, or a Gaia neighbour within 2".

The output is a pure function of its inputs: the same models, features, neighbour table, date and commit string produce
byte-identical files. Neighbours come from the Gaia archive once and are cached with the list bundle.
"""
import hashlib
import json
import subprocess
from pathlib import Path

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd

from .ablation import VARIANTS
from .apply_dr3 import VARIANT, flags
from .paths import MODELS, PREDICTIONS, PROCESSED

MS_OFFSET_MAX = 0.2
POOL = 3000       # candidates per list that get the neighbour query
LIST_SIZE = 1000  # rows written per list, ranked by rank_new (the frozen bet is the first 100)
NEIGHBOUR_ARCSEC = 2.0
COLUMNS = ["rank_new", "source_id", "score", "p_a", "p_m2_lt13", "rank_raw", "ms_offset", "known_dr3_orbit80",
           "known_dr3_orbit_any", "dr3_acceleration", "known_planet", "neighbour_2arcsec"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_state() -> str:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], text=True).strip() != ""
        return commit + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def manifest_version() -> str:
    for line in (Path(__file__).resolve().parents[2] / "MANIFEST.md").read_text().splitlines():
        if line.startswith("**Version:**"):
            return line.split("**Version:**")[1].strip()
    return "unknown"


def score_population(min_poe: float = 10) -> pd.DataFrame:
    feats = VARIANTS[VARIANT]
    df = duckdb.sql(f"""
        SELECT f.source_id, f.ra, f.dec, {', '.join('f.' + c for c in feats)}, a.p13 AS p_m2_lt13
        FROM '{PROCESSED}/features_dr3.parquet' f JOIN '{PROCESSED}/amplitude_dr3.parquet' a USING (source_id)
        WHERE f.parallax_over_error >= {min_poe}""").df()
    boosters = [lgb.Booster(model_file=str(MODELS / f"ablation_{VARIANT}_fold{k}.txt")) for k in range(5)]
    df["p_a"] = np.mean([b.predict(df[feats]) for b in boosters], axis=0)
    return flags(df)


def gaia_neighbours(pool: pd.DataFrame) -> pd.Series:
    """Number of Gaia DR3 sources within 2" of each pool star (archive query; cache the result with the bundle)."""
    from astropy.table import Table

    from .diagnose_top import HEIDELBERG
    from .download import run_async

    t = Table({"source_id": pool.source_id.to_numpy("int64"), "ra": pool.ra.to_numpy(float), "dec": pool.dec.to_numpy(float)})
    q = f"""SELECT u.source_id, count(*) AS n FROM TAP_UPLOAD.ids u
            JOIN gaiadr3.gaia_source g ON 1 = CONTAINS(POINT('ICRS', g.ra, g.dec), CIRCLE('ICRS', u.ra, u.dec, {NEIGHBOUR_ARCSEC / 3600}))
            WHERE g.source_id <> u.source_id GROUP BY u.source_id"""
    r = run_async(q, uploads={"ids": t}, url=HEIDELBERG, wall_clock=1800).to_pandas().set_index("source_id").n
    return pool.source_id.map(r).fillna(0).astype(int)


def rank_list(df: pd.DataFrame, score: pd.Series, neighbours: pd.Series) -> pd.DataFrame:
    d = df.assign(score=score.round(8), neighbour_2arcsec=df.source_id.map(neighbours).fillna(0).astype(int) > 0)
    d = d.sort_values(["score", "source_id"], ascending=[False, True], kind="stable")
    d["rank_raw"] = np.arange(1, len(d) + 1)
    ok = ~(d.known_dr3_orbit80 | d.known_planet | d.neighbour_2arcsec)
    d.loc[ok, "rank_new"] = np.arange(1, ok.sum() + 1)
    d["rank_new"] = d.rank_new.astype("Int64")
    d["p_a"] = d.p_a.round(8)
    d["p_m2_lt13"] = d.p_m2_lt13.round(8)
    d["ms_offset"] = d.ms_offset.round(6)
    return d


def build_lists(out_dir: Path, date: str, commit: str, neighbour_cache: Path, pop: pd.DataFrame | None = None,
                neighbour_fn=gaia_neighbours, version: str | None = None) -> dict:
    """Write list1/list2 CSVs (with header block and .sha256 files) and lists_manifest.json into `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pop = score_population() if pop is None else pop
    cand = {
        "list1_substellar": pop.assign(score=pop.p_a),
        "list2_planets": pop[pop.ms_offset < MS_OFFSET_MAX].assign(score=lambda x: x.p_a * x.p_m2_lt13),
    }
    pools = {k: v.sort_values(["score", "source_id"], ascending=[False, True]).head(POOL) for k, v in cand.items()}
    pool_ids = pd.concat(pools.values()).drop_duplicates("source_id")
    if neighbour_cache.exists():
        nb = pd.read_parquet(neighbour_cache)
    else:
        nb = pool_ids[["source_id"]].assign(n=neighbour_fn(pool_ids).to_numpy())
    if not set(pool_ids.source_id) <= set(nb.source_id):
        raise ValueError("neighbour cache does not cover the candidate pool; delete it and rebuild")
    nb.sort_values("source_id").to_parquet(neighbour_cache, index=False)
    nbs = nb.set_index("source_id").n
    files, meta = {}, {"date": date, "git_commit": commit, "manifest_version": manifest_version(),
                       "model_files": {f"ablation_{VARIANT}_fold{k}.txt": sha256_file(MODELS / f"ablation_{VARIANT}_fold{k}.txt") for k in range(5)},
                       "features_dr3_sha256": sha256_file(PROCESSED / "features_dr3.parquet"),
                       "amplitude_dr3_sha256": sha256_file(PROCESSED / "amplitude_dr3.parquet"),
                       "neighbour_table_sha256": sha256_file(neighbour_cache), "lists": {}}
    for name, df in cand.items():
        pool = pools[name]
        ranked = rank_list(pool, pool.score, nbs)
        top = ranked[ranked.rank_new.notna()].head(LIST_SIZE)
        top = top.sort_values("rank_new")[COLUMNS]
        path = out_dir / f"{name}.csv"
        header = [f"# {name}: Gaia Wobble Bet, list built from MANIFEST {meta['manifest_version']}",
                  f"# date {date}", f"# git {commit}", f"# population: Gaia DR3, parallax_over_error >= 10, {len(df)} candidate stars",
                  "# score: " + ("P_A" if name == "list1_substellar" else f"P_A * P(m2<13 MJ), ms_offset < {MS_OFFSET_MAX}") +
                  " (an ordering score, not a calibrated probability)",
                  f"# rank_new skips known DR3 orbit <80 MJ, known planets and Gaia neighbours within {NEIGHBOUR_ARCSEC} arcsec",
                  "# the frozen bet is rank_new <= 100"]
        path.write_text("\n".join(header) + "\n" + top.to_csv(index=False, float_format="%.8g", lineterminator="\n"))
        digest = sha256_file(path)
        (out_dir / f"{name}.csv.sha256").write_text(f"{digest}  {name}.csv\n")
        meta["lists"][name] = {"sha256": digest, "rows": len(top)}
        files[name] = path
    (out_dir / "lists_manifest.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return meta


if __name__ == "__main__":
    import sys
    from datetime import date as _date

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = PREDICTIONS / (args[0] if args else "dev_lists")
    if "--reproduce" in sys.argv:
        # Rebuild a published bundle: reuse its date, code state, manifest version and neighbour table, then compare checksums.
        ref = Path(sys.argv[sys.argv.index("--reproduce") + 1])
        r = json.loads((ref / "lists_manifest.json").read_text())
        out = Path(args[0]) if args else out
        m = build_lists(out, r["date"], r["git_commit"], ref / "neighbours_dr3.parquet", version=r["manifest_version"])
        for name, v in r["lists"].items():
            print(f"{name}: {'MATCH' if m['lists'][name]['sha256'] == v['sha256'] else 'DIFFERENT'} {m['lists'][name]['sha256']}")
        print("models:", "MATCH" if m["model_files"] == r["model_files"] else "DIFFERENT",
              "| features:", "MATCH" if m["features_dr3_sha256"] == r["features_dr3_sha256"] else "DIFFERENT",
              "| amplitude:", "MATCH" if m["amplitude_dr3_sha256"] == r["amplitude_dr3_sha256"] else "DIFFERENT")
        raise SystemExit(0)
    m = build_lists(out, _date.today().isoformat(), git_state(), out / "neighbours_dr3.parquet")
    print(json.dumps({k: v for k, v in m.items() if k in ("date", "git_commit", "manifest_version", "lists")}, indent=2))
