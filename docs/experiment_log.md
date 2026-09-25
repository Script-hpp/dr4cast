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

## 2026-09-25 – Massentabelle ersetzt, Ablationen, SHAP, Beschleunigungs-Lösungen, Modelle B/B'

**Massentabelle:** Die grobe Tabelle aus dem Gedächtnis ist ersetzt durch die Mittelwert-Hauptreihe von Mamajek (Version 2022.04.16, beruht auf Pecaut & Mamajek 2013; `src/gaia_wobble/data/mamajek_mg_mass.csv`, 72 Zeilen, absolute Gaia-G gegen Masse). Die alte Tabelle lag nahe daran (G2V 1,0 gegen 1,0; M0V 0,60 gegen 0,57; M5V 0,20 gegen 0,16). Features neu berechnet; die Zahlen des ersten Modell-A-Laufs (Eintrag oben) gelten damit als überholt, die Tabelle unten ersetzt sie. Es ist eine Zwergen-Hauptreihe: Riesen, Unterriesen und unaufgelöste Doppelsterne bekommen eine falsche Masse; `wobble_ratio` ist nur eine ungefähre Größenordnung.

**Ablationen** (gleiches Protokoll, je ein Lauf, vor dem Start festgelegt; Population DR2 mit `parallax_over_error >= 10`, 1.304 Treffer unter 80 M_Jup):

| Variante | Merkmale | P@30 | P@100 | P@1000 | AUC | AP | Recall@1 % | AP je Region (min–max) |
|---|---|---|---|---|---|---|---|---|
| full | 28 | 0,067 | 0,08 | 0,097 | 0,969 | 0,0434 | 54,5 % | 0,035–0,058 |
| no_poe | 27 | 0,133 | 0,09 | 0,091 | 0,969 | 0,0424 | 55,4 % | 0,033–0,054 |
| no_selection | 21 | 0,067 | 0,07 | 0,084 | 0,966 | 0,0370 | 51,5 % | 0,033–0,055 |
| physics | 9 | 0,167 | 0,15 | 0,093 | 0,966 | 0,0394 | 52,2 % | 0,032–0,054 |
| physics_strict | 6 | 0,167 | 0,15 | 0,096 | 0,962 | 0,0383 | 47,8 % | 0,032–0,047 |

`no_selection` lässt Parallaxen-Genauigkeit, Helligkeit, Beobachtungszahlen und Sichtbarkeitsperioden weg; `physics` behält nur Wackel- und Farben-Helligkeits-Merkmale; `physics_strict` entfernt zusätzlich alle von Parallaxe oder Entfernung abgeleiteten Merkmale (`wobble_ratio`, `abs_g`, `pm_total`). Die Unterschiede zwischen den Varianten (AP 0,038–0,043) liegen im Streuungsbereich der Regionen (0,032–0,058), P@30 und P@100 beruhen auf wenigen Treffern (5–15) und sind nicht unterscheidbar.

Deutung: Das Weglassen der Auswahl-Merkmale und selbst der Parallaxen-abgeleiteten Merkmale kostet kaum etwas. Die Auswahl-Information steckt also nicht in Parallaxe oder Helligkeit, sondern in den Wackel-Statistiken selbst (`ruwe_excess`, `astrometric_excess_noise_sig`, `chi2_per_dof`): Gaia hat Bahnlösungen für Sterne mit erhöhtem Astrometrie-Rauschen gerechnet, und das Modell lernt diese Schwelle mit. Physik und Auswahlregel lassen sich mit diesen Merkmalen nicht trennen. Das Übertragungsrisiko auf DR4 sinkt dadurch nicht, sondern hängt daran, ob Gaia für DR4 dieselben Schwellen auf RUWE und Rauschen benutzt.

