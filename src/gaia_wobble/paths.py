"""Central data paths: bulk data lives in <repo>/data (git-ignored)."""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("GAIA_DATA_DIR", REPO / "data"))
RAW = DATA_DIR / "raw"
INTERIM = DATA_DIR / "interim"
PROCESSED = DATA_DIR / "processed"
MODELS = DATA_DIR / "models"
PREDICTIONS = DATA_DIR / "predictions"
