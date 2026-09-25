# Manifest – Gaia Wobble Bet

**Status:** Entwurf (lebendes Dokument)
**Version:** 0.11
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
| Hauptziel (zwei gleichrangige Listen) | Stern hat in DR4 eine Bahnlösung (`nss_two_body_orbit` oder `nss_multiple_orbits`) mit Begleitermasse nach der eigenen Schätzung (siehe „Massenschätzung und Ziele“). **Liste 1:** unter 80 Jupitermassen. **Liste 2 („Planetenliste“):** unter 13 Jupitermassen. `nss_masses` zusätzlich als Vergleich |
| Nebenziel | Auswertung getrennt nach Helligkeitsklassen und nach `OrbitalTargetedSearch`; ESA-Massen aus `nss_masses` |
| Offizielle ESA-Liste | Falls veröffentlicht: zusätzliche Auswertung, ersetzt nicht das Hauptziel |
| Verknüpfung DR3→DR4 | Nur über die Tabelle `dr3_neighbourhood`, nie über gleiche `source_id` |
| Metriken | P@10, P@30, P@100, Recall@100, absolute Treffer; zusätzlich nach Helligkeitsklassen. Zusätzlich (Ergänzung 0.11, festgelegt nach Blick auf die Baseline, aber vor jedem Modell): ROC-AUC, Average Precision, Recall in den obersten 1 %, 5 % und 10 % der Population und der beste Rang eines Treffers. Jede Metrik wird zweifach berichtet: *alle Treffer* und *nur neue Treffer* (Sterne, die nicht in den Trainingslabels waren). **Hauptmetrik ist „nur neue Treffer“**, weil bekannte Planetensterne leicht wiederzufinden sind |
| Vergleich | RUWE-Sortierung, ExoDNN, Sahlmann & Gómez (P@20) |
| Offizielle Wette | Beide Listen werden vor dem Release eingefroren und immer beide berichtet. Keine wird nachträglich zur Hauptliste erklärt |

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

### Die zwei Listen der Wette

- **Liste 1 (unter 80 M_Jup):** Top 100 nach der Wahrscheinlichkeit `P(substellar)` aus Modell A. Im Backtest validiert (1.306 erreichbare Treffer).
- **Liste 2 (unter 13 M_Jup, Planetenliste):** Top 100 nach `P(substellar) × P(m2 < 13 M_Jup)`. Die zweite Wahrscheinlichkeit kommt aus einem zusätzlichen Feature: Aus `ruwe_excess` wird die Wackel-Amplitude abgeleitet, daraus mit Sternmasse und Parallaxe der Bereich möglicher Begleitermassen (Prinzip wie Kiefer et al. 2025).
- Beide Listen: Hauptmetrik „nur neue Treffer“ (siehe oben), beide werden vor dem Release eingefroren, beide werden berichtet.
- Der Kandidatenkatalog von Kiefer et al. (2025, A&A 702, A77: 9.698 Kandidaten) kommt als zusätzlicher Vergleich für Liste 2 ins Leaderboard, sofern er maschinenlesbar verfügbar ist. Er hat andere Grenzen als wir und wird so vermerkt: Quellen mit G < 16, Begleiter unter 13,5 M_Jup, Bahnabstände 1–3 AE.

