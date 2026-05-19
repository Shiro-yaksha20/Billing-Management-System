"""Integration tests for full billing scenarios."""

from __future__ import annotations

from decimal import Decimal

from app.dto.bill_dto import BillItemInput, BillOptions
from app.infrastructure import database as infra_db
from app.models import Customer, Service, Staff
from app.repositories.bill_repository import BillRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.staff_repository import StaffRepository
from app.services.billing_service import BillingService
from app.services.settings_service import SettingsService


def _build_services():
    session_factory = infra_db.db_session
    bill_repo = BillRepository(session_factory)
    customer_repo = CustomerRepository(session_factory)
    staff_repo = StaffRepository(session_factory)
    settings_repo = SettingsRepository(session_factory)
    settings_service = SettingsService(settings_repo)
    billing_service = BillingService(bill_repo, customer_repo, staff_repo, settings_service)
    return billing_service


def _seed_entities() -> tuple[int, int, int]:
    with infra_db.db_session() as db:
        customer = Customer(name="Test Customer", phone="1234567890")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Haircut", price=Decimal("50"), active=True)
        db.add_all([customer, staff, service])
        db.flush()
        return customer.id, staff.id, service.id


def test_full_billing_flow_with_discount(temp_db) -> None:
    customer_id, staff_id, service_id = _seed_entities()
    billing_service = _build_services()

    items = [BillItemInput(service_id=service_id, quantity=2, unit_price=Decimal("50"))]
    options = BillOptions(
        discount_type="flat",
        discount_value=Decimal("10"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )

    bill = billing_service.create_bill(customer_id, staff_id, items, options)

    assert bill.subtotal == Decimal("100")
    assert bill.discount_amount == Decimal("10")
    assert bill.total == Decimal("90")


def test_full_billing_flow_with_tax(temp_db) -> None:
    customer_id, staff_id, service_id = _seed_entities()
    billing_service = _build_services()

    items = [BillItemInput(service_id=service_id, quantity=1, unit_price=Decimal("50"))]
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("10"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )

    bill = billing_service.create_bill(customer_id, staff_id, items, options)

    assert bill.tax_amount == Decimal("5")
    assert bill.total == Decimal("55")


def test_full_billing_flow_with_upi_transaction(temp_db) -> None:
    customer_id, staff_id, service_id = _seed_entities()
    billing_service = _build_services()

    items = [BillItemInput(service_id=service_id, quantity=1, unit_price=Decimal("50"))]
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="UPI",
        transaction_id="TXN123",
        payment_status="Paid",
    )

    bill = billing_service.create_bill(customer_id, staff_id, items, options)

    assert bill.payment_method == "UPI"
    assert bill.transaction_id == "TXN123"


def test_full_billing_flow_with_pending_status(temp_db) -> None:
    customer_id, staff_id, service_id = _seed_entities()
    billing_service = _build_services()

    items = [BillItemInput(service_id=service_id, quantity=1, unit_price=Decimal("50"))]
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Pending",
    )

    bill = billing_service.create_bill(customer_id, staff_id, items, options)

    assert bill.status == "Pending"
    assert bill.payment_status == "Pending"
