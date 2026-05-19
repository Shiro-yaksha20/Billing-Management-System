"""End-to-end export flow tests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.infrastructure import database as infra_db
from app.models import Bill, BillItem, Customer, Service, Staff
from app.repositories.bill_repository import BillRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.report_service import ReportService
from app.services.settings_service import SettingsService


def _seed_bill() -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Test Customer", phone="1234567890")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Haircut", price=Decimal("50"), active=True)
        db.add_all([customer, staff, service])
        db.flush()

        bill = Bill(
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.now(),
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


def test_export_flow_excel(temp_db, tmp_path) -> None:
    _seed_bill()
    repo = BillRepository(infra_db.db_session)
    report_service = ReportService(repo, SettingsService(SettingsRepository(infra_db.db_session)))

    output_path = tmp_path / "export.xlsx"

    assert report_service.export_bills(str(output_path)) is True
    assert Path(output_path).exists()


def test_export_flow_csv(temp_db, tmp_path) -> None:
    _seed_bill()
    repo = BillRepository(infra_db.db_session)
    report_service = ReportService(repo, SettingsService(SettingsRepository(infra_db.db_session)))

    output_path = tmp_path / "export.csv"

    assert report_service.export_bills_csv(str(output_path)) is True
    assert Path(output_path).exists()


def test_export_flow_pdf_summary(temp_db, tmp_path) -> None:
    _seed_bill()
    repo = BillRepository(infra_db.db_session)
    report_service = ReportService(repo, SettingsService(SettingsRepository(infra_db.db_session)))

    output_path = tmp_path / "summary.pdf"

    assert report_service.export_bills_pdf_summary(str(output_path)) is True
    assert Path(output_path).exists()
