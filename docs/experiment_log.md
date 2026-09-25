# Experiment-Log

## 2026-09-25 – Qualität der Parallaxen im DR3-Hauptkatalog

Datensatz: DR3, `parallax >= 5`, 3.567.409 Sterne (146 von 192 Chunks).

| Gruppe | Sterne |
|---|---|
| `parallax_over_error < 5` | 1.012.722 (28 %) |
| 5 bis 10 | 906.148 (25 %) |
| >= 10 | 1.648.539 (46 %) |
| `parallax >= 10` (100 pc), alle | 411.767 |
| `parallax >= 10` und `parallax_over_error >= 10` | 277.695 |
| `phot_g_mean_mag > 19` | 2.031.233 |
| `RUWE > 1,4` | 1.195.887 (davon 899.261 mit `parallax_over_error < 10`) |

Beobachtung: Die 411.767 Sterne innerhalb von 100 pc liegen über den rund 330.000 des GCNS, der saubere Sterne enthält. Das bestätigt, dass ein reiner Parallaxen-Schnitt viele schlecht gemessene Sterne einschließt. Die meisten Sterne mit hohem RUWE haben auch eine schlechte Parallaxe.

Entscheidung (vorläufig): Rohdaten behalten, beim Aufbereiten `parallax_over_error > 10` setzen. Offen: Einfluss auf lichtschwache M-Zwerge, Auswertung nach Helligkeitsklassen.

## 2026-09-25 – DR3-Hauptkatalog vollständig, Filter-Prüfung

Download abgeschlossen: 192 von 192 Chunks, 5.244.458 Sterne, alle `source_id` eindeutig und `int64`, 676 MB. Sieben Chunks stichprobenartig gegen `SELECT COUNT(*)` beim Archiv geprüft (0, 16, 34, 64, 145, 162, 191): alle Zeilenzahlen gleich. Chunk 162 (Feld hoher Sterndichte) hat 149.114 Sterne.

Überleben der Schwellen (`parallax_over_error`):

| Gruppe | Sterne | >= 5 | >= 10 |
|---|---|---|---|
| alle | 5.244.458 | 68,5 % | 42,6 % (2.234.316) |
| bekannte Planetensterne (NASA, mit DR3-ID) | 1.629 | 100 % | 100 % |
| `Orbital`-Lösungen (DR3) | 10.375 | 100 % | 100 % |

Beobachtung: Kein Label-Stern und keine `Orbital`-Lösung fällt durch den Filter. Einschränkung: Beide Gruppen sind schon auf gute Messungen selektiert (helle Planetensterne, Bahnlösungen brauchen saubere Astrometrie). Der Test sagt nichts über schlecht gemessene wackelnde Sterne, die wir eigentlich finden wollen. Der Filter bleibt daher vorläufig; entschieden wird nach dem Backtest mit Auswertung nach Helligkeitsklassen.

Betriebsnotizen: Der TAP-Dienst des ESA-Archivs brach Async-Jobs ab; wir nutzen den Heidelberg-Spiegel. Einzelne Jobs hängen dort gelegentlich (Chunk 149), deshalb Timeout pro Chunk 180 s mit Wiederholung.

## 2026-09-25 – HGCA beide Versionen geladen

Quelle: Brandt, `physics.ucsb.edu/~tbrandt/HGCA_vDR2.fits` (2018, DR2-Bezugssystem) und `HGCA_vEDR3.fits` (2021). VizieR hat nur die 2021-Version (`J/ApJS/254/42`), deshalb Download direkt von der Autorenseite (Redirect http→https beachten, sonst kommt eine 382-Byte-HTML-Datei).

- `hgca_dr2.parquet`: 115.662 Zeilen, aber nur 115.658 verschiedene `source_id` (vier doppelte DR2-IDs). Beim Zusammenführen mit dem DR2-Katalog vorher deduplizieren.
- `hgca_edr3.parquet`: 115.346 Zeilen, IDs eindeutig; 50.254 davon liegen im DR3-Nahsternkatalog (unfiltert).
- `source_id` ist in der DR2-Edition eine DR2-ID, in der EDR3-Edition eine DR3-ID. Der Backtest verknüpft die DR2-Edition nur mit DR2-Sternen.

