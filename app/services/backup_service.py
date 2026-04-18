"""Backup service for local database backups."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..constants import BACKUP_DIR, DATABASE_FILE
from ..dto.backup_dto import BackupInfo
from ..infrastructure.cloud_drive import CloudDriveAdapter
from ..infrastructure.crypto import encrypt_file
from ..infrastructure.logging import logger


class BackupService:
    """Service for creating database backups."""

    def __init__(self, cloud_adapter: Optional[CloudDriveAdapter] = None) -> None:
        self._cloud_adapter = cloud_adapter

    def create_backup(
        self,
        reason: str = "manual",
        encrypt: bool = False,
        password: str | None = None,
        upload: bool = False,
    ) -> BackupInfo:
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"backup_{timestamp}_{reason}.db"

        db_path = Path(DATABASE_FILE)
        if not db_path.exists():
            raise FileNotFoundError("Database file not found")

        shutil.copy2(db_path, backup_file)

        if encrypt:
            if not password:
                raise ValueError("Password required for encrypted backups")
            if not self._is_strong_password(password):
                raise ValueError(
                    "Password must be at least 8 characters and include uppercase, "
                    "lowercase, number, and special character"
                )
            encrypted_path = backup_file.with_suffix(backup_file.suffix + ".enc")
            if not encrypt_file(str(backup_file), str(encrypted_path), password):
                raise RuntimeError("Backup encryption failed")
            backup_file.unlink(missing_ok=True)
            backup_file = encrypted_path

        if upload:
            if not self._cloud_adapter:
                raise RuntimeError("Cloud adapter not configured")
            remote_name = backup_file.name
            file_id = self._cloud_adapter.upload_file(str(backup_file), remote_name)
            if not file_id:
                raise RuntimeError("Cloud upload failed")

        logger.info("Database backup created: %s", backup_file)
        self.cleanup_old_backups(keep=10)
        return BackupInfo(path=str(backup_file), created_at=datetime.now(), reason=reason)

    def list_backups(self) -> List[BackupInfo]:
        backups: List[BackupInfo] = []
        for backup_file in sorted(BACKUP_DIR.glob("backup_*.db*"), key=lambda p: p.stat().st_mtime, reverse=True):
            created_at = datetime.fromtimestamp(backup_file.stat().st_mtime)
            reason = "manual"
            parts = backup_file.stem.split("_")
            if len(parts) >= 4:
                reason = "_".join(parts[3:]).replace(".db", "")
            backups.append(BackupInfo(path=str(backup_file), created_at=created_at, reason=reason))
        return backups

    def delete_old_backups(self, keep: int = 10) -> None:
        self.cleanup_old_backups(keep=keep)

    def cleanup_old_backups(self, keep: int = 10) -> None:
        backups = sorted(BACKUP_DIR.glob("backup_*.db*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old_backup in backups[keep:]:
            old_backup.unlink(missing_ok=True)
            logger.info("Deleted old backup: %s", old_backup)

    @staticmethod
    def _is_strong_password(password: str) -> bool:
        return bool(
            len(password) >= 8
            and re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"[0-9]", password)
            and re.search(r"[^A-Za-z0-9]", password)
        )
