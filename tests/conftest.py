"""Shared pytest fixtures for integration and E2E tests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure import database as infra_db
from app.infrastructure import pdf_generator
from app.models import Base, Bill, BillItem, Customer, Service, Staff
from app.repositories.settings_repository import SettingsRepository
from app.services.settings_service import SettingsService
import app.services.backup_service as backup_service
import app.services.restore_service as restore_service


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": True},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    monkeypatch.setattr(infra_db, "engine", engine)
    monkeypatch.setattr(infra_db, "SessionLocal", session_factory)
    Base.metadata.create_all(bind=engine)
    yield db_path
    engine.dispose()


@pytest.fixture
def receipts_dir(tmp_path, monkeypatch) -> Path:
    receipts_path = tmp_path / "receipts"
    monkeypatch.setattr(pdf_generator, "RECEIPTS_DIR", str(receipts_path))
    return receipts_path


@pytest.fixture
def settings_service(temp_db) -> SettingsService:
    repo = SettingsRepository(infra_db.db_session)
    return SettingsService(repo)


@pytest.fixture
def backup_paths(tmp_path, monkeypatch, temp_db) -> Path:
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(backup_service, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(backup_service, "DATABASE_FILE", str(temp_db))
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(temp_db))
    return backup_dir


@pytest.fixture
def sample_bill(temp_db) -> int:
    with infra_db.db_session() as db:
        customer = Customer(name="Test Customer", phone="1234567890")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Haircut", price=Decimal("50"), active=True)
        db.add_all([customer, staff, service])
        db.flush()

        bill = Bill(
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.utcnow(),
            subtotal=Decimal("50"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("50"),
            payment_method="Cash",
            payment_status="Paid",
        )
        bill.items.append(
            BillItem(
                service_id=service.id,
                quantity=1,
                unit_price=Decimal("50"),
                line_total=Decimal("50"),
            )
        )
        db.add(bill)
        db.flush()
        return bill.id
