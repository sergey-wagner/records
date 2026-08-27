# Epic 1 Context: records.py Database API Modernization

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Developers using `records` get provably exception-safe connection cleanup on `Database`/`Connection`, plus a fully type-hinted public API across `Database`, `Connection`, `Record`, and `RecordCollection`, with CI enforcement that prevents either guarantee from silently regressing — all without changing any existing public signature or behavior. This closes two real ergonomics gaps (an actual connection-leak bug on the exception path, and a public surface invisible to IDEs/static checkers) while keeping the library's zero-friction feel intact.

## Stories

- Story 1.1: Exception-safe connection cleanup
- Story 1.2: Regression tests for context-manager lifecycle
- Story 1.3: Documented usage pattern
- Story 1.4: Complete type hints on the public API
- Story 1.5: CI type-check enforcement

## Requirements & Constraints

- `with Database(url) as db:` and `with Connection(...) as conn:` must release all held resources (engine disposal / connection close) on both normal exit and exception exit. This includes the internal `close_with_result=True` path used by `Database.query()`/`query_file()`, which today leaves the underlying SQLAlchemy connection unclosed on exception even though `conn.open` reports `False`.
- Double-`close()` (manual close followed by `with`-exit, or vice versa, in either order) must remain a safe no-op — never raise.
- `Database.transaction()`'s existing catch-rollback-no-reraise behavior is a separate, already-correct, already-tested pattern and must not be touched.
- On the `close_with_result=True` *success* path (no exception), the existing lazy-close optimization must be preserved unchanged — no new closing behavior introduced there.
- Test suite must cover: happy path and exception path for both `Database` and `Connection` context managers, a dedicated test for the `close_with_result=True` exception case, and a regression test proving the classic `db = Database(url); ...; db.close()` pattern still passes unchanged. Full suite must stay green.
- README must show `with Database(url) as db:` as a supported pattern, alongside (not replacing) the existing manual-`close()` example.
- Every public method, property, `__init__`, protocol dunder (`__enter__`/`__exit__`/`__iter__`/`__next__`/`__len__`/`__getitem__`/`__repr__`/`__getattr__`), and public instance attribute (e.g. `Database.open`, `Database.db_url`, `Connection.open`, `RecordCollection.pending`) on the four core classes needs a resolvable type annotation. Private/internal (`_`-prefixed) members are out of scope.
- Adding annotations must not change any call-site signature: no new required params, no renames, no dropped defaults. Full test suite must pass unmodified.
- A CI step must run a type checker against `records.py` and fail the build when a public-API annotation is missing or removed; a PR touching only private/internal code with no public-API annotation change must still pass.
- No async/await, no change to SQL execution or commit/transaction semantics, no runtime type-enforcement library (e.g. no pydantic). Minimum supported Python is 3.7 — all new code/syntax must remain valid there.

## Technical Decisions

- **Cleanup mechanism (AD-1):** Exception-awareness lives exclusively in `Connection.__exit__` — the only call site with real exception info — via a private/internal helper that force-closes the underlying connection on the exception path only, regardless of `close_with_result`. `Connection.close()`'s public signature and direct-call behavior stay frozen exactly as today (zero args, respects `close_with_result` unconditionally on success). Ambient detection via `sys.exc_info()` is explicitly disallowed.
- **Typing mechanism (AD-2):** Inline PEP 484 annotations directly in `records.py`. No `.pyi` stub file, no `from __future__ import annotations`. `Any` is the correct (not a fallback) choice for `**params`/`**multiparams`, `Record`'s dynamic per-column value surface (`_values`, `values()`, `__getitem__`/`__getattr__` return), and `Database.__init__`'s `**kwargs` pass-through to `create_engine` — don't hand-craft narrower unions for these.
- **Annotation syntax (AD-3):** Use `typing.Optional[X]` / `typing.Union[X, Y]` only — never PEP 604 `X | Y` (would break import on Python 3.7–3.9). This is enforced structurally by the existing 3.7–3.12 pytest matrix, not by mypy.
- **CI job shape (AD-4):** New `mypy` step on the Python 3.12 matrix leg only (mypy 2.3.1 requires interpreter ≥3.10), invoked exactly as `mypy --disallow-untyped-defs records.py` with **no** `--python-version` flag (mypy 2.x rejects any target below 3.10). The out-of-scope `cli()` entry point and private/internal helpers are exempted via inline `# type: ignore[no-untyped-def]`, not by weakening the check globally. This step is the sole authoritative type-check gate; any other mypy invocation elsewhere in the repo must mirror its flags or be clearly non-blocking.
- **Naming:** No renames anywhere — existing class/method names are unchanged (non-breaking rollout is a hard constraint across all stories).
- No new files are introduced beyond test additions and the `ci.yml` edit; everything stays inside the existing single-module (`records.py`) structure.

## Cross-Story Dependencies

- Story 1.2's tests validate the fix made in Story 1.1 — implement 1.1's cleanup hardening before or alongside 1.2's regression tests.
- Story 1.5's CI enforcement assumes Story 1.4's type hints are already in place across the public API; sequence 1.4 before 1.5.
- Stories 1.3 (docs) and 1.4 (typing) are otherwise independent of the 1.1/1.2 cleanup work, but all five stories touch the same single file (`records.py`) plus `README` and `ci.yml`, so coordinate edits to avoid merge conflicts within the epic.
