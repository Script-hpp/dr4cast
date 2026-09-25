# Plan: Simulation für Liste 2 (Zusatzauswertung)

Festgelegt und committet **vor** dem ersten Simulationslauf. Stand: 2026-09-25.

**Rahmen.** Nach Regel 4 des Manifests (Abschnitt „Wie dieses Dokument funktioniert“) kann es nach dem Einfrieren keine offizielle Version 2 der Wette mehr geben. Die Simulation ist eine **Zusatzauswertung für den Bericht**. Sie ändert weder die Listen in `release/v1/` noch `MANIFEST.md` noch `evaluate_bet.py`. Modell A bleibt eingefroren: Es wird nur angewendet, nie trainiert. Ergebnisse stehen im Experiment-Log als „Simulation (Zusatzauswertung)“ und werden nirgends als Ersatz für die eingefrorene Liste 2 bezeichnet.

**Frage.** Sortiert eine Variante des Liste-2-Scores mit Amplituden-Korrektur und simulationskalibrierter `P(m2 < 13 M_Jup)` simulierte Planeten weiter nach oben als der Liste-2-Score v1?

## 0. Was heute nicht bekannt ist (wird in Schritt 1 geprüft, nicht angenommen)

- Die Schnittstelle von `astromet` (Version 1.1.9): welche Funktion aus Bahnelementen, Entfernung und Scan-Muster eine Gaia-artige Anpassung mit RUWE liefert, ob `astrometric_excess_noise` und `astrometric_chi2_al` ausgegeben werden, und wie das Scan-Muster angegeben wird. Quelle wird die Dokumentation und der Quelltext des Pakets sein.
- Welchen Zeitraum das eingebaute Scan-Muster abdeckt. Das Scan-Muster von DR4 (66 Monate) ist nach unserem Wissen nicht vollständig öffentlich; die Vorgabe lautet „Scan-Muster als Näherung“. Die Näherung wird beschrieben und ihr Einfluss (34 Monate gegen 66 Monate) im Bericht als Grenze genannt.
- Die Bahnelemente von Gaia-4 b und Gaia-5 b (Quelle: NASA Exoplanet Archive und die Entdeckungsarbeiten); fehlende Elemente werden im Log genannt und über Bereiche variiert.
- Die Rechenzeit je System. Sie wird in Schritt 1 gemessen; alle Größen unten sind Obergrenzen, die dieser Messung angepasst werden (mit Vermerk im Log), nicht nach oben.

`astromet` steht unter GPL-3.0. Es wird als externe Abhängigkeit installiert (`uv`-Extra `simulation`), nicht in das Repository kopiert; der eigene Code bleibt MIT.

## 1. Realitätscheck (zuerst; ohne bestandenen Check keine Produktion)

1. **Nullprobe:** Für 20.000 echte Kandidatensterne (siehe Schritt 2) je einen Einzelstern simulieren, mit dem Rauschen aus `amplitude.py` (`σ_formal` je Helligkeit und Farbe). Simulierte und echte Verteilung von RUWE müssen zusammenpassen: Median und 90. Perzentil des simulierten RUWE liegen innerhalb von 10 % der echten Werte. Sonst wird das Rauschmodell angepasst und der Check wiederholt, höchstens dreimal; danach Abbruch mit Bericht.
2. **Gaia-4 b (11,8 M_Jup) und Gaia-5 b (20,9 M_Jup):** Je 1.000 Simulationen mit Bahnneigung, Bahnphase und Scan-Ausrichtung zufällig, Bahnelemente aus den Literaturwerten. Der echte DR3-RUWE beider Sterne muss zwischen dem 5. und 95. Perzentil des simulierten RUWE liegen. Gleiches für `astrometric_excess_noise`, falls die Simulation es liefert.
3. **Merkmale von Modell A:** Für die neun Merkmale von Modell A wird festgehalten, welche die Simulation direkt liefert (`ruwe`, damit `ruwe_z` und `ruwe_excess` über das Kalibriergitter von DR3; `chi2_per_dof ≈ RUWE²` bei `u0 ≈ 1`) und welche nicht (`astrometric_excess_noise_sig`, `wobble_ratio`). Wenn ein Merkmal nicht simuliert werden kann, wird es aus einem dokumentierten Modell abgeleitet (Amplitude des Photozentrums mal Skalierung aus `amplitude.py`) und dieser Ersatz wird im Bericht genannt. Leuchtende Begleiter verschieben `ms_offset`, `abs_g` und `bp_rp` über das Helligkeitsverhältnis; dunkle Begleiter nicht.
4. **Zeitmessung:** Sekunden je System; daraus die Größe der Produktion.

