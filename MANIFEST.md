# Manifest – Gaia Wobble Bet

**Status:** Entwurf (lebendes Dokument)
**Version:** 0.7
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
| Hauptziel | Stern hat in DR4 eine Bahnlösung (`nss_two_body_orbit` oder `nss_multiple_orbits`) mit Begleitermasse unter 13 Jupitermassen; Masse nach der eigenen Schätzung (siehe „Massenschätzung und Ziele“), `nss_masses` zusätzlich als Vergleich |
| Nebenziel | Begleitermasse unter 80 Jupitermassen (inkl. Brauner Zwerge), gleiche Schätzung |
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

Die Modelle werden mit LightGBM trainiert. Die Reihenfolge ihrer Rollen steht vor dem ersten Training fest und hängt nicht vom Backtest-Ergebnis ab (Begründung im Änderungsprotokoll 0.7).

| Modell | Rolle | Training | Anwendung |
|---|---|---|---|
| **A – Transfer** | **Hauptmodell, offizielle Wette** | DR2-Features → Ziel „DR3-`Orbital`-Lösung mit geschätzter Masse unter 80 M_Jup“ | dasselbe Modell auf DR3-Features → DR4-Ziel |
| B – NASA-Labels | Vergleich | DR2-Features (Backtest) bzw. DR3-Features (Wette), bekannte Planetensterne = 1, Rest = 0, Klassengewichte, starke Regularisierung | wie A |
| B' – NASA-Labels, gefiltert | Vergleich | wie B, nur Planeten mit erwarteter messbarer Wackel-Amplitude | wie A |
| A2 – PU-Learning | nachrangig, nur bei stabilem A | wie A mit PU-Bagging und Umgewichtung nach Entfernung und Helligkeit | wie A |

Regeln:
- **Richtung des Transfers:** Modell A sieht im Training nur DR2-Features. Mit DR3-Features wäre das Ziel trivial (die Zielsterne haben dort schon die Bahnlösung, Median `ruwe_z` = 5,7).
- **Der NSS-Lösungstyp ist im Modell A kein Feature.** DR2 hat keine Bahnlösungen; ein Feature, das im Training immer fehlt, wäre bei der Anwendung wertlos. Er bleibt ein Feature nur dort, wo er in Training und Anwendung vorhanden ist (nicht in A). Die Doppelstern-Kontrolle in den Top 100 nutzt ihn nachträglich.
- **Verschiebung zwischen den Releases** (Messdauer DR2 22, DR3 34, DR4 66 Monate): RUWE wird je Release kalibriert (`ruwe_z`), das Modell benutzt die kalibrierten Größen; die Verschiebung bleibt als Grenze im Log dokumentiert.
- **Berichtet werden immer alle Modelle**, unabhängig davon, welches im Backtest am besten ist. Die Wahl des Hauptmodells wird nicht nachträglich geändert.
- Kontrollsterne Gaia-4 b und Gaia-5 b sind nie im Training.

**Features** (für DR2 und DR3 gleich berechnet): RUWE und seine Abweichung vom Erwartungswert je Helligkeit und Farbe (`ruwe_excess`, `ruwe_z`, siehe `calibration.py`), `astrometric_excess_noise`, Bildqualitätswerte (`ipd_*`, nur DR3), Helligkeit, Farbe, Entfernung, Anzahl Beobachtungen, HGCA-Beschleunigung (fehlend bleibt leer; DR2-Edition im Backtest, EDR3-Edition in der Wette). Merkmale, die es nur in einem der beiden Releases gibt, gehen nicht in Modell A ein.

**Erklärbarkeit:** SHAP; dominieren Helligkeit und Entfernung statt der Wackel-Features, lernt das Modell den Bias. Erwartung für Modell B: Wegen `ruwe_z` der Planetensterne von −0,03 lernt es vor allem den Survey-Bias; das ist als Beleg vorgesehen.

## Validierung

