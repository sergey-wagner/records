v0.7.0 (08-27-2026)
===================

- Added complete type hints (PEP 484) to the public API of ``Record``,
  ``RecordCollection``, ``Database`` and ``Connection``.
- Documented and tested the ``with Database(url) as db: ...`` /
  ``with db.get_connection() as conn: ...`` context manager idiom,
  including exception-safe closing of connections and the pool.
- Renamed the ``__exit__`` parameters of ``Database`` and ``Connection``
  (``exc_type``/``exc_val``/``exc_tb``) so they no longer shadow the
  module-level ``sqlalchemy.exc`` import.
- Added a ``py.typed`` marker (PEP 561) and ``mypy`` CI integration so
  downstream projects can type-check against ``records``.
- No breaking changes to runtime behavior.

v0.6.0 (04-29-2024)
===================

- Support for Python 3.6+ only.
- Support for SQLAlchemy 2+.
- Dropped support for Python 2.7 and 3.4, with the move to SQLAlchemy 2+.

v0.5.1 (09-01-2017)
===================

- Depend on ``tablib[pandas]``.
- Support for Bulk quies: ``Database.bulk_query()`` & ``Database.bulk_query_file()``.

v0.5.0 (11-15-2016)
===================

- Support for transactions: ``t = Database.transaction(); t.commit()``


v0.4.3 (02-16-2016)
===================

- The cake is a lie.

v0.4.2 (02-15-2016)
===================

- Packaging fix.

v0.4.1 (02-15-2016)
===================

- Bugfix for Python 3.

v0.4.0 (02-13-2016)
===================

- Refactored to be fully powered by SQLAlchemy!
- Support for all major databases (thanks, SQLAlchemy!).
- Support for non-alphanumeric column names.
- New ``Record`` class, for representing/accessing result rows.
- ``ResultSet`` renamed ``RecordCollection``.
- Removed Interactive Mode from the CLI.


v0.3.0 (02-11-2016)
===================

- New ``record`` command-line tool available!
- Various improvements.

v0.2.0 (02-10-2016)
===================

- Results are now represented as `Record`, a namedtuples class with dict-like qualities.
- New `ResultSet.export` method, for exporting to various formats.
- Slicing a `ResultSet` now works, and results in a new `ResultSet`.
- Lots of bugfixes and improvements!

v0.1.0 (02-07-2016)
===================

- Initial release.