Bestehen Punkt 1 oder 2 nicht, wird die Simulation **nicht** für die Score-Frage benutzt. Das steht dann so im Bericht.

## 2. Simulierte Systeme

- **Etwa 300.000 Systeme:** je etwa 100.000 Planeten (Begleitermasse bis 13 M_Jup), Braune Zwerge (13 bis 80 M_Jup) und leuchtende Doppelsterne (Begleiter über 80 M_Jup mit Helligkeit aus der Hauptreihe).
- **Wirtssterne:** 20.000 bis 50.000 echte Sterne aus den Kandidaten für Liste 2 (DR3, `parallax_over_error >= 10`, `ms_offset < 0,2`, ohne bekannte Fälle), je Stern mehrere unabhängige Systeme. Für jeden simulierten Stern werden Modell A und beide Scores auf den simulierten Merkmalen berechnet; die echte Population dient als Hintergrund für die Ränge.
- **Verteilungen (Prior):** Massen- und Periodenverteilung der Klassen nach bekannten Häufigkeiten aus Radialgeschwindigkeits-Surveys, mit Braune-Zwerge-Wüste, Doppelstern-Verteilungen für die leuchtenden Systeme. Die Zahlen und Quellen kommen in `configs/simulation_priors.yaml` und werden **vor dem Produktionslauf** committet, jede Zahl mit Quellenangabe. Kandidaten für die Quellen (noch nicht gelesen): Cumming et al. 2008 (Planeten), Grether & Lineweaver 2006 (Wüste), Raghavan et al. 2010 und Moe & Di Stefano 2017 (Doppelsterne). Bis sie gelesen sind, steht in der Datei keine Zahl.
- **Beobachtung:** Messdauer wie DR4 (66 Monate), Scan-Muster als Näherung (Schritt 0); Bahnperioden 0,1 bis 30 Jahre; Neigung isotrop.
- **Klassenanteile:** Die Klassen sind gleich groß (je 100.000) und nicht natürlich gewichtet. Alle Kennzahlen gibt es je Klasse. Eine Variante mit natürlichen Häufigkeiten aus den Quellen wird zusätzlich berichtet und als unsicher gekennzeichnet.
- **Zufall:** feste Startwerte je Lauf (im Konfigurationsstand festgehalten), Halbierung der Systeme in Kalibrier- und Testhälfte nach Wirtsstern (kein Stern in beiden).

## 3. Verglichene Scores

- **v1:** `P_A · P(m2 < 13)` wie in `release/v1/list2_planets.csv` (gleicher Code aus `amplitude.py`).
- **v2 (nur Vergleich):** (a) Amplitude durch 0,58 geteilt (der im Backtest gemessene Median von `a_est / a0`, siehe Experiment-Log); (b) `P(m2 < 13)` durch eine Kalibrierung ersetzt, die aus der Kalibrierhälfte lernt, wie oft simulierte Systeme mit gegebener geschätzter Amplitude, Parallaxe und Sternmasse wirklich unter 13 M_Jup liegen (isotone Regression auf einer skalaren Größe; genaue Größe wird im Code festgehalten, bevor die Testhälfte angesehen wird). Score v2 = `P_A · P_kalibriert`.

## 4. Auswertung (Kriterien vor den Ergebnissen)

- **Hauptmaß:** Anteil der simulierten Planeten der Testhälfte, die unter den obersten 1 % der Scores der Testpopulation (simulierte plus echte Sterne) liegen, je Score. **Nebenmaße:** mittlerer Rangprozentwert der Planeten; Treffer je 10.000 Sterne in den obersten 100 der Population; alles je Klasse (Planeten, Braune Zwerge, Doppelsterne).
- **Entscheidung:** v2 „sortiert Planeten weiter nach oben“, wenn das Hauptmaß bei v2 höher ist und das 95-%-Intervall der Differenz (gepaarter Bootstrap über Wirtssterne, 1.000 Wiederholungen) die Null nicht enthält. Sonst wird berichtet, dass sich kein Unterschied zeigt. Sortieren sie außerdem Doppelsterne höher (Anteil der Doppelsterne in den obersten 1 %), wird das genannt.
- **Was das nicht heißt:** Ein besserer Score v2 in der Simulation ist kein Beleg für das Verhalten bei DR4, weil die Simulation Prior, Rauschmodell und Scan-Muster annimmt. Er zeigt nur, ob die bekannte Verzerrung der Amplitude in der Simulation ein Problem ist.

