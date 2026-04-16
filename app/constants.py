"""Application-wide constants and configuration defaults."""

from __future__ import annotations

from pathlib import Path

# Resolve all paths relative to the project root
APP_DIR = Path(__file__).resolve().parent.parent

# Paths
DATABASE_FILE = str(APP_DIR / "billing.db")
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"
RECEIPTS_DIR = str(APP_DIR / "receipts")
LOGS_DIR = str(APP_DIR / "logs")
BACKUP_DIR = APP_DIR / "backups"

# Business rules
MAX_IMPORT_ERRORS = 10
MAX_DISCOUNT_PERCENT = 100.0

# UI limits
MAX_SERVICE_NAME_LEN = 100
MAX_CATEGORY_LEN = 50
MAX_NOTES_LEN = 500