**SHAP** (Out-of-Fold, 1.304 Treffer plus 40.000 zufällige Negative): Im vollen Modell `parallax_over_error` 22 % (höher = höherer Score), `ruwe_excess` 15 %, `ms_offset` 10 % (höher = höherer Score), `ruwe` 10 %, `wobble_ratio` 7 % (kleiner = höherer Score: das erwartete Fenster). In der Physik-Variante rückt `wobble_ratio` auf 23 %, `ruwe_excess` 22 %, `ms_offset` 15 %, `astrometric_excess_noise_sig` 12 %; die Wichtigkeit verschiebt sich auf Merkmale, die Parallaxe enthalten (`wobble_ratio`, `abs_g` 6 %). Erst `physics_strict` schließt diesen Umweg aus (siehe Tabelle: kaum Verlust). Das positive Vorzeichen von `ms_offset` heißt: Das Modell bevorzugt Sterne oberhalb der Hauptreihe, wie die Ziele selbst sie zeigen.

**Beschleunigungs-Lösungen** (`accel_check.py`, nur Auswertung): Anteil der Sterne, die in DR3 eine Lösung in `nss_acceleration_astro` haben (gekrümmte Bewegung, Messzeit für eine Bahn zu kurz; Kandidaten für DR4):

| Gruppe (ohne DR3-Bahnlösung) | Sterne | Anteil Beschleunigung |
|---|---|---|
| Top 1000 von Modell A (full) | 824 | 16,0 % |
| zufällige Population | 20.000 | 1,1 % |
| Kontrollgruppe mit gleicher Parallaxen-Genauigkeit, Helligkeit und `ruwe_z`-Spanne | 20.000 | 7,7 % |

Die Top 1000 enthalten 15-mal mehr Beschleunigungs-Lösungen als die Population und etwa doppelt so viele wie eine nach Qualität, Helligkeit und Wackeln ausgewählte Kontrollgruppe. Ein Teil der Anreicherung ist also Qualität und Wackeln, aber es bleibt ein Faktor 2 darüber. Hinweis, kein Beweis, dass die Top-Sterne Langzeit-Begleiter enthalten.

**Bestätigte Begleiter und `ms_offset`** (DR3-Features, NASA-Hosts): Astrometrisch entdeckte substellare Begleiter (6 Sterne: GJ 896 A b, HIP 66074 b, Gaia-4 b, HD 128717 b, Gaia-5 b, DENIS-P J082303.1-491201 b): Median `ms_offset` −0,08 (Quartile −0,46/0,17), Population −0,03. Transit-Hosts 0,08, Radialgeschwindigkeits-Hosts 0,31. Die Ziele des Backtests liegen bei 0,45. Bestätigte dunkle Begleiter sitzen also nahe der Hauptreihe, die Ziele deutlich darüber: Das stützt die Deutung, dass ein Teil der Ziele unter 80 M_Jup leichte Doppelsterne mit zu klein geschätzter Masse ist. Metallizität und die kleine Stichprobe (6) sind Einschränkungen. Die bestätigten astrometrischen Begleiter haben in DR3 auch sehr kleines `wobble_ratio` (0,01–0,12), sie wurden nicht über das RUWE-Signal gefunden.

**Modelle B und B'** (NASA-Labels, DR2-Features, gleiches Protokoll; B: 658 Wirtssterne, B': 106 mit erwarteter Amplitude >= 0,1 mas, 32 ohne Masse/Periode; Schwelle vorher festgelegt):

| Modell | AUC (eigenes Label) | AP (eigenes Label) | AUC (Ziel) | AP (Ziel) | P@100 (Ziel) | P@1000 (Ziel) | Recall@1 % (Ziel) |
|---|---|---|---|---|---|---|---|
| B | 0,942 | 0,0585 | 0,641 | 0,0008 | 0 | 0 | 0,4 % |
| B' | 0,985 | 0,0166 | 0,602 | 0,0009 | 0 | 0 | 0,8 % |
| A (full) | – | – | 0,969 | 0,0434 | 0,08 | 0,097 | 54,5 % |

