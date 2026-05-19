"""Unit tests for BackupService."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.backup_service import BackupService
import app.services.backup_service as backup_service


def test_create_backup_requires_password(backup_paths):
    service = BackupService()
    with pytest.raises(ValueError):
        service.create_backup(reason="test", encrypt=True, password=None)


def test_create_backup_encryption_failure(monkeypatch, backup_paths):
    service = BackupService()

    def _encrypt_file(source, dest, password):
        return False

    monkeypatch.setattr(backup_service, "encrypt_file", _encrypt_file)

    with pytest.raises(RuntimeError):
        service.create_backup(reason="test", encrypt=True, password="Secret123!")


def test_create_backup_weak_password_raises(backup_paths):
    service = BackupService()

    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        service.create_backup(reason="test", encrypt=True, password="weak")


def test_create_backup_plain_creates_file(backup_paths):
    service = BackupService()

    info = service.create_backup(reason="plain")

    assert info.path.endswith(".db")
    assert backup_paths.joinpath(Path(info.path).name).exists()


def test_create_backup_encrypted_creates_enc_file(backup_paths):
    service = BackupService()

    info = service.create_backup(reason="enc", encrypt=True, password="Secret123!")

    assert info.path.endswith(".db.enc")
    assert backup_paths.joinpath(Path(info.path).name).exists()


def test_create_backup_upload_without_adapter(backup_paths):
    service = BackupService()

    with pytest.raises(RuntimeError):
        service.create_backup(reason="test", upload=True)


def test_create_backup_upload_failure(backup_paths):
    class _StubAdapter:
        def upload_file(self, local_path, remote_name):
            return None

    service = BackupService(_StubAdapter())

    with pytest.raises(RuntimeError):
        service.create_backup(reason="test", upload=True)


def test_list_backups_parses_reason(backup_paths):
    backup_paths.mkdir(parents=True, exist_ok=True)
    backup_file = backup_paths / "backup_20240101_manual.db"
    backup_file.write_text("data", encoding="utf-8")

    service = BackupService()
    backups = service.list_backups()

    assert backups[0].reason == "manual"


def test_delete_old_backups_delegates_to_cleanup(monkeypatch):
    service = BackupService()
    calls = {"keep": None}

    def _cleanup(keep):
        calls["keep"] = keep

    monkeypatch.setattr(service, "cleanup_old_backups", _cleanup)

    service.delete_old_backups(keep=5)

    assert calls["keep"] == 5


def test_cleanup_old_backups_with_fewer_than_keep(backup_paths):
    backup_paths.mkdir(parents=True, exist_ok=True)
    backup_file = backup_paths / "backup_20240101_000000_test.db"
    backup_file.write_text("data", encoding="utf-8")

    service = BackupService()
    service.cleanup_old_backups(keep=5)

    assert backup_file.exists()


def test_cleanup_old_backups_handles_encrypted_files(backup_paths):
    backup_paths.mkdir(parents=True, exist_ok=True)
    for index in range(3):
        backup_file = backup_paths / f"backup_20240101_00000{index}_test.db.enc"
        backup_file.write_text("data", encoding="utf-8")

    service = BackupService()
    service.cleanup_old_backups(keep=1)

    remaining = list(backup_paths.glob("backup_*.db.enc"))
    assert len(remaining) == 1


def test_is_strong_password_edge_cases() -> None:
    service = BackupService()

    assert service._is_strong_password("Abcdef1!") is True
    assert service._is_strong_password("abcdefg1!") is False
