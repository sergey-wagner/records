"""Regression test for #142 / #206 / #212.

Excel export previously broke when the installed `openpyxl` version did
not satisfy both `records`' own pin and the version a co-installed
`pandas` requires. This test guards against that class of failure by
exercising `RecordCollection.export()` against the two Excel-based
formats (`xlsx` via `openpyxl`, `xls` via `xlwt`/`xlrd`) and asserting
that no exception is raised.
"""

import records


def _sample_rows():
    return records.RecordCollection(
        records.Record(["id", "name"], [i, "row-{}".format(i)]) for i in range(3)
    )


def test_export_xlsx_does_not_raise():
    rows = _sample_rows()
    exported = rows.export("xlsx")
    assert exported


def test_export_xls_does_not_raise():
    rows = _sample_rows()
    exported = rows.export("xls")
    assert exported
