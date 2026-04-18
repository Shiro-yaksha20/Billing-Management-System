"""Unit tests for ReportService."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.infrastructure import database as infra_db
from app.models import Bill, BillItem, Customer, Service, Staff
from app.repositories.bill_repository import BillRepository
from app.services.report_service import ReportService


def test_export_bills_creates_file(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Test", phone="123")
        staff = Staff(name="Staff", phone="", role="", active=True)
        service = Service(name="Cut", price=Decimal("10"), active=True)
        db.add_all([customer, staff, service])
        db.flush()

        bill = Bill(
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.utcnow(),
            subtotal=Decimal("10"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("10"),
            payment_method="Cash",
            payment_status="Paid",
        )
        bill.items.append(
            BillItem(
                service_id=service.id,
                quantity=1,
                unit_price=Decimal("10"),
                line_total=Decimal("10"),
            )
        )
        db.add(bill)
        db.flush()

    output_path = tmp_path / "export.xlsx"
    bill_repo = BillRepository(infra_db.db_session)
    service = ReportService(bill_repo)

    assert service.export_bills(str(output_path)) is True
    assert Path(output_path).exists()


def test_export_bills_csv_creates_file(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Test", phone="123")
        staff = Staff(name="Staff", phone="", role="", active=True)
        service = Service(name="Cut", price=Decimal("10"), active=True)
        db.add_all([customer, staff, service])
        db.flush()

        bill = Bill(
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.utcnow(),
            subtotal=Decimal("10"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("10"),
            payment_method="Cash",
            payment_status="Paid",
        )
        bill.items.append(
            BillItem(
                service_id=service.id,
                quantity=1,
                unit_price=Decimal("10"),
                line_total=Decimal("10"),
            )
        )
        db.add(bill)
        db.flush()

    output_path = tmp_path / "export.csv"
    bill_repo = BillRepository(infra_db.db_session)
    service = ReportService(bill_repo)

    assert service.export_bills_csv(str(output_path)) is True
    assert Path(output_path).exists()


def test_export_bills_pdf_summary_creates_file(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Test", phone="123")
        staff = Staff(name="Staff", phone="", role="", active=True)
        service = Service(name="Cut", price=Decimal("10"), active=True)
        db.add_all([customer, staff, service])
        db.flush()

        bill = Bill(
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.utcnow(),
            subtotal=Decimal("10"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("10"),
            payment_method="Cash",
            payment_status="Paid",
        )
        bill.items.append(
            BillItem(
                service_id=service.id,
                quantity=1,
                unit_price=Decimal("10"),
                line_total=Decimal("10"),
            )
        )
        db.add(bill)
        db.flush()

    output_path = tmp_path / "summary.pdf"
    bill_repo = BillRepository(infra_db.db_session)
    service = ReportService(bill_repo)

    assert service.export_bills_pdf_summary(str(output_path)) is True
    assert Path(output_path).exists()


def test_export_bills_handles_save_failure(temp_db, tmp_path, monkeypatch) -> None:
    bill_repo = BillRepository(infra_db.db_session)
    service = ReportService(bill_repo)

    class _FailWorkbook:
        def __init__(self):
            def cell_factory(*args, **kwargs):
                return type(
                    "Cell",
                    (),
                    {"font": None, "alignment": None},
                )()

            self.active = type(
                "Sheet",
                (),
                {"title": "Bills Export", "cell": cell_factory},
            )()

        def save(self, path):
            raise RuntimeError("fail")

    monkeypatch.setattr("app.services.report_service.Workbook", _FailWorkbook)

    assert service.export_bills(str(tmp_path / "export.xlsx")) is False


def test_export_bills_csv_handles_open_failure(temp_db, tmp_path, monkeypatch) -> None:
    bill_repo = BillRepository(infra_db.db_session)
    service = ReportService(bill_repo)

    def _open(*args, **kwargs):
        raise OSError("fail")

    monkeypatch.setattr(Path, "open", _open)

    assert service.export_bills_csv(str(tmp_path / "export.csv")) is False


def test_export_bills_pdf_summary_handles_failure(temp_db, tmp_path, monkeypatch) -> None:
    bill_repo = BillRepository(infra_db.db_session)
    service = ReportService(bill_repo)

    class _FailDoc:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, story):
            raise RuntimeError("fail")

    monkeypatch.setattr("app.services.report_service.SimpleDocTemplate", _FailDoc)

    assert service.export_bills_pdf_summary(str(tmp_path / "summary.pdf")) is False


def test_export_bills_pdf_summary_with_date_range(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Test", phone="123")
        staff = Staff(name="Staff", phone="", role="", active=True)
        service = Service(name="Cut", price=Decimal("10"), active=True)
        db.add_all([customer, staff, service])
        db.flush()

        bill = Bill(
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.utcnow(),
            subtotal=Decimal("10"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("10"),
            payment_method="Cash",
            payment_status="Paid",
        )
        bill.items.append(
            BillItem(
                service_id=service.id,
                quantity=1,
                unit_price=Decimal("10"),
                line_total=Decimal("10"),
            )
        )
        db.add(bill)
        db.flush()

    output_path = tmp_path / "summary_range.pdf"
    bill_repo = BillRepository(infra_db.db_session)
    report_service = ReportService(bill_repo)

    assert report_service.export_bills_pdf_summary(
        str(output_path),
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
    ) is True
