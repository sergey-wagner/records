---
title: 'Story 1.4 part 2: Type hints on Database and Connection'
type: 'feature'
created: '2026-08-27'
status: 'done'
route: 'one-shot'
---

# Story 1.4 part 2: Type hints on Database and Connection

## Intent

**Problem:** Story 1.4's spec was split at the token-budget checkpoint into two specs; `Record`/`RecordCollection` landed already, but `Database`/`Connection` (the pair with 4 of the file's 5 forward-reference sites) were deferred and still had zero type hints — blocking Story 1.5, which needs the full public API typed.

**Approach:** Apply inline PEP 484 annotations to every public method/`__init__`/protocol dunder/plain public attribute on `Database` and `Connection`, per Architecture AD-2/AD-3. Review caught 4 real gaps beyond the initial pass (an `Optional[str]` vs `str` type-lie on `db_url`, missing `-> None` on `__init__`s, untyped `__exit__` exception-triple parameters) — all patched and verified before this landed.

## Suggested Review Order

- `db_url`'s corrected `Optional[str]` annotation — the one finding that would have actually broken Story 1.5's future mypy gate if left as `str`.
  [`records.py:274`](../../records.py#L274)

- The forward-reference-heavy member: `Database.get_connection` returning `Connection` before it's defined in the file.
  [`records.py:314`](../../records.py#L314)

- `__exit__`'s now-fully-typed exception triple (both classes) — the second review pass's fix.
  [`records.py:399`](../../records.py#L399)

- Peripheral: new imports (`typing.Type`, `types.TracebackType`, aliased `sqlalchemy.engine` types) and the HISTORY.rst entry marking FR4 complete.
  [`records.py:8`](../../records.py#L8)
