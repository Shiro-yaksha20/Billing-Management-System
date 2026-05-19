"""Additional DTO converter tests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.dto.converters import bill_to_dto
from app.models import Bill


def test_bill_to_dto_uses_status_when_payment_status_missing() -> None:
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
        status="Pending",
        payment_status=None,
    )

    dto = bill_to_dto(bill)

    assert dto.status == "Pending"
    assert dto.payment_status == "Pending"