## 2026-09-25 – Backtest-Ziel: DR3 hat praktisch keine planetaren Begleiter in `binary_masses`

Zählung (`nss_two_body_orbit` verknüpft mit `binary_masses`, `m2` in Sonnenmassen, 1 M_Jup = 9,5479e-4 M_sun):

- `binary_masses`: 195.315 Zeilen, 195.239 verschiedene `source_id` (76 Sterne mit mehreren Zeilen).
- **Kein einziger Begleiter unter 13 M_Jup.** Die kleinste Masse ist 32,1 M_Jup. Das Hauptziel des Backtests hat damit 0 Treffer.
- Unter 80 M_Jup: 44 Zeilen (Kombinationen `Orbital+M1` 9, `Orbital+SB1+M1` 5, `AstroSpectroSB1+M1` 30), fast alle im Nahsternkatalog. Die Sterne mit `Orbital`-Lösung und `Orbital+M1` (nur astrometrisch, m2 aus der Bahn und m1 aus der Leuchtkraft) haben sehr rote, lichtschwache Primärsterne (m1 ca. 0,13 M_sun, G ca. 16–18): Es sind Braune-Zwerg-Begleiter von M-Zwergen.
- `m2` ist für `Orbital` nur bei 5.454 von 111.792 Zeilen vorhanden; `SB1+M1` hat nie `m2`.

Folgerung: Das im Manifest v0.2 festgelegte Backtest-Ziel ist mit den DR3-Daten nicht erreichbar. Das Modell kann im Backtest nicht auf planetare Begleiter geprüft werden. Entscheidung offen (siehe Manifest).

Nachtrag (gleicher Tag): Eigene Massenschätzung aus Thiele-Innes-Elementen, Parallaxe, Periode und `m1` (`masses.py`). Validierung an 6.948 Lösungen mit Gaia-eigenem `m2`: Verhältnis median 1,000, Quartile 1,000/1,000. Ergebnis für `Orbital` mit `m1` (nach Ausschluss von vier zurückgezogenen Lösungen): 1.503 unter 80 M_Jup, 17 unter 13 M_Jup; `OrbitalTargetedSearch` 18 bzw. 3, `OrbitalTargetedSearchValidated` 15 bzw. 5. Manifest 0.6.


## 2026-09-25 – Prüfung der Massenschätzung und des Backtest-Ziels

- **BD+75 510 = HIP 66074 = Gaia DR3 1712614124767394816** (SIMBAD). Die Ausschlussliste ist vollständig.
- **Vergleich mit Gaia:** Kiefer et al. (2025) nennen für die Gaia-Kollaboration (Gaia Collaboration 2023a) 1843 Kandidaten für Braune Zwerge und 72 für Exoplaneten (Quelle vom Projektpartner genannt, von mir nicht selbst nachgeprüft). Wir finden 1.503 (unter 80 M_Jup) und 17 (unter 13 M_Jup). Die Differenz ist erwartbar: Gaia zählte Kandidaten, deren Unsicherheitsbereich in den Planetenbereich reicht; wir zählen nur, wo der Schätzwert selbst darunter liegt.
- **Grenze der Validierung:** Das Verhältnis 1,000 zu Gaias `m2` (median, Quartile) zeigt nur, dass wir Gaias Rechnung reproduzieren, nicht dass die Massen genau sind. Systematische Fehler (dunkler-Begleiter-Annahme, `m1`) stecken in beiden Werten.
- **Abdeckung durch unsere Stichprobe (Parallaxe >= 5 mas, ca. 200 pc):** Von 1.503 Treffern unter 80 M_Jup liegen 1.306 (87 %) in der Stichprobe, alle 17 unter 13 M_Jup. Die übrigen 197 haben Parallaxen unter 5 mas (bis 2,1 mas, ca. 470 pc) und sind für das Modell nicht auffindbar. Der Recall im Backtest wird deshalb nur auf die 1.306 bzw. 17 bezogen. Alle 1.306 haben `parallax_over_error >= 10`, der Filter verliert keinen davon.
- **Fehlendes `m1`:** In der Stichprobe haben 461 von 10.375 `Orbital`-Lösungen (4,4 %) kein `m1` in `binary_masses`. Sie sind hell (Median G = 9,2, BP-RP = 1,03), also keine lichtschwachen M-Zwerge; der befürchtete Bias gegen M-Zwerge tritt nicht auf. Diese Sterne bekommen keine Massenschätzung und sind weder Treffer noch als sicher „kein Treffer“ eingestuft. Später zu klären: sie im Backtest aus Training und Auswertung ausschließen (Empfehlung) oder eine Masse-Helligkeits-Beziehung einsetzen und die Herkunft markieren.
- **`dr2_neighbourhood`:** Der Download der Verknüpfung für den ganzen DR2-Nahsternkatalog war zu langsam (ca. 2,4 min pro Chunk, hochgerechnet ca. 8 Stunden) und wurde abgebrochen. Ersatz: Wir laden nur die Verknüpfungszeilen der DR3-Quellen mit `Orbital*`-Lösung (Upload der IDs ans Archiv, `download_dr2_links`). Sie genügen, um DR3-Ergebnisse an DR2-Sterne zu hängen.

