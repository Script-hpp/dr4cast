# Manifest – Gaia Wobble Bet

**Status:** Entwurf (lebendes Dokument)
**Version:** 0.19
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
| Hauptziel (zwei gleichrangige Listen) | Stern hat in DR4 eine Bahnlösung (`nss_two_body_orbit` oder `nss_multiple_orbits`) mit Begleitermasse nach der eigenen Schätzung (siehe „Massenschätzung und Ziele“). **Liste 1:** unter 80 Jupitermassen. **Liste 2 („Planetenliste“):** unter 13 Jupitermassen **und** `ms_offset` unter 0,2 mag (mit den Werten des jeweiligen Releases; „dunkler Begleiter mit Planetenmasse“). Zusätzlich berichtet: das Ziel unter 13 Jupitermassen ohne `ms_offset`-Bedingung. `nss_masses` zusätzlich als Vergleich |
| Nebenziel | Auswertung getrennt nach Helligkeitsklassen und nach `OrbitalTargetedSearch`; ESA-Massen aus `nss_masses` |
| Offizielle ESA-Liste | Falls veröffentlicht: zusätzliche Auswertung, ersetzt nicht das Hauptziel |
| Verknüpfung DR3→DR4 | Nur über die Tabelle `dr3_neighbourhood`, nie über gleiche `source_id` |
| Metriken | P@10, P@30, P@100, P@1000, Recall@100, absolute Treffer; zusätzlich nach Helligkeitsklassen. Zusätzlich (Ergänzung 0.11, festgelegt nach Blick auf die Baseline, aber vor jedem Modell): ROC-AUC, Average Precision, Recall in den obersten 1 %, 5 % und 10 % der Population und der beste Rang eines Treffers. Jede Metrik wird zweifach berichtet: *alle Treffer* und *nur neue Treffer* (Sterne, die nicht in den Trainingslabels waren). **Hauptmetrik ist „nur neue Treffer“**, weil bekannte Planetensterne leicht wiederzufinden sind |
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
- **`ms_offset`-Regel für Liste 2:** Nur Sterne mit `ms_offset < 0,2` mag (nahe der Hauptreihe) können in Liste 2 stehen. Begründung: Das Modell bevorzugt Sterne über der Hauptreihe, die Ziele des Backtests liegen im Median bei 0,45 mag darüber (vermutlich leichte Doppelsterne mit zu klein geschätzter Masse), bestätigte astrometrische substellare Begleiter dagegen bei −0,08 (Quartile −0,46/0,17). Der Schwellwert 0,2 entspricht etwa dem oberen Quartil dieser bestätigten Begleiter und ist damit festgelegt, bevor Modell A auf DR3 angewendet wurde. Liste 1 bleibt ohne diese Regel (wir wetten auf das, was Gaia veröffentlicht, samt Verunreinigung).
- **Amplituden-Feature (Mindestgüte erfüllt, Details im Experiment-Log):** `σ_formal` nach Kiefer et al. (2025, Gl. 8) aus den Katalogdaten je Helligkeits- und Farbbin, `AEN_est = σ_formal · sqrt(max(χ²/(N − 5) − 1, 0))`, Amplitude `a_est = sqrt(2) · AEN_est`. Aus `a_est`, Parallaxe und Sternmasse (`mass_ms`) folgt der Massenbereich für Perioden von 0,5 bis 5 Jahren (logarithmisch gleichverteilt); `P(m2 < 13 M_Jup)` ist der Anteil dieses Bereichs unter 13 M_Jup. Validierung an 9.914 DR3-Bahnlösungen: Median `a_est / a0` = 0,58, Spearman-Rangkorrelation 0,92. Bekannte Verzerrung: Die Amplitude ist im Median um etwa 40 % zu klein, `P(m2 < 13)` damit eher zu groß; keine Korrektur.
- **Score von Liste 2:** `P_A(substellar) × P(m2 < 13 M_Jup)`, nur für Sterne mit `ms_offset < 0,2`. Die frühere Rückfallregel (Sternmasse unter 0,6 M_sun, unter 100 pc) gilt nur, falls das Feature seine Mindestgüte nicht erfüllt hätte; das ist nicht der Fall.
- **Nachbar-Filter (beide Listen):** Sterne mit einem Gaia-Nachbarn innerhalb von 2" (im Katalog des jeweiligen Releases) werden aus den Listen ausgeschlossen. Im Backtest lag die Trefferquote in den Top 2.000 mit Nachbar bei 0,9 % gegenüber 8,6 % ohne (Verhältnis 0,11, Fisher p < 0,0001); die vorab festgelegte Regel (Verhältnis höchstens 0,5, p < 0,01) ist erfüllt.
- **Grenze:** Liste 2 ist im Backtest mit nur 17 Treffern kaum validierbar. Sie ist bewusst eine Wette ins Unbekannte.

