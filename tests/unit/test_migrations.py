"""Unit tests for migration scripts."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import OperationalError

from app.infrastructure import database as infra_db
import app.migrate_service_schema as migrate_service_schema
import app.migrate_bill_receipt_fields as migrate_bill_receipt_fields


def test_migrate_service_table_runs(temp_db, monkeypatch) -> None:
    monkeypatch.setattr(migrate_service_schema, "engine", infra_db.engine)

    migrate_service_schema.migrate_service_table()


def test_migrate_bill_receipt_fields_runs(temp_db, monkeypatch) -> None:
    monkeypatch.setattr(migrate_bill_receipt_fields, "engine", infra_db.engine)

    migrate_bill_receipt_fields.migrate()


def test_migrate_service_table_adds_columns(monkeypatch):
    calls = {"alter": 0, "update": 0}

    class _Result:
        rowcount = 0

    class _Conn:
        def execute(self, stmt):
            sql = str(stmt)
            if sql.startswith("SELECT"):
                raise OperationalError("select", {}, Exception("missing"))
            if sql.startswith("ALTER TABLE"):
                calls["alter"] += 1
            if sql.startswith("UPDATE service"):
                calls["update"] += 1
                return _Result()
            return _Result()

    class _Begin:
        def __enter__(self):
            return _Conn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Engine:
        def begin(self):
            return _Begin()

    monkeypatch.setattr(migrate_service_schema, "engine", _Engine())

    migrate_service_schema.migrate_service_table()

    assert calls["alter"] == 4
    assert calls["update"] == 1


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_migrate_bill_receipt_fields_main(temp_db, monkeypatch) -> None:
    import runpy

    monkeypatch.setattr(migrate_bill_receipt_fields, "engine", infra_db.engine)

    runpy.run_module("app.migrate_bill_receipt_fields", run_name="__main__")


def test_migrate_service_table_invalid_column(monkeypatch) -> None:
    class _Result:
        rowcount = 0

    class _Conn:
        def execute(self, stmt):
            return _Result()

    class _Begin:
        def __enter__(self):
            return _Conn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Engine:
        def begin(self):
            return _Begin()

    monkeypatch.setattr(migrate_service_schema, "engine", _Engine())

    with pytest.raises(ValueError, match="Invalid column name"):
        migrate_service_schema.migrate_service_table(allowed_columns=set())


def test_migrate_service_table_alter_failure(monkeypatch) -> None:
    class _Conn:
        def execute(self, stmt):
            sql = str(stmt)
            if sql.startswith("SELECT"):
                raise OperationalError("select", {}, Exception("missing"))
            raise OperationalError("alter", {}, Exception("fail"))

    class _Begin:
        def __enter__(self):
            return _Conn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Engine:
        def begin(self):
            return _Begin()

    monkeypatch.setattr(migrate_service_schema, "engine", _Engine())

    with pytest.raises(OperationalError):
        migrate_service_schema.migrate_service_table()


def test_migrate_service_schema_main(temp_db, monkeypatch) -> None:
    monkeypatch.setattr(migrate_service_schema, "engine", infra_db.engine)

    migrate_service_schema.run_cli()


def test_migrate_service_schema_main_failure() -> None:
    def _fail():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        migrate_service_schema.run_cli(migrate_fn=_fail)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_migrate_service_schema_run_module(temp_db, monkeypatch) -> None:
    import runpy

    monkeypatch.setattr(migrate_service_schema, "engine", infra_db.engine)

    runpy.run_module("app.migrate_service_schema", run_name="__main__")


def test_migrate_bill_receipt_fields_adds_columns(tmp_path, monkeypatch) -> None:
    from sqlalchemy import create_engine, text

    db_path = tmp_path / "bill.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE bill (id INTEGER PRIMARY KEY, total NUMERIC(10,2))"
        ))

    monkeypatch.setattr(migrate_bill_receipt_fields, "engine", engine)

    migrate_bill_receipt_fields.migrate()