Anmerkung: DR2-Parallaxen haben einen kleinen systematischen Nullpunktversatz (einige hundertstel mas). Bei der Stichprobengrenze von 5 mas ist das vernachlässigbar (Grenze verschiebt sich um weniger als 1 %); wir korrigieren ihn nicht.

## 2026-09-25 – RUWE-Kalibrierung DR3 (`calibration.py`)

Verfahren: Median und 16/84-Perzentile von RUWE je Zelle aus G-Helligkeit (0,25 mag) und BP-RP (0,2 mag); Zellen mit weniger als 100 Sternen fallen auf den G-Streifen, dann auf den globalen Wert zurück. Kalibriert auf dem DR3-Nahsternkatalog selbst (5.228.166 Sterne mit RUWE und G); 900 Zellen, 70 G-Streifen. Features: `ruwe_expected`, `ruwe_excess`, `ruwe_z` (`data/processed/ruwe_features_dr3.parquet`). 5.215.484 Sterne nutzen eine Zelle, 12.328 den G-Streifen, 16.646 den globalen Wert (meist ohne BP-RP oder G).

Ergebnis:
- Der rohe RUWE hängt stark von der Helligkeit ab: Median 1,03 bei G = 6–10, 1,65 bei G = 18–20; 60 % der Sterne bei G = 18–20 haben RUWE > 1,4. Nach der Kalibrierung liegt der Median von `ruwe_z` in jedem G-Bereich bei 0,00 (Ausnahme: G < 4 mit 460 Sternen).
- Anteil `ruwe_z > 3`: 4–13 % je Helligkeitsbereich (statt 12–60 % beim rohen RUWE > 1,4).
- Signal: `Orbital`-Lösungen haben Median `ruwe_z` = 5,72 (74 % über 3). Die Treffer unter 80 M_Jup haben 2,75 (47 % über 3). Sie wackeln also erkennbar, aber ein großer Teil (53 %) fällt mit `ruwe_z` <= 3 nicht auf.
- **Bekannte Planetensterne (NASA, DR3-ID, in der Stichprobe): Median `ruwe_z` = -0,03, 0,9 % über 3.** Sie unterscheiden sich in RUWE nicht von der Population. Die meisten sind per Transit oder Radialgeschwindigkeit entdeckt und wackeln für Gaia nicht messbar.

Folgerung, offen: Ein Modell, das nur bekannte Planetensterne als Positive lernt (Manifest, Version 1), lernt kaum Wackel-Signal, weil dieses Label nicht mit RUWE zusammenhängt. Es besteht die Gefahr, dass es Helligkeit und Entfernung der Survey-Auswahl lernt (der Survey-Bias, den SHAP prüfen soll). Zu klären vor dem Training: (a) Label wie geplant und beobachten, (b) zusätzlich ein Modell direkt auf das Backtest-Ziel (DR3-Orbit-Lösung unter 80 M_Jup) trainieren, (c) Vergleich beider.