## 5. Größen und Stabilität

1. Produktion mit 300.000 Systemen (Obergrenze, siehe Schritt 0).
2. **Stabilitätstest** mit 600.000 Systemen und anderem Startwert: Hauptmaß und die Entscheidung müssen sich innerhalb der Intervalle wiederholen. Ist das nicht der Fall, wird berichtet, dass die Simulation die Frage nicht beantwortet.
3. **Empfindlichkeitskarten** (Masse × Periode × Entfernung × Sterntyp) nur nach bestandenem Stabilitätstest und mit 1 bis 3 Millionen Systemen. „Wiedergefunden“ heißt: Score größer als der Score des 100. Sterns der Liste 2 im DR3-Lauf.

## 6. Ablage

Code unter `src/gaia_wobble/simulation/`, Konfiguration unter `configs/`, Ergebnisse (Tabellen, Startwerte, Prüfsummen der Zwischendaten) unter `data/` (nicht im Repository) und Zusammenfassungen im Experiment-Log. Jede Abweichung von diesem Plan wird mit Begründung im Log vermerkt, bevor die betroffene Auswertung läuft.

## Befund Schritt 0 (2026-09-25, vor jedem Simulationslauf)

`astromet` 1.1.9 wurde in einer Wegwerf-Umgebung installiert und der Quelltext gelesen (`fits.py`, `tracks.py`). Was das Paket liefert und was nicht:

- **Liefert:** die Bahn eines Sterns mit Begleiter über die Klasse `params` (Beschreibung des Systems: Periode in Jahren, große Halbachse in AU, Exzentrizität, Massenverhältnis `q`, Lichtverhältnis `l`, Orientierung `vtheta`, `vphi`, `vomega`, Periastronzeit, Parallaxe, Eigenbewegung), eine Nachahmung der Gaia-Anpassung (`gaia_fit`) und die Ausgabe in Gaia-Spaltennamen (`gaia_results`): `astrometric_excess_noise`, `astrometric_chi2_al`, `astrometric_n_good_obs_al`, `astrometric_n_obs_al`, `visibility_periods_used` und `uwe`. Die Fehler einer Einzelmessung nach Helligkeit stammen aus den mitgelieferten Daten (`scatteral_edr3.csv`).
- **Liefert nicht:** das Scan-Muster. `gaia_fit` erwartet Beobachtungszeiten `ts` und Scan-Winkel `phis` als Eingabe; das Paket bringt keine Scanning-Law für DR3 oder DR4 mit (Abhängigkeiten: `numpy`, `astropy`, `scipy`). Die „Näherung des Scan-Musters“ aus dem Plan müssen wir also selbst bauen (Beobachtungszeiten und Winkel für 66 Monate). Das ist die größte Modellannahme der Simulation und wird vor dem Realitätscheck im Code und im Log beschrieben.
- **`uwe` ist nicht `RUWE`.** Die Normierung `u0(G, Farbe)` von Gaia fehlt. Ersatz (wird im Bericht genannt): `RUWE_sim = uwe / Median(uwe der simulierten Nullprobe bei gleicher Helligkeit)`. Die Nullprobe aus Schritt 1 liefert diese Normierung.
- **`astrometric_excess_noise_sig`** wird nicht ausgegeben. Ersatz: empirische Abbildung von `astrometric_excess_noise` auf die Signifikanz über die Nullprobe.

Die Schritte 1 bis 4 des Plans bleiben unverändert. Zum Realitätscheck kommt hinzu, dass die Nullprobe (Schritt 1, Punkt 1) auch die beiden Ersatzgrößen kalibriert. Gaia-4 b und Gaia-5 b werden mit den Bahnelementen aus dem NASA Exoplanet Archive und den Entdeckungsarbeiten simuliert (noch nicht abgerufen).

