"""Additional unit tests for BillingService."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

import pytest

from app.dto.bill_dto import BillItemInput, BillOptions
from app.exceptions.validation_errors import ValidationError
from app.models import Bill
from app.services.billing_service import BillingService


@dataclass
class _StubCustomer:
    id: int


@dataclass
class _StubStaff:
    id: int


class _StubBillRepo:
    def __init__(self) -> None:
        self.last_bill: Optional[Bill] = None

    def add(self, bill: Bill) -> Bill:
        bill.id = 1
        self.last_bill = bill
        return bill

    def update_bill_number(self, bill_id: int, bill_number: str) -> bool:
        if not self.last_bill:
            return False
        self.last_bill.bill_number = bill_number
        return True

    def update_pdf_path(self, bill_id: int, pdf_path: str) -> bool:
        return True

    def get_with_details(self, bill_id: int):
        return self.last_bill

    def update_whatsapp_status(self, bill_id: int, status: str, error: str | None = None) -> None:
        return None

    def update_payment_status(self, bill_id: int, payment_status: str) -> bool:
        return True


class _StubCustomerRepo:
    def get_by_id(self, customer_id: int):
        return _StubCustomer(id=customer_id)

    def update_last_visit(self, customer_id: int, last_visit_at) -> bool:
        return True


class _StubStaffRepo:
    def get_by_id(self, staff_id: int):
        return _StubStaff(id=staff_id)


class _StubSettingsService:
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        return default


def _service() -> BillingService:
    return BillingService(
        bill_repo=_StubBillRepo(),
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )


def test_calculate_discount_flat_equal_subtotal() -> None:
    service = _service()

    result = service.calculate_discount(Decimal("50"), "flat", Decimal("50"))

    assert result == Decimal("50")


@pytest.mark.parametrize(
    "subtotal,percent,expected",
    [
        (Decimal("99.99"), Decimal("12.5"), Decimal("12.49875")),
        (Decimal("0"), Decimal("0"), Decimal("0")),
    ],
)
def test_calculate_discount_percent_fractional(subtotal: Decimal, percent: Decimal, expected: Decimal) -> None:
    service = _service()

    result = service.calculate_discount(subtotal, "percent", percent)

    assert result == expected


def test_calculate_tax_fractional_percent() -> None:
    service = _service()

    result = service.calculate_tax(Decimal("99.99"), Decimal("12.5"))

    assert result == Decimal("12.49875")


def test_calculate_tax_invalid_string_raises() -> None:
    service = _service()

    with pytest.raises(ValidationError):
        service.calculate_tax(Decimal("10"), Decimal("-0.1"))


def test_create_bill_flat_discount_with_tax() -> None:
    service = _service()
    options = BillOptions(
        discount_type="flat",
        discount_value=Decimal("10"),
        tax_percent=Decimal("5"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )
    items = [BillItemInput(service_id=1, quantity=1, unit_price=Decimal("100"))]

    bill = service.create_bill(customer_id=1, staff_id=1, items=items, options=options)

    assert bill.subtotal == Decimal("100")
    assert bill.discount_amount == Decimal("10")
    assert bill.tax_amount == Decimal("4.5")
    assert bill.total == Decimal("94.5")


def test_generate_receipt_includes_transaction_id(monkeypatch) -> None:
    bill = Bill(
        id=1,
        bill_number="B1",
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
        transaction_id="TXN123",
    )

    repo = _StubBillRepo()
    repo.last_bill = bill
    service = BillingService(
        bill_repo=repo,
        customer_repo=_StubCustomerRepo(),
        staff_repo=_StubStaffRepo(),
        settings_service=_StubSettingsService(),
    )
    captured = {}

    def _fake_generate(receipt, settings_service):
        captured["transaction_id"] = receipt.transaction_id
        return "receipt.pdf"

    monkeypatch.setattr("app.services.billing_service.generate_receipt_pdf", _fake_generate)

    service.generate_receipt(1)

    assert captured["transaction_id"] == "TXN123"
