# Gaia Wobble Bet – frozen predictions (version 1)

Before Gaia Data Release 4 (planned for 2 December 2026) this package publishes, with a timestamp, which stars of Gaia DR3
a machine-learning model expects to receive an orbit solution with a substellar companion in DR4. After the release the lists
are evaluated against DR4 and against simple baselines and published methods (RUWE ordering, ExoDNN, Kiefer et al. 2025,
Sahlmann & Gómez 2025).

## Contents

| File | What it is |
|---|---|
| `list1_substellar.csv` | List 1: 1,000 stars ranked for a companion below 80 Jupiter masses (the bet is `rank_new <= 100`) |
| `list2_planets.csv` | List 2 ("planet list"): 1,000 stars ranked for a companion below 13 Jupiter masses that is dark (`ms_offset < 0.2`) |
| `*.csv.sha256`, `lists_manifest.json` | SHA-256 of each list and of the models, feature tables and neighbour table used |
| `MANIFEST.md` | The pre-registered rules: targets, metrics, exclusions, comparison methods, evaluation |
| `docs/experiment_log.md` | Everything that was learned before freezing, including the backtest DR2 to DR3 |
| `src/gaia_wobble/evaluate_bet.py` | The evaluation script that is applied to DR4 (frozen together with the lists) |
| `docs/competitors.json` | The competitor lists with checksums |

## How to read a list

Columns: `rank_new` (rank used for the bet; it skips stars with a known DR3 orbit below 80 Jupiter masses, known planet hosts and stars
with a Gaia neighbour within 2 arcsec), `source_id` (Gaia DR3), `score`, `p_a`, `p_m2_lt13`, `rank_raw`, `ms_offset`, and flags for
known cases. The score is an ordering score, not a calibrated probability.

## What the backtest says (DR2 to DR3, see the experiment log)

With DR2 data only, Model A places about 15 % real DR3 substellar-orbit stars in its top 100 and about 9 % in the top 1,000
(RUWE ordering: none in either). A large part of this is Gaia's own selection of stars for orbit solutions; a companion below 13
Jupiter masses is much rarer (17 targets; 4 with the dark-companion condition), so list 2 is a bet into the unknown.

## Verification

`sha256sum -c list1_substellar.csv.sha256 list2_planets.csv.sha256` must succeed. The code state is recorded in the header of every list.

## Licence (proposal, to be confirmed before publishing)

Lists and documentation: CC BY 4.0. Code: MIT.
