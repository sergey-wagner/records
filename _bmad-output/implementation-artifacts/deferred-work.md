- source_spec: `_bmad-output/implementation-artifacts/1-2-regression-tests-for-context-manager-lifecycle.md`
  summary: The shared `db` test fixture (`tests/conftest.py`) is only parametrized with sqlite in-memory — the Postgres case is present but commented out — so no test in the suite (including Story 1.2's new regression tests) exercises a real pooled/networked connection, the backend where a leaked connection is most consequential.
  evidence: Pre-existing limitation of the whole test suite (not introduced by Story 1.1 or 1.2); flagged by the blind-hunter review layer during Story 1.2's review.

- source_spec: `_bmad-output/implementation-artifacts/1-1-exception-safe-connection-cleanup.md`
  summary: Connection-cleanup calls (`Connection.close()`, `Connection._close_on_exception()`, `Database.transaction()`'s `finally: conn.close()`) are not wrapped in try/except, so a cleanup-time exception from `self._conn.close()` itself can mask the original in-flight exception being handled.
  evidence: Pre-existing pattern across records.py (present in `close()` and `Database.transaction()` before this story), extended by this story's diff to one more branch (the exception-exit path for `close_with_result=True`) rather than introduced as a new risk category. Flagged independently by the edge-case-hunter and blind-hunter review layers during Story 1.1's review.
