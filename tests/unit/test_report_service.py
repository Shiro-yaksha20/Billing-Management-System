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
            bill_datetime=datetime.now(),
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
            bill_datetime=datetime.now(),
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
            bill_datetime=datetime.now(),
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
            bill_datetime=datetime.now(),
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
        start_date=datetime.now(),
        end_date=datetime.now(),
    ) is True


def test_export_bills_with_date_range_filters(tmp_path) -> None:
    captured = {}

    class _Repo:
        def find_for_export(self, start_date=None, end_date=None, customer_id=None):
            captured["start_date"] = start_date
            captured["end_date"] = end_date
            captured["customer_id"] = customer_id
            return []

    service = ReportService(_Repo())
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 2)

    assert service.export_bills(str(tmp_path / "export.xlsx"), start_date=start_date, end_date=end_date)
    assert captured["start_date"] == start_date
    assert captured["end_date"] == end_date


def test_export_bills_with_customer_filter(tmp_path) -> None:
    captured = {}

    class _Repo:
        def find_for_export(self, start_date=None, end_date=None, customer_id=None):
            captured["customer_id"] = customer_id
            return []

    service = ReportService(_Repo())

    assert service.export_bills(str(tmp_path / "export.xlsx"), customer_id=7)
    assert captured["customer_id"] == 7


def test_export_bills_csv_with_date_range_filters(tmp_path) -> None:
    captured = {}

    class _Repo:
        def find_for_export(self, start_date=None, end_date=None, customer_id=None):
            captured["start_date"] = start_date
            captured["end_date"] = end_date
            return []

    service = ReportService(_Repo())
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 2)

    assert service.export_bills_csv(str(tmp_path / "export.csv"), start_date=start_date, end_date=end_date)
    assert captured["start_date"] == start_date
    assert captured["end_date"] == end_date


def test_export_bills_csv_empty_list_creates_header(tmp_path) -> None:
    class _Repo:
        def find_for_export(self, start_date=None, end_date=None, customer_id=None):
            return []

    service = ReportService(_Repo())
    output_path = tmp_path / "export.csv"

    assert service.export_bills_csv(str(output_path)) is True
    assert output_path.read_text(encoding="utf-8").splitlines()[0].startswith("Bill #")


def test_export_bills_pdf_summary_truncates(monkeypatch) -> None:
    captured = {}

    class _Repo:
        def find_for_export(self, start_date=None, end_date=None, customer_id=None):
            return [
                type(
                    "Bill",
                    (),
                    {
                        "id": index,
                        "bill_number": f"B{index}",
                        "bill_datetime": datetime(2024, 1, 1),
                        "customer": type("Customer", (), {"name": "Alex"})(),
                        "total": Decimal("1"),
                        "payment_status": "Paid",
                    },
                )()
                for index in range(55)
            ]

    class _Doc:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, story):
            captured["story"] = story

    monkeypatch.setattr("app.services.report_service.SimpleDocTemplate", _Doc)

    service = ReportService(_Repo())

    assert service.export_bills_pdf_summary("summary.pdf") is True

    texts = [getattr(item, "text", "") for item in captured.get("story", [])]
    assert any("Showing first 50" in text for text in texts)


def test_export_bills_pdf_summary_all_dates_label(monkeypatch) -> None:
    captured = {}

    class _Repo:
        def find_for_export(self, start_date=None, end_date=None, customer_id=None):
            return []

    class _Doc:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, story):
            captured["story"] = story

    monkeypatch.setattr("app.services.report_service.SimpleDocTemplate", _Doc)

    service = ReportService(_Repo())

    assert service.export_bills_pdf_summary("summary.pdf") is True

    texts = [getattr(item, "text", "") for item in captured.get("story", [])]
    assert any("All Dates" in text for text in texts)


def test_export_bills_pdf_summary_handles_pending_and_missing_status(monkeypatch) -> None:
    class _Repo:
        def find_for_export(self, start_date=None, end_date=None, customer_id=None):
            return [
                type(
                    "Bill",
                    (),
                    {
                        "id": 1,
                        "bill_number": "B1",
                        "bill_datetime": datetime(2024, 1, 1),
                        "customer": type("Customer", (), {"name": "Alex"})(),
                        "total": Decimal("10"),
                        "payment_status": "Pending",
                    },
                )(),
                type(
                    "Bill",
                    (),
                    {
                        "id": 2,
                        "bill_number": "B2",
                        "bill_datetime": datetime(2024, 1, 1),
                        "customer": type("Customer", (), {"name": "Alex"})(),
                        "total": Decimal("5"),
                        "payment_status": None,
                    },
                )(),
            ]

    class _Doc:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, story):
            return None

    monkeypatch.setattr("app.services.report_service.SimpleDocTemplate", _Doc)

    service = ReportService(_Repo())

    assert service.export_bills_pdf_summary("summary.pdf") is True