## 2026-09-25 – Erreichbarkeit der Backtest-Ziele in DR2-Begriffen

DR2↔DR3-Verknüpfung (`dr2_neighbourhood`, über TAP-Upload für alle 135.760 DR3-Quellen mit `Orbital*`-Lösung): 138.139 Zeilen, 2.336 Quellen mit mehreren DR2-Kandidaten. Auflösung: kleinster Winkelabstand.

`Orbital`-Ziele mit `m1`:

| Stufe | unter 80 M_Jup | unter 13 M_Jup |
|---|---|---|
| alle | 1.503 | 17 |
| in der DR3-Stichprobe (Parallaxe >= 5 mas) | 1.306 | 17 |
| DR2-Gegenstück gefunden | 1.503 | 17 |
| DR2-Gegenstück in der DR2-Stichprobe (DR2-Parallaxe >= 5 mas) | 1.304 | 17 |
| DR2 `parallax_over_error >= 10` | 1.304 | 17 |

Die Recall-Basis im Backtest ist 1.304 (bzw. 17). Die Sorge, die DR2-Stichprobe verliere viele Wackelsterne, bestätigt sich für die Ziele kaum: Nur zwei bis drei der 1.306 gehen verloren, und alle Ziele bestehen den DR2-Filter. Die DR2-Parallaxe der Ziele ist offenbar meist gut genug. Für die restlichen 199 Ziele gilt weiter: Parallaxe unter 5 mas.

Offen für Liste 2: Der Kiefer-et-al.-Katalog (A&A 702, A77, 2025; 9.698 Kandidaten, G < 16, Begleiter unter 13,5 M_Jup, 1–3 AE) ist vermutlich über Zenodo (Anhänge als PDF) und/oder VizieR erhältlich. Ob eine maschinenlesbare Tabelle existiert, ist nicht bestätigt (VizieR-Suche ohne Treffer).

## 2026-09-25 – DR2-Parallaxen der Ziele, Gaias Auswahl, RUWE-Kalibrierung DR2

**Warum die Ziele den DR2-Filter bestehen.** `parallax_over_error` in DR2 bei den 1.304 erreichbaren Zielen unter 80 M_Jup: Minimum 25,1, 5. Perzentil 67,4, Median 150,8 (zum Vergleich: Median der ganzen DR2-Stichprobe 7,1). Median-Parallaxe 10,4 mas (ca. 96 pc), Median G = 14,7. Die Ziele sind also nahe Sterne mit sehr genauer Parallaxe, selbst ein aufgeblähter Fehler senkt `parallax_over_error` nicht unter 25.

**Das Ziel ist teilweise durch Gaias eigene Auswahl definiert.** Gaia hat in DR3 Bahnlösungen nur für Sterne gerechnet, die bestimmte Kriterien erfüllten (u. a. erhöhter RUWE, ausreichende Helligkeit und Messqualität). Das Ziel heißt genau genommen: „Stern, den Gaias Pipeline ausgewählt hat und bei dem sie einen substellaren Begleiter fand“. Das ist für die Wette richtig, denn gemessen wird gegen Gaias Veröffentlichung. Folgen: (1) Das Modell lernt neben der Physik auch Gaias Auswahlkriterien mit; ein hohes `parallax_over_error` ist schon eine Eigenschaft der Zielsterne (Median 151 gegenüber 7,1). (2) Ändert Gaia die Kriterien für DR4, kann sich das Verhalten des Modells verschieben. Das ist eine bekannte Grenze neben der längeren Messzeit.

**Kalibrierung DR2** (`ruwe_grid_dr2.parquet`, `ruwe_features_dr2.parquet`; gleicher Code wie DR3): 5.960.755 Sterne, 888 Zellen; 5.946.344 Sterne nutzen eine Zelle, 14.156 den G-Streifen, 255 den globalen Wert. Der rohe RUWE-Median steigt von 1,03 (G = 6–10) auf 1,67 (G = 18–20, dort 62 % über 1,4); nach der Kalibrierung liegt `ruwe_z` in jedem Bereich bei 0,00 (Ausnahme G < 4, weniger als 600 Sterne).

