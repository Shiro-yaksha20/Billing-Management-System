"""Integration tests for backup/restore."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.services.backup_service import BackupService
from app.services.restore_service import RestoreService
import app.services.backup_service as backup_service


def test_backup_restore_round_trip(temp_db, backup_paths):
    """Validate backup and restore using a temporary database file."""
    original_bytes = Path(temp_db).read_bytes()

    backup_info = BackupService().create_backup(reason="test")
    backup_path = Path(backup_info.path)
    assert backup_path.exists()

    Path(temp_db).write_bytes(b"corrupt")

    result = RestoreService().restore_backup(str(backup_path))
    assert result.success
    assert Path(temp_db).read_bytes() == original_bytes


def test_create_backup_encrypted_round_trip(temp_db, backup_paths):
    """Validate encrypted backup and restore using a temporary database file."""
    original_bytes = Path(temp_db).read_bytes()

    backup_info = BackupService().create_backup(reason="test", encrypt=True, password="Secret123!")
    backup_path = Path(backup_info.path)
    assert backup_path.exists()

    Path(temp_db).write_bytes(b"corrupt")

    result = RestoreService().restore_backup(
        str(backup_path),
        decrypt=True,
        password="Secret123!",
    )
    assert result.success
    assert Path(temp_db).read_bytes() == original_bytes


def test_create_backup_missing_db_raises(monkeypatch, backup_paths):
    """Backup should fail if database file is missing."""
    missing_path = backup_paths / "missing.db"
    monkeypatch.setattr(backup_service, "DATABASE_FILE", str(missing_path))
    with pytest.raises(FileNotFoundError):
        BackupService().create_backup(reason="test")


def test_list_backups_returns_sorted(temp_db, backup_paths):
    """Backups should be listed newest-first."""
    service = BackupService()
    first = service.create_backup(reason="first")
    second = service.create_backup(reason="second")

    os.utime(first.path, (1, 1))

    backups = service.list_backups()

    assert len(backups) >= 2
    assert backups[0].created_at >= backups[1].created_at


def test_cleanup_old_backups_keeps_only_n(backup_paths):
    """Cleanup should keep only the most recent backups."""
    backup_paths.mkdir(parents=True, exist_ok=True)
    for index in range(3):
        backup_file = backup_paths / f"backup_20240101_00000{index}_test.db"
        backup_file.write_text("data", encoding="utf-8")
        os.utime(backup_file, (index + 1, index + 1))

    service = BackupService()
    service.cleanup_old_backups(keep=1)

    remaining = list(backup_paths.glob("backup_*.db*"))
    assert len(remaining) == 1


def test_restore_missing_file_returns_failure(backup_paths):
    """Restore should fail when the backup file is missing."""
    missing_path = backup_paths / "missing.db"
    result = RestoreService().restore_backup(str(missing_path))
    assert result.success is False


def test_restore_decrypt_wrong_password_returns_failure(temp_db, backup_paths):
    """Restore should fail when the decryption password is incorrect."""
    backup_info = BackupService().create_backup(reason="test", encrypt=True, password="Secret123!")
    result = RestoreService().restore_backup(
        backup_info.path,
        decrypt=True,
        password="wrong",
    )
    assert result.success is False