B und B' lernen ihr eigenes Label gut (AUC 0,94/0,99, vor allem über Helligkeit und Entfernung der beobachteten Planetensterne), finden das Backtest-Ziel aber praktisch nicht. Die Negativ-Kontrolle bestätigt, dass Planetenlabels ohne Wackel-Bezug für dieses Ziel nichts beitragen. SHAP für B/B' und die AP-Streuung je Region fehlen noch.

## 2026-09-25 – Manifest 0.13 und erste Anwendung von Modell A (Physik-Variante) auf DR3

Festlegung vor der Anwendung (Manifest 0.13): Modell A = Physik-Variante, Mittel der fünf Regions-Modelle; Liste 2 nur mit `ms_offset < 0,2`. Die Wahl fiel nach Blick auf die Ablationen (Leistung im Streuungsbereich der Regionen); Hauptargument: Beobachtungszahlen, Sichtbarkeitsperioden und Parallaxen-Fehler verändern sich mit der Messdauer der Releases. Die Ablationen senken das Übertragungsrisiko nicht: Die Auswahlschwelle von Gaia (erhöhtes Astrometrie-Rauschen) steckt in den Wackel-Statistiken selbst und lässt sich nicht herausnehmen, ohne das Signal zu entfernen. Das Modell überträgt sich auf DR4 nur, wenn Gaia dort ähnliche Schwellen benutzt.

**Anwendung auf DR3** (`apply_dr3.py`, Entwicklungslauf, nicht die eingefrorene Liste; 2.234.316 Sterne mit `parallax_over_error >= 10`):

| Gruppe | DR3-Bahn unter 80 M_Jup | irgendeine DR3-Bahn | Beschleunigungs-Lösung | bekannter Planet | Median `ms_offset` | Median G |
|---|---|---|---|---|---|---|
| Top 100 | 11 % | 13 % | 11 % | 0 % | 0,26 | 15,0 |
| Top 100 ohne bekannte Fälle | 0 % | 2 % | 11 % | 0 % | 0,24 | 15,0 |
| Top 1000 | 7,4 % | 11,8 % | 12,7 % | 0,1 % | 0,34 | 14,5 |
| Top 1000 ohne bekannte Fälle | 0 % | 4,7 % | 13,4 % | 0 % | 0,34 | 14,5 |
| Population | 0,1 % | 0,5 % | 1,2 % | 0,1 % | −0,03 | 16,5 |

- Nur 11 % der Top 100 (74 von 1000) haben schon eine DR3-Bahn unter 80 M_Jup. Das Modell füllt die Liste nicht mit Sternen, deren Ergebnis feststeht; die Regel „neue Treffer“ (Manifest 0.8) verändert die Top 100 wenig.
- Nach dem Ausschluss der bekannten Fälle haben 11 % der Top 100 und 13 % der Top 1000 eine Beschleunigungs-Lösung (Population 1,2 %), also ein Faktor 10 über der Population. Diese Sterne sind Kandidaten für eine DR4-Bahn.
- Der Median von `ms_offset` in den Top 100 liegt bei 0,26 (Population −0,03): Auch auf DR3 bevorzugt das Modell Sterne über der Hauptreihe. Nur 37,7 % der Top 1000 erfüllen `ms_offset < 0,2`; Liste 2 würde also aus einem deutlich kleineren Kreis wählen.
- Verteilung der Scores: Median 0,0017 (DR2 Out-of-Fold 0,0019), 90. Perzentil 0,024 (0,016), 99. Perzentil 0,41 (0,31), 99,9. Perzentil 0,67 (0,67). Die DR3-Scores liegen im mittleren Bereich etwas höher, ohne große Verschiebung. Das Modell sieht in DR3 also keinen Bereich, der im Training völlig fehlte.
- Die Top 100 haben keinen bekannten Planetenstern. Das ist zu erwarten (bekannte Planetensterne wackeln nicht: Median `ruwe_z` −0,03) und kein Zeichen für ein Problem.