### Modell A: festgelegte Variante

Modell A ist die **Physik-Variante mit 9 Merkmalen**: `ruwe_z`, `ruwe_excess`, `astrometric_excess_noise_sig`, `wobble_ratio`, `ms_offset`, `chi2_per_dof`, `bp_rp`, `abs_g`, `pm_total`. Das Modell der Wette ist der Mittelwert der fünf Regions-Modelle aus der Kreuzvalidierung (`ablation_physics_fold0-4`), gewählt vor der ersten Anwendung auf DR3.

Begründung (offen benannt: die Wahl fällt nach Blick auf die Ablationen; Leistung aller Varianten liegt im Streuungsbereich der Regionen, AP 0,037–0,043 gegenüber 0,032–0,058 je Region, sie wurde nicht nach der besten Zahl getroffen):
- Gleiche Leistung im Rahmen der Streuung, weniger Merkmale, einfacher zu erklären.
- Die ausgelassenen Merkmale (Parallaxen-Genauigkeit, Helligkeit, Beobachtungszahlen, Sichtbarkeitsperioden, rohe Wackelwerte, `parallax_over_error`) wachsen oder schrumpfen mit der Messdauer der Releases (22, 34, 66 Monate). Das Modell würde sonst bei der Übertragung in Bereiche geraten, die es im Training nie gesehen hat.
- `wobble_ratio` bleibt drin, weil es die Messdauer des Releases explizit einrechnet (Periode gleich Messdauer) und das erwartete Fenster (auffällig, aber nicht zu stark) abbildet.
- Die Variante mit 6 Merkmalen (ohne `wobble_ratio`, `abs_g`, `pm_total`) ist ähnlich gut, wird aber nicht gewählt, weil `wobble_ratio` für Liste 2 gebraucht wird.

Bekanntes Risiko, das durch die Ablationen nicht sinkt: Die Auswahl von Gaia (erhöhtes Astrometrie-Rauschen) steckt in den Wackel-Statistiken selbst. Ein Modell, das das Wackeln nutzt, lernt diese Schwelle mit. Es überträgt sich auf DR4 nur, wenn Gaia dort ähnliche Schwellen benutzt.

### Ziel von Liste 2 (Ergänzung 0.15)

Die Liste 2 lässt nur Sterne mit `ms_offset < 0,2` zu. Von den 17 Backtest-Zielen unter 13 M_Jup erfüllen nur 4 diese Bedingung (DR3-Werte); die anderen 13 liegen 0,41 bis 0,91 mag über der Hauptreihe, wie unaufgelöste Doppelsterne mit zu klein geschätzter Masse. Gemessen am Ziel ohne Bedingung würde Liste 2 schlecht abschneiden, weil die meisten Treffer des Ziels Sterne sind, die sie nicht auswählen darf. Deshalb gilt für Liste 2 als Hauptziel: DR4-Bahn, geschätzte Masse unter 13 M_Jup **und** `ms_offset < 0,2` (berechnet mit den DR4-Werten nach der Methode dieses Manifests). Das bisherige Ziel ohne die Bedingung wird zusätzlich berichtet. Im Backtest entspricht das 4 Zielen (bzw. 430 von 1.306 für das Ziel unter 80 M_Jup mit derselben Bedingung), also einer Tendenz ohne Signifikanzaussage. Beide Fassungen und diese Begründung stehen vor der Anwendung auf DR4 fest.

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