## Scan-Muster: Entscheidung (2026-09-25, vor jedem `astromet`-Lauf)

**Quelle:** das Paket `gaiascanlaw` 0.2.0 (Penoyre, vom Autor von `astromet`; GPL-3.0, externe Abhängigkeit im `uv`-Extra `simulation`, nicht ins Repository kopiert). Es liefert für eine Position (Rektaszension, Deklination) die Zeiten und Winkel der nominellen Gaia-Übergänge, seine Daten stammen aus dem Gaia Observation Forecast Tool (GOST) der ESA. Eine händische Abfrage von GOST ist damit nicht nötig. Die Zeiträume kennt das Paket selbst: Beginn 2014,563, Ende von DR3 2017,404 (`tdr3`), Ende von DR4 2020,054 (`tdr4`), Ende der Daten 2025,039 (`tdr5`). Der DR4-Zeitraum (66 Monate) ist also abgedeckt; die Näherung ist nicht die Zeit, sondern dass es das **nominelle** Scan-Gesetz ist (die tatsächliche Ausrichtung des Satelliten weicht laut Dokumentation der verwandten `scanninglaw`-Pakete bis zu etwa 30 Bogensekunden ab, was hier keine Rolle spielt).

**Gelesen bzw. geprüft:** README von `gaiascanlaw`, seine Konstanten und die Signatur `scanlaw(ra, dec, tstart, tend, ccd_row, obstype)`. Vergleich mit den echten DR3-Zahlen für die beiden Kontrollplaneten:

| Stern | echte Übergänge in DR3 (`astrometric_n_obs_al / 9`) | Vorhersage DR3-Zeitraum (alle / nur Astrometrie) | Vorhersage DR4-Zeitraum |
|---|---|---|---|
| Gaia-5 | 47 | 47 / 43 | 98 / 94 |
| Gaia-4 | 52 | 57 / 45 | 111 / 99 |

Die nominelle Vorhersage trifft die Übergangszahl im Rahmen von etwa 10 %, im DR4-Zeitraum sind es rund doppelt so viele wie in DR3, wie bei 66 statt 34 Monaten zu erwarten.

**Regel (festgelegt):**
1. `obstype='astrometry'` (schließt bekannte Datenlücken aus).
2. Für jeden Wirtsstern werden die nominellen Übergänge im DR3-Zeitraum zufällig auf die **echte** Zahl der Übergänge des Sterns in DR3 (`astrometric_n_obs_al / 9`) ausgedünnt (ohne Zurücklegen); ist die Vorhersage kleiner als die echte Zahl, werden alle genommen und der Stern in der Nullprobe markiert.
3. Für den DR4-Zeitraum werden die nominellen Übergänge mit demselben Anteil ausgedünnt (echte Zahl geteilt durch nominelle Zahl im DR3-Zeitraum), so dass Lücken, die im Mittel für diesen Stern gelten, erhalten bleiben. Die Zahl der Übergänge im DR4-Zeitraum ist damit eine Näherung, im Bericht als solche genannt.
4. Je Übergang neun Einzelmessungen (`nmeasure = 9`, wie in `astromet.mock_obs` und wie `astrometric_n_obs_al = 9 · Übergänge` im Katalog).

Der Realitätscheck (Schritt 1 des Plans) prüft zusätzlich, ob die nominelle Übergangszahl über die ganze Nullprobe zur echten passt (Median des Verhältnisses und 16./84. Perzentil werden im Log berichtet).

## Realitätscheck: Bestehenskriterien und Aufbau (2026-09-26, festgelegt vor der ersten berechneten Zahl)

