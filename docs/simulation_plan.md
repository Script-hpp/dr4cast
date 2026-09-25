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
