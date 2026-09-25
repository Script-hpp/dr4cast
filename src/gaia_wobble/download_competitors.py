"""Competitor candidate lists as Parquet with int64 Gaia DR3 ids, plus SHA-256 checksums (docs/competitors.json)."""
import hashlib
import json
from datetime import date

import pyarrow.parquet as pq
import pyvo

from .download import to_arrow
from .paths import RAW, REPO

VIZIER = "http://tapvizier.cds.unistra.fr/TAPVizieR/tap"
CATALOGS = {
    "exodnn": ('"J/A+A/704/A150/exodnnv1"', "Abreu et al. (2025), ExoDNN, A&A 704, A150; 7414 DR3 candidates within 100 pc, score PredProb1"),
    "kiefer": ('"J/A+A/702/A77/tableb1"', "Kiefer et al. (2025), A&A 702, A77; 9698 candidates, G < 16, companion mass min. Mplmin, pRUWE"),
}


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download() -> dict:
    out_dir = RAW / "competitors"
    out_dir.mkdir(parents=True, exist_ok=True)
    svc = pyvo.dal.TAPService(VIZIER)
    info = {}
    for name, (table, desc) in CATALOGS.items():
        t = svc.run_async(f"SELECT * FROM {table}", maxrec=100000, timeout=600).to_table()
        t.rename_column("GaiaDR3", "source_id")
        tab = to_arrow(t)
        path = out_dir / f"{name}.parquet"
        pq.write_table(tab, path)
        info[name] = {"vizier_table": table.strip('"'), "description": desc, "rows": tab.num_rows,
                      "distinct_source_id": len(set(tab["source_id"].to_pylist())), "sha256": sha256(path),
                      "retrieved": date.today().isoformat()}
    (REPO / "docs" / "competitors.json").write_text(json.dumps(info, indent=2, sort_keys=True) + "\n")
    return info


if __name__ == "__main__":
    print(json.dumps(download(), indent=2))
