---
title: 'Story 1.4: Complete type hints on the public API (part 1 — Record, RecordCollection)'
type: 'feature'
created: '2026-08-27'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: '879d0dc66d44be179f069eada677eba375ef7fe8'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `records.py`'s four core classes have zero type hints. This spec covers the `Record`/`RecordCollection` half — the self-contained result-representation pair with no forward-reference dependency on `Database`/`Connection`. The `Database`/`Connection` half is split off to its own follow-up spec (logged in `deferred-work.md`), which must land before Story 1.5 (CI enforcement).

**Approach:** Add inline PEP 484 annotations to every public method/property/`__init__`/protocol dunder/plain public attribute on `Record` and `RecordCollection`, per Architecture AD-2/AD-3's already-settled mechanism (inline, `typing.Optional`/`Union`, no `.pyi`, no `from __future__ import annotations`). Return types traced precisely from actual code behavior (see Code Map), not guessed.

## Boundaries & Constraints

**Always:** Inline PEP 484 annotations directly in `records.py` only (AD-2) — the one forward-reference site in this scope (`RecordCollection.__getitem__`'s self-reference) uses string-quoting (`"RecordCollection"`), never `from __future__ import annotations` (AD-2 explicitly rules this out despite being simpler). `typing.Optional[X]`/`typing.Union[X, Y]` only, never PEP 604 `X | Y` (AD-3). `Any` for genuinely dynamic surfaces (AD-2's carve-out): `Record`'s per-column value surface (`__getitem__`/`__getattr__`/`get`'s return, the `values` param), `export`'s `**kwargs`, and any `default` parameter that accepts an arbitrary caller value (`Record.get`, `RecordCollection.first`/`one`/`scalar`). No signature changes visible at the call site (FR5) — no new required params, no renames, no removed defaults. Full existing 38-test suite passes unmodified.

**Ask First:** If a concrete return type would require importing a private/internal SQLAlchemy type, default to `Any`/`Sequence` instead — confirm before importing anything not already imported by this file.

**Never:** Use `from __future__ import annotations`. Touch `Database` or `Connection` (separate, deferred spec). Touch any call-site-visible signature. Type `dataset` differently than leaving it un-required (it's a `@property`, out of FR4's required scope — optionally typeable but not mandatory). Change any runtime behavior.

</frozen-after-approval>

## Code Map

Ground truth traced from the current file. `Record` is defined first (no dependency on any other class here); `RecordCollection` depends only on `Record` (defined above it — no quoting needed for that reference).

### `Record` (`records.py:25-104`)
| Member | Line | Annotation |
|---|---|---|
| `__init__(self, keys, values)` | 30 | `keys: Sequence[Any]`, `values: Sequence[Any]` |
| `keys()` | 37 | `-> Sequence[Any]` (returns `self._keys` verbatim) |
| `values()` | 41 | `-> Sequence[Any]` (returns `self._values` verbatim) |
| `__repr__()` | 45 | `-> str` |
| `__getitem__(key)` | 48 | `key: Union[int, str]`, `-> Any` (single column value) |
| `__getattr__(key)` | 67 | `key: str`, `-> Any` |
| `__dir__()` | 73 | `-> List[str]` |
| `get(key, default=None)` | 78 | `key: Union[int, str]`, `default: Any = None`, `-> Any` (dict.get-shaped) |
| `as_dict(ordered=False)` | 85 | `ordered: bool = False`, `-> Union[dict, OrderedDict]` |
| `export(format, **kwargs)` | 102 | `format: str`, `**kwargs: Any`, `-> Union[str, bytes]` (tablib: binary formats → bytes) |

