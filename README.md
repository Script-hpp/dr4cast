# Gaia Wobble Bet

Pre-registered ML prediction of which Gaia DR3 stars get a planetary/substellar companion orbit solution in Gaia DR4.

- Code and bulk data live in this folder; `data/` is git-ignored.
- Layout: `data/raw` (downloads), `interim`, `processed` (Parquet), `models`, `predictions`.
- Plan: `docs/plan.md`. Regeln der Wette: `MANIFEST.md` (maßgebliche Version). Log: `docs/experiment_log.md`.
- Set `GAIA_DATA_DIR` (see `.env.example`) to move the data elsewhere.
