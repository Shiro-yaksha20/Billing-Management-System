"""Integration tests for CSV import/export round trips."""

from __future__ import annotations

from app.csv_service_importer import export_services_to_csv, import_services_from_csv
from app.infrastructure import database as infra_db
from app.models import Service
from app.repositories.service_repository import ServiceRepository


def test_import_export_round_trip(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair Cut,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is True

    export_path = tmp_path / "export.csv"
    assert export_services_to_csv(str(export_path), service_repo=repo, active_only=False) is True
    assert export_path.exists()


def test_export_active_only_filters(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Active", display_name="Active", price=10, active=True))
        db.add(Service(name="Inactive", display_name="Inactive", price=10, active=False))

    repo = ServiceRepository(infra_db.db_session)
    export_path = tmp_path / "export.csv"

    assert export_services_to_csv(str(export_path), service_repo=repo, active_only=True) is True
    content = export_path.read_text(encoding="utf-8")

    assert "Active" in content
    assert "Inactive" not in content


def test_import_updates_existing_service(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Cut", display_name="Cut", price=10, active=True))

    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Cut,15,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["updated"] == 1


def test_export_creates_parent_directory(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Cut", display_name="Cut", price=10, active=True))

    repo = ServiceRepository(infra_db.db_session)
    export_path = tmp_path / "nested" / "export.csv"

    assert export_services_to_csv(str(export_path), service_repo=repo, active_only=False) is True
    assert export_path.exists()


def test_import_with_missing_columns_returns_errors(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text("name,price\nCut,10\n", encoding="utf-8")
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert results["errors"]
