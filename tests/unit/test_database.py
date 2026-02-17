"""Unit tests for database session management."""

from __future__ import annotations

import pytest

from app.infrastructure import database as infra_db
from app.models import Customer


def test_init_db_creates_tables(temp_db) -> None:
    infra_db.init_db()


def test_db_session_commits(temp_db) -> None:
    with infra_db.db_session() as db:
        db.add(Customer(name="Alex", phone="123"))

    with infra_db.db_session() as db:
        count = db.query(Customer).count()
    assert count == 1


def test_db_session_rolls_back(temp_db) -> None:
    with pytest.raises(ValueError):
        with infra_db.db_session() as db:
            db.add(Customer(name="Fail", phone="000"))
            raise ValueError("boom")

    with infra_db.db_session() as db:
        count = db.query(Customer).count()
    assert count == 0
