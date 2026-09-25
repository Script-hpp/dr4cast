# Manifest – Gaia Wobble Bet

**Status:** Entwurf (lebendes Dokument)
**Version:** 0.5
**Eingefroren am:** – (noch nicht)

## Wie dieses Dokument funktioniert

Das Manifest darf jederzeit angepasst werden, solange wir lernen. Die Glaubwürdigkeit der Wette kommt nicht daher, dass nie etwas geändert wurde, sondern daher, dass jede Änderung nachvollziehbar ist:

1. Jede Änderung ist ein Git-Commit. Die Änderungen stehen unten im Änderungsprotokoll, mit Datum und Begründung.
2. Es gilt die Regel: **Nichts wird nach Blick auf DR4-Ergebnisse geändert.** Bis DR4 erscheint, sind Änderungen erlaubt. Danach nur noch als klar gekennzeichnete Nachträge.
3. Beim Einfrieren der Wette (Version 1 bzw. 2) wird ein Git-Tag gesetzt. Der SHA-256-Hash dieser Datei und der Vorhersageliste kommt in die Zenodo-Veröffentlichung.
4. Änderungen am Zielkriterium nach dem Einfrieren gelten nicht mehr für die offizielle Wette. Sie erscheinen als zusätzliche Auswertung.

## Festlegungen

| Regel | Festlegung |
|---|---|
| Hauptziel | Stern hat in DR4 eine Bahnlösung (`nss_two_body_orbit` oder `nss_multiple_orbits`) mit Begleitermasse unter 13 Jupitermassen laut `nss_masses` |
| Nebenziel | Begleitermasse unter 80 Jupitermassen (inkl. Brauner Zwerge) |
| Offizielle ESA-Liste | Falls veröffentlicht: zusätzliche Auswertung, ersetzt nicht das Hauptziel |
| Verknüpfung DR3→DR4 | Nur über die Tabelle `dr3_neighbourhood`, nie über gleiche `source_id` |
| Metriken | P@10, P@30, P@100, Recall@100, absolute Treffer; zusätzlich nach Helligkeitsklassen. Jede Metrik wird zweifach berichtet: *alle Treffer* und *nur neue Treffer* (Sterne, die nicht in den Trainingslabels waren). **Hauptmetrik ist „nur neue Treffer“**, weil bekannte Planetensterne leicht wiederzufinden sind |
| Vergleich | RUWE-Sortierung, ExoDNN, Sahlmann & Gómez (P@20) |
| Offizielle Wette | Version 2, falls vor dem Release veröffentlicht und stabil, sonst Version 1 |

Hinweis: Laut ESA gibt es in DR4 keine eigene Exoplaneten-Tabelle; Begleiter erscheinen in den Non-Single-Star-Tabellen (ESA, Stand 14.09.2026).

## Daten

Rohdaten liegen unter `data/raw/` (Parquet, `int64`-IDs). Größen in Klammern sind gemessen (Stand 2026-09-25, Hauptkatalog vollständig, 192/192 Chunks).

| Datensatz | Zweck | Größe |
|---|---|---|
| DR3-Hauptkatalog, `parallax >= 5` mas (ca. 200 pc), 29 Spalten | Features | 0,68 GB (5.244.458 Sterne, ungefiltert) |
| DR3-NSS-Tabellen (two_body_orbit, acceleration_astro, non_linear_spectro, vim_fl) | Lösungstyp, Bahnlösungen | 0,13 GB |
| `binary_masses` (DR3) | Begleitermassen für das Backtest-Ziel | klein |
| NASA Exoplanet Archive (`pscomppars`) | Labels | < 1 MB |
| DR2 (nahe Sterne) + `gaiadr2.ruwe` + `dr2_neighbourhood` | Backtest | ca. 1 GB (geschätzt) |
| HGCA | Beschleunigung, ca. 100k helle Sterne | < 1 GB |
| Große Himmelsstichprobe | RUWE-Kalibrierung nach Helligkeit und Farbe | fest eingeplant (Größe klein genug, siehe Änderungsprotokoll) |

Nur nahe Sterne, absichtlich: Das Signal eines Jupiters geht bei großer Entfernung im Rauschen unter.

### Qualitätsfilter (vorläufig)

Rohdaten bleiben vollständig erhalten; gefiltert wird erst beim Aufbereiten. Grund: Im ungefilterten Datensatz haben 28 % der Sterne `parallax_over_error < 5` und weitere 25 % zwischen 5 und 10. Sie sind lichtschwach, ihre Parallaxe ist teils nur durch Messfehler groß, und viele haben `RUWE > 1,4` (899.000 mit `parallax_over_error < 10`). Sie sähen wie Wackel-Kandidaten aus, sind aber nur schlecht gemessen.

- Vorläufig: `parallax_over_error > 10`. Endgültig festgelegt wird der Schwellwert vor dem Einfrieren, begründet im Experiment-Log (`docs/experiment_log.md`).
- Der Filter hängt mit dem Signal zusammen: Gaia rechnet den Excess Noise in `parallax_error` ein, ein wackelnder Stern bekommt also ein kleineres `parallax_over_error`. Prüfung vor der Festlegung: Anteil der Labels und der `Orbital`-Lösungen, die die Schwellen 5, 10 und „kein Filter“ überleben, im Vergleich zu allen Sternen (Eintrag im Experiment-Log).
- Nachteil, der mitentschieden werden muss: Der Filter bevorzugt helle Sterne und entfernt lichtschwache M-Zwerge in 100–200 pc. Das wirkt wie zusätzlicher Survey-Bias und wird nach Helligkeitsklassen ausgewertet.

