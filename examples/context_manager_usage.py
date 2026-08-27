#!/usr/bin/env python3
# coding: utf-8

"""Demonstrates the recommended context-manager usage of records.Database.

The connection pool is closed automatically when the `with` block exits,
even if an exception is raised inside it.
"""

import records

DATABASE_URL = "sqlite:///:memory:"

with records.Database(DATABASE_URL) as db:
    db.query("CREATE TABLE persons (id INTEGER PRIMARY KEY, name TEXT)")
    db.query("INSERT INTO persons (name) VALUES (:name)", name="Ada Lovelace")

    rows = db.query("SELECT * FROM persons")
    print(rows.export("csv"))

print("db.open after the with block:", db.open)

try:
    with records.Database(DATABASE_URL) as db:
        db.query("SELECT * FROM does_not_exist")
except Exception as e:
    print("Exception raised inside the block:", e)

print("db.open after the exception:", db.open)
