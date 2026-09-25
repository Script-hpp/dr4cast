# Klarstellung und Nachtrag zu v1.0

**Keine Änderung an Listen, Manifest oder Auswertungsskript.** Dieses Dokument erklärt, was mit dem Tag `v1.0` (Commit `705b357`) schon eingefroren ist, und schließt eine Lücke bei der Sternmasse `m1` für DR4 (Abschnitt d). Es legt sonst nichts Neues fest. Stand: 2026-09-25, vor dem Release von Gaia DR4.

Prüfung, dass die eingefrorenen Teile unverändert sind:

```bash
git diff --stat v1.0 HEAD -- release MANIFEST.md src/gaia_wobble/evaluate_bet.py   # muss leer sein
cd release/v1 && sha256sum -c list1_substellar.csv.sha256 list2_planets.csv.sha256
```

```
8cb67a02c6c757ba5cd4bdfaa3171367fb84f369c2ec60cadcd0784e1900256e  list1_substellar.csv
9a7130bd01be7d04dd882482fa13d000a65976f5654beecab8d64a7bb967d05d  list2_planets.csv
```

## a) Der Tag `v1.0` ist das Einfrieren

`MANIFEST.md` trägt im Kopf „Status: Entwurf (lebendes Dokument)“ und „Eingefroren am: – (noch nicht)“, und Regel 2 im Abschnitt „Wie dieses Dokument funktioniert“ erlaubt Änderungen, „bis DR4 erscheint“. Beides ist veraltet, weil das Manifest nach dem Einfrieren nicht mehr geändert wird (es bleibt unverändert, damit die Prüfsumme des Tags gilt). Es gilt:

- **Eingefroren** sind mit dem GitHub-Release `v1.0` (veröffentlicht 2026-09-25) die Listen in `release/v1/`, `MANIFEST.md` in Version 0.19 und `src/gaia_wobble/evaluate_bet.py`.
- Ab jetzt sind nur zwei Dinge erlaubt: (1) Klarstellungen wie dieses Dokument, die nichts Neues festlegen, und (2) die im Manifest (Abschnitt „Auswertungsskript“) erlaubten Schema-Anpassungen an das echte DR4-Format (nur Datei- und Spaltennamen, mit Diff im Experiment-Log). Jede inhaltliche Ergänzung ist ein gekennzeichneter Nachtrag, wie der in Abschnitt d.
- Der Zenodo-Eintrag mit der DOI gehört zum Release; die DOI wird nach der Vergabe in README und `CITATION.cff` nachgetragen (kein Einfluss auf die eingefrorenen Teile).

## b) Welche Ziele der Wette gelten

Im Abschnitt „Massenschätzung und Ziele“ steht eine Tabelle mit „Wette DR3→DR4: Hauptziel unter 13 M_Jup, Nebenziel unter 80 M_Jup“. Sie stammt aus Version 0.6 und wurde in 0.9 durch zwei gleichrangige Listen ersetzt, ohne dass die Tabelle angepasst wurde. Maßgeblich sind der Abschnitt „Festlegungen“ und das Auswertungsskript:

- **Liste 1:** Ziel `y80` (DR4-Bahn, geschätzte Begleitermasse unter 80 M_Jup).
- **Liste 2:** Hauptziel `y13_ms` (unter 13 M_Jup und `ms_offset < 0,2` mit DR4-Werten); zusätzlich berichtet `y13` (ohne die Bedingung).
- Beide gleichrangig; `y80_ms` wird als Referenz mit ausgegeben. Die Tabelle gilt weiter für den **Backtest** (Spalte DR2→DR3).

## c) Aufteilung der Trainingsdaten

„Validierung“, Punkt 2 („Planetensysteme liegen komplett in Training oder Test“) stammt aus der Zeit, als bekannte Planetensterne das Trainingsziel waren. Für Modell A gilt die Aufteilung nach Himmelsregionen: 5-fach-Kreuzvalidierung, ganze HEALPix-Level-2-Pixel je Fold (`src/gaia_wobble/model_a.py`, `region_folds`). Die Konfidenzintervalle kommen aus einem Bootstrap über die 192 Level-2-Zellen. Die Planeten-Label-Modelle B und B' benutzen dieselbe Aufteilung.

## d) Nachtrag zu `m1` bei DR4 (Lückenfüllung, keine Zieländerung)

**Die Lücke.** Das eingefrorene Skript verlangt für DR4 eine Datei `primary_masses.parquet` mit `source_id` und `m1` (`evaluate_bet.py:20`, `:37`, `:40`), legt aber nicht fest, woher sie kommt. Im Probelauf auf DR3 stammt `m1` aus `binary_masses` (`evaluate_bet.py:119` und `:121`), einem DR3-Produkt; für DR4 gibt es dazu keine Regel. Weil `m1` die Begleitermasse und damit `y80`, `y13` und `y13_ms` bestimmt, muss die Quelle vor dem Release feststehen.

