"""Unit tests for repository layer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.infrastructure import database as infra_db
from app.models import Bill, BillItem, Customer, Service, Setting, Staff
from app.repositories.base_repository import BaseRepository
from app.repositories.bill_repository import BillRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.staff_repository import StaffRepository
from app.repositories.utils import escape_like


def test_base_repository_crud(temp_db) -> None:
    repo = BaseRepository(infra_db.db_session, Customer)
    customer = Customer(name="Alex", phone="123")

    created = repo.add(customer)

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.name == "Alex"

    listed = list(repo.list_all())
    assert len(listed) == 1

    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None


def test_base_repository_delete_missing_returns_false(temp_db) -> None:
    repo = BaseRepository(infra_db.db_session, Customer)
    assert repo.delete(9999) is False


def test_bill_repository_queries(temp_db) -> None:
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
            bill_datetime=datetime.utcnow(),
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

    repo = BillRepository(infra_db.db_session)
    assert repo.get_by_bill_number("B1") is not None
    assert len(list(repo.list_by_customer(customer.id))) == 1
    assert len(list(repo.find_recent(limit=5))) == 1
    assert len(list(repo.find_by_date_range(datetime.min, datetime.max))) == 1
    assert len(list(repo.search(bill_number="B1"))) == 1
    assert len(list(repo.search(customer_name="Alex"))) == 1
    assert len(list(repo.search(payment_status="Paid"))) == 1
    assert len(list(repo.search(payment_method="Cash"))) == 1
    assert len(list(repo.search(start_date=datetime.min))) == 1
    assert len(list(repo.search(end_date=datetime.max))) == 1
    assert len(list(repo.find_for_export(customer_id=customer.id))) == 1
    assert len(list(repo.find_for_export(start_date=datetime.min))) == 1
    assert len(list(repo.find_for_export(end_date=datetime.max))) == 1


def test_bill_repository_updates(temp_db) -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Alex", phone="123")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Cut", price=Decimal("10"), active=True)
        db.add_all([customer, staff, service])
        db.flush()
        bill = Bill(
            bill_number=None,
            customer_id=customer.id,
            staff_id=staff.id,
            bill_datetime=datetime.utcnow(),
            subtotal=Decimal("10"),
            discount_amount=Decimal("0"),
            discount_type="none",
            tax_amount=Decimal("0"),
            tax_percent=Decimal("0"),
            total=Decimal("10"),
            payment_method="Cash",
            payment_status="Paid",
        )
        db.add(bill)
        db.flush()
        bill_id = bill.id

    repo = BillRepository(infra_db.db_session)
    assert repo.update_bill_number(9999, "X") is False
    assert repo.update_whatsapp_status(9999, "Sent") is False
    assert repo.update_pdf_path(9999, "path.pdf") is False
    assert repo.update_bill_number(bill_id, "B2") is True
    assert repo.update_whatsapp_status(bill_id, "Sent", "") is True
    assert repo.update_pdf_path(bill_id, "path.pdf") is True
    assert repo.get_with_details(bill_id) is not None


def test_customer_repository_methods(temp_db) -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Alex", phone="123")
        db.add(customer)
        db.flush()
        customer_id = customer.id

    repo = CustomerRepository(infra_db.db_session)
    assert len(list(repo.search("Alex"))) == 1
    assert len(list(repo.search(""))) == 1
    assert repo.get_with_bills(customer_id) is not None
    assert repo.get_bills(customer_id) == []
    assert repo.update_customer(customer_id, "New", "321", None) is not None
    assert repo.update_customer(9999, "New", "321", None) is None
    assert repo.update_last_visit(customer_id, datetime.utcnow()) is True
    assert repo.update_last_visit(9999, datetime.utcnow()) is False


def test_customer_repository_search_escapes_like_wildcards(temp_db) -> None:
    with infra_db.db_session() as db:
        db.add(Customer(name="A%lex", phone="12_3"))
        db.flush()

    repo = CustomerRepository(infra_db.db_session)
    by_percent = list(repo.search("%"))
    by_underscore = list(repo.search("_"))

    assert len(by_percent) == 1
    assert len(by_underscore) == 1


def test_escape_like_escapes_special_chars() -> None:
    escaped = escape_like(r"a%b_c\\")

    assert escaped == r"a\%b\_c\\\\"


def test_service_repository_methods(temp_db) -> None:
    with infra_db.db_session() as db:
        service = Service(
            name="Cut",
            display_name="Cut",
            category="Hair",
            price=Decimal("10"),
            active=True,
        )
        db.add(service)
        db.flush()
        service_id = service.id

    repo = ServiceRepository(infra_db.db_session)
    assert len(list(repo.list_active())) == 1
    assert len(list(repo.list_by_category("Hair"))) == 1
    assert repo.list_categories() == ["Hair"]
    assert repo.rename_category("Hair", "Hair2") == 1
    assert repo.clear_category("Hair2") == 1
    assert repo.get_by_display_name("Cut") is not None
    assert repo.update_service(service_id, "New", None, Decimal("12"), 30) is not None
    assert repo.update_service(9999, "New", None, None, None) is None
    assert repo.toggle_active(service_id) is True
    assert repo.toggle_active(9999) is False
    assert len(list(repo.list_for_export())) == 1
    assert repo.deactivate_all() >= 1
    assert repo.delete_all() >= 1
    assert repo.upsert_from_import("Display", "Name", None, None, Decimal("5"), None) is False
    assert repo.upsert_from_import("Display", "Name", None, None, Decimal("6"), None) is True


def test_bill_repository_get_daily_stats(temp_db) -> None:
    with infra_db.db_session() as db:
        customer = Customer(name="Alex", phone="123")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        db.add_all([customer, staff])
        db.flush()

        db.add(
            Bill(
                bill_number="B1",
                customer_id=customer.id,
                staff_id=staff.id,
                bill_datetime=datetime.utcnow(),
                subtotal=Decimal("10"),
                discount_amount=Decimal("0"),
                discount_type="none",
                tax_amount=Decimal("0"),
                tax_percent=Decimal("0"),
                total=Decimal("10"),
                payment_method="Cash",
                payment_status="Paid",
            )
        )
        db.add(
            Bill(
                bill_number="B2",
                customer_id=customer.id,
                staff_id=staff.id,
                bill_datetime=datetime.utcnow(),
                subtotal=Decimal("20"),
                discount_amount=Decimal("0"),
                discount_type="none",
                tax_amount=Decimal("0"),
                tax_percent=Decimal("0"),
                total=Decimal("20"),
                payment_method="Cash",
                payment_status="Pending",
            )
        )

    repo = BillRepository(infra_db.db_session)
    stats = repo.get_daily_stats(datetime.utcnow().date())

    assert stats["total_bills"] >= 2
    assert stats["paid_total"] >= Decimal("10")
    assert stats["pending_total"] >= Decimal("20")


def test_staff_repository_methods(temp_db) -> None:
    with infra_db.db_session() as db:
        staff = Staff(name="Stylist", phone="", role="", active=True)
        db.add(staff)
        db.flush()
        staff_id = staff.id

    repo = StaffRepository(infra_db.db_session)
    assert len(list(repo.list_active())) == 1
    assert repo.update_staff(staff_id, "New", "1", "Role") is not None
    assert repo.update_staff(9999, "New", "1", "Role") is None
    assert repo.toggle_active(staff_id) is True
    assert repo.toggle_active(9999) is False


def test_settings_repository_methods(temp_db) -> None:
    repo = SettingsRepository(infra_db.db_session)
    assert repo.get_by_key("missing") is None
    created = repo.set_value("key", "value")
    assert isinstance(created, Setting)
    updated = repo.set_value("key", "new")
    assert updated.value == "new"
    assert repo.get_by_key("key") is not None
