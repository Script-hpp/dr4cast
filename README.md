# dr4cast

**Predicting, before the release, which stars get a substellar companion in Gaia DR4.**

Gaia DR4 is planned for **2 December 2026** (ESA). It rests on 66 months of data instead of the 34 months of DR3, and it will publish
new astrometric orbit solutions. dr4cast trains a model on older data, publishes a ranked list of DR3 stars with a timestamp
*before* the release, and then checks it openly against DR4 and against simple baselines and published methods.

![status](https://img.shields.io/badge/status-release%20candidate%20v1-orange)
![code](https://img.shields.io/badge/code-MIT-blue)
![lists](https://img.shields.io/badge/lists-CC%20BY%204.0-lightgrey)

> **Status:** frozen. The lists in [`release/v1/`](release/v1), [`MANIFEST.md`](MANIFEST.md) (version 0.19) and the evaluation script
> [`evaluate_bet.py`](src/gaia_wobble/evaluate_bet.py) are fixed by the GitHub release `v1.0` (2026-09-25); the Zenodo record and its DOI
> will be added here. Until DR4 only clarifications and the schema adaptations allowed by the manifest are made, see
> [`docs/clarifications_v1.md`](docs/clarifications_v1.md) (including the rule for the primary mass `m1`).

## The idea in one minute

A planet or brown dwarf makes its star wobble a little. Gaia measures that wobble. Stars that wobble too much for a single star show
up as high **RUWE** (a Gaia fit-quality number), but RUWE alone points mostly to stellar binaries. dr4cast asks a sharper question:

> Which DR3 stars will have an orbit solution with a companion below 80 Jupiter masses in DR4 (list 1),
> and, among the dark ones, below 13 Jupiter masses (list 2, the "planet list")?

The link between releases is made **only through the official neighbourhood table**, never through equal `source_id`s.

## What is published

| | |
|---|---|
| [`MANIFEST.md`](MANIFEST.md) | The pre-registered rules: targets, metrics, exclusions, comparison methods, evaluation. Versioned, every change is logged with its reason. |
| [`release/v1/`](release/v1) | The two lists (1,000 stars each; the bet is the first 100), SHA-256 checksums, and the inputs' checksums. |
| [`docs/clarifications_v1.md`](docs/clarifications_v1.md) | Clarifications and one addendum (primary mass `m1` for DR4), published after the freeze. They change no list, no manifest text and no evaluation code. |
| [`src/gaia_wobble/evaluate_bet.py`](src/gaia_wobble/evaluate_bet.py) | The evaluation script that will be applied to DR4. It is frozen together with the lists. |
| [`docs/experiment_log.md`](docs/experiment_log.md) | Everything learned before freezing, including the negative results. |

Verify the lists: `cd release/v1 && sha256sum -c list1_substellar.csv.sha256 list2_planets.csv.sha256`

## How it works

```
Gaia DR2 + DR3 (nearby stars, ~200 pc)        NSS orbit solutions, binary masses
        |                                               |
   RUWE calibration per release                 companion mass from the orbit
   (expected RUWE for brightness and colour)    (dark-companion assumption)
        |                                               |
   physical features:  ruwe_z, wobble amplitude vs. the largest substellar wobble,
                       offset above the main sequence, ...
        |
   LightGBM trained on DR2 features -> target: DR3 orbit with mass < 80 M_Jup      (backtest DR2 -> DR3)
        |
   the same model applied to DR3 features -> ranked list for DR4                  (the bet DR3 -> DR4)
```

- **Model A** (the model of the bet) uses nine physical features and is trained on DR2 with a target from DR3. It uses no feature that
  changes with the observing time of a release (observation counts, parallax errors), so it can be moved from one release to the next.
- **List 2** additionally requires the star to sit near the main sequence (`ms_offset < 0.2` mag: a dark companion adds no light) and
  weights the score by an estimate of the share of possible companion masses below 13 Jupiter masses.
- Stars with a known DR3 orbit below 80 Jupiter masses, known planet hosts, and stars with a Gaia neighbour within 2 arcsec are
  marked and skipped in `rank_new`, so a "hit" is a prediction, not a repeat.

## The backtest (DR2 → DR3), honestly

The same recipe was run one release earlier: predict from DR2 alone which stars get a substellar orbit in DR3.
2.30 million stars, 1,304 targets (base rate 0.057 %). The full numbers and 95 % intervals (bootstrap over 192 sky cells) are in the log.

| Method | P@100 | P@1000 | ROC-AUC |
|---|---|---|---|
| **Model A** | **0.15** (0.09–0.23) | **0.093** (0.077–0.115) | 0.966 |
| RUWE ordering | 0 | 0 | 0.783 |
| RUWE calibrated for brightness and colour | 0 | 0 | 0.830 |
| Hand-built rule, no ML | 0 | 0 | – |
| Logistic regression, same features | 0 | 0 | 0.862 |

Please read the caveats before quoting these numbers:

- **The target is what Gaia's pipeline published**, not what is physically there. Many DR3 "substellar" solutions sit about
  0.4–0.5 mag above the main sequence, like unresolved binaries with an underestimated companion mass. Confirmed dark companions sit
  on the main sequence. The bet is about Gaia's release, and the same contamination will be in DR4.
- Part of the skill is Gaia's own selection (which stars get an orbit at all). Removing parallax- and brightness-based features costs
  almost nothing, because the selection lives in the noise statistics themselves; the model may transfer poorly to DR4 if Gaia's
  thresholds change (we cannot know that before the release).
- **List 2 has almost no backtest.** Only 17 DR3 targets are below 13 Jupiter masses, and only 4 of them are dark. It is a bet into
  the unknown, and it is labelled as such.
- DR3's own mass table (`binary_masses`) contains no companion below 32 Jupiter masses, so companion masses are estimated from the orbit
  (the estimate reproduces Gaia's own values where they exist, but that only shows we repeat Gaia's formula, not that the masses are exact).

## Reproduce

```bash
uv sync                                   # Python 3.11+, see pyproject.toml
python -m gaia_wobble.download            # DR3 nearby stars (Heidelberg TAP mirror)
python -m gaia_wobble.download_aux        # labels, NSS tables, DR2 sample, HGCA, DR2-DR3 links
python -m gaia_wobble.download_competitors
python -m gaia_wobble.targets             # DR3 orbit targets with estimated companion masses
python -m gaia_wobble.labels              # NASA Exoplanet Archive labels, cut by release date
python -m gaia_wobble.calibration         # expected RUWE per release
python -m gaia_wobble.features
python -m gaia_wobble.physics_features
python -m gaia_wobble.amplitude
python -m gaia_wobble.ablation physics    # trains the five region models of Model A
python -m gaia_wobble.make_lists my_lists # both lists in one run
python -m gaia_wobble.evaluate_bet        # backtest dry run of the evaluation script
uv run pytest
```

Data (about 4 GB) goes to `data/` (git-ignored); set `GAIA_DATA_DIR` to change that. The steps were run one by one during development;
a clean-room re-run of the whole chain in one go has not been done. Downloads take a few hours.

## Data and credits

**Gaia acknowledgement.** This work has made use of data from the European Space Agency (ESA) mission Gaia
(<https://www.cosmos.esa.int/gaia>), processed by the Gaia Data Processing and Analysis Consortium (DPAC,
<https://www.cosmos.esa.int/web/gaia/dpac/consortium>). Funding for the DPAC has been provided by national institutions, in particular
the institutions participating in the Gaia Multilateral Agreement.

Other data and methods:

- Heidelberg ARI Gaia archive mirror (queries), NASA Exoplanet Archive (planet labels)
- Hipparcos-Gaia Catalog of Accelerations (Brandt 2018 for the DR2 edition, Brandt 2021 for the EDR3 edition)
- Main-sequence table of E. Mamajek, version 2022.04.16 (Pecaut & Mamajek 2013, ApJS 208, 9)
- Kiefer et al., *Searching for substellar companion candidates with Gaia*: paper I (the GaiaPMEX method, arXiv 2409.16992), whose
  Eq. 8 we use for the wobble amplitude; paper II (the catalogue of 9,698 candidates, arXiv 2409.16993, A&A 702, A77, 2025), used as a comparison list
- Abreu et al. (2025), ExoDNN, A&A 704, A150 (comparison list)
- Sahlmann & Gómez (2025), MNRAS 537, 1130 (comparison list)

The comparison lists are not part of this repository: only the download script and the checksums (`docs/competitors.json`) are.

## Licence and citation

Code: MIT, lists and documentation: CC BY 4.0. Copyright (c) 2026 Onuralp Akca. See [`LICENSE`](LICENSE) and [`LICENSE-DATA.md`](LICENSE-DATA.md).

Citation: Onuralp Akca, *dr4cast: a pre-registered forecast of Gaia DR4 substellar companions*, 2026, Zenodo DOI to follow.