Nicht geprüft: die Top-Sterne selbst (Namen, bekannte Doppelstern-Einträge in SIMBAD), der Anteil bekannter Doppelsterne in den Top 100 (Manifest, Validierung Punkt 4) und SHAP für B/B'.

## 2026-09-25 – Diagnose der Top 100 in DR3 (SIMBAD, nahe Nachbarn; `diagnose_top.py`)

Population: Top 100 von Modell A (Physik-Variante) auf DR3 nach Ausschluss der bekannten Fälle (DR3-Bahn unter 80 M_Jup, bekannte Planetensterne). Kontrollgruppe: 1.000 Sterne aus der Population mit gleicher Parallaxen-Genauigkeit, Helligkeit und `ruwe_z`-Spanne (5.–95. Perzentil der Top 100). Reine Auswertung, nichts davon geht ins Modell.

| Anteil | Top 100 | Kontrolle |
|---|---|---|
| in SIMBAD verzeichnet | 100 % | 22,4 % |
| Doppelstern-Typen (SB*, EB*, **, El*) | 1 % | 0,2 % |
| junge Sterne (Y*O, TT*, Or*) | 0 % | 0 % |
| Weiße Zwerge | 0 % | 0,3 % |
| Veränderliche (V*, Fl*, BY*, RS*) | 0 % | 0,2 % |
| Nachbar in Gaia DR3 innerhalb von 2" | 31 % | 15,4 % |

SIMBAD-Typen der Top 100: 92 Sterne mit hoher Eigenbewegung (PM*), 4 M-Zwerge (LM*), 3 Emissionslinien-Sterne (Em*), 1 Doppelstern (**).

Befunde:
1. Die Top 100 sind fast ausschließlich nahe Sterne mit hoher Eigenbewegung (Typ PM*). Sie sind alle in SIMBAD verzeichnet, die Kontrollgruppe nur zu 22 %. Das passt zu nahen M-Zwergen und zum Merkmal `pm_total` (ein Entfernungs-Indikator) im Modell. Es sagt nichts über Planeten, eher etwas über die Auswahl: nahe, gut katalogisierte Sterne.
2. Bekannte Doppelstern-Typen sind in den Top 100 kaum vertreten (1 %). Das ist keine Entwarnung: SIMBAD kennt nur die bekannten Doppelsterne, und Sterne, die nicht in SIMBAD stehen, fehlen in dieser Statistik (in der Kontrollgruppe 78 %).
3. **Nahe Nachbarn:** 31 % der Top 100 haben einen Gaia-Nachbarn innerhalb von 2 Bogensekunden, in der Kontrollgruppe 15 %, also das Doppelte. Enge Paare überlagern sich in den Bildern und erhöhen RUWE und Rauschen künstlich. Ein Teil des Wackel-Signals in der Liste ist damit vermutlich Bildüberlagerung und nicht Bewegung. Als Feature ist das nicht im Modell (Manifest 0.13), gehört aber als Grenze in den Bericht.
4. Keine jungen Sterne. Weiße Zwerge und Veränderliche sind nicht überrepräsentiert.

Noch nicht gemacht: Abgleich mit ExoDNN, Sahlmann & Gómez und dem Kiefer-Katalog (Listen nicht beschafft; ein Abgleich ist keine Validierung, weil die Methoden ähnliche Daten nutzen). Liste 2 besteht bisher nur aus Liste 1 mit dem Filter `ms_offset < 0,2`; die im Manifest vorgesehene Massen-Wahrscheinlichkeit aus der Wackel-Amplitude ist noch nicht gebaut.

## 2026-09-25 – Vorab-Regel für den Nachbar-Test im Backtest (vor dem Ergebnis festgelegt)

Frage: Sind Sterne mit einem Nachbarn innerhalb von 2" (in Gaia DR2, nur DR2-Daten) seltener echte Treffer des Backtest-Ziels? Beobachtung in DR3: 31 % der Top 100 haben einen solchen Nachbarn, in einer angepassten Kontrollgruppe 15 %.

