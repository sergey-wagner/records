- source_spec: `_bmad-output/implementation-artifacts/1-4-complete-type-hints-on-the-public-api.md`
  summary: This story's function-annotation and PEP 526 variable-annotation syntax (`def f(x: T)`, `self.pending: bool = True`) is Python 3-only, and `self.pending: bool` further needs 3.6+ — `tox.ini` (py27/py34/py35/py36) and `.travis.yml` would fail on those legs if actually run.
  evidence: Same pre-existing, already-dead CI configuration flagged during the Architecture phase (`tox.ini`/`.travis.yml` are superseded by the live `.github/workflows/ci.yml` 3.7-3.12 matrix, and Python <3.7 installs are already broken by the existing `SQLAlchemy>=2.0` dependency regardless of this story). Independently re-surfaced by the blind-hunter review layer during Story 1.4's review.

- source_spec: `_bmad-output/implementation-artifacts/1-4-complete-type-hints-on-the-public-api.md`
  summary: `setup.py` still has no `python_requires` pin, so `pip install records` on Python <3.7 will install a package that now cannot even be imported (was already broken via the SQLAlchemy>=2.0 dependency; the new syntax makes the breakage more immediate/explicit).
  evidence: Same item already noted in the PRD (§9) and Architecture Spine (Deferred) as pre-existing and out of scope; logged again here at the build-phase level since the blind-hunter review layer independently re-surfaced it against the actual shipped diff.

- source_spec: `_bmad-output/implementation-artifacts/1-4-complete-type-hints-on-the-public-api.md`
  summary: Type hints for `Database` and `Connection` (the connection-management pair) were split off from Story 1.4's spec, which now covers only `Record`/`RecordCollection` (the self-contained result-representation pair with no forward-ref dependency on Database/Connection), because the full 4-class spec exceeded the 1600-token target and the human chose to split rather than accept the oversized spec.
  evidence: Human decision at Story 1.4's Checkpoint 1 token-count gate, 2026-08-27. Must be picked up as its own spec before Story 1.5 (CI type-check enforcement), which assumes the full public API is typed.

- source_spec: `_bmad-output/implementation-artifacts/1-3-documented-usage-pattern.md`
  summary: README.md and README.rst duplicate the same usage examples with no single source of truth, so they can (and already had, before this story's fix) drift apart wording- or formatting-wise.
  evidence: Pre-existing structure of this repo (two independently-maintained README files), not introduced by this story; flagged by the blind-hunter review layer during Story 1.3's review, which also caught one instance of drift (a missing RST blank line) that this story fixed.

- source_spec: `_bmad-output/implementation-artifacts/1-2-regression-tests-for-context-manager-lifecycle.md`
  summary: The shared `db` test fixture (`tests/conftest.py`) is only parametrized with sqlite in-memory — the Postgres case is present but commented out — so no test in the suite (including Story 1.2's new regression tests) exercises a real pooled/networked connection, the backend where a leaked connection is most consequential.
  evidence: Pre-existing limitation of the whole test suite (not introduced by Story 1.1 or 1.2); flagged by the blind-hunter review layer during Story 1.2's review.

- source_spec: `_bmad-output/implementation-artifacts/1-1-exception-safe-connection-cleanup.md`
  summary: Connection-cleanup calls (`Connection.close()`, `Connection._close_on_exception()`, `Database.transaction()`'s `finally: conn.close()`) are not wrapped in try/except, so a cleanup-time exception from `self._conn.close()` itself can mask the original in-flight exception being handled.
  evidence: Pre-existing pattern across records.py (present in `close()` and `Database.transaction()` before this story), extended by this story's diff to one more branch (the exception-exit path for `close_with_result=True`) rather than introduced as a new risk category. Flagged independently by the edge-case-hunter and blind-hunter review layers during Story 1.1's review.
