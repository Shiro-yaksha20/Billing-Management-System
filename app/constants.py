"""Application-wide constants and configuration defaults."""
from pathlib import Path

# Paths
DATABASE_FILE = "salon_billing.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"
RECEIPTS_DIR = "receipts"
LOGS_DIR = "logs"
BACKUP_DIR = Path("backups")

# Business rules
MAX_IMPORT_ERRORS = 10
MAX_DISCOUNT_PERCENT = 100.0

# UI limits
MAX_SERVICE_NAME_LEN = 100
MAX_CATEGORY_LEN = 50
MAX_NOTES_LEN = 500