## Modell

- **Version 1:** LightGBM, bekannte Planetensterne = 1, Rest = 0, Klassengewichte, starke Regularisierung.
- **Version 2:** PU-Learning (Bagging), Umgewichtung nach Entfernung und Helligkeit, kein „ist in RV-Survey“-Feature.
- **Features:** RUWE, `astrometric_excess_noise`, `ipd_*`, RUWE-Abweichung vom Erwartungswert, NSS-Lösungstyp (Kategorie, kein Filter), HGCA-Beschleunigung (fehlend bleibt leer), Helligkeit, Farbe, Entfernung, Anzahl Beobachtungen.
- **Erklärbarkeit:** SHAP; dominieren Helligkeit/Entfernung, lernt das Modell den Bias.

## Validierung

1. Backtest DR2→DR3.
2. Planetensysteme liegen komplett in Training oder Test.
3. Bekannte Fälle (z. B. Gaia-4 b) müssen weit oben landen.
4. Anteil bekannter Doppelsterne in den Top 100; das Modell muss die RUWE-Sortierung schlagen.
5. Optional: künstliche Signale mit den DR4-Vorabzeitreihen.

## Backtest DR2→DR3: Zieldefinition

DR3 hat keine Tabelle `nss_masses` (kommt erst mit DR4). Die Rolle übernimmt `gaiadr3.binary_masses` (Spalte `m2`, in Sonnenmassen; 13 M_Jup = 0,0124 M_sun, 80 M_Jup = 0,0764 M_sun).

| Ziel | Definition |
|---|---|
| Hauptziel | DR3-Lösung vom Typ `Orbital`, Begleitermasse `m2` aus `binary_masses` unter 13 M_Jup. Wo `binary_masses` fehlt: eigene Schätzung nach der Näherung „dunkler Begleiter“ (Licht nur vom Hauptstern), gekennzeichnet als Schätzung |
| Nebenziel | Begleitermasse unter 80 M_Jup |
| Getrennt ausgewertet | `OrbitalTargetedSearch` und `OrbitalTargetedSearchValidated` |

Begründung für die Trennung: Gaia hat `OrbitalTargetedSearch` gezielt für Sterne gerechnet, die schon aus anderen Katalogen als Planetenkandidaten bekannt waren. Unsere Labels stammen aus ähnlichen Quellen, das Modell würde dort bekannte Sterne wiedererkennen und der Backtest wäre zu optimistisch.

Grenzen des Backtests (nicht überinterpretieren):
- **Kein Leakage:** Die Backtest-Stichprobe wird komplett mit DR2-Werten ausgewählt und gefiltert: DR2-Parallaxe, DR2-Qualitätsfilter, RUWE aus `gaiadr2.ruwe`. Nahe Sterne dürfen nie über DR3-Parallaxen bestimmt werden, sonst fließt Wissen aus der Zukunft in den Test.
- DR2 hatte keine Bahnlösungen. Dem Modell fehlt im Backtest der NSS-Lösungstyp als Feature, den es bei der echten Wette hat. Der Backtest ist dadurch eher pessimistisch.
- RUWE steht in DR2 nicht im Hauptkatalog, sondern in `gaiadr2.ruwe`. Die Tabelle wird für die Baseline benötigt.
- Verknüpfung DR2→DR3 nur über `gaiadr3.dr2_neighbourhood`.

### Regeln gegen Leakage im Backtest

- **Stand DR2:** Jedes Feature im Backtest stammt aus Quellen, die zum DR2-Release (April 2018) verfügbar waren. Das gilt auch für HGCA: Backtest mit der DR2-Version (Brandt 2018), echte Wette mit der EDR3-Version (Brandt 2021). Der RUWE-Erwartungswert wird je Release separat kalibriert.
- **Labels:** Für den Backtest nur Planeten mit `disc_year <= 2017` (konservativ; das Jahr 2018 lässt sich nicht sauber vor/nach dem Release trennen).
- **Kontrollsterne:** Gaia-4 b und Gaia-5 b (2025 entdeckt) sind nie im Training. Sie sind eine gezielte Stichprobe für die Kontrolle „bekannte Fälle müssen weit oben landen“, und nur für die Vorhersage von DR4, nicht für den Backtest.

## Änderungsprotokoll

| Version | Datum | Änderung | Grund |
|---|---|---|---|
| 0.1 | 2026-09-25 | Erster Entwurf aus den Projektanforderungen | – |
| 0.2 | 2026-09-25 | Backtest-Zieldefinition: nur `Orbital` im Hauptziel, Masse aus `binary_masses`, `OrbitalTargetedSearch` getrennt; Grenzen des Backtests dokumentiert | DR3 hat kein `nss_masses`; gezielte Suchen würden den Backtest verzerren |
| 0.3 | 2026-09-25 | Datenbasis mit gemessenen Größen; vorläufiger Qualitätsfilter `parallax_over_error > 10`; RUWE-Kalibrierung fest eingeplant | Ungefilterter Katalog enthält viele schlecht gemessene Sterne mit hohem RUWE; Daten sind klein genug für die Kalibrierung |
| 0.4 | 2026-09-25 | Regel „kein Leakage“ für die DR2-Stichprobe; Filter-Prüfung an Labels und `Orbital`-Lösungen vorgeschrieben | Filter kann gerade die wackelnden Sterne entfernen |
| 0.5 | 2026-09-25 | Hauptmetrik „nur neue Treffer“; Leakage-Regeln (Stand DR2, `disc_year <= 2017`, Kontrollsterne) | Bekannte Planetensterne und Zukunftsdaten machen Backtest und Metrik zu leicht |