1. Backtest DR2→DR3.
2. Planetensysteme liegen komplett in Training oder Test.
3. Bekannte Fälle (z. B. Gaia-4 b) müssen weit oben landen.
4. Anteil bekannter Doppelsterne in den Top 100; das Modell muss die RUWE-Sortierung schlagen.
5. Optional: künstliche Signale mit den DR4-Vorabzeitreihen.

## Massenschätzung und Ziele

`gaiadr3.binary_masses` enthält keinen einzigen Begleiter unter 32 M_Jup (Experiment-Log 2026-09-25). Die Tabelle ist deshalb das falsche Werkzeug für das Ziel. Wir schätzen die Begleitermasse selbst aus den Bahnparametern (`src/gaia_wobble/masses.py`):

- Photozentrum-Bahn aus den Thiele-Innes-Elementen (A, B, F, G) und Parallaxe, Periode aus `nss_two_body_orbit`.
- Annahme „dunkler Begleiter“ (Licht nur vom Hauptstern), Kepler: `m2^3 / (m1 + m2)^2 = a1^3 / P^2`. Die Thiele-Innes-Elemente enthalten die Neigung, das Ergebnis ist eine echte Masse, keine Mindestmasse.
- Hauptsternmasse `m1` aus `binary_masses` (Gaia-eigene Schätzung). Lösungen ohne `m1` bekommen keine Schätzung und zählen nicht.
- Validierung: Für 6.948 Lösungen mit Gaia-eigenem `m2` liegt das Verhältnis Schätzung/Gaia bei median 1,000 (Quartile 1,000/1,000). Die Formel entspricht der von Gaia.
- Zurückgezogene Lösungen sind ausgeschlossen (Gaia DR3 „known issues“): Gaia DR3 4698424845771339520 (WD 0141-675), 5765846127180770432 (HIP 64690), 522135261462534528 (54 Cas), 1712614124767394816 (HIP 66074).

Ergebnis in DR3, Typ `Orbital`, mit `m1` (110.693 Lösungen): 1.503 unter 80 M_Jup, 17 unter 13 M_Jup.

| Ziel | Backtest DR2→DR3 | Wette DR3→DR4 |
|---|---|---|
| Hauptziel | `Orbital`-Lösung mit geschätzter Masse unter **80 M_Jup** (substellar) | `nss_two_body_orbit` oder `nss_multiple_orbits`, geschätzte Masse unter **13 M_Jup** (gleiche Formel) |
| Nebenziel | unter 13 M_Jup, nur als Tendenz (17 Treffer) | unter 80 M_Jup; zusätzlich ausgewertet mit `nss_masses`, falls vorhanden |
| Getrennt ausgewertet | `OrbitalTargetedSearch(Validated)` | dito |

Begründung für die Trennung: Gaia hat `OrbitalTargetedSearch` gezielt für Sterne gerechnet, die schon aus anderen Katalogen als Planetenkandidaten bekannt waren. Unsere Labels stammen aus ähnlichen Quellen, das Modell würde dort bekannte Sterne wiedererkennen.

Vergleichbarkeit: Backtest und Wette benutzen dieselbe Massenformel und hängen nicht davon ab, welche Massen ESA in `nss_masses` aufnimmt.

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
| 0.6 | 2026-09-25 | Massenschätzung aus Bahnparametern statt `binary_masses`; Backtest-Hauptziel unter 80 M_Jup, Nebenziel unter 13 M_Jup; DR4-Hauptziel auf dieselbe Schätzung umgestellt; zurückgezogene DR3-Lösungen ausgeschlossen | `binary_masses` hat keinen Begleiter unter 32 M_Jup, Backtest-Ziel hätte 0 Treffer; Vergleichbarkeit zwischen Backtest und Wette |
| 0.7 | 2026-09-25 | Hauptmodell A = Transfer (DR2-Features → DR3-Ziel, angewendet auf DR3-Features → DR4); NASA-Label-Modelle als Vergleich (B, B'); NSS-Lösungstyp in A kein Feature | Bekannte Planetensterne haben `ruwe_z` −0,03 (nicht von der Population unterscheidbar), das Label enthält kein Wackel-Signal; Entscheidung vor dem ersten Training und unabhängig vom Backtest-Ergebnis |