Signal in DR2 (`ruwe_z`, Median und Anteil über 3):

| Gruppe | Sterne | Median | Anteil über 3 | DR3 zum Vergleich |
|---|---|---|---|---|
| alle | 5.960.755 | 0,00 | 6,0 % | 6,7 % |
| bekannte Planetensterne (`disc_year <= 2017`) | 674 | −0,08 | 1,2 % | 0,9 % |
| Ziele unter 80 M_Jup | 1.304 | 1,43 | 22,4 % | 47 % |
| Ziele unter 13 M_Jup | 17 | 0,24 | 0 % | – |
| `Orbital` insgesamt (mit Verknüpfung) | 9.891 | 3,58 | 56 % | 74 % |

Befunde: (1) Das Wackel-Signal ist in DR2 deutlich schwächer als in DR3, wie erwartet (kürzere Messdauer). (2) Die 17 Ziele unter 13 M_Jup zeigen in DR2 im RUWE praktisch kein Signal (Median 0,24, keiner über 3): Für Liste 2 trägt RUWE allein im Backtest nicht; die Validierung stützt sich auf andere Größen. (3) Die bekannten Planetensterne bleiben unauffällig, wie in DR3.

## 2026-09-25 – Feature-Tabellen und RUWE-Baseline im Backtest DR2→DR3

Tabellen: `features_dr2.parquet` (5.960.755 Sterne), `features_dr3.parquet` (5.244.458), `targets_dr2.parquet`. Gemeinsame Merkmale (`COMMON` in `features.py`) sind für beide Releases gleich berechnet; DR2 enthält keine DR3-only-Spalten (per Test geprüft). HGCA-Abdeckung 0,8 % (DR2) und 1,0 % (DR3). Ziel je DR2-Stern: verknüpfte DR3-`Orbital`-Lösung (kleinster Winkelabstand) mit geschätzter Masse unter 80 bzw. 13 M_Jup. Ausgeschlossen (Label unbekannt, weder positiv noch negativ): 897 Sterne, davon 451 mit `Orbital`-Lösung ohne `m1` und 446 mit `OrbitalTargetedSearch*`/`OrbitalAlternative*`. Positive und ausgeschlossene Sterne überlappen sich nicht. Die Negativen enthalten 9.033 Sterne mit `Orbital`-Lösung und größerer Begleitermasse (Median `ruwe_z` 3,96): Das Modell muss substellar von stellar unterscheiden, nicht nur wackelnd von ruhig.

**Baseline** (Population = DR2-Stichprobe mit Filter `parallax_over_error >= 10`: 2.304.869 Sterne, 1.304 Treffer unter 80 M_Jup, Basisrate 0,057 %):

| Score | AUC | AP | Recall@1 % | Recall@5 % | Recall@10 % | bester Rang | P@100 |
|---|---|---|---|---|---|---|---|
| RUWE | 0,783 | 0,0012 | 0,0 % | 1,3 % | 9,8 % | 35.627 | 0 |
| `ruwe_z` | 0,830 | 0,0017 | 0,0 % | 5,8 % | 39,7 % | 52.653 | 0 |
| `astrometric_excess_noise_sig` | 0,786 | 0,0015 | 0,1 % | 7,5 % | 25,7 % | 22.881 | 0 |

Ohne Filter: AUC RUWE 0,684, `ruwe_z` 0,809, `astrometric_excess_noise_sig` 0,762. Variante „nur neue Treffer“ ist von „alle“ praktisch nicht zu unterscheiden (658 bekannte Planetensterne, fast keiner unter den Treffern).

