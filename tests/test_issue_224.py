"""Regression tests for GitHub issue #224.

`Database.query()`, `Database.bulk_query()`, and `Database.bulk_query_file()`
silently discarded write statements (INSERT/UPDATE/DELETE) because
SQLAlchemy 2.0 removed implicit autocommit and `records` never called
`.commit()` before the underlying connection closed or returned to the
pool.

These tests must use a *file-backed* sqlite URL, never `sqlite:///:memory:`.
An in-memory sqlite URL is served by SQLAlchemy's `SingletonThreadPool`, so
two `records.Database` instances pointed at the same `:memory:` URL never
actually cross a real connection boundary -- the bug never reproduces there,
even on the unfixed code. Only a file-backed DB, queried from two
independent `Database` instances, proves the write survived the connection
being closed/returned rather than merely being visible via a shared pooled
connection.
"""

import pytest

import records


@pytest.fixture
def file_db_url(tmp_path):
    """A file-backed sqlite URL, unique per test."""
    return "sqlite:///{}".format(tmp_path / "issue_224.sqlite")


@pytest.fixture
def sql_file(tmp_path):
    """Writes a .sql file with a single parametrized INSERT statement (fed
    multiple rows via bulk_query_file's *multiparams) and returns its path.

    A single statement is used deliberately: sqlite3's DBAPI cursor only
    supports one statement per execute() call, so a file with several
    semicolon-separated statements would fail for reasons unrelated to
    this fix.
    """
    path = tmp_path / "insert_rows.sql"
    path.write_text("INSERT INTO foo VALUES (:a)\n")
    return str(path)


def test_query_insert_persists_across_fresh_instance(file_db_url):
    """CAP-1: a write via Database.query() survives db.close() and is
    visible from a brand-new Database instance against the same file."""
    db1 = records.Database(file_db_url)
    db1.query("CREATE TABLE foo (a integer)")
    db1.query("INSERT INTO foo VALUES (42)")
    db1.close()

    db2 = records.Database(file_db_url)
    try:
        assert db2.query("SELECT count(*) AS n FROM foo")[0].n == 1
    finally:
        db2.close()


def test_bulk_query_insert_persists_across_fresh_instance(file_db_url):
    """CAP-2: a bulk write via Database.bulk_query() survives db.close()
    and is visible from a brand-new Database instance against the same
    file."""
    db1 = records.Database(file_db_url)
    db1.query("CREATE TABLE foo (a integer)")
    db1.bulk_query(
        "INSERT INTO foo VALUES (:a)", [{"a": 42}, {"a": 43}, {"a": 44}]
    )
    db1.close()

    db2 = records.Database(file_db_url)
    try:
        assert db2.query("SELECT count(*) AS n FROM foo")[0].n == 3
    finally:
        db2.close()


def test_bulk_query_file_insert_persists_across_fresh_instance(
    file_db_url, sql_file
):
    """CAP-2: a bulk write via Database.bulk_query_file() survives
    db.close() and is visible from a brand-new Database instance against
    the same file. bulk_query_file() duplicates bulk_query()'s execute()
    call rather than delegating to it, so it needs its own coverage."""
    db1 = records.Database(file_db_url)
    db1.query("CREATE TABLE foo (a integer)")
    db1.bulk_query_file(sql_file, [{"a": 42}, {"a": 43}])
    db1.close()

    db2 = records.Database(file_db_url)
    try:
        assert db2.query("SELECT count(*) AS n FROM foo")[0].n == 2
    finally:
        db2.close()


def test_query_update_persists_across_fresh_instance(file_db_url):
    """UPDATE issued via Database.query() persists, same as INSERT."""
    db1 = records.Database(file_db_url)
    db1.query("CREATE TABLE foo (a integer)")
    db1.query("INSERT INTO foo VALUES (42)")
    db1.query("UPDATE foo SET a = 99 WHERE a = 42")
    db1.close()

    db2 = records.Database(file_db_url)
    try:
        assert db2.query("SELECT a FROM foo")[0].a == 99
    finally:
        db2.close()


def test_query_delete_persists_across_fresh_instance(file_db_url):
    """DELETE issued via Database.query() persists, same as INSERT."""
    db1 = records.Database(file_db_url)
    db1.query("CREATE TABLE foo (a integer)")
    db1.query("INSERT INTO foo VALUES (42)")
    db1.query("INSERT INTO foo VALUES (43)")
    db1.query("DELETE FROM foo WHERE a = 42")
    db1.close()

    db2 = records.Database(file_db_url)
    try:
        assert db2.query("SELECT count(*) AS n FROM foo")[0].n == 1
        assert db2.query("SELECT a FROM foo")[0].a == 43
    finally:
        db2.close()


def test_failed_statement_on_reused_connection_does_not_block_next_commit(
    file_db_url,
):
    """P1 regression test.

    A failed statement on a `Connection` obtained via
    `Database.get_connection()` and reused (no explicit transaction) must
    not leave `self._conn.in_transaction()` == True afterward. Before this
    fix, the failed `execute()` auto-began an implicit transaction that was
    never committed or rolled back, so the *next* successful write on that
    same reused connection wrongly read `in_transaction()` as True,
    concluded it was inside a caller-managed explicit transaction, and
    skipped the commit -- silently reproducing GH #224.
    """
    db = records.Database(file_db_url)
    db.query("CREATE TABLE foo (a integer)")

    conn = db.get_connection()
    try:
        with pytest.raises(Exception):
            conn.query("INSERT INTO foo VALUES (bad_syntax_here")

        # This write must actually commit, not silently be skipped because
        # in_transaction() was left True by the failed statement above.
        conn.query("INSERT INTO foo VALUES (99)")
    finally:
        conn.close()
    db.close()

    db2 = records.Database(file_db_url)
    try:
        assert db2.query("SELECT count(*) AS n FROM foo")[0].n == 1
        assert db2.query("SELECT a FROM foo")[0].a == 99
    finally:
        db2.close()
