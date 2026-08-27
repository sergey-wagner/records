import inspect

import records


RECORD_METHODS = [
    "__init__",
    "keys",
    "values",
    "__getitem__",
    "__getattr__",
    "get",
    "as_dict",
    "export",
]

RECORD_COLLECTION_METHODS = [
    "__init__",
    "__iter__",
    "__next__",
    "__getitem__",
    "__len__",
    "export",
    "all",
    "as_dict",
    "first",
    "one",
    "scalar",
]

DATABASE_METHODS = [
    "__init__",
    "get_engine",
    "close",
    "__enter__",
    "__exit__",
    "get_table_names",
    "get_connection",
    "query",
    "bulk_query",
    "query_file",
    "bulk_query_file",
    "transaction",
]

CONNECTION_METHODS = [
    "__init__",
    "close",
    "__enter__",
    "__exit__",
    "query",
    "bulk_query",
    "query_file",
    "bulk_query_file",
    "transaction",
]


def _assert_fully_annotated(func):
    signature = inspect.signature(func)
    assert signature.return_annotation is not inspect.Signature.empty, (
        "{} is missing a return type annotation".format(func.__qualname__)
    )
    for name, param in signature.parameters.items():
        if name == "self":
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        assert param.annotation is not inspect.Parameter.empty, (
            "{} parameter '{}' is missing a type annotation".format(
                func.__qualname__, name
            )
        )


class TestRecordTypeHints:
    def test_methods_are_annotated(self):
        for name in RECORD_METHODS:
            _assert_fully_annotated(getattr(records.Record, name))

    def test_dataset_property_is_annotated(self):
        fget = records.Record.dataset.fget
        assert inspect.signature(fget).return_annotation is records.tablib.Dataset


class TestRecordCollectionTypeHints:
    def test_methods_are_annotated(self):
        for name in RECORD_COLLECTION_METHODS:
            _assert_fully_annotated(getattr(records.RecordCollection, name))

    def test_dataset_property_is_annotated(self):
        fget = records.RecordCollection.dataset.fget
        assert inspect.signature(fget).return_annotation is records.tablib.Dataset


class TestDatabaseTypeHints:
    def test_methods_are_annotated(self):
        for name in DATABASE_METHODS:
            _assert_fully_annotated(getattr(records.Database, name))

    def test_query_returns_record_collection(self):
        signature = inspect.signature(records.Database.query)
        assert signature.return_annotation is records.RecordCollection

    def test_exit_does_not_shadow_exc_module(self):
        # Regression test: the `__exit__` parameter must not be named `exc`,
        # since that shadows the module-level `sqlalchemy.exc` import.
        params = list(inspect.signature(records.Database.__exit__).parameters)
        assert "exc" not in params


class TestConnectionTypeHints:
    def test_methods_are_annotated(self):
        for name in CONNECTION_METHODS:
            _assert_fully_annotated(getattr(records.Connection, name))

    def test_query_returns_record_collection(self):
        signature = inspect.signature(records.Connection.query)
        assert signature.return_annotation is records.RecordCollection

    def test_exit_does_not_shadow_exc_module(self):
        # Regression test: the `__exit__` parameter must not be named `exc`,
        # since that shadows the module-level `sqlalchemy.exc` import.
        params = list(inspect.signature(records.Connection.__exit__).parameters)
        assert "exc" not in params
