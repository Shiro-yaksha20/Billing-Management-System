"""Additional unit tests for BackupService."""

from __future__ import annotations

from pathlib import Path

from app.services.backup_service import BackupService


def test_create_backup_upload_success(backup_paths):
    class _StubAdapter:
        def upload_file(self, local_path, remote_name):
            return "file-id"

    service = BackupService(_StubAdapter())

    info = service.create_backup(reason="upload", upload=True)

    assert Path(info.path).exists()


def test_list_backups_parses_reason_with_underscores(backup_paths):
    backup_paths.mkdir(parents=True, exist_ok=True)
    backup_file = backup_paths / "backup_20240101_000000_month_end.db"
    backup_file.write_text("data", encoding="utf-8")

    service = BackupService()
    backups = service.list_backups()

    assert backups[0].reason == "month_end"
