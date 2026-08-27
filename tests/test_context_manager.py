"""Tests for the context-manager behavior of `Database` and `Connection`.

Covers, for both `Database` and `Connection`:

- entering the `with` block yields an open, functional instance
- leaving the block closes the instance (and, for `Database`, disposes the
  engine pool)
- an exception raised inside the block still triggers `close()`
- using a closed instance for a query raises `exc.ResourceClosedError`
"""
import pytest
from sqlalchemy import exc

import records


SQLITE_MEMORY_URL = "sqlite:///:memory:"


class TestDatabaseContextManager:
    def test_context_manager_yields_open_functional_database(self):
        with records.Database(SQLITE_MEMORY_URL) as db:
            assert db.open is True
            assert db.query("SELECT 1 AS n")[0].n == 1

    def test_exiting_closes_database_and_disposes_pool(self):
        db = records.Database(SQLITE_MEMORY_URL)
        dispose_calls = []
        original_dispose = db._engine.dispose

        def spy_dispose(*args, **kwargs):
            dispose_calls.append(True)
            return original_dispose(*args, **kwargs)

        db._engine.dispose = spy_dispose

        with db:
            assert db.open is True

        assert db.open is False
        assert dispose_calls == [True]

    def test_exception_in_with_block_still_closes_database(self):
        db = records.Database(SQLITE_MEMORY_URL)
        with pytest.raises(ValueError):
            with db:
                raise ValueError("boom")
        assert db.open is False

    def test_query_on_closed_database_raises_resource_closed_error(self):
        db = records.Database(SQLITE_MEMORY_URL)
        with db:
            pass
        with pytest.raises(exc.ResourceClosedError):
            db.query("SELECT 1")


class TestConnectionContextManager:
    def test_context_manager_yields_open_functional_connection(self):
        with records.Database(SQLITE_MEMORY_URL) as db:
            with db.get_connection() as conn:
                assert conn.open is True
                assert conn.query("SELECT 1 AS n")[0].n == 1

    def test_exiting_closes_connection(self):
        with records.Database(SQLITE_MEMORY_URL) as db:
            conn = db.get_connection()
            with conn:
                assert conn.open is True
            assert conn.open is False
            assert conn._conn.closed is True

    def test_exception_in_with_block_still_closes_connection(self):
        with records.Database(SQLITE_MEMORY_URL) as db:
            conn = db.get_connection()
            with pytest.raises(ValueError):
                with conn:
                    raise ValueError("boom")
            assert conn.open is False
            assert conn._conn.closed is True

    def test_query_on_closed_connection_raises_resource_closed_error(self):
        with records.Database(SQLITE_MEMORY_URL) as db:
            conn = db.get_connection()
            with conn:
                pass
            with pytest.raises(exc.ResourceClosedError):
                conn.query("SELECT 1")
