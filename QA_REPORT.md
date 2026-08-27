# QA-Report: Issue #212 (openpyxl/Pandas-Versionskonflikt)

## Hinweis zur Persona

`personas/qa.md` existiert weder im Arbeitsverzeichnis noch an anderer
Stelle im Repository/Workspace (auch nicht in der Git-Historie). Ich
konnte die dort beschriebene Rolle daher nicht wörtlich übernehmen und
bin stattdessen als unabhängige, skeptische QA-Instanz vorgegangen: Ich
habe nichts aus ANALYSIS.md/ARCHITECTURE_DECISION.md unbesehen
übernommen, sondern jede Behauptung anhand des tatsächlichen Code- und
Testzustands nachvollzogen bzw. selbst nachgestellt (siehe unten). Bitte
`personas/qa.md` ergänzen bzw. den Pfad korrigieren, falls für künftige
Durchläufe eine striktere/andere Rollenvorgabe gewünscht ist — dieser
Report ersetzt sie nur behelfsmäßig für diesen einen Lauf.

## Prüfung gegen ARCHITECTURE_DECISION.md

| Akzeptanzkriterium | Status | Befund |
|---|---|---|
| `setup.py`: `openpyxl>=2.6.0`, keine Obergrenze | ✅ erfüllt | `setup.py:52` — `"openpyxl>=2.6.0"`, kein Upper-Pin in `requires`. |
| Neuer Regressionstest exportiert `xlsx` und `xls`, keine Exception | ✅ erfüllt | `tests/test_export.py` — `test_export_xlsx_does_not_raise`, `test_export_xls_does_not_raise`, beide grün. |
| CI installiert zusätzlich aktuelles `pandas` neben `records[pandas]` in einem eigenen Job | ✅ erfüllt | `.github/workflows/ci.yml`, Job `pandas-compat`: `pip install ".[pandas]" "pandas>=1.2.4"`, danach `pytest`. |
| `pytest tests/ -v` läuft vollständig grün | ✅ erfüllt | Verifiziert (siehe unten), 33/33 Tests grün. |
| `HISTORY.rst` enthält Eintrag zu #212 (Verweis auf #212 und #206) | ✅ erfüllt | Abschnitt "Unreleased" verweist explizit auf `(#212, #206)`. |

Keine Abweichung zwischen dem, was ARCHITECTURE_DECISION.md als "[x]"
markiert, und dem tatsächlichen Code-/Repo-Zustand gefunden.

## Eigene Verifikation (nicht nur Nachlesen)

### 1. `pytest tests/ -v` in der bestehenden Entwicklungsumgebung

```
33 passed in 0.34s
```

Alle Tests inkl. der beiden neuen Excel-Export-Tests grün.

### 2. Fresh-Venv-Installationstest: records + neues openpyxl + aktuelles Pandas

Frisches, isoliertes virtuelles Environment angelegt und **ausschließlich**
über `pip install ".[pandas]" "pandas>=1.2.4"` befüllt (kein Rückgriff auf
bereits im Dev-Environment vorhandene Pakete):

```
records            0.6.0
openpyxl           3.1.5
pandas             3.0.5
SQLAlchemy         2.0.52
tablib             3.10.0
```

Installation lief **ohne** Dependency-Konflikt oder Resolver-Fehler durch
— genau das Szenario aus #212 (records + aktuelles Pandas gemeinsam
installieren) ist damit nicht mehr reproduzierbar.

Zusätzlich in diesem frischen Environment `pytest`, `xlwt`, `xlrd`
installiert (Testabhängigkeiten für `tests/test_export.py`) und die volle
Suite erneut ausgeführt:

```
33 passed in 1.54s
```

Insbesondere `test_export_xlsx_does_not_raise` und
`test_export_xls_does_not_raise` sind auch mit dem in diesem Environment
frisch aufgelösten, deutlich neueren `openpyxl`/`pandas` grün — der Fix
ist also nicht nur "installierbar", sondern auch funktional wirksam
gegen die in #212/#206 beschriebene Fehlerklasse.

### 3. Abgleich mit ANALYSIS.md

Die in ANALYSIS.md dokumentierte technische Ursache (`openpyxl<2.5.0`
vs. Pandas' `openpyxl>=2.6.0`) ist im aktuellen Code nicht mehr vorhanden;
der einzige verbliebene Pin (`openpyxl>=2.6.0`) überschneidet sich mit
Pandas' Anforderung, wie unter Punkt 2 empirisch bestätigt.

## Offene Punkte (keine Blocker für diesen Fix)

- Das in ANALYSIS.md benannte Release-Prozess-Problem (Fix seit
  2020-03-30 im Code, aber erst mit v0.6.0 am 2024-03-29 released) ist
  laut ARCHITECTURE_DECISION.md bewusst nicht durch diesen Workflow
  gelöst, sondern nur durch den neuen CI-Job kompensiert. Das ist konsistent
  zur getroffenen Entscheidung, sollte aber im PR-Text als offener Punkt
  für die Maintainer benannt werden (dort bereits so vorgesehen).
- `personas/qa.md` fehlt (siehe oben) — organisatorischer Punkt für den
  Workflow, kein Code-Mangel.

## Freigabe: Ja

Alle Akzeptanzkriterien aus ARCHITECTURE_DECISION.md sind erfüllt und
eigenständig verifiziert (nicht nur anhand der `[x]`-Markierungen
übernommen). Die konkrete QA-Zusatzfrage — lässt sich `records` mit der
neuen `openpyxl`-Version zusammen mit einem aktuellen Pandas installieren
— ist mit einem frischen venv-Test empirisch mit **Ja** beantwortet.
Aus QA-Sicht bereit für die menschliche Freigabe vor dem PR.
