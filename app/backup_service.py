import shutil
from datetime import datetime
from pathlib import Path
from .utils import logger

BACKUP_DIR = Path("backups")
DATABASE_FILE = "salon_billing.db"

def create_backup(reason: str = "manual") -> str:
    """Create timestamped database backup and return path."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{timestamp}_{reason}.db"

    db_path = Path(DATABASE_FILE)
    if db_path.exists():
        shutil.copy2(db_path, backup_file)
        logger.info(f"Database backup created: {backup_file}")
        cleanup_old_backups(keep=10)
        return str(backup_file)
    else:
        raise FileNotFoundError("Database file not found")

def cleanup_old_backups(keep: int = 10) -> None:
    """Keep only the N most recent backups."""
    backups = sorted(BACKUP_DIR.glob("backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_backup in backups[keep:]:
        old_backup.unlink(missing_ok=True)
        logger.info(f"Deleted old backup: {old_backup}")