Befunde:
1. **P@10, P@30 und P@100 sind für alle Baselines 0.** Die obersten Plätze der RUWE-Sortierung sind Extremfälle (RUWE 38–112, G ca. 12): sehr wahrscheinlich enge stellare Doppelsterne oder Messartefakte, kein Ziel darunter. Der beste Treffer steht auf Rang 23.000–53.000 von 2,3 Mio. Für den Backtest folgt: Ein Modell, das schon einen Treffer in die Top 100 bringt, schlägt die Baseline, aber ein Verhältnis zur Baseline ist nicht definiert. Deshalb die Zusatzmetriken (Manifest 0.11).
2. Die Kalibrierung hilft: `ruwe_z` schlägt den rohen RUWE deutlich (AUC 0,83 gegenüber 0,78; Recall@10 % 40 % gegenüber 10 %).
3. Der Qualitätsfilter `parallax_over_error >= 10` verbessert die Baseline (AUC RUWE 0,68 → 0,78), weil er Sterne mit verfälschtem RUWE entfernt, ohne ein Ziel zu verlieren.
4. Eine reine Wackel-Sortierung findet die Ziele nicht an der Spitze, weil dort stellare Doppelsterne stehen. Erwartung für Modell A: Es muss lernen, extreme Wackler (Doppelsterne) von moderaten (substellare Begleiter) zu trennen.

## 2026-09-25 – Physikalische Features und ein Befund zum Ziel

Neue Features (`physics_features.py`, je Release aus eigenen Daten): `ms_offset` (Abstand über der Hauptreihe bei gleicher Farbe, Hauptreihe = Median der absoluten G-Helligkeit je Farbbin, Sterne unter 100 pc mit `parallax_over_error >= 20`), `mass_ms` (grobe Hauptreihen-Massentabelle in `MASS_TABLE`, aus dem Gedächtnis, **nicht gegen eine Quelle geprüft**) und `wobble_ratio` (`astrometric_excess_noise` geteilt durch die größte Reflexbewegung eines 80-M_Jup-Begleiters bei einer Periode gleich der Messdauer: DR2 22, DR3 34 Monate). Fehlende Werte: 4 % bei `ms_offset` (kein BP-RP).

Werte in DR2 (Filter `parallax_over_error >= 10`):

| Gruppe | Median `ms_offset` | Median `wobble_ratio` | 90. Perzentil `wobble_ratio` |
|---|---|---|---|
| Ziele unter 80 M_Jup (1.304) | 0,45 | 0,21 | 0,37 |
| Sterne mit `Orbital`-Lösung, größere Masse (8.587) | 0,32 | 0,39 | 0,86 |
| Übrige Population | −0,06 | 0,23 | 1,13 |

- `wobble_ratio` zeigt das erwartete Fenster: Die Ziele haben ein enges Band unter 1 (90. Perzentil 0,37), Doppelsterne mit größerer Masse wackeln stärker (0,39/0,86), die übrige Population hat einen langen Schwanz nach oben (1,13).
- **`ms_offset` verhält sich anders als erwartet.** Erwartet: Doppelsterne über der Hauptreihe, Ziele (dunkle Begleiter) darauf. Beobachtet: Die Ziele liegen in jeder Farbe und Entfernung etwa 0,4–0,5 mag *über* der Hauptreihe (bei BP-RP 2: 0,42 gegenüber −0,10 in der Population; bei 50 bis 200 pc: 0,43–0,61 gegenüber −0,17 bis −0,04) und sind darin von den stellaren `Orbital`-Sternen (0,32 bzw. 0,52) nicht zu trennen. Eine Doppelstern-Signatur (gleich große Begleiter heben ein System um 0,75 mag). Mögliche Deutung, nicht belegt: Ein Teil der Ziele unter 80 M_Jup sind unaufgelöste leichte Doppelsterne, deren `m1` (FLAME für Einzelsterne) zu groß und deren `m2` damit zu klein geschätzt ist. Das passt zu Nachfolgemessungen, die unter astrometrischen Gaia-Kandidaten Braune Zwerge und „Impostor“-Doppelsterne finden (Radialgeschwindigkeits-Nachbeobachtung, arXiv 2609.08590; von mir nicht gelesen). Für die Wette ändert sich nichts (gemessen wird gegen Gaias Veröffentlichung), für die Aussage „substellar“ gilt: Ein Teil der Treffer ist ein Kandidat, keine bestätigte Masse.