Test: DR2-Out-of-Fold-Scores der Physik-Variante; Treffer-Anteil (Ziel unter 80 M_Jup) unter den Top 2.000 mit und ohne Nachbar. Entscheidungsregel: Ein Filter „Nachbar innerhalb von 2" ausschließen“ wird nur dann ins Manifest aufgenommen, wenn der Treffer-Anteil mit Nachbar höchstens die Hälfte des Anteils ohne Nachbar beträgt und der exakte Test nach Fisher p < 0,01 ergibt. Sonst bleibt der Nachbar eine reine Diagnose im Bericht.

## 2026-09-25 – Amplituden-Feature für Liste 2: Methode und Mindestgüte (vor der Berechnung festgelegt)

**Quelle der Methode:** Kiefer et al., „Searching for substellar companion candidates with Gaia. I. Introducing the GaiaPMEX tool“ (arXiv 2409.16992, A&A). Gelesen: Abschnitte 2–3 (Gleichungen 1–14). Relevant: `AEN² + σ_att² + σ_AL² = Σ R² / (N − 5)` (Gl. 2), `ruwe ≈ (1/u0) · sqrt((AEN² + σ_formal²) / σ_formal²)` (Gl. 4), `σ_formal = AEN · (χ²_astro / (N − 5) − 1)^(−1/2)` (Gl. 8, aus Katalogdaten für Quellen mit `astrometric_excess_noise_sig >= 2`), typischer Wert von σ_formal 0,08–0,3 mas in Abhängigkeit von Helligkeit, Farbe und Himmelsposition (Abb. 2). Ihre Warnung: In DR3 ist der `astrometric_excess_noise` für viele Quellen mit G > 13 fälschlich 0 (χ² unter dem 95. Perzentil), deshalb ist er dort unzuverlässig. Sie beschreiben nur das Prinzip der GaiaPMEX-Simulation (Bayes, simulierte Beobachtungen); den Code habe ich nicht.

**Unser Verfahren (keine Kurve aus dem Gedächtnis):**
1. `σ_formal` je Release aus dem eigenen Katalog nach Gl. 8, Mediane je Bin aus G (0,25 mag) und BP-RP (0,25).
2. `AEN_est = σ_formal · sqrt(max(χ²/(N − 5) − 1, 0))`: die Umkehrung von Gl. 8, auch dort verfügbar, wo der Katalogwert 0 ist.
3. Amplitude `a_est = sqrt(2) · AEN_est` (für eine Kreisbahn ist die Streuung der Residuen `a/sqrt(2)`; gilt für Perioden innerhalb der Messdauer, sonst wird ein Teil der Bahn vom Fit aufgenommen und `a_est` ist zu klein).
4. Aus `a_est`, Parallaxe und Sternmasse (`mass_ms`) der Bereich möglicher Begleitermassen für Perioden zwischen 0,5 und 5 Jahren (Kepler wie in `masses.py`); `P(m2 < 13 M_Jup)` ist der Anteil dieses (logarithmisch gleichverteilten) Periodenbereichs mit einer Masse unter 13 M_Jup.

**Mindestgüte (vor der Berechnung festgelegt):** Validierung an den DR3-`Orbital`-Lösungen mit Massenschätzung (bekannte Photozentrum-Amplitude `a0` aus den Thiele-Innes-Elementen). Das Feature gilt als tauglich, wenn (a) der Median des Verhältnisses `a_est / a0` zwischen 0,5 und 2 liegt und (b) die Spearman-Rangkorrelation zwischen `a_est` und `a0` über 0,6 liegt. Getrennt berichtet nach Helligkeitsklasse und Periode. Erfüllt das Feature das nicht, bleibt Liste 2 „Liste 1 mit `ms_offset`-Filter“ und das steht so im Manifest.

