"""Additional unit tests for RestoreService."""

from __future__ import annotations

from app.services.restore_service import RestoreService
import app.services.restore_service as restore_service


def test_restore_backup_plain_success(tmp_path, monkeypatch) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_text("data", encoding="utf-8")
    db_path = tmp_path / "db.sqlite"
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(db_path))

    service = RestoreService()
    result = service.restore_backup(str(backup_path))

    assert result.success is True
    assert db_path.exists()


def test_restore_backup_missing_file_returns_failure(tmp_path, monkeypatch) -> None:
    missing_path = tmp_path / "missing.db"
    db_path = tmp_path / "db.sqlite"
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(db_path))

    service = RestoreService()
    result = service.restore_backup(str(missing_path))

    assert result.success is False
    assert "not found" in result.message.lower()