**Aufbau der Simulation eines Sterns** (Code unter `src/gaia_wobble/simulation/`):
1. Beobachtungszeiten und Scan-Winkel nach der Regel im Abschnitt „Scan-Muster“ (gaiascanlaw, ausgedünnt auf die echte Übergangszahl).
2. Die Bahn des Photozentrums erzeugen wir selbst (Kepler-Gleichung, Thiele-Innes-Konvention von Gaia): `Δα* = B·X + G·Y`, `Δδ = A·X + F·Y` mit `X = cos E − e`, `Y = sqrt(1 − e²)·sin E`, Mittlere Anomalie `M = 2π (t − T_peri) / P`, `t` in Tagen seit J2010,0 (Konvention von `t_periastron` in DR3; wird am Kontrollfall geprüft). Grund: Thiele-Innes-Elemente gehen so ohne Umrechnung von Winkeln in die Simulation, und die Bahn ist nachprüfbar.
3. Je Übergang neun Messungen mit dem Fehler `astromet.sigma_ast(G)` (aus Lindegren et al. 2020, Abb. A.1 digitalisiert, im Paket mitgeliefert) und unabhängigem Rauschen; Projektion auf den Scan-Winkel `x = Δα*·sin φ + Δδ·cos φ`.
4. Anpassung mit `astromet.fit` (Nachahmung von AGIS); Ausgaben `uwe`, `excess_noise`, `chi2`, `n_good_obs`. Bekannte Eigenschaften des Pakets, die wir hinnehmen: `gaia_fit` ignoriert das übergebene `G` und den Bezugszeitpunkt (fest 12 und 2016,0; ohne Einfluss bei mindestens 6 Sichtbarkeitsperioden); der Fehler stammt aus einer digitalisierten Abbildung.
5. `RUWE_sim = uwe · k(G)`. Die Normierung `k(G)` je Helligkeitsintervall (0,5 mag) folgt aus der Nullprobe: Median des echten RUWE der Sterne im Intervall geteilt durch den Median des simulierten `uwe` der Nullprobe.

**Prüfungen** (jede mit festen Startwerten; Ergebnisse und alle Zahlen im Experiment-Log):

- **N: Nullprobe.** 2.000 echte Kandidatensterne (Liste-2-Population, geschichtet nach Helligkeit), je ein Einzelstern ohne Begleiter, Rauschen wie oben. Bestanden, wenn das 90. Perzentil des simulierten RUWE je Helligkeitsklasse (G < 10, 10 bis 13, 13 bis 16, ab 16) höchstens 10 % vom echten abweicht (der Median ist durch die Normierung festgelegt und zählt nicht). Sonst Rauschmodell anpassen (höchstens dreimal), danach Abbruch mit Bericht. Zusätzlich gemessen: Rechenzeit je System.
- **A: Gaias eigene DR3-Bahnlösungen der Kontrollplaneten.** Für Gaia-4 b (1457486023639239296) und Gaia-5 b (2074815898041643520) die `Orbital`-Lösung aus `nss_two_body_orbit` (Periode 564 und 358 Tage; Thiele-Innes-Elemente, Exzentrizität, Periastronzeit). 1.000 Rausch-Realisierungen je Stern, Bahn fest. **Bestanden**, wenn der echte DR3-RUWE (Gaia-4: 1,50; Gaia-5: 3,55) im mittleren 90-%-Bereich (5. bis 95. Perzentil) der simulierten Verteilung liegt. Gleiches für `astrometric_excess_noise` (echt 0,156 und 0,408 mas), berichtet.
- **B: Veröffentlichte Bahnelemente der Kontrollplaneten** (NASA Exoplanet Archive, Stefánsson et al. 2025). Gaia-4 b: P = 571,3 ± 1,4 d, e = 0,338 ± 0,026, i = 116,9° ± 4,2°, 11,8 M_Jup, Sternmasse 0,644 M_sun; Gaia-5 b: P = 358,62 ± 0,2 d, e = 0,6423 ± 0,0026, i = 129,7° ± 1,0°, 20,87 M_Jup, Sternmasse 0,339 M_sun. 1.000 Varianten: Periode, Exzentrizität, Neigung und Massen aus Normalverteilungen mit den veröffentlichten Unsicherheiten, `Ω`, `ω` und Periastronzeit gleichverteilt (nicht veröffentlicht), dunkler Begleiter, Entfernung aus der DR3-Parallaxe. **Bestanden** wie bei A (echter RUWE im 5. bis 95. Perzentil). Da die Winkel unbekannt sind, ist die Verteilung breit; ein Bestehen ist deshalb der schwächere Test als A.
- **C: Allgemeiner Check an 200 DR3-Bahnlösungen.** 200 zufällige Sterne mit `Orbital`-Lösung, geschichtet nach geschätzter Begleitermasse (5 logarithmische Klassen) und Helligkeit (4 Klassen); Bahn aus den Thiele-Innes-Elementen von Gaia, je Stern 20 Rausch-Realisierungen; Vergleich mit dem echten RUWE des Sterns. **Bestanden** nur, wenn alle drei Bedingungen gelten: (i) Spearman-Rangkorrelation zwischen dem Median des simulierten und dem echten RUWE über 0,6; (ii) Median des Verhältnisses (simuliert durch echt) zwischen 0,7 und 1,4; (iii) bei mindestens 70 % der Sterne liegt der echte RUWE im 5. bis 95. Perzentil der simulierten Verteilung. **Grenze:** Sterne mit Bahnlösung sind die mit gut messbarem Wackeln; ein Bestehen zeigt nicht, dass die Simulation bei schwachen Signalen genauso gut ist.

