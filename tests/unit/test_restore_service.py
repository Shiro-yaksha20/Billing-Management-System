"""Unit tests for RestoreService."""

from __future__ import annotations

from pathlib import Path

from app.services.restore_service import RestoreService
import app.services.restore_service as restore_service


def test_restore_backup_requires_password(tmp_path, monkeypatch) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_text("data", encoding="utf-8")
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(tmp_path / "db.sqlite"))

    service = RestoreService()
    result = service.restore_backup(str(backup_path), decrypt=True, password=None)

    assert result.success is False
    assert result.message == "Password required for decryption"


def test_restore_backup_decrypt_failure(tmp_path, monkeypatch) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_text("data", encoding="utf-8")
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(tmp_path / "db.sqlite"))

    def _decrypt_file(source, dest, password):
        return False

    monkeypatch.setattr(restore_service, "decrypt_file", _decrypt_file)

    service = RestoreService()
    result = service.restore_backup(str(backup_path), decrypt=True, password="secret")

    assert result.success is False
    assert result.message == "Decryption failed"


def test_restore_backup_decrypt_success_cleans_temp(tmp_path, monkeypatch) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_text("data", encoding="utf-8")
    db_path = tmp_path / "db.sqlite"
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(db_path))

    def _decrypt_file(source, dest, password):
        Path(dest).write_text("data", encoding="utf-8")
        return True

    monkeypatch.setattr(restore_service, "decrypt_file", _decrypt_file)

    service = RestoreService()
    result = service.restore_backup(str(backup_path), decrypt=True, password="secret")

    assert result.success is True
    assert db_path.exists()


def test_restore_backup_copy_failure(tmp_path, monkeypatch) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_text("data", encoding="utf-8")
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(tmp_path / "db.sqlite"))

    def _copy(source, dest):
        raise OSError("fail")

    monkeypatch.setattr("shutil.copy2", _copy)

    service = RestoreService()
    result = service.restore_backup(str(backup_path))

    assert result.success is False


def test_restore_from_cloud_without_adapter() -> None:
    service = RestoreService()
    result = service.restore_from_cloud("file", "dest.db")

    assert result.success is False
    assert result.message == "Cloud adapter not configured"


def test_restore_from_cloud_download_failure(tmp_path) -> None:
    class _StubAdapter:
        def download_file(self, file_id, local_path):
            return False

    service = RestoreService(_StubAdapter())
    result = service.restore_from_cloud("file", str(tmp_path / "dest.db"))

    assert result.success is False
    assert result.message == "Cloud download failed"


def test_restore_from_cloud_download_success(tmp_path, monkeypatch) -> None:
    backup_path = tmp_path / "downloaded.db"
    db_path = tmp_path / "db.sqlite"
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(db_path))

    class _StubAdapter:
        def download_file(self, file_id, local_path):
            Path(local_path).write_text("data", encoding="utf-8")
            return True

    service = RestoreService(_StubAdapter())
    result = service.restore_from_cloud("file", str(backup_path))

    assert result.success is True
    assert db_path.exists()


def test_restore_from_file_delegates(tmp_path, monkeypatch) -> None:
    backup_path = tmp_path / "backup.db"
    backup_path.write_text("data", encoding="utf-8")
    monkeypatch.setattr(restore_service, "DATABASE_FILE", str(tmp_path / "db.sqlite"))

    service = RestoreService()
    result = service.restore_from_file(str(backup_path))

    assert result.success is True
