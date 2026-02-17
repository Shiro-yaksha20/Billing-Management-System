"""Restore service for database backups."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from ..constants import DATABASE_FILE
from ..dto.backup_dto import RestoreResult
from ..infrastructure.cloud_drive import CloudDriveAdapter
from ..infrastructure.crypto import decrypt_file
from ..infrastructure.logging import logger


class RestoreService:
    """Service for restoring database backups."""

    def __init__(self, cloud_adapter: Optional[CloudDriveAdapter] = None) -> None:
        self._cloud_adapter = cloud_adapter

    def restore_backup(
        self,
        backup_path: str,
        decrypt: bool = False,
        password: str | None = None,
    ) -> RestoreResult:
        backup_file = Path(backup_path)
        if not backup_file.exists():
            return RestoreResult(success=False, message="Backup file not found")

        source_path = backup_file
        temp_decrypted: Optional[Path] = None

        if decrypt:
            if not password:
                return RestoreResult(success=False, message="Password required for decryption")
            temp_decrypted = backup_file.with_suffix(backup_file.suffix + ".dec")
            if not decrypt_file(str(backup_file), str(temp_decrypted), password):
                return RestoreResult(success=False, message="Decryption failed")
            source_path = temp_decrypted

        try:
            shutil.copy2(source_path, DATABASE_FILE)
            logger.info("Database restored from backup: %s", backup_file)
            return RestoreResult(success=True, message="Restore completed", restored_path=str(backup_file))
        except Exception as exc:
            logger.error("Restore failed: %s", exc, exc_info=True)
            return RestoreResult(success=False, message=str(exc))
        finally:
            if temp_decrypted and temp_decrypted.exists():
                temp_decrypted.unlink(missing_ok=True)

    def restore_from_file(self, backup_path: str) -> RestoreResult:
        """Restore the database from a backup file."""
        return self.restore_backup(backup_path)

    def restore_from_cloud(self, file_id: str, destination_path: str) -> RestoreResult:
        """Download a cloud backup and restore it."""
        if not self._cloud_adapter:
            return RestoreResult(success=False, message="Cloud adapter not configured")
        if not self._cloud_adapter.download_file(file_id, destination_path):
            return RestoreResult(success=False, message="Cloud download failed")
        return self.restore_backup(destination_path)
