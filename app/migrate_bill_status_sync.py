"""Migration: Backfill and synchronize bill status fields.

Run with: python -m app.migrate_bill_status_sync
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .infrastructure.database import engine
from .infrastructure.logging import logger


def migrate() -> None:
    """Synchronize `status` and `payment_status` for legacy bill rows."""
    with engine.begin() as conn:
        try:
            conn.execute(text("SELECT status, payment_status FROM bill LIMIT 1"))
        except OperationalError:
            logger.info("Bill status columns unavailable; skipping status sync migration.")
            return

        conn.execute(
            text(
                """
                UPDATE bill
                SET payment_status = status
                WHERE (payment_status IS NULL OR TRIM(payment_status) = '')
                  AND status IS NOT NULL
                """
            )
        )

        conn.execute(
            text(
                """
                UPDATE bill
                SET status = payment_status
                WHERE (status IS NULL OR TRIM(status) = '')
                  AND payment_status IS NOT NULL
                """
            )
        )

        conn.execute(
            text(
                """
                UPDATE bill
                SET payment_status = 'Paid'
                WHERE payment_status IS NULL OR TRIM(payment_status) = ''
                """
            )
        )

        conn.execute(
            text(
                """
                UPDATE bill
                SET status = payment_status
                WHERE status IS NULL OR TRIM(status) = '' OR status != payment_status
                """
            )
        )

    logger.info("Bill status sync migration completed.")


if __name__ == "__main__":
    migrate()