## 2026-09-25 – Modell A, erster Lauf im Backtest DR2→DR3 (`model_a.py`)

Aufbau (vor dem Lauf festgelegt, nicht getunt): LightGBM, 28 gemeinsame Merkmale (`COMMON`), Population DR2 mit `parallax_over_error >= 10` (2.304.869 Sterne, 1.304 Treffer unter 80 M_Jup, 897 Sterne mit unbekanntem Label ausgeschlossen), 5-fach-Kreuzvalidierung nach HEALPix-Level-2-Region (ganze Pixel pro Fold), Negative im Training 1:50 heruntergesampelt, Early Stopping auf Average Precision mit einer weiteren ausgehaltenen Region, `num_leaves` 15, `min_child_samples` 200, `reg_lambda` 10, Seed 42. Bewertet wird mit den Out-of-Fold-Scores auf der vollen Population. Genau ein Lauf, keine Hyperparameter-Suche.

| Metrik | Modell A | Baseline `ruwe_z` | Baseline RUWE |
|---|---|---|---|
| P@10 | 0,00 | 0 | 0 |
| P@30 | 0,033 | 0 | 0 |
| P@100 | 0,11 (11 Treffer) | 0 | 0 |
| P@1000 | 0,111 (111 Treffer) | – | – |
| Recall@1 % | 55,7 % | 0,0 % | 0,0 % |
| Recall@10 % | 93,0 % | 39,7 % | 9,8 % |
| AUC | 0,971 | 0,830 | 0,783 |
| AP (Basisrate 0,057 %) | 0,0448 | 0,0017 | 0,0012 |
| bester Rang | 25 | 52.653 | 35.627 |

„Nur neue Treffer“ ist von „alle“ nicht zu unterscheiden. Nach Helligkeit (Liste je Klasse): G 13–16 trägt die meisten Treffer (929 Ziele, P@100 0,14), G 10–13 P@100 0,06, G 16–19 0,09, G < 10 keine Treffer in den Top 100 (30 Ziele), G >= 19 keine Ziele. Wichtigste Merkmale (Gain-Anteil): `ruwe_excess` 29 %, `parallax_over_error` 23 %, `ruwe` 7 %, `wobble_ratio` 7 %, `bp_rp` 5 %, `ms_offset` 5 %.

**Was das Modell gelernt hat (Diagnose, Out-of-Fold):**
- In den Top 100: 11 substellare Ziele, 6 Sterne mit `Orbital`-Lösung größerer Masse, 83 Sterne ohne DR3-Bahnlösung. In den Top 1000: 111, 70 und 819.
- Das Modell findet Sterne mit *irgendeiner* DR3-Bahnlösung gut (AUC 0,87 gegen den Rest): ein großer Teil ist Gaias Auswahl (hohe Parallaxen-Genauigkeit, mäßiges Wackeln, G 13–16), nicht Physik. `parallax_over_error` als Nr. 2 der Merkmale bestätigt das.
- Innerhalb der Sterne mit Bahnlösung trennt es substellar von stellar mit AUC 0,82 und AP 0,42 (Basisrate 0,13): Das ist der physikalische Teil, er ist echt, aber deutlich schwächer als der Gesamt-AUC vermuten lässt.
- 82 % der Top 1000 haben in DR3 keine Bahnlösung. Ob sie Fehlalarme sind oder in DR3 nur knapp unter Gaias Auswahlschwelle lagen und in DR4 (66 statt 34 Monate) eine Lösung bekommen, kann der Backtest nicht klären.

Grenzen: Genau ein Datensatz-Split; die Streuung zwischen den Folds ist groß (AP 0,034–0,061 je Region). Der Gesamt-AUC ist durch die Auswahl-Signale aufgebläht. SHAP-Auswertung, Vergleich mit den NASA-Label-Modellen B/B' und Feature-Ablationen stehen noch aus.