Vor dem Einfrieren zu klären (Teil des Manifests):
- Die Ableitung Amplitude → Massenbereich ist neu. Sie wird gegen die Methode GaiaPMEX von Kiefer et al. (2025) geprüft (Masse und Bahnabstand aus RUWE, optional mit Hipparcos-Gaia-Bewegungsanomalie) und an den DR3-Bahnlösungen validiert, wo die Amplitude bekannt ist. Die Mindestgüte wird vor der ersten Auswertung im Log festgelegt. Die Validierung an den Bahnlösungen ist geschönt: Diese Sterne wackeln stark und haben Perioden im günstigen Bereich. Dass das Feature dort funktioniert, sagt nicht, dass es bei schwachen Signalen genauso gut ist.
- **Rückfallregel (unabhängig vom Amplituden-Feature):** Erfüllt das Feature die Mindestgüte nicht, ist Liste 2 die Top 100 nach `P(substellar)` unter nahen, leichten Sternen: Sternmasse unter 0,6 Sonnenmassen und Entfernung unter 100 pc. Das benutzt nur die Physik (leichte, nahe Sterne zeigen den Planeten-Wackel am stärksten), keine Größe aus der Amplitudenrechnung.
- **Sternmasse für alle Sterne** (nicht nur für Sterne mit NSS-Lösung): In der Wette FLAME-Massen aus `gaiadr3.astrophysical_parameters`, bei Lücken eine Masse-Helligkeits-Beziehung (Herkunft markiert). Im Backtest nur die Masse-Helligkeits-Beziehung mit DR2-Photometrie, weil FLAME ein DR3-Produkt ist und sonst Wissen aus der Zukunft einfließt.
- **Grenze:** Liste 2 ist im Backtest mit nur 17 Treffern kaum validierbar. Sie ist bewusst eine Wette ins Unbekannte.

### „Neue Treffer“ in der Wette

In DR3 haben schon über tausend Sterne eine Bahnlösung mit substellarem Begleiter (1.306 in unserer Stichprobe), und sie haben einen hohen `ruwe_z` (Median 5,7). Modell A sortiert sie weit oben ein, und sie bekommen in DR4 fast sicher wieder eine Bahn. Im Backtest gab es das nicht, weil DR2 keine Bahnlösungen hatte. Ein Treffer bei diesen Sternen ist keine Vorhersage.

- **Hauptmetrik der Wette:** Nur Sterne ohne DR3-Bahnlösung mit geschätzter Masse unter 80 M_Jup (Typ `Orbital*`, ohne zurückgezogene Lösungen) und ohne bekannten Planeten (NASA-Labels) zählen als „neue Treffer“.
- **Zusätzlich berichtet:** Die Auswertung der ganzen Top-Liste, inklusive dieser Sterne, klar gekennzeichnet.
- **Eingefrorene Liste:** Die bekannten Sterne bleiben in der Liste und werden nur markiert (`known_dr3_orbit`, `known_planet`), damit die Liste nachvollziehbar ist. Die Top-100 der Hauptmetrik werden nach dem Ausschluss dieser Sterne gebildet, die 100 Plätze also mit Sternen ohne bekanntes Ergebnis gefüllt.

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
| 0.8 | 2026-09-25 | Wette: „neue Treffer“ schließt Sterne mit DR3-Bahnlösung unter 80 M_Jup und bekannte Planetensterne aus; Markierung statt Streichung in der eingefrorenen Liste | In DR3 gibt es schon über tausend solcher Sterne, sie wären Treffer ohne Vorhersage |
| 0.9 | 2026-09-25 | Wette mit zwei gleichrangigen Listen (unter 80 M_Jup und unter 13 M_Jup); Liste 2 mit Massenwahrscheinlichkeit aus `ruwe_excess`; Rückfallregel bei ungenügender Validierung | Modell A wird auf unter 80 M_Jup trainiert (1.306 Treffer); das Planetenziel unter 13 M_Jup (17 Treffer) bleibt als eigene Liste erhalten |
| 0.10 | 2026-09-25 | Rückfallregel für Liste 2 unabhängig vom Amplituden-Feature (Sternmasse < 0,6 M_sun, unter 100 pc); Herkunft der Sternmassen (FLAME / Masse-Helligkeits-Beziehung, im Backtest nur DR2-Photometrie); GaiaPMEX als Vergleich; Grenze der Validierung an Bahnlösungen | Die alte Rückfallregel war zirkulär (dieselbe Rechnung wie das Feature) |
| 0.11 | 2026-09-25 | Zusatzmetriken AUC, AP, Recall@1/5/10 % neben P@k und Recall@100 | Die RUWE-Baseline hat im Backtest P@100 = 0; ohne Kurvenmetriken lassen sich die Modelle nicht vergleichen. Festgelegt nach Blick auf die Baseline, vor jedem Modell |
