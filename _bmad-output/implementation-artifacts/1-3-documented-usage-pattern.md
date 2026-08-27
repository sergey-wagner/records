---
title: 'Story 1.3: Documented usage pattern'
type: 'chore'
created: '2026-08-27'
status: 'done'
route: 'one-shot'
---

# Story 1.3: Documented usage pattern

## Intent

**Problem:** `README.md`/`README.rst` only show the manual `db = Database(url); ...; db.close()` pattern — nothing demonstrates `with Database(url) as db:`, even though it's now hardened and regression-tested (Stories 1.1–1.2).

**Approach:** Add a `with Database(...) as db:` example directly after the existing connect example in both README files, alongside (not replacing) the manual pattern.

## Suggested Review Order

- The corrected example — consumes `rows` inside the block, avoiding the disposed-engine footgun caught during review (verified empirically both broken and fixed).
  [`README.md:33`](../../README.md#L33)

- Mirrored RST version, including the blank-line fix a fresh drift-check caught.
  [`README.rst:38`](../../README.rst#L38)
