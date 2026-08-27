---
title: 'Story 1.2: Regression tests for context-manager lifecycle'
type: 'chore'
created: '2026-08-27'
status: 'done'
route: 'one-shot'
---

# Story 1.2: Regression tests for context-manager lifecycle

## Intent

**Problem:** Story 1.1's exception-safety fix for `Connection`'s `close_with_result=True` leak shipped with zero automated regression coverage — the exact bug it fixed had no test proving it stays fixed.

**Approach:** Add a dedicated test file (`tests/test_context_manager.py`) covering the full exception/success × `close_with_result` True/False matrix for `Connection`, plus the `Database`-level exception exit and the existing non-context-manager usage pattern, following the project's existing `db`/`foo_table` fixture conventions.

## Suggested Review Order

- The regression test that would have caught Story 1.1's bug directly — verified independently by reverting the fix and confirming this test fails.
  [`test_context_manager.py:126`](../../tests/test_context_manager.py#L126)

- Success-path guard: proves the `close_with_result=True` lazy-close optimization is untouched.
  [`test_context_manager.py:40`](../../tests/test_context_manager.py#L40)

- Success-path guard: `close_with_result=False` still closes for real on normal exit.
  [`test_context_manager.py:54`](../../tests/test_context_manager.py#L54)

- Double-close guard: exercises `_close_on_exception`'s own idempotency check.
  [`test_context_manager.py:67`](../../tests/test_context_manager.py#L67)

- General `Connection` exception-safety (not `close_with_result`-specific).
  [`test_context_manager.py:84`](../../tests/test_context_manager.py#L84)

- `Database`-level exception exit — Story 1.2's AC names Database alongside Connection.
  [`test_context_manager.py:25`](../../tests/test_context_manager.py#L25)

- Peripheral: unchanged manual (non-`with`) usage pattern, now leak-safe on assertion failure too.
  [`test_context_manager.py:129`](../../tests/test_context_manager.py#L129)