**Verwendung:** Die Simulation wird für die Score-Frage nur benutzt, wenn N, A und C bestanden sind. B ist der gezielte Einzelfall für den Planetenbereich: Besteht B nicht (bei bestandenen N, A und C), bleibt die Simulation zulässig, aber alle Aussagen für Planetenmassen tragen den Vermerk „im Einzelfall nicht bestätigt“. Besteht A oder C nicht, wird die Simulation nicht für die Score-Frage benutzt, sondern nur beschreibend berichtet.

### Änderung an Kriterium N (2026-09-26, vor jeder berechneten Zahl)

Das Kriterium N oben verglich das 90. Perzentil des simulierten mit dem des echten RUWE. Das ist ungeeignet: Die echte Population enthält echte Doppelsterne, Sterne mit Nachbarn und andere Störungen; sie bestimmen den oberen Rand der echten Verteilung, den eine Nullprobe aus Einzelsternen nicht enthält. Das Kriterium würde deshalb an der Population scheitern und nicht an der Simulation. Geändert (es wurde noch nichts berechnet):

- **N (neu):** Verglichen werden nur die Helligkeitsklassen G < 10, 10 bis 13 und 13 bis 16 (ab G = 16 ist ein großer Teil der echten Sterne durch Dichte und Rauschen gestört). Je Klasse muss das **75. Perzentil** des simulierten RUWE höchstens 10 % vom echten abweichen und die **Breite des mittleren Bereichs** (75. minus 25. Perzentil) höchstens 25 %. Der Median ist durch die Normierung festgelegt und zählt nicht. Das 90. und 99. Perzentil und die Klasse ab G = 16 werden berichtet, zählen aber nicht. Die Nullprobe wird auf die drei Klassen geschichtet (je 700 Sterne, 2.100 insgesamt).
- Die Normierung `k(G)` benutzt weiter alle vier Helligkeitsklassen. Für G ≥ 16 ist sie eine Extrapolation der Fehlerkurve über den Bereich hinaus, den Kiefer et al. angeben, und wird so vermerkt.

## Ergänzungen zum Realitätscheck und zur Auswertung (2026-09-26, vor der ersten berechneten Zahl)

Diese Punkte präzisieren oder ergänzen den Plan oben; wo sie ihm widersprechen, gelten sie.

**1. Bestehenskriterium mit Varianten aus den Unsicherheiten.**
- Je Stern werden viele Varianten der Bahn gezogen, die zu den Unsicherheiten der Bahnelemente passen: bei den DR3-Bahnlösungen aus den veröffentlichten Fehlern der Thiele-Innes-Elemente (`a_thiele_innes_error` usw.), der Periode, Exzentrizität und Periastronzeit, als unabhängige Normalverteilungen (die Korrelationen `corr_vec` liegen bei uns nicht vor; die Verteilung ist damit etwas zu breit oder zu schmal, das wird genannt); bei den Elementen aus den Entdeckungsarbeiten aus den dort veröffentlichten Unsicherheiten (Check B). Je Variante zusätzlich unabhängige Rausch-Realisierungen.
- Ein Stern besteht, wenn sein echter DR3-RUWE im mittleren 90-%-Bereich (5. bis 95. Perzentil) der so entstandenen simulierten Verteilung liegt.
- Über viele Sterne werden berichtet: der **Anteil der Sterne im 90-%-Bereich** (Sollwert etwa 90 %; ein perfekt kalibriertes Modell träfe ihn) und der **Median des Verhältnisses simuliert durch echt**. Die Schwelle 70 % in Bedingung (iii) von C ist eine Untergrenze für „die Simulation ist brauchbar“; der Abstand zu 90 % wird berichtet und nicht wegdiskutiert.

