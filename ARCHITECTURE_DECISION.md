## Entscheidung

1. **Frage 1 (ist 0.6.0 schon die Lösung?):** Der in `setup.py` seit
   Commit `8346dad` bestehende Pin `openpyxl>2.6.0` löst den in #212
   beschriebenen Konflikt mit Pandas 1.2.4 (`openpyxl>=2.6.0`)
   grundsätzlich bereits, da sich beide Bereiche überschneiden
   (z. B. `openpyxl==3.0.5`). Er bleibt als **untere** Grenze ohne
   Obergrenze erhalten — eine erneute Obergrenze wie beim ursprünglichen
   `openpyxl<2.5.0`-Workaround würde das gleiche Problem nur erneut in
   die Zukunft verschieben und wird deshalb bewusst **nicht**
   wieder eingeführt.
2. **Frage 2 (exakte Untergrenze):** Der Pin wird von `openpyxl>2.6.0`
   auf `openpyxl>=2.6.0` präzisiert, damit er exakt der von Pandas
   selbst kommunizierten Mindestanforderung ("Pandas requires version
   '2.6.0' or newer") entspricht, statt sie um einen Patch-Level knapp zu
   verfehlen.
3. **Frage 3 (künftiges Release-Delay vermeiden):** Da dieser Workflow
   keinen PyPI-Zugriff hat, kann er die 3+ Jahre alte Release-Lücke
   selbst nicht schließen. Als Kompensation wird der Testsuite ein
   Regressionstest für den Excel-Export hinzugefügt und die CI so
   erweitert, dass sie zusätzlich gegen ein aktuelles Pandas-Release
   installiert und testet. Damit fällt eine künftige erneute
   Pin-Divergenz spätestens bei der nächsten CI-Ausführung auf,
   unabhängig davon, wann als nächstes tatsächlich auf PyPI released
   wird. Das eigentliche Nachziehen eines PyPI-Releases bleibt
   Maintainer-Aufgabe und wird im PR-Text explizit als offener Punkt
   benannt.

## Begründung

- **Tradeoffs:** Eine harte Ober- *und* Untergrenze (z. B.
  `openpyxl>=2.6.0,<4.0.0`) würde zwar zusätzliche Sicherheit vor
  zukünftigen Breaking Changes in `openpyxl` geben, hätte aber genau das
  Verhalten erzeugt, das #212 überhaupt erst verursacht hat: ein zu enger
  Pin, der irgendwann mit einer neuen Pandas-Mindestanforderung
  kollidiert und erneut ein manuelles Nachziehen erfordert. Eine offene
  Untergrenze ohne Obergrenze ist hier die bewusst gewählte, einfachere
  und robustere Lösung; das Restrisiko (ein zukünftiges Breaking
  `openpyxl`-Release) wird durch den neuen CI-Test gegen ein aktuelles
  Pandas abgefangen, nicht durch einen präventiven Pin.
- **Breaking-Change-Risiko:** `>2.6.0` → `>=2.6.0` ist eine reine
  Erweiterung der zulässigen Menge (Obermenge der vorherigen Bedingung)
  und damit für bestehende Nutzer nicht breaking.
- **Konsistenz mit bestehender API:** Es wird keine öffentliche
  Schnittstelle von `records` verändert, nur eine Dependency-Grenze in
  `setup.py` und die Testabdeckung. Das Verhalten von
  `Record(Set).export(...)` bleibt unverändert.
- Die Wahl, das Release-Problem nicht durch Prozess-Bürokratie (z. B.
  einen "Release-Trigger") zu lösen, sondern durch einen automatisierten
  Kompatibilitätstest, passt zum Umfang dieses Workflows: Code und CI
  liegen in unserer Kontrolle, der PyPI-Release-Vorgang nicht.

## Akzeptanzkriterien

- [x] `setup.py`: Die `openpyxl`-Anforderung lautet `openpyxl>=2.6.0`
      (keine Obergrenze).
- [x] Ein neuer Test in `tests/` exportiert ein `RecordCollection` sowohl
      nach `xlsx` als auch nach `xls` und prüft, dass dabei kein
      `ImportError`/keine Exception auftritt (Regressionstest für die
      Fehlerklasse aus #142/#206/#212).
- [x] Die CI-Konfiguration installiert in mindestens einem Testlauf
      zusätzlich ein aktuelles `pandas`-Release (`pip install
      "pandas>=1.2.4"`) neben `records[pandas]` in derselben Umgebung und
      führt die Testsuite gegen diese Kombination aus, ohne dass ein
      Versionskonflikt beim Installieren auftritt.
- [x] `pytest tests/ -v` läuft vollständig grün.
- [x] `HISTORY.rst` erhält einen Einträge zum Fix von #212 (Verweis auf
      #212 und #206).

## Bekannte Breaking Changes

Keine. Die Änderung von `openpyxl>2.6.0` zu `openpyxl>=2.6.0` erweitert
lediglich die zulässige Versionsmenge um exakt `2.6.0` und ändert keine
öffentliche API. Nutzer, die aktuell schon eine kompatible
`openpyxl`-Version (>2.6.0) installiert haben, sind nicht betroffen.
