"""Additional migration script tests."""

from __future__ import annotations

from sqlalchemy import create_engine

import app.migrate_bill_receipt_fields as migrate_bill_receipt_fields


def test_migrate_bill_receipt_fields_idempotent(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "bill.db"
    engine = create_engine(f"sqlite:///{db_path}")

    monkeypatch.setattr(migrate_bill_receipt_fields, "engine", engine)

    migrate_bill_receipt_fields.migrate()
    migrate_bill_receipt_fields.migrate()