**2. Breiter Check.** C zieht 200 zufällige DR3-`Orbital`-Lösungen, geschichtet nach geschätzter Begleitermasse (5 Klassen), Helligkeit (4 Klassen) **und Periode** (3 Klassen: unter 200 d, 200 bis 500 d, über 500 d), zufällig innerhalb der Zellen; fehlt eine Zelle, wird aus den nächsten aufgefüllt. Gaia-4 b und Gaia-5 b werden zusätzlich als Einzelfälle geprüft: A (ihre DR3-Bahnlösungen) und B (die Elemente aus den Entdeckungsarbeiten), wie oben. Beide Sterne sind aus der Stichprobe von C ausgeschlossen und werden nirgends zum Anpassen benutzt.

**3. Kalibrier- und Testteil (gegen Überanpassung).**
- Die 200 Vergleichssterne von C und die 2.100 Sterne der Nullprobe werden vorab in einen Kalibrier- und einen Testteil geteilt, 50/50, nach Stern (kein Stern in beiden), Startwert 20260926 (`numpy.random.default_rng`). Die Teilung wird vor dem ersten Lauf erzeugt und mit Prüfsumme der ID-Listen abgelegt.
- **Angepasst werden darf nur** (mit dem Kalibrierteil von Nullprobe und C): (a) die Normierung `k(G)` je Helligkeitsintervall, (b) ein globaler Faktor `s` für den Messfehler `σ_AL` aus dem Raster {0,8; 0,9; 1,0; 1,1; 1,25; 1,5}, gewählt so, dass das 75. Perzentil des simulierten RUWE in der Nullprobe des Kalibrierteils dem echten am nächsten kommt (Klassen G < 16).
- **Alles andere bleibt fest:** Scan-Regel, Bahn-Generator und Zeitkonvention, Zahl der Messungen je Übergang, alle Kriterien und Schwellen, Startwerte.
- **Fehlerklausel:** Stellt sich ein Umsetzungsfehler heraus (etwa eine falsche Zeitkonvention der Periastronzeit), darf er korrigiert werden, wenn er im Log mit Begründung steht und der Check danach nur am Kalibrierteil neu läuft; der Testteil wird erst mit dem endgültigen Stand ausgewertet und **einmal** angesehen. Alle Kriterien (N, A, B, C) werden am Testteil bewertet; A und B sind unabhängig von der Teilung.

**4. Nullprobe als Gegenkontrolle.** Kriterium N (geändert oben) gilt: Sterne ohne Begleiter, RUWE-Verteilung nach Helligkeit gegen die echte Verteilung ruhiger Sterne, bewertet am Testteil.

**5. Alle astrometrischen Merkmale von Modell A vergleichen.** Nicht nur RUWE, sondern für jeden Stern der Prüfungen N und C die simulierten Werte von `ruwe_z`, `ruwe_excess`, `astrometric_excess_noise_sig`, `chi2_per_dof` und `wobble_ratio` gegen die echten Werte (Median des Verhältnisses und Rangkorrelation je Merkmal; für die Nullprobe Verteilungen nach Helligkeit). Ableitung aus der Simulation:
- `chi2_per_dof = chi2 / (n_good − 5)` direkt aus der Anpassung; `RUWE_sim` wie oben.
- `ruwe_expected` und `ruwe_sigma` aus dem DR3-Kalibriergitter (`data/processed/ruwe_grid_dr3.parquet`) mit Helligkeit und Farbe des echten Sterns; `ruwe_excess = RUWE_sim − ruwe_expected`, `ruwe_z = ruwe_excess / ruwe_sigma`.
- `astrometric_excess_noise_sig` gibt `astromet` nicht aus. Ersatz: monotone (isotone) Abbildung von `AEN_sim / σ_formal(G, Farbe)` auf die echte Signifikanz, angepasst an den echten Sternen des **Kalibrierteils**; bewertet am Testteil.
- `wobble_ratio = AEN_sim / a1_max` mit `a1_max` wie im Merkmal (Sternmasse `mass_ms`, Parallaxe, Messdauer des Releases). Der echte Wert nutzt den Katalog-`astrometric_excess_noise`, der bei G > 13 oft fälschlich 0 ist (Kiefer et al.); dieser Unterschied wird beim Vergleich genannt.
Ein Merkmal gilt als „nicht reproduziert“, wenn sein Median-Verhältnis außerhalb von 0,7 bis 1,4 liegt oder seine Rangkorrelation unter 0,6; das wird berichtet und begrenzt die Aussagen, die auf diesem Merkmal beruhen.

