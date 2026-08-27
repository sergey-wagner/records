---
title: 'Story 1.5: CI type-check enforcement'
type: 'feature'
created: '2026-08-27'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: '0d5038707dbbab9408d0b96855992e08abbfe91f'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `records.py`'s public API is now fully type-hinted (Story 1.4), but nothing enforces it — a future PR could silently remove or weaken an annotation and nothing would catch it.

**Approach:** Add a `mypy --disallow-untyped-defs records.py` CI step on the Python 3.12 matrix leg only, per Architecture AD-4. Running the exact command locally (mypy 2.3.1 is available in this environment) surfaced 15 real errors beyond the expected private/CLI exemptions — this spec fixes all of them precisely, verified against the actual tool output, not guessed.

## Boundaries & Constraints

**Always:** The CI step is exactly `mypy --disallow-untyped-defs records.py` (no `--python-version` flag — AD-4), added to `.github/workflows/ci.yml` gated to the `python-version == '3.12'` leg only. Every fix below preserves runtime behavior exactly (verified: 38 tests pass unchanged after each category of fix). Private/internal functions and `cli()` get `# type: ignore[no-untyped-def]`, never a real annotation (Never list, Story 1.4). `dataset` properties (left unannotated in Story 1.4 as "outside required scope") now get a real one-line return annotation instead of an ignore comment, since they're genuinely public and trivially typeable — a `# type: ignore` there would be dishonest given the true type is knowable.

**Ask First:** None — every fix below has a single correct resolution verified against the actual mypy output; there's no judgment call requiring escalation.

**Never:** Add a `mypy.ini`/`pyproject.toml` config file (AD-4 leaves this to build-phase judgment; inline flags/comments are simpler and sufficient here — no need for a config file for this small a surface). Run mypy across the full 3.7–3.12 matrix (AD-4: single leg only). Weaken any existing type accuracy just to silence an error (e.g., no blanket `# type: ignore` on a line where a precise `cast()` is the honest fix).

</frozen-after-approval>

## Code Map

