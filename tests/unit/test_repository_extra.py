"""Additional repository layer tests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.infrastructure import database as infra_db
from app.models import Bill, BillItem, Customer, Service, Staff
from app.repositories.bill_repository import BillRepository
from app.repositories.staff_repository import StaffRepository


def _seed_bill() -> tuple[int, int]:
    with infra_db.db_session() as db:
        customer = Customer(name="Alex", phone="123")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Cut", price=Decimal("10"), active=True)
        db.add_all([customer, staff, service])
        db.flush()

        bill = Bill(
            bill_number="B1",
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.now(),
            subtotal=Decimal("10"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("10"),
            payment_method="Cash",
            payment_status="Paid",
        )
        bill.items.append(
            BillItem(
                service_id=service.id,
                quantity=1,
                unit_price=Decimal("10"),
                line_total=Decimal("10"),
            )
        )
        db.add(bill)
        db.flush()
        return customer.id, staff.id


def test_bill_repository_search_combined_filters(temp_db) -> None:
    _seed_bill()
    repo = BillRepository(infra_db.db_session)

    results = list(repo.search(bill_number="B1", customer_name="Alex", payment_status="Paid"))

    assert len(results) == 1


def test_staff_repository_list_active_excludes_inactive(temp_db) -> None:
    with infra_db.db_session() as db:
        active_staff = Staff(name="Active", phone="", role="", active=True)
        inactive_staff = Staff(name="Inactive", phone="", role="", active=False)
        db.add_all([active_staff, inactive_staff])

    repo = StaffRepository(infra_db.db_session)

    results = list(repo.list_active())

    assert len(results) == 1
    assert results[0].name == "Active"
