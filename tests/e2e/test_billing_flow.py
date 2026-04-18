"""End-to-end billing flow tests."""

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


def test_billing_flow(temp_db):
    """End-to-end billing flow using service and repository layers."""
    with infra_db.db_session() as db:
        customer = Customer(name="Test Customer", phone="1234567890")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Haircut", price=Decimal("50"), active=True)
        db.add_all([customer, staff, service])
        db.flush()
        customer_id = customer.id
        staff_id = staff.id
        service_id = service.id

    session_factory = infra_db.db_session
    bill_repo = BillRepository(session_factory)
    customer_repo = CustomerRepository(session_factory)
    staff_repo = StaffRepository(session_factory)
    settings_repo = SettingsRepository(session_factory)

    settings_service = SettingsService(settings_repo)
    billing_service = BillingService(bill_repo, customer_repo, staff_repo, settings_service)

    items = [BillItemInput(service_id=service_id, quantity=1, unit_price=Decimal("50"))]
    options = BillOptions(
        discount_type="none",
        discount_value=Decimal("0"),
        tax_percent=Decimal("0"),
        payment_method="Cash",
        transaction_id=None,
        payment_status="Paid",
    )

    bill = billing_service.create_bill(customer_id, staff_id, items, options)

    assert bill.total == Decimal("50")
    assert bill.customer_id == customer_id
    assert bill.staff_id == staff_id