### Konkurrenz-Listen (festgelegt vor dem Release)

Die drei Listen liegen als Parquet mit `int64`-Gaia-IDs und SHA-256-Prüfsumme vor (`docs/competitors.json`, Abruf 2026-09-25):

| Liste | Quelle | Umfang | Ordnung für die Auswertung |
|---|---|---|---|
| ExoDNN | Abreu et al. (2025), A&A 704, A150, VizieR `J/A+A/704/A150/exodnnv1` | 7.414 Sterne (unter 100 pc, F–M) | `PredProb1` absteigend, Gleichstand nach `source_id` |
| Kiefer et al. | Kiefer et al. (2025), A&A 702, A77, VizieR `J/A+A/702/A77/tableb1` | 9.698 Kandidaten (G < 16, Begleitermasse unter 13,5 M_Jup) | `s_RUWE` absteigend, dann `Mplmin` aufsteigend, dann `source_id`. Der Katalog ist eine Menge und keine Rangliste; die Ordnung ist unsere dokumentierte Festlegung |
| Sahlmann & Gómez | Sahlmann & Gómez (2025), MNRAS 537, 1130, Tabelle 4 (arXiv 2404.09350v2) | 22 Zeilen, abzüglich der zwei von Gaia zurückgezogenen Lösungen (54 Cas, BD+75 510) = 20 | ungeordnete Menge; P@20 als Anteil der 20 |

Die Tabelle von Sahlmann & Gómez wurde aus dem Text des PDF gelesen (`pdftotext`), nicht aus einer maschinenlesbaren Quelle; sie wurde durch Zeilenzahl und die beiden zurückgezogenen Lösungen geprüft. Alle drei Listen benutzen DR3-Daten, wie unsere Listen, und lassen sich deshalb nur in der Auswertung DR3→DR4 vergleichen, nicht im Backtest DR2→DR3 (dort wäre es Leakage).

Abdeckung in unserer Grundgesamtheit (`parallax_over_error >= 10`): ExoDNN 7.414 von 7.414, Kiefer 9.470 von 9.698, Sahlmann & Gómez 18 von 20. Davon haben 25, 26 und 8 Sterne schon eine DR3-Bahn unter 80 M_Jup oder sind bekannte Planetensterne.

Asymmetrie, die im Bericht stehen muss: Die Liste von Sahlmann & Gómez besteht aus Sternen mit DR3-Bahnlösung, die sie als Planeten- oder Braune-Zwerg-Kandidaten einordnet. Sie sind nach unserer Regel „neue Treffer“ bekannte Fälle; ihre Liste wird deshalb nur in der Fassung „alle Treffer“ verglichen. ExoDNN sagt „Doppelstern-Begleiter“ voraus, nicht substellare Begleiter; Kiefer et al. suchen Planeten mit 1–3 AE, andere Grenzen als wir.

### Zusätzliche Benchmarks (festgelegt vor den Ergebnissen)

