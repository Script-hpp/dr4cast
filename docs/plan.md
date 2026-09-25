# Plan nach dem DR3-Download

Stand: 2026-09-25. Erledigt: DR3-Hauptkatalog (Download läuft), NSS-Tabellen, NASA-Labels, Manifest 0.4, Experiment-Log. Reihenfolge ist verbindlich für Abhängigkeiten, nicht für die Zeit. Änderungen an Zielen gehören ins `MANIFEST.md`, Beobachtungen ins `docs/experiment_log.md`.

## 1. Download abschließen und prüfen
- Alle 192 Chunks vorhanden, keine `.tmp`-Dateien, `source_id` eindeutig und `int64`.
- Chunk-Zeilenzahlen stichprobenartig gegen `SELECT COUNT(*)` beim Archiv vergleichen.
- Filter-Prüfung am vollständigen Katalog wiederholen (Anteil der Labels und `Orbital`-Lösungen bei Schwellen 5, 10, ohne Filter) und mit Einschränkung in den Experiment-Log schreiben (Labels und Orbital-Lösungen sind schon auf gute Messungen selektiert).

## 2. Weitere Daten laden (`download_aux.py`, gleiches Muster: int64, Parquet, Retry)
1. `gaiadr3.binary_masses` (Begleitermassen, Backtest-Ziel).
2. `gaiadr2.ruwe` (Baseline im Backtest).
3. `gaiadr3.dr2_neighbourhood` (Verknüpfung DR2→DR3, nur über diese Tabelle).
4. `gaiadr2.gaia_source`, nahe Sterne. Auswahl **nur mit DR2-Parallaxe** (kein Leakage), gleiche Chunk-Technik.
5. HGCA (Beschleunigung, ca. 100k helle Sterne): zwei Versionen, Brandt 2018 (DR2) für den Backtest, Brandt 2021 (EDR3) für die Wette. Erledigt: beide Versionen von Brandts Seite geladen (`data/raw/hgca/`).
6. Labels für den Backtest: nur `disc_year <= 2017`. Gaia-4 b und Gaia-5 b bleiben immer aus dem Training und dienen als Kontrollstichprobe.

## 3. Aufbereiten (DuckDB, Parquet nach `data/processed/`)
- Ein Feature-Table pro Katalog: `features_dr3`, `features_dr2`.
- Qualitätsfilter aus dem Manifest anwenden, Schwellwert als Parameter.
- RUWE-Erwartungswert nach Helligkeit und Farbe (Kalibrierung aus den Sternen selbst, später aus der großen Himmelsstichprobe).
- Backtest-Ziel bauen: DR3-Lösungen `Orbital` mit `m2` (`binary_masses`) unter 13 bzw. 80 M_Jup; getrennt `OrbitalTargetedSearch`.
- Tests: keine doppelten `source_id`, Verknüpfung nur über die Nachbarschaftstabelle, Dtypes.

## 4. Baseline und Modell v1
- Baseline: RUWE-Sortierung, Metriken P@10, P@30, P@100, Recall@100, absolute Treffer, nach Helligkeitsklassen. Jede Metrik zweifach: alle Treffer und nur neue Treffer (Hauptmetrik).
- LightGBM v1 mit Klassengewichten und starker Regularisierung.
- Aufteilung gruppiert nach Planetensystem (nie gemischt in Training und Test).
- Prüfen: Gaia-4 b und Gaia-5 b (nicht im Training) weit oben, erst bei der DR4-Vorhersage; Anteil bekannter Doppelsterne in den Top 100.

## 5. Erklärbarkeit und Bias
- SHAP: Dominieren Helligkeit und Entfernung statt der Wackel-Features?
- Vergleich der Filter-Schwellen 5, 10, ohne Filter nach Helligkeitsklassen; endgültigen Schwellwert dann im Manifest festlegen.

## 6. Backtest DR2→DR3 auswerten
- Ergebnis mit Grenzen (kein NSS-Feature in DR2, eher pessimistisch) dokumentieren.
- Trefferquote ins Manifest und in die spätere Zenodo-Veröffentlichung.

## 7. Danach
- Modell v2 (PU-Learning, Umgewichtung) nur, wenn v1 stabil ist.
- Große Himmelsstichprobe für die RUWE-Kalibrierung.
- DR3-Vorhersageliste erzeugen, Manifest einfrieren (Tag, SHA-256), GitHub-Repo veröffentlichen, Zenodo-DOI.

## Offene Entscheidungen
- Endgültiger Qualitätsfilter (nach Schritt 5).
- GitHub-Repo: öffentlich oder privat, Name (erst zum Veröffentlichen nötig).