**6. Score-Vergleich für Liste 2: keine freie Optimierung.** Getestet werden nur die zwei Änderungen im Abschnitt „Verglichene Scores“: Amplitude geteilt durch 0,58 und `P(m2 < 13)` durch die isotone Kalibrierung ersetzt (angepasst am Kalibrierteil der Simulation, bewertet am Testteil). Keine weiteren Varianten, kein Ausprobieren von Schwellen oder Faktoren. Die Antwort wird immer an echten Daten gegengeprüft, bevor sie berichtet wird:
- Ränge von Gaia-4 b und Gaia-5 b im Score v1 und v2 (echte DR3-Sterne, Grundgesamtheit wie in den Listen),
- Ränge der dunklen Backtest-Ziele (`y13_ms`, 4 Sterne mit den DR2-Werten des Backtests) in v1 und v2,
- Anreicherung mit DR3-Beschleunigungs-Lösungen in den Top 100 und Top 1.000 (Liste-2-Population, ohne bekannte Fälle) in v1 und v2.
„v2 sortiert Planeten weiter nach oben“ gilt nur, wenn keiner dieser drei realen Tests klar gegen v2 spricht: Gaia-4 b und Gaia-5 b beide mehr als doppelt so weit hinten wie in v1, oder die Anreicherung in den Top 1.000 unter der Hälfte von v1. Sonst wird berichtet: „die Simulation und die echten Daten widersprechen sich“.

**7. Robustheit der Häufigkeitsannahmen.** Hauptlauf mit gleich großen Klassen. Zusätzlich zwei Varianten, in denen die simulierten Planeten gegenüber den Braunen Zwergen mit halbem und mit doppeltem Gewicht in die Auswertung eingehen (Gewichtung der vorhandenen Systeme; die Zahl der Doppelsterne bleibt unverändert). Berichtet wird, ob Vorzeichen und Signifikanz des Unterschieds zwischen v1 und v2 in allen drei Läufen gleich bleiben. Ändert sich die Schlussfolgerung, steht das im Bericht als „nicht stabil“.

**8. Grenzen (stehen im Bericht).**
- Alle Vergleichssterne (Bahnlösungen, Kontrollplaneten) wackeln deutlich; für **schwache Signale** gibt es keine Prüfung gegen echte Daten.
- Das Scan-Muster ist das **nominelle** und nicht das tatsächliche Scan-Gesetz. Die Zahl der Übergänge im DR4-Zeitraum ist eine Näherung (Anteil aus DR3), keine Messung.
- Der Messfehler stammt aus einer digitalisierten Abbildung und ist über G = 16 hinaus extrapoliert; das Rauschen durch Nachbarn und Dichte ist nicht simuliert.
- Die Häufigkeiten und Verteilungen der Klassen sind Annahmen aus der Literatur (siehe `configs/simulation_priors.yaml`, noch leer).
- Die Korrelationen der Bahnelemente von Gaia sind nicht gespeichert.
- Die Simulation zeigt, ob eine bekannte Verzerrung der Amplitude in der Simulation ein Problem ist; sie zeigt nicht, was bei DR4 passiert.

**9. Test gegen den ID-Fehler** ist eingebaut (`tests/test_source_ids.py`, Commit 9c497d5): Jede Datei mit einer Spalte `*source_id` muss `BIGINT` (int64) sein, die Feature-Tabellen müssen dieselben IDs wie die Kataloge haben (kein Verlust, kein Rundungsfehler), und zwei Sterne mit 19-stelliger ID müssen unverändert vorhanden sein. Für die Simulation gilt derselbe Test für alle neuen Dateien (Teilung, Ergebnisse).

**Rahmen (Erinnerung).** Die Simulation ist eine Zusatzauswertung. Liste 1, Liste 2, `MANIFEST.md` und `evaluate_bet.py` aus `v1.0` bleiben unverändert.
