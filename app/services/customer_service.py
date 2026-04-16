"""Customer service for customer operations."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Iterable, List

from ..dto.bill_dto import BillData
from ..dto.converters import bill_to_dto
from ..dto.customer_dto import CustomerData, CustomerSummary
from ..exceptions.business_errors import CustomerNotFoundError, InsufficientDataError
from ..exceptions.validation_errors import ValidationError
from ..models import Bill, Customer
from ..repositories.bill_repository import BillRepository
from ..repositories.customer_repository import CustomerRepository


class CustomerService:
    """Service for customer operations and summaries."""

    def __init__(self, customer_repo: CustomerRepository, bill_repo: BillRepository) -> None:
        self._customer_repo = customer_repo
        self._bill_repo = bill_repo

    def get_customer(self, customer_id: int) -> CustomerData:
        """Fetch a single customer by id."""
        customer = self._customer_repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError("Customer not found.")
        return self._to_customer_data(customer)

    def search_customers(self, term: str) -> List[CustomerData]:
        """Search customers by name or phone."""
        return [self._to_customer_data(c) for c in self._customer_repo.search(term)]

    def get_customer_summary(self, customer_id: int) -> CustomerSummary:
        """Return a customer summary with basic statistics."""
        customer = self._customer_repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError("Customer not found.")
        bills = list(self._bill_repo.list_by_customer(customer_id))
        total_spent = sum((Decimal(b.total or 0) for b in bills), Decimal("0"))
        return CustomerSummary(
            customer=self._to_customer_data(customer),
            total_visits=len(bills),
            total_spent=total_spent,
        )

    def create_customer(self, name: str, phone: str, notes: str | None) -> CustomerData:
        """Create a new customer."""
        if not name.strip() or not phone.strip():
            raise InsufficientDataError("Customer name and phone are required.")

        normalized_phone = self._normalize_phone(phone)
        if not normalized_phone:
            raise ValidationError("Customer phone number is invalid.")

        customer = Customer(name=name.strip(), phone=normalized_phone, notes=notes)
        created = self._customer_repo.add(customer)
        return self._to_customer_data(created)

    def update_customer(self, customer_id: int, data: CustomerData) -> CustomerData:
        """Update an existing customer."""
        if not self._customer_repo.get_by_id(customer_id):
            raise CustomerNotFoundError("Customer not found.")

        normalized_phone = self._normalize_phone(data.phone)
        if not normalized_phone:
            raise ValidationError("Customer phone number is invalid.")

        updated = self._customer_repo.update_customer(
            customer_id, data.name.strip(), normalized_phone, data.notes
        )
        if not updated:
            raise CustomerNotFoundError("Customer not found.")
        return self._to_customer_data(updated)

    @staticmethod
    def _normalize_phone(phone: str) -> str | None:
        cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
        if cleaned.startswith("+"):
            digits = cleaned[1:]
            return cleaned if digits.isdigit() and 3 <= len(digits) <= 15 else None
        return cleaned if cleaned.isdigit() and 3 <= len(cleaned) <= 15 else None

    def get_customer_bills(self, customer_id: int) -> List[BillData]:
        """Return bill history for a customer."""
        bills = self._bill_repo.list_by_customer(customer_id)
        return [self._to_bill_data(bill) for bill in bills]

    def delete_customer(self, customer_id: int) -> None:
        """Delete a customer if they have no bills."""
        bills = list(self._bill_repo.list_by_customer(customer_id))
        if bills:
            raise ValidationError("Cannot delete a customer with existing bills.")

        if not self._customer_repo.delete(customer_id):
            raise CustomerNotFoundError("Customer not found.")

    @staticmethod
    def _to_customer_data(customer: Customer) -> CustomerData:
        return CustomerData(
            id=customer.id,
            name=customer.name,
            phone=customer.phone,
            notes=customer.notes,
            last_visit_at=customer.last_visit_at,
        )

    @staticmethod
    def _to_bill_data(bill: Bill) -> BillData:
        return bill_to_dto(bill)
