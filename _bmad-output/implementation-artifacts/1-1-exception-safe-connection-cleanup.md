---
title: 'Story 1.1: Exception-safe connection cleanup'
type: 'bugfix'
created: '2026-08-27'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: '8a8299052d92f64a53e532f03b6e73de51f76912'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `Connection.close()` (`records.py:358-363`) only closes the underlying SQLAlchemy connection when `close_with_result=False`. `Database.query()`/`query_file()` internally use `close_with_result=True` (`records.py:314,326`), so a query that raises mid-execution leaves the connection checked out and unclosed even though `conn.open` reports `False` — a real connection leak on the exception path.

**Approach:** Move exception-awareness exclusively into `Connection.__exit__` (`records.py:368-369`), the only call site with real exception info, via a new private helper that force-closes the connection when exiting due to an exception. `close()`'s existing public signature and direct-call behavior stay byte-for-byte unchanged, per Architecture AD-1.

## Boundaries & Constraints

**Always:** Exception-awareness lives exclusively in `Connection.__exit__`, dispatching to a new private helper — never inside `close()`'s own logic or signature. `Connection.close()` keeps its exact current zero-argument signature and behavior for direct/manual calls (respects `close_with_result` unconditionally). The `close_with_result=True` success path (no exception) is byte-for-byte unchanged. Double-close (manual + `with`-exit, either order) stays a safe no-op. `Database.transaction()` (`records.py:335-347`) is not touched.

**Ask First:** If satisfying this without a new private method turns out to require any change visible outside `Connection` (e.g. a new parameter anywhere, a change to `Database`), stop and ask — the spine only sanctions a private-helper-in-`__exit__` mechanism.

**Never:** Use `sys.exc_info()` or any ambient/global exception detection. Add a parameter to `close()`. Touch `Database.transaction()`'s catch-rollback-no-reraise behavior. Write the formal regression test suite (Story 1.2), README (Story 1.3), or type hints (Story 1.4) — those are separate stories.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Query raises, `close_with_result=True` | `Database.query()`/`query_file()` raises inside its internal `with self.get_connection(True) as conn:` | `__exit__` sees `exc is not None`, force-closes `conn._conn` via the new private helper | Original exception still propagates unchanged |
| Query succeeds, `close_with_result=True` | Same internal `with` block, no exception | Unchanged: lazy-close optimization preserved, `_conn` stays open | N/A |
| Manual direct close, either `close_with_result` value | `conn = db.get_connection(...); conn.close()` outside any `with` | Byte-for-byte identical to current behavior | N/A |
| Double-close, either order | `close()` then `with`-exit, or `with`-exit then manual `close()` | No exception raised | N/A |
| Nested `Connection` inside `Database` `with`-block, exception in inner block | `with Database(url) as db:` / `with db.get_connection() as conn: raise` | Neither resource left open | Exception propagates |

</frozen-after-approval>

## Code Map

- `records.py:350-372` -- `Connection` class: `__init__`, `close()`, `__enter__`, `__exit__`, `__repr__` — the code being modified
- `records.py:280-289` -- `Database.close()`/`__enter__`/`__exit__` — read-only context, not modified (Database's own cleanup is already unconditional)
- `records.py:300-327` -- `Database.get_connection()`, `query()`, `query_file()` — read-only context; lines 314 and 326 show the `close_with_result=True` call sites this fix must cover
- `records.py:335-347` -- `Database.transaction()` — read-only context, explicitly must NOT be touched
- `records.py:449` -- `_reduce_datetimes` — only existing leading-underscore method in the file; the only naming precedent for the new private helper (module-level, not a class method, but establishes single-underscore snake_case as the file's convention)
- `tests/conftest.py:19-36` -- `db` fixture (sqlite in-memory) — for manual verification only in this story; formal tests land in Story 1.2

## Tasks & Acceptance

**Execution:**
- [x] `records.py` -- Add a private helper method on `Connection` (e.g. `_close_on_exception`) that closes `self._conn` unconditionally (guarded so it's a no-op if already closed) and sets `self.open = False` -- implements AD-1's mechanism without changing `close()`'s signature
- [x] `records.py` -- Update `Connection.__exit__` to call the new private helper when `exc is not None`, otherwise call the existing unchanged `self.close()` -- exception-driven exits always close regardless of `close_with_result`; success path untouched

**Acceptance Criteria:**
- Given a `Database.query()`/`query_file()` call that raises inside its internal `with self.get_connection(True) as conn:` block, when the exception propagates, then the underlying SQLAlchemy connection object is actually closed (not just `conn.open == False`)
- Given the `close_with_result=True` success path, when no exception occurs, then behavior is unchanged from before this story
- Given a manual `conn.close()` call outside any `with` block, when `close_with_result` is `True` or `False`, then behavior is identical to before this story
- Given `close()` called twice in either order relative to `with`-exit, when executed, then no exception is raised

## Spec Change Log

## Design Notes

The mechanism, concretely:

```python
def close(self):                      # UNCHANGED
    if not self._close_with_result:
        self._conn.close()
    self.open = False

def _close_on_exception(self):         # NEW
    if not self._conn.closed:
        self._conn.close()
    self.open = False

def __exit__(self, exc, val, traceback):
    if exc is not None:
        self._close_on_exception()
    else:
        self.close()
```

`self._conn.closed` guards against double-close inside the new helper too (SQLAlchemy's own `Connection.close()` is independently idempotent, but the explicit check keeps this helper self-contained).

## Verification

**Commands:**
- `pytest` -- expected: full existing suite passes unchanged (no test yet exercises the new behavior directly — that's Story 1.2)

**Manual checks (if no CLI):**
- Run a short script: open `records.Database('sqlite:///:memory:')`, call `db.query("SELECT * FROM sqlite_master WHERE 1=0")` wrapped to force an exception (e.g. invalid SQL) inside `db.query(...)`, catch it, then inspect the connection object reached via `db.get_connection(True)` in a separate call to confirm the fixed code path force-closes on exception (exact inspection approach left to the implementer — the point is confirming `_conn.closed is True` after an exception inside the `close_with_result=True` path).

## Suggested Review Order

- Entry point: dispatch logic decides close-on-success vs. force-close-on-exception.
  [`records.py:381`](../../records.py#L381)

- New helper: the actual exception-path fix — force-closes regardless of `close_with_result`.
  [`records.py:365`](../../records.py#L365)

- Unchanged for comparison: `close()`'s original signature/behavior, frozen per AD-1.
  [`records.py:358`](../../records.py#L358)

- Peripheral: changelog entry for this fix.
  [`HISTORY.rst:1`](../../HISTORY.rst#L1)
