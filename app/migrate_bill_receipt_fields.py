"""Migration: Add transaction_id and payment_status columns to bill table.

Run with: python -m app.migrate_bill_receipt_fields
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .infrastructure.database import engine
from .infrastructure.logging import logger


def migrate() -> None:
    """Add transaction_id and payment_status columns to bill table if missing."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE bill ADD COLUMN transaction_id TEXT"))
            logger.info("Added column 'transaction_id' to bill table.")
        except OperationalError:
            logger.info("Column 'transaction_id' already exists, skipping.")

        try:
            conn.execute(text(
                "ALTER TABLE bill ADD COLUMN payment_status TEXT DEFAULT 'Paid'"
            ))
            logger.info("Added column 'payment_status' to bill table.")
        except OperationalError:
            logger.info("Column 'payment_status' already exists, skipping.")

        conn.commit()


if __name__ == "__main__":
    migrate()
