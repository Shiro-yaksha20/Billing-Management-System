"""Additional end-to-end flows for backups, CSV imports, and receipts."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.csv_service_importer import import_services_from_csv
from app.dto.bill_dto import BillItemInput, BillOptions
from app.infrastructure import database as infra_db
from app.models import Customer, Service, Staff
from app.repositories.bill_repository import BillRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.staff_repository import StaffRepository
from app.services.backup_service import BackupService
from app.services.billing_service import BillingService
from app.services.restore_service import RestoreService
from app.services.settings_service import SettingsService


def _build_billing_service() -> BillingService:
    session_factory = infra_db.db_session
    bill_repo = BillRepository(session_factory)
    customer_repo = CustomerRepository(session_factory)
    staff_repo = StaffRepository(session_factory)
    settings_repo = SettingsRepository(session_factory)
    settings_service = SettingsService(settings_repo)
    return BillingService(bill_repo, customer_repo, staff_repo, settings_service)


def _seed_entities() -> tuple[int, int, int]:
    with infra_db.db_session() as db:
        customer = Customer(name="Test Customer", phone="1234567890")
        staff = Staff(name="Stylist", phone="", role="", active=True)
        service = Service(name="Haircut", price=Decimal("50"), active=True)
        db.add_all([customer, staff, service])
        db.flush()
        return customer.id, staff.id, service.id


def test_backup_restore_flow(temp_db, backup_paths) -> None:
    backup_info = BackupService().create_backup(reason="e2e")
    assert Path(backup_info.path).exists()

    result = RestoreService().restore_backup(backup_info.path)

    assert result.success is True


def test_csv_import_flow(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair Cut,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is True
    assert len(list(repo.list_all())) == 1


def test_bill_receipt_pdf_flow(temp_db, receipts_dir) -> None:
    customer_id, staff_id, service_id = _seed_entities()
    billing_service = _build_billing_service()

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
    pdf_path = billing_service.generate_receipt(bill.id)

    assert Path(pdf_path).exists()