Ground truth: `python -m mypy --disallow-untyped-defs records.py` run directly against the current committed code (mypy 2.3.1, Python 3.14 interpreter — satisfies AD-4's ≥3.10 requirement). 15 errors found, each mapped to its fix:

| # | Line(s) | Error | Fix |
|---|---|---|---|
| 1 | 11 | `tablib` has no stubs/py.typed (`import-untyped`) | `# type: ignore[import-untyped]` on the `import tablib` line |
| 2 | 12 | `docopt` has no stubs (`import-untyped`) | `# type: ignore[import-untyped]` on the `from docopt import docopt` line |
| 3 | 17 | `isexception(obj)` missing annotation | `# type: ignore[no-untyped-def]` — private module helper, not part of FR4's 4-class scope |
| 4 | 49 | `Record.__repr__`: `self.export("json")[1:-1]` — `export()`'s declared `Union[str, bytes]` return makes mypy flag the implicit str-format as possibly producing `b'...'` garbage, even though the `"json"` format arg always yields `str` at runtime | `cast(str, self.export("json"))[1:-1]` (needs `from typing import cast`) — honest: this specific call site is contractually str, the general signature isn't |
| 5 | 95 | `Record.dataset` property missing return annotation | Add `-> tablib.Dataset` (module already imported; tablib itself is stub-less so mypy treats its internals as `Any`, but the function signature is now present, satisfying `--disallow-untyped-defs`) |
| 6 | 115 | `RecordCollection.__init__`: `self._all_rows = []` — mypy can't infer the empty list's element type | Annotate `self._all_rows: List[Record] = []` (private attribute; annotating it is allowed even though FR4 doesn't require private members typed) |
| 7 | 129 | `RecordCollection.__iter__`: `yield self[i]` — `self[i]` resolves via `__getitem__`'s `Union[Record, "RecordCollection"]` signature, but `__iter__` declares `Iterator[Record]`; at this call site `i` is always an `int` key, which `__getitem__` always resolves to a `Record`, but mypy can't infer that without `@overload` (deliberately not used, per Story 1.4's review) | `cast(Record, self[i])` |
| 8 | 155-156, 158 | `RecordCollection.__getitem__`: `is_int = isinstance(key, int)` then `if is_int: key = slice(key, key + 1)` — mypy doesn't narrow `key`'s type through the intermediate `is_int` boolean variable, so it still sees `key: Union[int, slice]` inside the branch (breaking `key + 1`) and after it (breaking `key.stop`) | Change `if is_int:` (only the branch that reassigns `key`) to `if isinstance(key, int):` — behaviorally identical (same boolean value), but lets mypy's flow-sensitive narrowing work. Keep the separate `is_int` variable for the later `if is_int: return rows[0]` branch, which needs no type narrowing |
| 9 | 178 | `RecordCollection.dataset` property missing return annotation | Add `-> tablib.Dataset`, same as row 5 |
| 10 | 215 | `RecordCollection.as_dict`: `return self.all(...)` — `all()`'s signature returns the full 3-way `Union[List[Record], List[dict], List[OrderedDict]]`, but `as_dict()` declares the narrower `Union[List[dict], List[OrderedDict]]` (per Story 1.4's Design Notes: `as_dict()` always passes exactly one flag `True`, so the `List[Record]` branch is structurally unreachable here — but the type system can't see that without `@overload`) | `cast(Union[List[dict], List[OrderedDict]], self.all(...))` |
| 11 | 383 | `Connection._close_on_exception` missing annotation | `# type: ignore[no-untyped-def]` — private, Story 1.4 explicitly left unannotated |
| 12 | 492 | `_reduce_datetimes(row)` missing annotation | `# type: ignore[no-untyped-def]` — private module helper |
| 13 | 503 | `cli()` missing annotation | `# type: ignore[no-untyped-def]` — explicitly out of scope (Story 1.4 Never list, Architecture Deferred) |
| 14 | 596 | `print_bytes(content)` missing annotation | `# type: ignore[no-untyped-def]` — private CLI helper |

Other locations: `.github/workflows/ci.yml` (add the mypy step); `requirements.txt` is NOT modified (mypy stays a CI-only install, not a project dependency, per AD-4's Stack table).

## Tasks & Acceptance

**Execution:**
- [x] `records.py` -- Apply all 14 fixes in the Code Map table exactly as specified (7 `type: ignore` comments, 2 `dataset` return annotations, 1 `_all_rows` annotation, 2 `cast()` calls, 1 `isinstance` restructure, 2 import ignores), plus the 15th fix logged in Spec Change Log -- resolves every real mypy error found
- [x] `.github/workflows/ci.yml` -- Add a step after the existing "Test with pytest" step, gated `if: matrix.python-version == '3.12'`, that installs mypy 2.3.1 and runs `mypy --disallow-untyped-defs records.py` -- implements AD-4/FR6

**Acceptance Criteria:**
- Given `records.py` after this story, when `mypy --disallow-untyped-defs records.py` is run, then it exits 0 with zero errors
- Given `.github/workflows/ci.yml` after this story, when a PR or push to `master` triggers CI, then the new mypy step runs on the Python 3.12 leg only (not 3.7-3.11)
- Given a PR that removes a public-method type hint, when the CI mypy step runs, then it fails
- Given a PR that only touches private/internal code with no public-API annotation change, when the CI mypy step runs, then it passes
- Given the full existing test suite, when run after this story's fixes, then all 38 tests pass unchanged — every fix in the Code Map is a type-only change with no behavioral difference

## Spec Change Log

- **Trigger:** Implementing fix #9 (adding `-> tablib.Dataset` to `RecordCollection.dataset`) caused mypy to start body-checking that property for the first time (mypy skips deep-checking untyped functions), surfacing a 16th, previously-invisible error: `first = self[0]` (line 189) has type `Union[Record, "RecordCollection"]` per `__getitem__`'s signature, but `first.keys()` two lines later requires `Record`.
- **Amendment:** Added `first = cast(Record, self[0])` — same honest-cast pattern as fixes #7 and #10 (a real runtime invariant — `self[0]` with an int literal key always returns a `Record` — that `@overload`-free typing can't express).
- **Avoids:** Shipping a CI gate that still fails on the very first run despite following every row in the original Code Map table.
- **KEEP:** All 14 original fixes landed exactly as specified — this is a strict addition, not a correction of any of them.

## Design Notes

Two of the fourteen fixes are `cast()`, not blanket suppressions — both encode a true runtime invariant the type system can't express without `@overload` (deliberately rejected in Story 1.4 for complexity):

```python
from typing import cast
...
# Record.__repr__ (row 4)
return "<Record {}>".format(cast(str, self.export("json"))[1:-1])

# RecordCollection.__iter__ (row 7)
yield cast(Record, self[i])

# RecordCollection.as_dict (row 10)
return cast(Union[List[dict], List[OrderedDict]], self.all(as_dict=not (ordered), as_ordereddict=ordered))
```

The `isinstance` restructure (row 8) is the only non-annotation code change in this story — confirmed behaviorally identical (`is_int = isinstance(key, int)` and `isinstance(key, int)` evaluate to the same boolean; only the narrowing-visible expression changes, not the logic).

## Verification

**Commands:**
- `python -m mypy --disallow-untyped-defs records.py` -- expected: `Success: no issues found in 1 source file`
- `python -m pytest tests -q` -- expected: 38 passed, unchanged
- `python -c "import records"` -- expected: succeeds (the `type: ignore` comments and casts are erased at runtime, same as any annotation)

**Manual checks (if no CLI):**
- Read the final `.github/workflows/ci.yml` diff and confirm the new step's `if:` condition matches `matrix.python-version == '3.12'` exactly (a typo here would silently make the gate never run, or run on every leg).

## Suggested Review Order

- The CI gate itself — install + run collapsed into one step per review feedback (avoids a duplicated `if:` condition).
  [`ci.yml:36`](../../.github/workflows/ci.yml#L36)

- The two `cast()`s encoding real runtime invariants mypy can't derive without `@overload` — reviewed and empirically re-verified (`export("json")` confirmed to always return `str`, never `bytes`).
  [`records.py:49`](../../records.py#L49)

- The `isinstance` narrowing fix — the only non-annotation logic change, confirmed behaviorally identical by the verification-gap review layer.
  [`records.py:155`](../../records.py#L155)

- Peripheral: the 7 private/CLI `# type: ignore[no-untyped-def]` exemptions and 2 third-party import-stub ignores.
  [`records.py:17`](../../records.py#L17)
