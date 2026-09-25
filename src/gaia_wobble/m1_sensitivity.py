"""Sensitivity of the DR3 targets to the source of the primary mass m1 (docs/clarifications_v1.md).

Same solutions, same code (`evaluate_bet.outcomes_from_solutions`), once with m1 from `binary_masses` and once with `mass_ms`
(Mamajek main sequence, `primary_masses.mass_ms_strict`). Population: DR3 nearby sample. Run before DR4; the choice of `mass_ms` as the
official rule does not depend on this result.
"""
import duckdb, numpy as np, pandas as pd
from gaia_wobble import evaluate_bet as eb
from gaia_wobble.primary_masses import mass_ms_strict
from gaia_wobble.paths import PROCESSED, RAW


def run():
    pd.set_option("display.width", 200)
    sol = duckdb.sql(f"""
      SELECT n.source_id, n.nss_solution_type, n.a_thiele_innes, n.b_thiele_innes, n.f_thiele_innes, n.g_thiele_innes, n.parallax, n.period,
             b.m1 AS m1_bm, f.abs_g, f.ms_offset
      FROM '{RAW}/nss/nss_two_body_orbit.parquet' n
      JOIN '{PROCESSED}/features_dr3.parquet' f USING (source_id)
      LEFT JOIN (SELECT source_id, any_value(m1) m1 FROM '{RAW}/dr3_tables/binary_masses.parquet' WHERE combination_method LIKE 'Orbital%' GROUP BY 1) b USING (source_id)
      WHERE n.nss_solution_type LIKE 'Orbital%'
        AND n.source_id NOT IN (4698424845771339520, 5765846127180770432, 522135261462534528, 1712614124767394816)""").df()
    sol["m1_ms"] = mass_ms_strict(sol.abs_g.to_numpy(float))
    f3 = sol[["source_id", "ms_offset"]].drop_duplicates("source_id")
    res = {}
    for name, col in (("binary_masses", "m1_bm"), ("mass_ms", "m1_ms")):
        o = eb.outcomes_from_solutions(sol.assign(m1=sol[col]), f3).set_index("source_id")
        res[name] = o
    print("solutions in the DR3 sample:", sol.source_id.nunique(), "| type Orbital:", int((sol.nss_solution_type == "Orbital").sum()))
    print("m1 available: binary_masses", int(sol.m1_bm.notna().sum()), "| mass_ms", int(sol.m1_ms.notna().sum()), "| both", int((sol.m1_bm.notna() & sol.m1_ms.notna()).sum()))
    b = sol[sol.m1_bm.notna() & sol.m1_ms.notna() & (sol.nss_solution_type == "Orbital")]
    r = b.m1_ms / b.m1_bm
    print("m1_ms / m1_bm on Orbital solutions with both: median", round(r.median(), 3), "| quartiles", r.quantile([.25, .75]).round(3).tolist(), "| share within +-20 %:", round(((r > .8) & (r < 1.2)).mean(), 3))
    rows = []
    for t in ("y80", "y13", "y13_ms", "y80_ms"):
        a, c = res["binary_masses"][t], res["mass_ms"][t]
        idx = a.index.union(c.index)
        a, c = a.reindex(idx).fillna(False), c.reindex(idx).fillna(False)
        rows.append({"target": t, "binary_masses": int(a.sum()), "mass_ms": int(c.sum()), "both": int((a & c).sum()), "only_binary_masses": int((a & ~c).sum()), "only_mass_ms": int((~a & c).sum())})
    print(pd.DataFrame(rows).to_string(index=False))
    ex = {k: int(v.excluded.sum()) for k, v in res.items()}
    print("excluded (label unknown):", ex)

    print("\n--- where do the extra targets come from (y80)?")
    a, c = res["binary_masses"]["y80"], res["mass_ms"]["y80"]
    idx = a.index.union(c.index); a, c = a.reindex(idx).fillna(False), c.reindex(idx).fillna(False)
    s = sol.drop_duplicates("source_id").set_index("source_id")
    only_ms, only_bm = c & ~a, a & ~c
    print("only mass_ms:", int(only_ms.sum()), "| of these without m1 in binary_masses:", int(s.loc[only_ms[only_ms].index].m1_bm.isna().sum()),
          "| with m1 in binary_masses (mass changes across the limit):", int(s.loc[only_ms[only_ms].index].m1_bm.notna().sum()))
    print("only binary_masses:", int(only_bm.sum()), "| median m1_ms/m1_bm:", round((s.loc[only_bm[only_bm].index].m1_ms / s.loc[only_bm[only_bm].index].m1_bm).median(), 3))
    print("solution types of the extra targets:", s.loc[only_ms[only_ms].index].nss_solution_type.value_counts().to_dict())
    print("median ms_offset: extra targets", round(s.loc[only_ms[only_ms].index].ms_offset.median(), 2), "| targets in both", round(s.loc[(a & c)[a & c].index].ms_offset.median(), 2))


if __name__ == "__main__":
    run()
