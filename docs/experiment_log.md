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
