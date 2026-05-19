"""Additional unit tests for CustomerService."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

import pytest

from app.dto.customer_dto import CustomerData
from app.exceptions.validation_errors import ValidationError
from app.models import Bill, Customer
from app.services.customer_service import CustomerService


@dataclass
class _StubCustomerRepo:
    customer: Optional[Customer] = None

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.customer

    def search(self, term: str) -> Iterable[Customer]:
        return [self.customer] if self.customer else []

    def add(self, customer: Customer) -> Customer:
        customer.id = 1
        self.customer = customer
        return customer

    def update_customer(self, customer_id: int, name: str, phone: str, notes: str | None):
        if not self.customer or self.customer.id != customer_id:
            return None
        self.customer.name = name
        self.customer.phone = phone
        self.customer.notes = notes
        return self.customer

    def delete(self, customer_id: int) -> bool:
        if not self.customer or self.customer.id != customer_id:
            return False
        self.customer = None
        return True


@dataclass
class _StubBillRepo:
    bills: Iterable[Bill]

    def list_by_customer(self, customer_id: int) -> Iterable[Bill]:
        return self.bills


def test_create_customer_trims_name_and_preserves_notes() -> None:
    repo = _StubCustomerRepo()
    service = CustomerService(repo, _StubBillRepo(bills=[]))

    result = service.create_customer(" Alex ", "1234567", " Notes ")

    assert result.name == "Alex"
    assert result.notes == " Notes "


def test_update_customer_trims_name() -> None:
    customer = Customer(id=1, name="Old", phone="1234567")
    repo = _StubCustomerRepo(customer=customer)
    service = CustomerService(repo, _StubBillRepo(bills=[]))

    result = service.update_customer(
        1,
        CustomerData(id=1, name=" New ", phone="1234567", notes=None, last_visit_at=None),
    )

    assert result.name == "New"


def test_normalize_phone_invalid_plus_raises() -> None:
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=[]))

    with pytest.raises(ValidationError):
        service.create_customer("Alex", "+ABC", None)


def test_search_customers_by_phone_returns_result() -> None:
    customer = Customer(id=1, name="Alex", phone="999")
    service = CustomerService(_StubCustomerRepo(customer=customer), _StubBillRepo(bills=[]))

    results = service.search_customers("999")

    assert len(results) == 1
    assert results[0].phone == "999"


def test_get_customer_summary_counts_zero_with_none_bills() -> None:
    customer = Customer(id=1, name="Alex", phone="999")
    bills = [Bill(id=1, customer_id=1, staff_id=1, total=None)]
    service = CustomerService(_StubCustomerRepo(customer=customer), _StubBillRepo(bills=bills))

    summary = service.get_customer_summary(1)

    assert summary.total_visits == 1
    assert summary.total_spent == Decimal("0")