Einschränkungen, die vorab feststehen: Die Validierung an Bahnlösungen ist geschönt (starke Wackler, Perioden im günstigen Bereich); die Amplitude wird für Perioden über der Messdauer unterschätzt; `σ_formal` hängt bei Kiefer et al. auch von der Himmelsposition ab (bis Faktor 2, dichte Felder), wir nutzen nur Helligkeit und Farbe.

## 2026-09-25 – Ergebnis Nachbar-Test (DR2) und Amplituden-Feature (Regeln vom Vortag)

**Nachbar-Test im Backtest** (Gaia-DR2-Positionen, Radius 2", Out-of-Fold-Scores der Physik-Variante, Top 2.000):

| | Sterne | Treffer | Treffer-Anteil |
|---|---|---|---|
| ohne Nachbar | 1.780 | 153 | 8,6 % |
| mit Nachbar | 220 | 2 | 0,9 % |

Verhältnis 0,11, exakter Test nach Fisher p < 0,0001. Die vorab festgelegte Regel (Verhältnis höchstens 0,5 und p < 0,01) ist erfüllt. Nachbaranteil: Ziele 1 %, zufällige Negative 12,9 %, Top 100 8 %, Top 1.000 10,6 %; in den Top 100 und Top 1.000 Trefferquote mit Nachbar 0 % bzw. 0,9 %, ohne 16,3 % bzw. 10,3 %. Sterne mit engem Nachbarn sind fast nie Treffer: Enge Paare erzeugen Rauschen, das die Bahnlösung von Gaia nicht annimmt. (Beobachtung in DR3: 31 % der Top 100 haben einen DR3-Nachbarn innerhalb von 2", in DR2 nur 8 %; DR3 löst engere Paare besser auf, und die Nachbarzahl ist je Katalog zu bestimmen.) Folge: Manifest 0.14, Nachbar-Filter für beide Listen.

**Amplituden-Feature** (`amplitude.py`): `σ_formal` nach Kiefer et al. Gl. 8 aus unseren Katalogdaten, Median je Bin: G < 13: 0,082 mas, G 13–16: 0,19 mas, G 16–18: 0,50 mas, G ≥ 18: 1,8 mas. Das entspricht den Werten von Kiefer et al. für G < 16 (0,08–0,3 mas; Abb. 2). Für G > 16 gibt das Paper keine Werte an; die Extrapolation ist von uns. Validierung an 9.914 DR3-`Orbital`-Lösungen (wahre Amplitude `a0` aus den Thiele-Innes-Elementen):

| Größe | Wert | Vorgabe |
|---|---|---|
| Median `a_est / a0` | 0,58 | 0,5 bis 2 |
| Spearman-Rangkorrelation | 0,92 | über 0,6 |

Beide Kriterien erfüllt. Nach Periode: unter 200 d 0,62 (ρ 0,87), 200–500 d 0,60 (0,88), 500–1.200 d 0,58 (0,87), über 1.200 d 0,35 (0,69: Bahn länger als die Messdauer, Amplitude wird unterschätzt). Nach Helligkeit: G < 10 0,53 (ρ 0,91), 10–13 0,55 (0,90), 13–16 0,60 (0,92), > 16 0,64 (0,91). Substellare Teilmenge (unter 80 M_Jup, 1.306): 0,63 (ρ 0,95).

Die Amplitude wird im Median um etwa 40 % unterschätzt (Vorfaktor `sqrt(2)` für Kreisbahnen, Teile der Bahn gehen in den 5-Parameter-Fit). Damit werden die Begleitermassen zu klein und `P(m2 < 13 M_Jup)` zu groß geschätzt. Eine Korrektur ist nicht eingebaut (die Prüfung galt dem Feature wie definiert); sie wäre eine Manifest-Änderung. Die Validierung bleibt geschönt (starke Wackler, günstige Perioden), und die Bahnlösungen sind selbst die Sterne, deren Amplitude gut messbar ist.

**Vorschau Liste 2** (Entwicklungslauf auf DR3, ohne Nachbar-Filter, bekannte Fälle ausgeschlossen): Score = Score von Modell A × `P(m2 < 13 M_Jup)`, nur `ms_offset < 0,2`. Die Top 100 überschneiden sich nur mit 3 Sternen mit den Top 100 von Liste 1, mittleres `P(m2 < 13)` = 1,0, Median `ms_offset` 0,04, 12 % mit DR3-Beschleunigungs-Lösung (Population 1,2 %), 2 % mit DR3-Bahnlösung. Liste 2 ist damit eine andere Liste als Liste 1. In den Top 1.000 von Liste 1 haben 37,6 % ein `P(m2 < 13) > 0,5`, 38,1 % ein `ms_offset < 0,2` und 13,9 % beides.

## 2026-09-25 – Listen-Generator (`make_lists.py`) und Plausibilität von Liste 2 (`plausibility.py`)

**Generator:** Beide Listen in einem Lauf aus demselben Stand. Liste 1: Score `P_A`; Liste 2: `P_A · P(m2 < 13 M_Jup)`, nur `ms_offset < 0,2`. Ausgeschlossen aus `rank_new` (Rang der Hauptmetrik): bekannte DR3-Bahn unter 80 M_Jup, bekannte Planetensterne, Gaia-Nachbar innerhalb von 2". Je Liste die ersten 1.000 Zeilen nach `rank_new`; die eingefrorene Wette sind die ersten 100. Jede Zeile hat `source_id`, `rank_new`, `rank_raw`, Score, beide Teilwerte und die Markierungen `known_dr3_orbit80`, `known_dr3_orbit_any`, `dr3_acceleration`, `known_planet`, `neighbour_2arcsec`. Kopf der Datei: Manifest-Version, Datum, Git-Stand, Beschreibung des Scores; daneben `.sha256` je Liste und `lists_manifest.json` (Prüfsummen der Modelle, der Feature-Tabellen, der Nachbartabelle). Datum und Git-Stand sind Parameter, dadurch entstehen bei gleichen Eingaben byte-identische Dateien (Test `test_make_lists.py`, beide Listen zweimal erzeugt und verglichen). Die Nachbartabelle wird einmal beim Archiv abgefragt und mit dem Listenpaket zwischengespeichert; ohne diesen Zwischenspeicher wäre die Liste vom Archiv abhängig. Die Werte sind Ordnungs-Scores, keine kalibrierten Wahrscheinlichkeiten (Verzerrung der Amplitude um etwa 40 %, siehe oben); im Bericht wird „Score“ geschrieben.

**Kontrollplaneten** (nicht im Training, nicht als bekannt ausgeschlossen; Grundgesamtheit wie in den Listen: 2.234.316 DR3-Sterne mit `parallax_over_error >= 10`, davon 1.488.768 mit `ms_offset < 0,2`; ein erster Lauf hatte ohne Filter gerechnet, gleiche Ränge, andere Nenner, korrigiert):

| Planet | `parallax_over_error` | G | `ms_offset` | `P(m2 < 13)` | Rang Score Liste 1 | Rang Score Liste 2 |
|---|---|---|---|---|---|---|
| Gaia-4 b (11,8 M_Jup) | 650 | 11,9 | −0,06 | 0,80 | 81.298 (3,6 %) | 6.244 von 1.488.768 (0,4 %) |
| Gaia-5 b (20,9 M_Jup) | 673 | 13,2 | −0,58 | 0,84 | 6.430 (0,3 %) | 532 von 1.488.768 (0,036 %) |

Beide liegen im Score von Liste 2 im obersten Promille bis Prozent, besser als im Score von Liste 1, und beide erfüllen die `ms_offset`-Regel. Die Bewertung ist ein Einzelfall mit zwei Sternen und keine Validierung.

**Backtest für Liste 2** (DR2, Out-of-Fold-`P_A` der Physik-Variante mal `P(m2 < 13)` aus DR2, `ms_offset < 0,2`; 1.541.482 Sterne):
- **Von den 17 Zielen unter 13 M_Jup erfüllen nur 4 die `ms_offset`-Regel**; die Regel entfernt also 13 der 17 Ziele (und 409 von 1.304 Zielen unter 80 M_Jup bleiben). Das passt zur Deutung, dass die Ziele meist über der Hauptreihe liegen (Verunreinigung durch leichte Doppelsterne); es heißt aber auch, dass die Backtest-Validierung von Liste 2 auf 4 Sternen beruht.
- Score von Liste 2: Treffer unter 13 M_Jup in den Top 100/1000/10000: 0/2/2; mittlerer Rang der 4 Ziele 9.540 von 1.541.482. Score von Liste 1 auf derselben Menge: 0/0/2, mittlerer Rang 27.129. Treffer unter 80 M_Jup in den Top 100/1000: Liste 2 2/38, Liste 1 9/77.
- 2 von 4 Zielen in den Top 1000 von 1,5 Mio. (Erwartung bei Zufall: 0,003) ist eine deutliche Anreicherung, bleibt aber bei 4 Zielen eine Tendenz ohne Signifikanzaussage.

**Einordnung:** Gaia-4 b (Rang 6.244) und Gaia-5 b (Rang 532) liegen deutlich besser als der Durchschnitt, kämen aber in keine Top-100-Liste. Die Richtung stimmt, das Netz aus 100 Sternen ist eng. Der Bericht sagt das so.

**Ziel von Liste 2 (Manifest 0.15).** Von den 17 Zielen unter 13 M_Jup haben 4 ein `ms_offset < 0,2` (−0,31, −0,20, 0,01, 0,07); die übrigen 13 liegen bei 0,41 bis 0,91 mag (Werte 0,41 0,45 0,47 0,51 0,52 0,57 0,60 0,60 0,68 0,77 0,85 0,87 0,91), alle mit `parallax_over_error` zwischen 282 und 1.298. Das entspricht der Deutung, dass diese Ziele überwiegend leichte, unaufgelöste Doppelsterne sind (ein gleich heller Doppelstern liegt 0,75 mag über der Hauptreihe). Für das Ziel unter 80 M_Jup erfüllen 430 von 1.306 die Bedingung.

## 2026-09-25 – Entwicklungslauf der Listen (`data/predictions/dev_lists/`, nicht eingefroren)

Beide Listen aus einem Lauf (Manifest-Stand 0.14, Git-Stand 41a4961, Datei-Kopf entsprechend); je 1.000 Zeilen. Nachbartabelle: 5.488 Kandidaten abgefragt, 17,5 % mit Nachbar innerhalb von 2". Prüfsummen (SHA-256): Liste 1 `99a40bb2…7efba`, Liste 2 `cac53dbc…f3d61`.

| | Liste 1 (unter 80 M_Jup) | Liste 2 (Planeten) |
|---|---|---|
| Rang in der Rohsortierung beim 100. Platz von `rank_new` | 150 | 123 |
| Beschleunigungs-Lösung in den Top 100 | 19 % | 12 % |
| irgendeine DR3-Bahn in den Top 100 | 3 % | 1 % |
| Median `ms_offset` | 0,33 | 0,05 |
| Median `P(m2 < 13)` | 0,32 | 1,0 |

Die Ausschlüsse (bekannte Fälle, Planetensterne, Nachbarn) entfernen nur 50 bzw. 23 Sterne aus den ersten 150 bzw. 123 Rohplätzen. Die Top 100 der beiden Listen überschneiden sich in 6 Sternen. Beide Listen haben einen Beschleunigungs-Anteil, der etwa zehnmal bis 16-mal über der Population liegt (1,2 %). Der Lauf ist ein Test des Werkzeugs, keine Einfrierung: Die Modelle, Features und Regeln sind nach 0.15 noch nicht als endgültig erklärt.
