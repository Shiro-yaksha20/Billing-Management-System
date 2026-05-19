"""End-to-end customer lifecycle tests."""

from __future__ import annotations

from decimal import Decimal

from app.dto.bill_dto import BillItemInput, BillOptions
from app.dto.customer_dto import CustomerData
from app.infrastructure import database as infra_db
from app.models import Customer, Service, Staff
from app.repositories.bill_repository import BillRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.staff_repository import StaffRepository
from app.services.billing_service import BillingService
from app.services.customer_service import CustomerService
from app.services.settings_service import SettingsService


def _build_services():
    session_factory = infra_db.db_session
    bill_repo = BillRepository(session_factory)
    customer_repo = CustomerRepository(session_factory)
    staff_repo = StaffRepository(session_factory)
    settings_repo = SettingsRepository(session_factory)
    settings_service = SettingsService(settings_repo)
    billing_service = BillingService(bill_repo, customer_repo, staff_repo, settings_service)
    customer_service = CustomerService(customer_repo, bill_repo)
    return billing_service, customer_service


def test_customer_create_update_delete(temp_db) -> None:
    _, customer_service = _build_services()

    customer = customer_service.create_customer("Alex", "1234567890", None)
    updated = customer_service.update_customer(
        customer.id,
        CustomerData(
            id=customer.id,
            name="Alex Updated",
            phone="1234567890",
            notes="Notes",
            last_visit_at=None,
        ),
    )

    assert updated.name == "Alex Updated"

    customer_service.delete_customer(customer.id)


def test_customer_create_bill_view_history(temp_db) -> None:
    billing_service, customer_service = _build_services()
    with infra_db.db_session() as db:
        customer = Customer(name="Test Customer", phone="1234567890")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Haircut", price=Decimal("50"), active=True)
        db.add_all([customer, staff, service])
        db.flush()
        customer_id = customer.id
        staff_id = staff.id
        service_id = service.id

    items = [BillItemInput(service_id=service_id, quantity=1, unit_price=Decimal("50"))]
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )

    billing_service.create_bill(customer_id, staff_id, items, options)

    bills = customer_service.get_customer_bills(customer_id)

    assert len(bills) == 1


def test_customer_search_returns_multiple(temp_db) -> None:
    _, customer_service = _build_services()
    with infra_db.db_session() as db:
        db.add(Customer(name="Alex", phone="111"))
        db.add(Customer(name="Alice", phone="222"))

    results = customer_service.search_customers("Al")

    assert len(results) == 2