Alle Methoden werden im Backtest und später bei DR4 mit denselben Ausschlüssen ausgewertet und jeweils **einmal mit und einmal ohne Nachbar-Filter** (2", im Katalog des Ausgangsreleases; Nachbarn werden für die obersten 3.000 Sterne jeder Methode abgefragt, das genügt für P@100 und P@1000).

1. **Handgebaute Regel ohne ML** (`rule_based`): Sterne mit `ruwe_z > τ` und `wobble_ratio < 1`, sortiert nach `ruwe_z` absteigend (Nachbar-Filter wie oben). τ wird im Backtest aus {2, 3, 4, 5, 6, 8} gewählt: die kleinste Schwelle mit dem größten P@1000 (mit Nachbar-Filter, Ziel `y80`, alle Treffer), danach festgeschrieben. **Festgeschrieben: τ = 2** (im Backtest hatte die Regel für jede Schwelle 0 Treffer in den Top 1.000, die Vorgabe „kleinste Schwelle mit dem größten P@1000“ ergibt dann die kleinste, τ = 2).
2. **Logistische Regression** (`logreg`) mit denselben 9 Merkmalen wie Modell A: fehlende Werte durch den Median ersetzt, an den Perzentilen 0,5 und 99,5 des Trainingsteils gekappt, standardisiert, `C = 0,1`, ausgeglichene Klassengewichte; gleiches Protokoll wie Modell A (regionale Aufteilung, Negative 1:50).
3. **HGCA-Liste** (`hgca`): Sterne mit HGCA-Werten, sortiert nach der Signifikanz der Beschleunigung `hg_sig_gaia` absteigend (im Backtest die HGCA-Version auf DR2-Basis, bei DR4 die EDR3-Version). Verglichen wird nur auf der Teilmenge der Sterne mit HGCA-Werten: HGCA-Liste gegen Modell A und die Baselines, alle nur auf diesen Sternen; zusätzlich die Abdeckung (Anteil der Ziele mit HGCA-Werten).
4. **Konfidenzintervalle:** Bootstrap über HEALPix-Level-2-Zellen (192 Zellen, Ziehen mit Zurücklegen), 95-%-Intervall aus den Perzentilen 2,5 und 97,5, für P@100, P@1000 und Average Precision; im Backtest im Entwicklungslauf mit 200, in der endgültigen Auswertung mit 1.000 Wiederholungen.
5. **Ohne Verknüpfung:** Das Auswertungsskript gibt aus, wie viele Sterne jeder Liste keine Verknüpfung zum späteren Release haben. Sterne ohne Verknüpfung zählen als negativ, die Zahl steht aber im Bericht.
6. **Sahlmann & Gómez** (ungeordnete Menge von 20, davon 18 in unserer Grundgesamtheit): Metrik ist die Trefferquote der 18 Sterne (Treffer geteilt durch 18) im Vergleich zur Trefferquote unserer Top 18 (Fassung „alle Treffer“, Ziel `y80`).

## Auswertungsskript

Das Skript `src/gaia_wobble/evaluate_bet.py` wird zusammen mit den Listen eingefroren (derselbe Git-Tag). Es enthält alle Entscheidungen, die sonst erst nach dem Release fielen:
- **Verknüpfung DR3→DR4:** nur über `dr3_neighbourhood`; bei mehreren Kandidaten gewinnt der kleinste Winkelabstand, bei Gleichstand der kleinste Betrag des Helligkeitsunterschieds. Ein Stern ohne Verknüpfung hat kein Ergebnis und zählt als negativ.
- **Ziele:** `y80`, `y13`, `y13_ms` (Hauptziel Liste 2), `y80_ms`; `OrbitalTargetedSearch*`, `OrbitalAlternative*` und Bahnen ohne Massenschätzung sind ausgeschlossen (Label unbekannt), gezielte Suchen werden getrennt gezählt. Die Massenschätzung ist die aus `masses.py`; `ms_offset` für `y13_ms` kommt aus den DR4-Werten mit derselben Methode wie in DR2 und DR3 (Hauptreihe je Release aus dem eigenen Nahsternkatalog).
- **Metriken:** alle Kennzahlen des Manifests je Liste, je Ziel, jeweils „alle Treffer“ und „nur neue Treffer“, nach Helligkeitsklassen, dazu die Baselines RUWE und `ruwe_z` und, falls beschafft, die Konkurrenz-Listen.
- **Probelauf:** Auf den Backtest-Daten (DR2-Scores gegen das DR3-Ziel) liefert das Skript die bereits im Log stehenden Zahlen; ein Test (`test_evaluate_bet.py`) prüft das.
- **Grenze:** Die DR4-Seite (Laden der Tabellen) ist nicht testbar, bevor DR4 existiert. Das erwartete Format steht im Kopf des Skripts, `check_dr4_schema` bricht bei abweichenden Tabellen mit einer klaren Meldung ab. Anpassungen an das echte DR4-Schema sind nach dem Release erlaubt, wenn sie sich nur auf Dateinamen und Spaltennamen beziehen; sie werden als „Schema-Anpassung“ mit dem Diff im Experiment-Log veröffentlicht. Jede inhaltliche Änderung (Ziele, Metriken, Verknüpfungsregel) gilt als Nachtrag und wird gekennzeichnet.

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
| 0.12 | 2026-09-25 | P@1000 als praxisnahe Zwischenstufe aufgenommen; Features `ms_offset`, `wobble_ratio`, `mass_ms` (physikalisch motiviert, je Release aus eigenen Daten) in die gemeinsamen Merkmale; Training mit regionaler Aufteilung (HEALPix) | Baseline: Extremwackler sind Doppelsterne, das Modell braucht ein Fenster; Gaias Messfehler sind regional korreliert |
| 0.13 | 2026-09-25 | Modell A = Physik-Variante (9 Merkmale, Mittel der fünf Regions-Modelle); `ms_offset < 0,2` als Bedingung für Liste 2 | Ablationen: gleiche Leistung im Streuungsbereich; Beobachtungszahlen und Parallaxen-Fehler verändern sich mit der Messdauer der Releases; das Modell bevorzugt Sterne über der Hauptreihe, bestätigte dunkle Begleiter liegen darauf |
| 0.14 | 2026-09-25 | Amplituden-Feature nach Mindestgüte angenommen, Score von Liste 2 festgelegt; Nachbar-Filter (2") für beide Listen | Mindestgüte (Median 0,58 in 0,5–2, ρ 0,92 > 0,6) erfüllt; Nachbar-Test im Backtest erfüllt die vorab festgelegte Regel (Verhältnis 0,11, p < 0,0001) |
| 0.15 | 2026-09-25 | Hauptziel von Liste 2 um `ms_offset < 0,2` ergänzt; Ziel ohne die Bedingung zusätzlich berichtet | 13 von 17 Backtest-Zielen unter 13 M_Jup liegen 0,41–0,91 mag über der Hauptreihe (vermutlich leichte Doppelsterne) und sind für Liste 2 ausgeschlossen; Liste und Ziel sollen dieselbe Idee umsetzen |
| 0.16 | 2026-09-25 | Auswertungsskript und seine Entscheidungen (Verknüpfung, Ziele, Ausschlüsse, Schema-Anpassung) festgeschrieben | Sonst würden diese Entscheidungen erst nach dem Release fallen |
| 0.17 | 2026-09-25 | Konkurrenz-Listen (ExoDNN, Kiefer et al., Sahlmann & Gómez) beschafft, mit Prüfsumme abgelegt, Ordnungsregeln und Vergleichsbedingungen festgelegt | Vor dem Release festlegen, sonst wirken Ordnung und Auswahl nachträglich gewählt |
| 0.18 | 2026-09-25 | Zusatz-Benchmarks (handgebaute Regel, logistische Regression, HGCA-Liste), Bootstrap über HEALPix-Zellen, Auswertung mit und ohne Nachbar-Filter, Zahl der Sterne ohne Verknüpfung, eigene Metrik für Sahlmann & Gómez | Vor den Ergebnissen festgelegt, damit sie nicht nachträglich gewählt wirken |
| 0.19 | 2026-09-25 | Schwelle der handgebauten Regel festgeschrieben (τ = 2) | Ergebnis der im Manifest 0.18 festgelegten Auswahlregel im Backtest |
