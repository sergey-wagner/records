"""Regression tests for `Connection`/`Database` context-manager lifecycle.

Story 1.1 fixed a connection leak: `Connection.__exit__` used to call
`close()` unconditionally, which for `close_with_result=True` connections
(used internally by `Database.query()`/`query_file()`) skipped the actual
`self._conn.close()` call -- even when the `with`-block exited via an
exception. `conn.open` reported `False`, but the underlying SQLAlchemy
connection stayed open. The fix added `Connection._close_on_exception()`,
called from `__exit__` whenever the block exits with an exception,
regardless of `close_with_result`.

These tests cover:

- general context-manager exception-safety for `Connection` (AC 1)
- the specific `close_with_result=True` leak that Story 1.1 fixed (AC 2)
- the existing non-context-manager (manual `db.close()`) usage pattern,
  unaffected by the fix (AC 3)
"""
import pytest
from sqlalchemy.exc import OperationalError

import records


def test_database_open_false_after_exception_in_with_block():
    """AC 1 (Database side): a `with Database(url) as db:` block that exits
    via an unhandled exception must leave `db.open` False and the engine
    disposed -- unchanged by Story 1.1 (Database.close() already disposed
    unconditionally), but pinned here since Story 1.2's AC explicitly names
    Database alongside Connection.
    """
    with pytest.raises(ValueError):
        with records.Database('sqlite:///:memory:') as db:
            raise ValueError()

    assert db.open is False


@pytest.mark.usefixtures('foo_table')
def test_connection_close_with_result_unchanged_on_success(db):
    """Success-path guard: a `close_with_result=True` connection that exits
    its `with` block WITHOUT an exception must keep the pre-Story-1.1
    lazy-close optimization -- the underlying connection stays open so a
    lazily-iterated result can still consume it.
    """
    with db.get_connection(True) as conn:
        pass

    assert conn.open is False  # the wrapper always reports closed...
    assert conn._conn.closed is False  # ...but the real connection is not, by design


@pytest.mark.usefixtures('foo_table')
def test_connection_close_with_result_false_closes_on_success(db):
    """Success-path guard: a `close_with_result=False` connection (the
    `bulk_query`/manual `get_connection()` default) closes for real on a
    normal (non-exception) `with`-block exit, same as before Story 1.1.
    """
    with db.get_connection() as conn:
        pass

    assert conn.open is False
    assert conn._conn.closed is True


@pytest.mark.usefixtures('foo_table')
def test_close_on_exception_is_a_noop_if_already_closed(db):
    """Exercises `_close_on_exception`'s own double-close guard: a
    connection manually closed *before* an exception propagates through its
    `with`-block must not raise on the resulting force-close attempt.
    """
    conn = db.get_connection()
    conn.close()

    with pytest.raises(ValueError):
        with conn:
            raise ValueError()

    assert conn.open is False
    assert conn._conn.closed is True


@pytest.mark.usefixtures('foo_table')
def test_connection_closed_after_exception_in_with_block(db):
    """General context-manager exception-safety (not close_with_result-specific):
    a `with db.get_connection() as conn:` block that exits via an unhandled
    exception must leave both `conn.open` and the underlying SQLAlchemy
    connection closed.
    """
    conn = db.get_connection()

    with pytest.raises(ValueError):
        with conn:
            raise ValueError()

    assert conn.open is False
    assert conn._conn.closed is True


@pytest.mark.usefixtures('foo_table')
def test_query_close_with_result_connection_closed_on_exception(db, monkeypatch):
    """The exact bug fixed in Story 1.1: `Database.query()` uses
    `close_with_result=True` internally. When the query raises mid-execution,
    the underlying SQLAlchemy connection must actually be closed
    (`._conn.closed is True`), not just `conn.open` reporting `False`.

    This test fails against the pre-Story-1.1 code (where the `with`-block's
    `__exit__` skips the real close for `close_with_result=True` connections
    even on exception) and passes against the current code.
    """
    captured = {}
    original_get_connection = db.get_connection

    def spying_get_connection(*args, **kwargs):
        conn = original_get_connection(*args, **kwargs)
        captured['conn'] = conn
        return conn

    monkeypatch.setattr(db, 'get_connection', spying_get_connection)

    with pytest.raises(OperationalError):
        db.query('SELECT * FROM this_table_does_not_exist')

    assert 'conn' in captured
    assert captured['conn'].open is False
    assert captured['conn']._conn.closed is True


def test_database_manual_close_without_context_manager():
    """The existing non-context-manager pattern (`db = Database(url); ...;
    db.close()`, no `with`) must still work exactly as before Story 1.1.
    """
    db = records.Database('sqlite:///:memory:')
    try:
        db.query('CREATE TABLE foo (a integer)')
        db.query('INSERT INTO foo VALUES (42)')

        assert db.query('SELECT count(*) AS n FROM foo')[0].n == 1
    finally:
        db.close()  # idempotent (AD-1) even if an assertion above already failed

    assert db.open is False