**Offizielle Regel.**

- `m1 = mass_ms` aus der Mamajek-Tabelle (`src/gaia_wobble/data/mamajek_mg_mass.csv`), berechnet mit der DR4-Photometrie und der DR4-Parallaxe: absolute G = G + 5·log10(Parallaxe/mas) − 10, dann lineare Interpolation in der Tabelle (`physics_features.py`, gleiche Formel wie beim Feature).
- Sterne außerhalb des Tabellenbereichs der absoluten G-Helligkeit (−1,19 bis 17,3) bekommen **kein `m1`**; ihre Bahnlösungen bekommen keine Massenschätzung und zählen als Label unbekannt (ausgeschlossen), wie bisher bei fehlendem `m1`. Der Code dafür ist `src/gaia_wobble/primary_masses.py` (`mass_ms_strict`, `build_primary_masses`); er kappt nicht auf die Randwerte, anders als `stellar_mass_ms`. Das Skript `evaluate_bet.py` bleibt unverändert; `primary_masses.py` erzeugt nur seine Eingabedatei aus der Feature-Tabelle des späteren Releases.
- **Zusätzlich berichtet, nicht offiziell:** Ziele mit FLAME-Massen aus DR4 und mit einer Gaia-eigenen Primärmassen-Tabelle, falls es sie gibt.

**Sensitivitätsprüfung an DR3** (vorab, `python -m gaia_wobble.m1_sensitivity`; gleiche Lösungen, gleicher Code `outcomes_from_solutions`, einmal mit `m1` aus `binary_masses`, einmal aus `mass_ms`; DR3-Nahsternkatalog, 10.822 Bahnlösungen ohne die vier zurückgezogenen):

| | `binary_masses` | `mass_ms` |
|---|---|---|
| Lösungen mit `m1` | 10.184 | 10.819 |
| ausgeschlossen (Label unbekannt) | 908 | 447 |

`m1_ms / m1_bm` bei den 10.184 Lösungen mit beiden Werten: Median 0,958, Quartile 0,897 bis 1,0; 95,9 % liegen innerhalb von ±20 %.

| Ziel | `binary_masses` | `mass_ms` | in beiden | nur `binary_masses` | nur `mass_ms` |
|---|---|---|---|---|---|
| `y80` | 1.306 | 1.636 | 1.291 | 15 | 345 |
| `y13` | 17 | 25 | 17 | 0 | 8 |
| `y13_ms` | 4 | 6 | 4 | 0 | 2 |
| `y80_ms` | 430 | 512 | 423 | 7 | 89 |

Von den 345 zusätzlichen `y80`-Zielen hatten 47 in `binary_masses` gar kein `m1`; 298 haben in `binary_masses` ein `m1`, das die Begleitermasse etwas über 80 M_Jup lässt (`mass_ms` ist bei den Lösungen mit beiden Werten im Median 4 % kleiner). Der Median von `ms_offset` der zusätzlichen Ziele (0,46) ist derselbe wie der der übrigen Ziele (0,45). Alle 17 bisherigen `y13`-Ziele bleiben erhalten.

**Die Wahl von `mass_ms` steht unabhängig vom Ergebnis dieser Prüfung fest.** Sie wurde vor der Prüfung getroffen, weil sie heute vollständig festlegbar ist, nur von DR4-Helligkeit, Farbe und Parallaxe und einer Tabelle im Repository abhängt und nichts erst nach dem Release entscheiden lässt.

**Folgen und Grenzen.**

- Modell A wurde mit einem Ziel trainiert, das auf `binary_masses` beruht, und wird nicht neu trainiert. Das Ziel der Wette ist die Fassung mit `mass_ms`; sie ist um etwa ein Viertel größer (in der DR3-Stichprobe 1.636 statt 1.306 Ziele unter 80 M_Jup). Alle Zahlen des Backtests im Experiment-Log benutzen `binary_masses` und bleiben unverändert.
- `mass_ms` ist eine Zwergen-Hauptreihe: Riesen, Unterriesen und unaufgelöste Doppelsterne bekommen eine falsche Masse. Überhelle Systeme (Doppelsterne) bekommen ein größeres `m1` und damit eine etwas größere Begleitermasse, so ist die Erwartung; gemessen wurde das hier nicht.
- Das Ergebnis der Wette hängt damit an der Hauptreihen-Näherung. Das ist eine offene Schwäche.

## e) Konkurrenz-Listen nicht im Repository

Geprüft am Tag `v1.0`: `git ls-tree -r v1.0 --name-only` enthält von den Konkurrenz-Listen (ExoDNN, Kiefer et al., Sahlmann & Gómez) nur `docs/competitors.json` (Prüfsummen) und `src/gaia_wobble/download_competitors.py` (Abrufskript). Die Listen selbst liegen nicht im Repository. (`release/v1/neighbours_dr3.parquet` ist die eigene Nachbartabelle der Listen.)
