"""Parameterized BillingService tests for additional coverage."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import pytest

from app.services.billing_service import BillingService


@dataclass
class _StubCustomer:
    id: int


@dataclass
class _StubStaff:
    id: int


class _StubBillRepo:
    def add(self, bill):
        bill.id = 1
        return bill

    def update_bill_number(self, bill_id: int, bill_number: str) -> bool:
        return True

    def update_pdf_path(self, bill_id: int, pdf_path: str) -> bool:
        return True

    def get_with_details(self, bill_id: int):
        return None

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


@pytest.mark.parametrize(
    "subtotal,amount",
    [
        (Decimal("10"), Decimal("0")),
        (Decimal("10"), Decimal("5")),
        (Decimal("10"), Decimal("10")),
        (Decimal("50"), Decimal("25")),
        (Decimal("99.99"), Decimal("9.99")),
    ],
)
def test_calculate_discount_flat_param(subtotal: Decimal, amount: Decimal) -> None:
    service = _service()

    result = service.calculate_discount(subtotal, "flat", amount)

    assert result == amount


@pytest.mark.parametrize(
    "subtotal,percent,expected",
    [
        (Decimal("10"), Decimal("0"), Decimal("0")),
        (Decimal("10"), Decimal("5"), Decimal("0.5")),
        (Decimal("10"), Decimal("10"), Decimal("1")),
        (Decimal("50"), Decimal("25"), Decimal("12.5")),
        (Decimal("99.99"), Decimal("12.5"), Decimal("12.49875")),
    ],
)
def test_calculate_discount_percent_param(
    subtotal: Decimal, percent: Decimal, expected: Decimal
) -> None:
    service = _service()

    result = service.calculate_discount(subtotal, "percent", percent)

    assert result == expected


@pytest.mark.parametrize(
    "amount,percent,expected",
    [
        (Decimal("10"), Decimal("0"), Decimal("0")),
        (Decimal("10"), Decimal("5"), Decimal("0.5")),
        (Decimal("10"), Decimal("10"), Decimal("1")),
        (Decimal("50"), Decimal("25"), Decimal("12.5")),
        (Decimal("99.99"), Decimal("12.5"), Decimal("12.49875")),
        (Decimal("100"), Decimal("100"), Decimal("100")),
        (Decimal("0"), Decimal("5"), Decimal("0")),
        (Decimal("1"), Decimal("0.5"), Decimal("0.005")),
        (Decimal("20"), Decimal("2.5"), Decimal("0.5")),
        (Decimal("200"), Decimal("1.25"), Decimal("2.5")),
    ],
)
def test_calculate_tax_param(amount: Decimal, percent: Decimal, expected: Decimal) -> None:
    service = _service()

    result = service.calculate_tax(amount, percent)

    assert result == expected
