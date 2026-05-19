"""Additional unit tests for ReportService."""

from __future__ import annotations

from datetime import datetime

from app.services.report_service import ReportService


class _BillItem:
    def __init__(self) -> None:
        self.service = None
        self.quantity = 1
        self.unit_price = None
        self.line_total = None


class _Bill:
    def __init__(self) -> None:
        self.bill_number = None
        self.id = 1
        self.bill_datetime = None
        self.customer = None
        self.staff = None
        self.items = [_BillItem()]
        self.subtotal = None
        self.discount_amount = None
        self.tax_percent = None
        self.tax_amount = None
        self.total = None
        self.payment_method = None
        self.payment_status = None
        self.transaction_id = None


class _Repo:
    def __init__(self, bills):
        self._bills = bills

    def find_for_export(self, start_date=None, end_date=None, customer_id=None):
        return list(self._bills)


def test_export_bills_handles_none_fields(tmp_path) -> None:
    service = ReportService(_Repo([_Bill()]))

    assert service.export_bills(str(tmp_path / "export.xlsx")) is True


def test_export_bills_csv_handles_missing_relations(tmp_path) -> None:
    service = ReportService(_Repo([_Bill()]))

    assert service.export_bills_csv(str(tmp_path / "export.csv")) is True


def test_export_bills_pdf_summary_handles_missing_status(monkeypatch) -> None:
    class _Doc:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, story):
            return None

    bill = _Bill()
    bill.bill_datetime = datetime.now()
    service = ReportService(_Repo([bill]))

    monkeypatch.setattr("app.services.report_service.SimpleDocTemplate", _Doc)

    assert service.export_bills_pdf_summary("summary.pdf") is True
