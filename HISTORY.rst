Unreleased
==========

- **Fixed:** ``Database.query()``, ``Database.bulk_query()``, and
  ``Database.bulk_query_file()`` now commit immediately after executing,
  so INSERT/UPDATE/DELETE statements issued through these one-shot methods
  persist. The v0.6.0 upgrade to SQLAlchemy 2.0+ removed legacy implicit
  autocommit, and ``records`` never called ``.commit()`` on these paths,
  so writes were silently discarded once the connection closed or
  returned to the pool (`#224 <https://github.com/kennethreitz/records/issues/224>`_).
  This restores the documented pre-2.0 behavior. ``Database.transaction()``
  is unchanged and remains the way to group multiple statements into a
  single atomic write, or to deliberately roll one back. This is not a
  breaking change for any dry-run usage: writes issued via ``query()`` /
  ``bulk_query()`` / ``bulk_query_file()`` were discarded 100% of the time
  before this fix, so no code could have been relying on them being rolled
  back. That said, code that (intentionally or not) depended on this
  discard-by-default behavior -- for example, throwaway test setup or
  exploratory scripts that issued writes via these methods expecting them
  *not* to persist -- will now observe different, persisting behavior.
  Also fixed: a failed statement issued through these methods no longer
  leaves a dangling implicit transaction on a reused ``Connection``, which
  previously could cause the *next* successful write on that same
  connection to silently skip its commit.

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
