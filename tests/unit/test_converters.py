"""Unit tests for DTO converters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.dto.converters import bill_to_dto
from app.models import Bill, Customer


@dataclass
class _PlainBill:
    id: int
    bill_number: str | None
    customer_id: int | None
    staff_id: int | None
    bill_datetime: datetime | None
    subtotal: Decimal | None
    discount_amount: Decimal | None
    discount_type: str | None
    tax_amount: Decimal | None
    tax_percent: Decimal | None
    total: Decimal | None
    payment_method: str | None
    status: str | None
    pdf_path: str | None
    whatsapp_status: str | None
    whatsapp_last_error: str | None
    transaction_id: str | None
    payment_status: str | None


def test_bill_to_dto_handles_none_fields() -> None:
    bill = _PlainBill(
        id=1,
        bill_number=None,
        customer_id=None,
        staff_id=None,
        bill_datetime=None,
        subtotal=None,
        discount_amount=None,
        discount_type=None,
        tax_amount=None,
        tax_percent=None,
        total=None,
        payment_method=None,
        status=None,
        pdf_path=None,
        whatsapp_status=None,
        whatsapp_last_error=None,
        transaction_id=None,
        payment_status=None,
    )

    dto = bill_to_dto(bill)

    assert dto.total == Decimal("0")
    assert dto.discount_type == "none"
    assert dto.payment_method == "Cash"


def test_bill_to_dto_with_customer_loaded(monkeypatch) -> None:
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
        status="Paid",
        payment_status="Paid",
    )
    bill.customer = Customer(id=1, name="Alex", phone="999")

    class _State:
        unloaded: set[str] = set()

    monkeypatch.setattr("app.dto.converters.sa_inspect", lambda target: _State())

    dto = bill_to_dto(bill)

    assert dto.customer_name == "Alex"
    assert dto.customer_phone == "999"


def test_bill_to_dto_with_customer_unloaded(monkeypatch) -> None:
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
        status="Paid",
        payment_status="Paid",
    )
    bill.customer = Customer(id=1, name="Alex", phone="999")

    class _State:
        unloaded = {"customer"}

    monkeypatch.setattr("app.dto.converters.sa_inspect", lambda target: _State())

    dto = bill_to_dto(bill)

    assert dto.customer_name is None


def test_bill_to_dto_preserves_decimal_precision() -> None:
    bill = _PlainBill(
        id=1,
        bill_number="B1",
        customer_id=1,
        staff_id=1,
        bill_datetime=datetime.now(),
        subtotal=Decimal("10.99"),
        discount_amount=Decimal("0"),
        discount_type="none",
        tax_amount=Decimal("0"),
        tax_percent=Decimal("0"),
        total=Decimal("10.99"),
        payment_method="Cash",
        status="Paid",
        pdf_path=None,
        whatsapp_status=None,
        whatsapp_last_error=None,
        transaction_id=None,
        payment_status="Paid",
    )

    dto = bill_to_dto(bill)

    assert dto.total == Decimal("10.99")


def test_bill_to_dto_prefers_payment_status() -> None:
    bill = _PlainBill(
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
        payment_method="Card",
        status="Pending",
        pdf_path=None,
        whatsapp_status=None,
        whatsapp_last_error=None,
        transaction_id=None,
        payment_status="Paid",
    )

    dto = bill_to_dto(bill)

    assert dto.status == "Paid"
    assert dto.payment_status == "Paid"


def test_bill_to_dto_zero_amounts() -> None:
    bill = _PlainBill(
        id=1,
        bill_number="B1",
        customer_id=1,
        staff_id=1,
        bill_datetime=datetime.now(),
        subtotal=Decimal("0"),
        discount_amount=Decimal("0"),
        discount_type="none",
        tax_amount=Decimal("0"),
        tax_percent=Decimal("0"),
        total=Decimal("0"),
        payment_method="Cash",
        status="Paid",
        pdf_path=None,
        whatsapp_status=None,
        whatsapp_last_error=None,
        transaction_id=None,
        payment_status="Paid",
    )

    dto = bill_to_dto(bill)

    assert dto.subtotal == Decimal("0")
    assert dto.total == Decimal("0")
