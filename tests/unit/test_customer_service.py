"""Unit tests for CustomerService."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

import pytest

from app.dto.customer_dto import CustomerData
from app.exceptions.business_errors import CustomerNotFoundError, InsufficientDataError
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


def test_create_customer_requires_name_and_phone() -> None:
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=[]))
    with pytest.raises(InsufficientDataError):
        service.create_customer("", "", None)


def test_get_customer_missing_raises() -> None:
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=[]))
    with pytest.raises(CustomerNotFoundError):
        service.get_customer(1)


def test_get_customer_summary_calculates_totals() -> None:
    customer = Customer(id=1, name="A", phone="1")
    bills = [
        Bill(id=1, customer_id=1, staff_id=1, total=Decimal("10")),
        Bill(id=2, customer_id=1, staff_id=1, total=Decimal("5")),
    ]
    service = CustomerService(_StubCustomerRepo(customer=customer), _StubBillRepo(bills=bills))

    summary = service.get_customer_summary(1)

    assert summary.customer.id == 1
    assert summary.total_visits == 2
    assert summary.total_spent == Decimal("15")


def test_update_customer_missing_raises() -> None:
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=[]))
    with pytest.raises(CustomerNotFoundError):
        service.update_customer(1, CustomerData(id=1, name="A", phone="1", notes=None, last_visit_at=None))


def test_delete_customer_with_bills_raises() -> None:
    customer = Customer(id=1, name="A", phone="1")
    bills = [Bill(id=1, customer_id=1, staff_id=1, total=Decimal("10"))]
    service = CustomerService(_StubCustomerRepo(customer=customer), _StubBillRepo(bills=bills))

    with pytest.raises(ValidationError):
        service.delete_customer(1)


def test_delete_customer_missing_raises() -> None:
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=[]))
    with pytest.raises(CustomerNotFoundError):
        service.delete_customer(1)


def test_create_customer_success_returns_data() -> None:
    repo = _StubCustomerRepo()
    service = CustomerService(repo, _StubBillRepo(bills=[]))

    result = service.create_customer("Alex", "999", "Notes")

    assert result.id == 1
    assert result.name == "Alex"
    assert result.phone == "999"
    assert result.notes == "Notes"


def test_create_customer_normalizes_phone() -> None:
    repo = _StubCustomerRepo()
    service = CustomerService(repo, _StubBillRepo(bills=[]))

    result = service.create_customer("Alex", " +91 999-888-7777 ", None)

    assert result.phone == "+919998887777"


def test_create_customer_invalid_phone_raises_validation_error() -> None:
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=[]))

    with pytest.raises(ValidationError):
        service.create_customer("Alex", "ABC", None)


def test_get_customer_success_returns_data() -> None:
    customer = Customer(id=1, name="Alex", phone="999")
    service = CustomerService(_StubCustomerRepo(customer=customer), _StubBillRepo(bills=[]))

    result = service.get_customer(1)

    assert result.id == 1


def test_get_customer_summary_missing_raises() -> None:
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=[]))
    with pytest.raises(CustomerNotFoundError):
        service.get_customer_summary(1)


def test_update_customer_success_returns_data() -> None:
    customer = Customer(id=1, name="Alex", phone="999")
    repo = _StubCustomerRepo(customer=customer)
    service = CustomerService(repo, _StubBillRepo(bills=[]))

    result = service.update_customer(
        1,
        CustomerData(id=1, name="New", phone="123", notes=None, last_visit_at=None),
    )

    assert result.name == "New"


def test_update_customer_normalizes_phone() -> None:
    customer = Customer(id=1, name="Alex", phone="999")
    repo = _StubCustomerRepo(customer=customer)
    service = CustomerService(repo, _StubBillRepo(bills=[]))

    result = service.update_customer(
        1,
        CustomerData(id=1, name="New", phone="(999) 123-4567", notes=None, last_visit_at=None),
    )

    assert result.phone == "9991234567"


def test_search_customers_empty_returns_list() -> None:
    customer = Customer(id=1, name="Alex", phone="999")
    service = CustomerService(_StubCustomerRepo(customer=customer), _StubBillRepo(bills=[]))

    results = service.search_customers("")

    assert len(results) == 1


def test_get_customer_bills_returns_list() -> None:
    bills = [Bill(id=1, customer_id=1, staff_id=1, total=Decimal("10"))]
    service = CustomerService(_StubCustomerRepo(), _StubBillRepo(bills=bills))

    results = service.get_customer_bills(1)

    assert len(results) == 1


def test_get_customer_bills_includes_customer_info() -> None:
    customer = Customer(id=1, name="Alex", phone="999")
    bill = Bill(
        id=1,
        bill_number="B1",
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
        whatsapp_status=None,
        whatsapp_last_error=None,
        transaction_id=None,
        payment_status="Paid",
    )
    bill.customer = customer
    service = CustomerService(_StubCustomerRepo(customer=customer), _StubBillRepo(bills=[bill]))

    results = service.get_customer_bills(1)

    assert results[0].customer_name == "Alex"


def test_to_bill_data_handles_inspect_failure() -> None:
    class _Bill:
        def __init__(self):
            self.id = 1
            self.bill_number = "B1"
            self.customer_id = 1
            self.staff_id = 1
            self.bill_datetime = None
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

    result = CustomerService._to_bill_data(_Bill())

    assert result.customer_name is None
