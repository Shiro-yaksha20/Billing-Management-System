"""Unit tests for BillingService."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta

import pytest

from app.dto.bill_dto import BillItemInput, BillOptions
from app.exceptions.business_errors import (
    CustomerNotFoundError,
    DiscountExceedsSubtotalError,
    InsufficientDataError,
    StaffNotFoundError,
    NegativeTotalError,
)
from app.exceptions.validation_errors import ValidationError
from app.models import Bill, Customer, Staff
from app.services.billing_service import BillingService


@dataclass
class _StubCustomer:
    id: int


@dataclass
class _StubStaff:
    id: int


class _StubBillRepo:
    def __init__(self) -> None:
        self._next_id = 1
        self.last_bill: Optional[Bill] = None
        self.updated_pdf_path: Optional[str] = None

    def add(self, bill: Bill) -> Bill:
        bill.id = self._next_id
        self._next_id += 1
        self.last_bill = bill
        return bill

    def update_bill_number(self, bill_id: int, bill_number: str) -> bool:
        if not self.last_bill or self.last_bill.id != bill_id:
            return False
        self.last_bill.bill_number = bill_number
        return True

    def update_whatsapp_status(self, bill_id, status, error=None):
        pass

    def update_pdf_path(self, bill_id, pdf_path):
        self.updated_pdf_path = pdf_path
        return True

    def get_with_details(self, bill_id: int):
        return self.last_bill


class _StubCustomerRepo:
    def __init__(self, exists: bool = True) -> None:
        self.exists = exists
        self.updated_last_visit: List[int] = []

    def get_by_id(self, customer_id: int):
        return _StubCustomer(id=customer_id) if self.exists else None

    def update_last_visit(self, customer_id: int, last_visit_at) -> bool:
        self.updated_last_visit.append(customer_id)
        return True


class _StubStaffRepo:
    def __init__(self, exists: bool = True) -> None:
        self.exists = exists

    def get_by_id(self, staff_id: int):
        return _StubStaff(id=staff_id) if self.exists else None


class _StubSettingsService:
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        if key == "bill_number_prefix":
            return "INV"
        return default


class _StubBillQueryRepo:
    def __init__(self, bills=None, recent=None) -> None:
        self._bills = bills or []
        self._recent = recent or []

    def search(
        self,
        bill_number=None,
        customer_name=None,
        start_date=None,
        end_date=None,
        payment_status=None,
        payment_method=None,
    ):
        return list(self._bills)

    def find_by_date_range(self, start_date, end_date):
        return list(self._bills)

    def find_recent(self, limit=5):
        return list(self._recent)

    def get_daily_stats(self, target_date):
        paid_total = sum(
            (Decimal(b.total or 0) for b in self._bills if (b.payment_status or "") == "Paid"),
            Decimal("0"),
        )
        pending_total = sum(
            (Decimal(b.total or 0) for b in self._bills if (b.payment_status or "") == "Pending"),
            Decimal("0"),
        )
        pending_count = sum(1 for b in self._bills if (b.payment_status or "") == "Pending")
        unique_customers = len({b.customer_id for b in self._bills if b.customer_id})
        return {
            "total_bills": len(self._bills),
            "paid_total": paid_total,
            "pending_total": pending_total,
            "pending_count": pending_count,
            "unique_customers": unique_customers,
        }


class _StubBill:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _service(customer_exists: bool = True, staff_exists: bool = True) -> BillingService:
    return BillingService(
        bill_repo=_StubBillRepo(),
        customer_repo=_StubCustomerRepo(exists=customer_exists),
        staff_repo=_StubStaffRepo(exists=staff_exists),
        settings_service=_StubSettingsService(),
    )


def test_calculate_discount_flat_exceeds_subtotal_raises() -> None:
    service = _service()
    with pytest.raises(DiscountExceedsSubtotalError):
        service.calculate_discount(Decimal("100"), "flat", Decimal("200"))


def test_calculate_discount_percent_over_100_raises() -> None:
    service = _service()
    with pytest.raises(ValidationError):
        service.calculate_discount(Decimal("100"), "percent", Decimal("150"))


def test_create_bill_requires_items() -> None:
    service = _service()
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    with pytest.raises(InsufficientDataError):
        service.create_bill(customer_id=1, staff_id=1, items=[], options=options)


def test_create_bill_requires_customer() -> None:
    service = _service(customer_exists=False)
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [BillItemInput(service_id=1, quantity=1, unit_price=Decimal("50"))]
    with pytest.raises(CustomerNotFoundError):
        service.create_bill(customer_id=1, staff_id=1, items=items, options=options)


def test_create_bill_requires_staff() -> None:
    service = _service(staff_exists=False)
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [BillItemInput(service_id=1, quantity=1, unit_price=Decimal("50"))]
    with pytest.raises(StaffNotFoundError):
        service.create_bill(customer_id=1, staff_id=1, items=items, options=options)


def test_create_bill_sets_bill_number() -> None:
    bill_repo = _StubBillRepo()
    customer_repo = _StubCustomerRepo()
    staff_repo = _StubStaffRepo()
    service = BillingService(
        bill_repo=bill_repo,
        customer_repo=customer_repo,
        staff_repo=staff_repo,
        settings_service=_StubSettingsService(),
    )
    options = BillOptions(
        discount_type="flat",
        discount_value=Decimal("10"),
        tax_percent=Decimal("5"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [BillItemInput(service_id=1, quantity=2, unit_price=Decimal("50"))]

    bill = service.create_bill(customer_id=1, staff_id=1, items=items, options=options)

    assert bill.id == 1
    assert bill.bill_number == f"INV-{bill.bill_datetime.year}-0001"
    assert bill.total == Decimal("94.5")


def test_create_bill_keeps_existing_bill_number() -> None:
    bill_repo = _StubBillRepo()
    customer_repo = _StubCustomerRepo()
    staff_repo = _StubStaffRepo()
    service = BillingService(
        bill_repo=bill_repo,
        customer_repo=customer_repo,
        staff_repo=staff_repo,
        settings_service=_StubSettingsService(),
    )
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [BillItemInput(service_id=1, quantity=1, unit_price=Decimal("10"))]

    bill = Bill(
        customer_id=1,
        staff_id=1,
        bill_datetime=datetime.utcnow(),
        subtotal=Decimal("10"),
        discount_amount=Decimal("0"),
        discount_type="none",
        tax_amount=Decimal("0"),
        tax_percent=Decimal("0"),
        total=Decimal("10"),
        payment_method="Cash",
        payment_status="Paid",
        bill_number="B1",
    )

    class _Repo(_StubBillRepo):
        def add(self, incoming):
            return bill

    service = BillingService(
        bill_repo=_Repo(),
        customer_repo=customer_repo,
        staff_repo=staff_repo,
        settings_service=_StubSettingsService(),
    )

    result = service.create_bill(customer_id=1, staff_id=1, items=items, options=options)

    assert result.bill_number == "B1"


def test_to_bill_data_includes_customer_info() -> None:
    customer = Customer(id=1, name="Alex", phone="123")
    bill = Bill(
        id=1,
        bill_number="1",
        customer_id=1,
        staff_id=1,
        bill_datetime=datetime.utcnow(),
        subtotal=Decimal("10"),
        discount_amount=Decimal("0"),
        discount_type="none",
        tax_amount=Decimal("0"),
        tax_percent=Decimal("0"),
        total=Decimal("10"),
        payment_method="Cash",
        status="Paid",
        pdf_path=None,
        whatsapp_status="Not Sent",
        whatsapp_last_error=None,
        transaction_id=None,
        payment_status="Paid",
    )
    bill.customer = customer

    result = BillingService._to_bill_data(bill)

    assert result.customer_name == "Alex"
    assert result.customer_phone == "123"


def test_get_dashboard_stats_empty_returns_zero() -> None:
    service = BillingService(
        bill_repo=_StubBillQueryRepo(bills=[], recent=[]),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    stats = service.get_dashboard_stats()

    assert stats.today_sales == Decimal("0")
    assert stats.pending_amount == Decimal("0")
    assert stats.today_bills_count == 0
    assert stats.pending_count == 0
    assert stats.today_customers == 0


def test_to_bill_data_handles_inspect_failure() -> None:
    class _Bill:
        def __init__(self):
            self.id = 1
            self.bill_number = "1"
            self.customer_id = 1
            self.staff_id = 1
            self.bill_datetime = datetime.utcnow()
            self.subtotal = Decimal("10")
            self.discount_amount = Decimal("0")
            self.discount_type = "none"
            self.tax_amount = Decimal("0")
            self.tax_percent = Decimal("0")
            self.total = Decimal("10")
            self.payment_method = "Cash"
            self.status = "Paid"
            self.pdf_path = None
            self.whatsapp_status = None
            self.whatsapp_last_error = None
            self.transaction_id = None
            self.payment_status = None

    result = BillingService._to_bill_data(_Bill())

    assert result.customer_name is None


def test_update_whatsapp_status_calls_repo() -> None:
    calls = {}

    class _StubRepo(_StubBillRepo):
        def update_whatsapp_status(self, bill_id, status, error=None):
            calls["bill_id"] = bill_id
            calls["status"] = status
            calls["error"] = error

    service = BillingService(
        bill_repo=_StubRepo(),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    service.update_whatsapp_status(1, "Sent", "")

    assert calls["bill_id"] == 1
    assert calls["status"] == "Sent"


def test_calculate_discount_flat_valid_returns_amount() -> None:
    service = _service()
    result = service.calculate_discount(Decimal("100"), "flat", Decimal("20"))
    assert result == Decimal("20")


def test_calculate_discount_percent_valid_returns_amount() -> None:
    service = _service()
    result = service.calculate_discount(Decimal("200"), "percent", Decimal("10"))
    assert result == Decimal("20")


def test_calculate_discount_none_returns_zero() -> None:
    service = _service()
    result = service.calculate_discount(Decimal("200"), "none", Decimal("0"))
    assert result == Decimal("0")


def test_calculate_discount_negative_value_raises() -> None:
    service = _service()
    with pytest.raises(ValidationError):
        service.calculate_discount(Decimal("100"), "flat", Decimal("-5"))


def test_calculate_discount_invalid_type_raises() -> None:
    service = _service()
    with pytest.raises(ValidationError):
        service.calculate_discount(Decimal("100"), "unknown", Decimal("5"))


def test_calculate_tax_valid_returns_amount() -> None:
    service = _service()
    result = service.calculate_tax(Decimal("100"), Decimal("5"))
    assert result == Decimal("5")


def test_calculate_tax_negative_percent_raises() -> None:
    service = _service()
    with pytest.raises(ValidationError):
        service.calculate_tax(Decimal("100"), Decimal("-1"))


def test_create_bill_negative_total_raises() -> None:
    service = _service()
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [BillItemInput(service_id=1, quantity=1, unit_price=Decimal("-50"))]

    with pytest.raises(NegativeTotalError):
        service.create_bill(customer_id=1, staff_id=1, items=items, options=options)


def test_get_bills_with_filters_returns_data() -> None:
    bills = [
        _StubBill(
            id=1,
            bill_number="1",
            customer_id=1,
            staff_id=1,
            bill_datetime=None,
            subtotal=Decimal("10"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("10"),
            payment_method="Cash",
            status="Paid",
            pdf_path=None,
            whatsapp_status="Not Sent",
            whatsapp_last_error=None,
            transaction_id=None,
            payment_status="Paid",
        )
    ]
    service = BillingService(
        bill_repo=_StubBillQueryRepo(bills=bills),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    results = service.get_bills(
        bill_number="1",
        customer_name="Alex",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        payment_status="Paid",
        payment_method="Cash",
    )

    assert len(results) == 1


def test_generate_receipt_returns_path(monkeypatch) -> None:
    bill = Bill(
        id=1,
        bill_number="1",
        customer_id=1,
        staff_id=1,
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
    bill.customer = Customer(id=1, name="Alex", phone="999")
    bill.staff = Staff(id=1, name="Stylist", phone="", role="", active=True)
    bill.items = []

    repo = _StubBillRepo()
    repo.last_bill = bill
    service = BillingService(
        bill_repo=repo,
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    def _fake_generate(receipt, settings_service):
        return "receipt.pdf"

    monkeypatch.setattr("app.services.billing_service.generate_receipt_pdf", _fake_generate)

    assert service.generate_receipt(1) == "receipt.pdf"
    assert repo.updated_pdf_path == "receipt.pdf"
