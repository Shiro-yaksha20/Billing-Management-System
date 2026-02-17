"""Unit tests for CSV service import/export."""

from __future__ import annotations

from pathlib import Path

from app.csv_service_importer import export_services_to_csv, import_services_from_csv
from app.infrastructure import database as infra_db
from app.models import Service
from app.repositories.service_repository import ServiceRepository


def test_import_services_success(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair - Cut,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is True
    assert results["imported"] == 1


def test_import_services_missing_file_returns_error(temp_db) -> None:
    repo = ServiceRepository(infra_db.db_session)
    results = import_services_from_csv("missing.csv", service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert "File not found" in results["errors"][0]


def test_import_services_invalid_price_skips(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair - Cut,abc,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert results["skipped"] == 1


def test_export_services_to_csv_creates_file(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Cut", display_name="Cut", price=10, active=True))

    repo = ServiceRepository(infra_db.db_session)
    output = tmp_path / "export.csv"

    assert export_services_to_csv(str(output), service_repo=repo, active_only=True) is True
    assert Path(output).exists()


def test_import_services_missing_columns(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text("name,price\nCut,10\n", encoding="utf-8")
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert "Missing required columns" in results["errors"][0]


def test_import_services_clear_existing(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Old", display_name="Old", price=10, active=True))

    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair - Cut,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(
        str(csv_path),
        service_repo=repo,
        clear_existing=True,
        deactivate_existing=False,
    )

    assert results["cleared"] >= 1
    assert results["imported"] == 1


def test_import_services_deactivate_existing(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Old", display_name="Old", price=10, active=True))

    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair - Cut,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(
        str(csv_path),
        service_repo=repo,
        clear_existing=False,
        deactivate_existing=True,
    )

    assert results["deactivated"] >= 1


def test_import_services_aborts_on_max_errors(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    rows = ["category,service_name,variant,display_name,price,notes"]
    rows.extend(["Hair,Cut,,Hair - Cut,10,"] * 12)
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    class _FailingRepo(ServiceRepository):
        def upsert_from_import(self, *args, **kwargs):
            raise RuntimeError("boom")

    repo = _FailingRepo(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert "Import aborted" in results["errors"][0]


def test_export_services_to_csv_permission_error(temp_db, tmp_path, monkeypatch) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Cut", display_name="Cut", price=10, active=True))

    repo = ServiceRepository(infra_db.db_session)
    output = tmp_path / "export.csv"

    monkeypatch.setattr("os.access", lambda *args, **kwargs: False)

    assert export_services_to_csv(str(output), service_repo=repo, active_only=True) is False


def test_import_services_backup_failure(temp_db, tmp_path, monkeypatch) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Old", display_name="Old", price=10, active=True))

    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair - Cut,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    def _fail_export(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr("app.csv_service_importer.export_services_to_csv", _fail_export)

    results = import_services_from_csv(
        str(csv_path),
        service_repo=repo,
        clear_existing=True,
        deactivate_existing=False,
    )

    assert results["success"] is False
    assert "Backup failed" in results["errors"][0]


def test_import_services_missing_display_name(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,,10,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert results["skipped"] == 1


def test_import_services_negative_price_skips(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair - Cut,-5,\n",
        encoding="utf-8",
    )
    repo = ServiceRepository(infra_db.db_session)

    results = import_services_from_csv(str(csv_path), service_repo=repo, deactivate_existing=False)

    assert results["success"] is False
    assert results["skipped"] == 1


def test_export_services_cleanup_ignores_remove_failure(temp_db, tmp_path, monkeypatch) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Cut", display_name="Cut", price=10, active=True))

    repo = ServiceRepository(infra_db.db_session)
    output = tmp_path / "export.csv"

    def _move(src, dst):
        return None

    def _exists(path):
        return True

    def _remove(path):
        raise OSError("fail")

    monkeypatch.setattr("shutil.move", _move)
    monkeypatch.setattr("os.path.exists", _exists)
    monkeypatch.setattr("os.remove", _remove)

    assert export_services_to_csv(str(output), service_repo=repo, active_only=True) is True


def test_export_services_overwrite_existing(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Cut", display_name="Cut", price=10, active=True))

    repo = ServiceRepository(infra_db.db_session)
    output = tmp_path / "export.csv"
    output.write_text("existing", encoding="utf-8")

    assert export_services_to_csv(str(output), service_repo=repo, active_only=True) is True


def test_export_services_creates_directory_and_handles_missing_price(temp_db, tmp_path) -> None:
    with infra_db.db_session() as db:
        db.add(Service(name="Cut", display_name="Cut", price=None, active=True))

    repo = ServiceRepository(infra_db.db_session)
    output = tmp_path / "nested" / "export.csv"

    assert export_services_to_csv(str(output), service_repo=repo, active_only=True) is True
    assert output.exists()


def test_import_services_fatal_error(temp_db, tmp_path) -> None:
    csv_path = tmp_path / "services.csv"
    csv_path.write_text(
        "category,service_name,variant,display_name,price,notes\n"
        "Hair,Cut,,Hair - Cut,10,\n",
        encoding="utf-8",
    )

    class _FailRepo(ServiceRepository):
        def deactivate_all(self) -> int:
            raise RuntimeError("fail")

    repo = _FailRepo(infra_db.db_session)

    results = import_services_from_csv(
        str(csv_path),
        service_repo=repo,
        clear_existing=False,
        deactivate_existing=True,
    )

    assert results["success"] is False
    assert "Fatal error" in results["errors"][0]