(`dataset` at line 91 is a `@property` — outside FR4's required scope, leave unannotated.)

### `RecordCollection` (`records.py:107-256`)
| Member | Line | Annotation |
|---|---|---|
| `__init__(rows)` | 110 | `rows: Iterator[Record]` |
| `self.pending` attr | 113 | `bool` |
| `__repr__()` | 115 | `-> str` |
| `__iter__()` | 118 | `-> Iterator[Record]` |
| `next(self)` | 136 | `-> Record` |
| `__next__()` | 139 | `-> Record` |
| `__getitem__(key)` | 148 | `key: Union[int, slice]`, `-> Union[Record, "RecordCollection"]` (quote self-ref) |
| `__len__()` | 167 | `-> int` |
| `export(format, **kwargs)` | 170 | same as `Record.export` |
| `all(as_dict=False, as_ordereddict=False)` | 195 | `-> Union[List[Record], List[dict], List[OrderedDict]]` |
| `as_dict(ordered=False)` | 209 | `-> Union[List[dict], List[OrderedDict]]` (never `List[Record]` — always delegates to `all()` with exactly one flag `True`) |
| `first(default=None, as_dict=False, as_ordereddict=False)` | 212 | `default: Any = None`, `-> Union[Record, dict, OrderedDict, Any]` |
| `one(...)` | 233 | same signature/return shape as `first` |
| `scalar(default=None)` | 252 | `default: Any = None`, `-> Any` (note: does not forward `default` into its internal `self.one()` call — pre-existing behavior, do not "fix") |

(`dataset` at line 174 is a `@property` — outside FR4's required scope.)

## Tasks & Acceptance

**Execution:**
- [x] `records.py` -- Add `from typing import Any, Iterator, List, Sequence, Union` near the existing imports (only names actually used in this scope) -- enables the annotations below
- [x] `records.py` -- Annotate all `Record` members per Code Map table -- FR4
- [x] `records.py` -- Annotate all `RecordCollection` members per Code Map table, using a quoted `"RecordCollection"` self-reference in `__getitem__` -- FR4

**Acceptance Criteria:**
- Given `records.py` after this story, when a type checker (mypy/pyright) is run against it, then every public method/`__init__`/protocol dunder/plain public attribute on `Record` and `RecordCollection` carries a type annotation, and no annotation uses PEP 604 `X | Y` syntax
- Given the full existing test suite (38 tests), when run after this story, then all pass unmodified
- Given a diff review of `Record`'s and `RecordCollection`'s public signatures before/after, when compared, then only annotation additions are present

## Spec Change Log

## Design Notes

The one forward-reference site in this scope:

```python
# RecordCollection.__getitem__ (line 148) — self-reference, RecordCollection
# isn't bound as a name until its own class statement finishes executing
def __getitem__(self, key: Union[int, slice]) -> Union[Record, "RecordCollection"]: ...
```

`RecordCollection.as_dict()` always delegates to `all()` with exactly one of `as_dict`/`as_ordereddict` `True` — its true return type is `Union[List[dict], List[OrderedDict]]`, never `List[Record]`, even though `all()` itself can return that third variant when called directly with both flags `False`.

## Verification

**Commands:**
- `python -m pytest tests -q` -- expected: 38 passed, unchanged
- `python -c "import records"` -- expected: no `SyntaxError`/`NameError` at import time (catches the unquoted-forward-ref failure mode immediately)

**Manual checks (if no CLI):**
- `python -c "import typing, records; print(typing.get_type_hints(records.RecordCollection.__getitem__))"` -- confirms the quoted forward reference actually resolves.

## Suggested Review Order

- The one forward-reference site — a self-referencing quoted type, the trickiest annotation in this scope.
  [`records.py:149`](../../records.py#L149)

- `RecordCollection`'s branching-return methods — flat `Union` types traced precisely from actual control flow (`all`/`first`/`one`/`scalar`).
  [`records.py:259`](../../records.py#L259)

- `Record`'s dynamic-value surface — `Any` used deliberately per Architecture AD-2's carve-out, not as a shortcut.
  [`records.py:49`](../../records.py#L49)

- Peripheral: the new `typing` import.
  [`records.py:8`](../../records.py#L8)
