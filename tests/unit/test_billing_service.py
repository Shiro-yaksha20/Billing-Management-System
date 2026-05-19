"""Unit tests for BillingService."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

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
from app.models import Bill, BillItem, Customer, Service, Staff
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

    def update_payment_status(self, bill_id: int, payment_status: str) -> bool:
        return True


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
    assert bill.status == "Paid"
    assert bill.payment_status == "Paid"
    assert bill.bill_datetime.tzinfo is None


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
        bill_datetime=datetime.now(),
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
        bill_datetime=datetime.now(),
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
            self.bill_datetime = datetime.now()
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


def test_cancel_bill_calls_repo() -> None:
    calls = {}

    class _StubRepo(_StubBillRepo):
        def update_payment_status(self, bill_id: int, payment_status: str) -> bool:
            calls["bill_id"] = bill_id
            calls["payment_status"] = payment_status
            return True

    service = BillingService(
        bill_repo=_StubRepo(),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    result = service.cancel_bill(1)

    assert result is True
    assert calls["bill_id"] == 1
    assert calls["payment_status"] == "Cancelled"


def test_calculate_discount_flat_valid_returns_amount() -> None:
    service = _service()
    result = service.calculate_discount(Decimal("100"), "flat", Decimal("20"))
    assert result == Decimal("20")


def test_calculate_discount_percent_valid_returns_amount() -> None:
    service = _service()
    result = service.calculate_discount(Decimal("200"), "percent", Decimal("10"))
    assert result == Decimal("20")


def test_calculate_discount_percent_hundred_returns_subtotal() -> None:
    service = _service()
    result = service.calculate_discount(Decimal("200"), "percent", Decimal("100"))
    assert result == Decimal("200")


def test_calculate_discount_percent_zero_subtotal_returns_zero() -> None:
    service = _service()
    result = service.calculate_discount(Decimal("0"), "percent", Decimal("10"))
    assert result == Decimal("0")


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


def test_calculate_tax_zero_percent_returns_zero() -> None:
    service = _service()
    result = service.calculate_tax(Decimal("100"), Decimal("0"))
    assert result == Decimal("0")


def test_calculate_tax_hundred_percent_returns_amount() -> None:
    service = _service()
    result = service.calculate_tax(Decimal("100"), Decimal("100"))
    assert result == Decimal("100")


def test_calculate_tax_negative_percent_raises() -> None:
    service = _service()
    with pytest.raises(ValidationError):
        service.calculate_tax(Decimal("100"), Decimal("-1"))


def test_calculate_tax_over_hundred_percent_raises() -> None:
    service = _service()
    with pytest.raises(ValidationError):
        service.calculate_tax(Decimal("100"), Decimal("101"))


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
        start_date=datetime.now(),
        end_date=datetime.now(),
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


def test_create_bill_calls_update_last_visit() -> None:
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
    items = [BillItemInput(service_id=1, quantity=1, unit_price=Decimal("20"))]

    service.create_bill(customer_id=7, staff_id=1, items=items, options=options)

    assert customer_repo.updated_last_visit == [7]


def test_create_bill_multiple_items_sums_correctly() -> None:
    service = _service()
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [
        BillItemInput(service_id=1, quantity=2, unit_price=Decimal("50")),
        BillItemInput(service_id=2, quantity=1, unit_price=Decimal("20")),
    ]

    bill = service.create_bill(customer_id=1, staff_id=1, items=items, options=options)

    assert bill.subtotal == Decimal("120")
    assert bill.total == Decimal("120")


def test_create_bill_percent_discount_and_tax_combined() -> None:
    service = _service()
    options = BillOptions(
        discount_type="percent",
        discount_value=Decimal("10"),
        tax_percent=Decimal("5"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [BillItemInput(service_id=1, quantity=2, unit_price=Decimal("50"))]

    bill = service.create_bill(customer_id=1, staff_id=1, items=items, options=options)

    assert bill.subtotal == Decimal("100")
    assert bill.discount_amount == Decimal("10")
    assert bill.tax_amount == Decimal("4.5")
    assert bill.total == Decimal("94.5")


def test_get_bills_without_filters_returns_all() -> None:
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
        ),
        _StubBill(
            id=2,
            bill_number="2",
            customer_id=2,
            staff_id=1,
            bill_datetime=None,
            subtotal=Decimal("20"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("20"),
            payment_method="Cash",
            status="Pending",
            pdf_path=None,
            whatsapp_status="Not Sent",
            whatsapp_last_error=None,
            transaction_id=None,
            payment_status="Pending",
        ),
    ]
    service = BillingService(
        bill_repo=_StubBillQueryRepo(bills=bills),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    results = service.get_bills()

    assert len(results) == 2


def test_get_bills_returns_empty_when_no_matches() -> None:
    service = BillingService(
        bill_repo=_StubBillQueryRepo(bills=[]),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    results = service.get_bills(bill_number="NOT-FOUND")

    assert results == []


def test_get_dashboard_stats_with_mixed_paid_pending() -> None:
    bills = [
        _StubBill(customer_id=1, total=Decimal("30"), payment_status="Paid"),
        _StubBill(customer_id=2, total=Decimal("20"), payment_status="Pending"),
        _StubBill(customer_id=1, total=Decimal("10"), payment_status="Pending"),
    ]
    service = BillingService(
        bill_repo=_StubBillQueryRepo(bills=bills, recent=[]),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    stats = service.get_dashboard_stats()

    assert stats.today_sales == Decimal("30")
    assert stats.pending_amount == Decimal("30")
    assert stats.pending_count == 2
    assert stats.today_customers == 2


def test_generate_receipt_bill_not_found_raises() -> None:
    class _MissingRepo(_StubBillRepo):
        def get_with_details(self, bill_id: int):
            return None

    service = BillingService(
        bill_repo=_MissingRepo(),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    with pytest.raises(ValidationError, match="Bill not found"):
        service.generate_receipt(1)


def test_generate_receipt_builds_item_mapping(monkeypatch) -> None:
    captured = {}
    bill = Bill(
        id=1,
        bill_number="1",
        customer_id=1,
        staff_id=1,
        bill_datetime=datetime.now(),
        subtotal=Decimal("100"),
        discount_amount=Decimal("0"),
        discount_type="none",
        tax_amount=Decimal("0"),
        tax_percent=Decimal("0"),
        total=Decimal("100"),
        payment_method="Cash",
        payment_status="Paid",
    )
    bill.customer = Customer(id=1, name="Alex", phone="999")
    bill.staff = Staff(id=1, name="Stylist", phone="", role="", active=True)
    service_item = Service(
        id=9,
        name="Hair Cut",
        display_name="Hair Cut Premium",
        variant="Premium",
        active=True,
    )
    bill.items = [
        BillItem(
            id=1,
            service_id=9,
            quantity=2,
            unit_price=Decimal("50"),
            line_total=Decimal("100"),
            service=service_item,
        )
    ]

    repo = _StubBillRepo()
    repo.last_bill = bill
    service = BillingService(
        bill_repo=repo,
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )

    def _fake_generate(receipt, settings_service):
        captured["items"] = receipt.items
        return "receipt.pdf"

    monkeypatch.setattr("app.services.billing_service.generate_receipt_pdf", _fake_generate)

    service.generate_receipt(1)

    assert len(captured["items"]) == 1
    assert captured["items"][0].service_name == "Hair Cut"
    assert captured["items"][0].display_name == "Hair Cut Premium"
    assert captured["items"][0].variant == "Premium"


def test_generate_bill_number_uses_custom_prefix() -> None:
    class _PrefixSettings(_StubSettingsService):
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            if key == "bill_number_prefix":
                return "BILL"
            return default

    service = BillingService(
        bill_repo=_StubBillRepo(),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_PrefixSettings(),
    )
    bill = Bill(id=7, customer_id=1, staff_id=1, total=Decimal("1"), bill_datetime=datetime.now())

    number = service._generate_bill_number(bill)

    assert number.startswith("BILL-")
    assert number.endswith("-0007")
