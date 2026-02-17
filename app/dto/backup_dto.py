"""Backup DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class BackupInfo:
    """Information about a backup file."""

    path: str
    created_at: datetime
    reason: str


@dataclass(frozen=True)
class RestoreResult:
    """Result of a restore operation."""

    success: bool
    message: str
    restored_path: Optional[str] = None
