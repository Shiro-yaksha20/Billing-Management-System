"""Additional CSV import/export tests."""

from __future__ import annotations

from app.csv_service_importer import export_services_to_csv, import_services_from_csv
from app.infrastructure import database as infra_db
from app.repositories.service_repository import ServiceRepository


def test_export_services_empty_creates_header(temp_db, tmp_path) -> None:
    repo = ServiceRepository(infra_db.db_session)
    output = tmp_path / "export.csv"

    assert export_services_to_csv(str(output), service_repo=repo, active_only=True) is True

    content = output.read_text(encoding="utf-8")
    assert content.splitlines()[0].startswith("category")


def test_import_services_with_notes(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair Cut,10,Special\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is True
    services = list(repo.list_all())
    assert services[0].notes == "Special"


def test_import_services_skips_empty_service_name(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,,Cut,Hair Cut,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert results["skipped"] == 1
