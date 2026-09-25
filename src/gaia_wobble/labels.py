"""Training labels from the NASA Exoplanet Archive, cut by release date to avoid leakage."""
import duckdb

from .paths import PROCESSED, RAW

DR2_CUTOFF_YEAR = 2017  # DR2 appeared in April 2018; the discovery year alone cannot separate 2018 (see MANIFEST)
CONTROL_PLANETS = ["Gaia-4 b", "Gaia-5 b"]  # never in training; kept for the DR4 known-case check

_SRC = f"'{RAW}/labels/nasa_pscomppars.parquet'"


def build_labels() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    names = ", ".join(f"'{n}'" for n in CONTROL_PLANETS)
    # Backtest (DR2 stars): planets known before DR2, linked by their DR2 id
    duckdb.sql(f"""COPY (SELECT pl_name, hostname, dr2_source_id AS source_id, pl_bmassj, pl_orbper,
        discoverymethod, disc_year FROM {_SRC}
        WHERE dr2_source_id IS NOT NULL AND disc_year <= {DR2_CUTOFF_YEAR}
          AND pl_name NOT IN ({names}))
        TO '{PROCESSED}/labels_backtest_dr2.parquet' (FORMAT parquet)""")
    # Bet (DR3 stars): all known planets except the control cases
    duckdb.sql(f"""COPY (SELECT pl_name, hostname, dr3_source_id AS source_id, pl_bmassj, pl_orbper,
        discoverymethod, disc_year FROM {_SRC}
        WHERE dr3_source_id IS NOT NULL AND pl_name NOT IN ({names}))
        TO '{PROCESSED}/labels_bet_dr3.parquet' (FORMAT parquet)""")
    duckdb.sql(f"""COPY (SELECT pl_name, hostname, dr3_source_id AS source_id, pl_bmassj
        FROM {_SRC} WHERE pl_name IN ({names}))
        TO '{PROCESSED}/labels_control_dr3.parquet' (FORMAT parquet)""")


if __name__ == "__main__":
    build_labels()
    for f in ["labels_backtest_dr2", "labels_bet_dr3", "labels_control_dr3"]:
        n, u = duckdb.sql(f"SELECT count(*), count(DISTINCT source_id) FROM '{PROCESSED}/{f}.parquet'").fetchone()
        print(f, n, "rows,", u, "distinct hosts")
    print("backtest labels in DR2 nearby sample:", duckdb.sql(
        f"SELECT count(DISTINCT l.source_id) FROM '{PROCESSED}/labels_backtest_dr2.parquet' l "
        f"JOIN '{RAW}/dr2_nearby/*.parquet' g USING (source_id)").fetchone()[0])
    print("bet labels in DR3 nearby sample:", duckdb.sql(
        f"SELECT count(DISTINCT l.source_id) FROM '{PROCESSED}/labels_bet_dr3.parquet' l "
        f"JOIN '{RAW}/dr3_nearby/*.parquet' g USING (source_id)").fetchone()[0])
