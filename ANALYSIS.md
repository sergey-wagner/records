# Analyse: Issue #212 — openpyxl/Pandas-Versionskonflikt

**Quelle:** https://github.com/kennethreitz/records/issues/212
**Titel:** "records (v0.5.3) is incompatible with latest Pandas (v1.2.4) cause they have different openpyxl version dependency requirements"
**Status:** offen seit 2021-05-31

## Zusammenfassung aus Nutzersicht

Nutzer, die `records` zusammen mit einem aktuellen Pandas in derselben
Umgebung installieren wollen, können das nicht: `pip` bricht die
Installation ab bzw. `records` wirft beim Excel-Export einen
`ImportError`, weil Pandas eine neuere `openpyxl`-Version verlangt, als
`records` erlaubt. Betroffen sind konkret Nutzer, die Datenbank-Abfragen
per `records` nach Excel exportieren und gleichzeitig Pandas 1.2.4 (oder
neuer) im selben Environment einsetzen — ein for sie alltäglicher
Anwendungsfall (Reporting/Data-Science-Stack). Ein Community-Workaround
("openpyxl manuell auf 3.0.5 pinnen") funktioniert laut Kommentaren,
ist aber kein offizieller Fix und für neue Nutzer nicht offensichtlich.
Aus Nutzersicht ist das Problem also: die auf PyPI veröffentlichte
`records`-Version lässt sich nicht gemeinsam mit einem modernen
Data-Science-Stack installieren.

## Klärung der konkreten Versionsanforderungen

- **records 0.5.3 (PyPI-Release vom 2019-02-21, in Issue #212 zitiert):**
  `setup.py` verlangt `openpyxl<2.5.0`. Dieser Pin stammt aus einem
  historischen Workaround für Issue #142 ("Fix #142: failure to export
  to XLSX (downgrade openpyxl)", Commit `a096d9a`, 2018) und war nie als
  dauerhafte Anforderung gedacht.
- **Pandas 1.2.4** (im Issue zitiert): verlangt laut der zitierten
  Fehlermeldung `openpyxl>=2.6.0` ("Pandas requires version '2.6.0' or
  newer of 'openpyxl'").
- **Überschneidung:** `<2.5.0` und `>=2.6.0` schließen sich gegenseitig
  aus — es gibt **keine** Version, die beide Anforderungen der
  PyPI-Version 0.5.3 gleichzeitig erfüllt. Das ist die technische
  Ursache des gemeldeten Fehlers.
- **Wichtiger Befund:** Im Git-Verlauf dieses Repos wurde der Pin bereits
  am 2019-09-02 entfernt (Commit `28aac29`, "remove temporary openpyxl
  fix") und am 2020-03-30 durch `openpyxl>2.6.0` ersetzt (Commit
  `8346dad`) — also **vor** Eröffnung von Issue #212 (2021-05-31). Diese
  Änderung wurde jedoch **nicht als neues PyPI-Release veröffentlicht**:
  Laut PyPI-Metadaten blieb 0.5.3 (2019-02-21) bis 2024-03-29 die
  aktuellste verfügbare Version; erst Release 0.6.0 (2024-03-29) enthält
  den gelockerten Pin `openpyxl>2.6.0`.
- Jede `openpyxl`-Version `>2.6.0` (z. B. die von Nutzern erfolgreich
  getesteten `openpyxl==3.0.5` / `3.0.7`) erfüllt sowohl die
  aktuelle `records`-Anforderung als auch die von Pandas 1.2.4 verlangte
  Untergrenze. Ein gemeinsamer, funktionierender Bereich existiert also
  bereits im aktuellen Quellcode — er war zum Zeitpunkt der Issue-Meldung
  nur nicht auf PyPI verfügbar.

## Klassifikation

Reiner **Bug**, genauer: ein veralteter, zu enger Dependency-Pin
(`openpyxl<2.5.0`), der ursprünglich als befristeter Workaround gedacht
war, aber nie aus dem für Endnutzer sichtbaren Release entfernt wurde.
Kein Design-Problem und keine fehlende Funktionalität — die zugrunde
liegende Excel-Export-Funktionalität selbst ist nicht betroffen.

Zusätzlich deutet der Befund (Fix im Quellcode vorhanden, aber
3+ Jahre nicht released) auf ein **Release-Prozess-Problem** hin, das
über den reinen Code-Fix hinausgeht.

## Verwandte Issues (möglicherweise gleiche Ursache)

- **#142** ("Failing export to xlsx", geschlossen) — der ursprüngliche
  Anlass für den `openpyxl<2.5.0`-Pin. Historische Ursache des jetzigen
  Konflikts.
- **#206** ("Export XLS error", offen) — `ImportError: cannot import
  name 'ExcelReader' from 'openpyxl.reader.excel'`. Gleiche Fehlerklasse:
  Inkompatibilität zwischen der installierten `openpyxl`-Version und dem,
  was `records`/`tablib` zur Laufzeit erwartet. Sollte zusammen mit #212
  betrachtet werden, da eine Lösung des Versionskonflikts vermutlich auch
  dieses Issue adressiert.

## Offene Fragen für den Architect

1. Ist Release 0.6.0 (2024-03-29, bereits mit `openpyxl>2.6.0` in
   `setup.py`) bereits die Lösung für #212, sodass nur noch verifiziert
   und das Issue geschlossen werden muss — oder gibt es einen Grund,
   weshalb der aktuelle Pin (`openpyxl>2.6.0`, keine Obergrenze) noch
   nicht ausreicht bzw. angepasst werden sollte?
2. Soll eine explizite Untergrenze gesetzt werden, die sich direkt an
   Pandas' eigener Anforderung orientiert (`openpyxl>=2.6.0`), um
   zukünftige Drift zwischen beiden Projekten zu vermeiden, oder reicht
   der bestehende Pin?
3. Wie soll verhindert werden, dass ein Fix künftig erneut Jahre auf
   ein Release wartet (siehe Zeitspanne 2020-03-30 Fix-Commit bis
   2024-03-29 Release) — braucht es z. B. einen Release-Trigger oder
   eine CI-Prüfung auf offene, bereits gefixte Issues vor dem nächsten
   Release?
