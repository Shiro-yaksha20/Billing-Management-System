"""
Database migration script to add new columns to Service table.

This script safely adds:
- category (String)
- variant (String)
- display_name (String)
- notes (Text)

Run this once to upgrade existing databases.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .infrastructure.database import engine
from .infrastructure.logging import logger


def migrate_service_table(allowed_columns: set[str] | None = None) -> None:
    """Add new columns to service table if they don't exist."""

    migrations = [
        ("category", "ALTER TABLE service ADD COLUMN category VARCHAR"),
        ("variant", "ALTER TABLE service ADD COLUMN variant VARCHAR"),
        ("display_name", "ALTER TABLE service ADD COLUMN display_name VARCHAR"),
        ("notes", "ALTER TABLE service ADD COLUMN notes TEXT"),
    ]

    # Whitelist allowed column names to avoid SQL injection
    valid_columns: set[str] = (
        allowed_columns
        if allowed_columns is not None
        else {"category", "variant", "display_name", "notes"}
    )

    # Use a single transaction for all migrations
    with engine.begin() as conn:
        for column_name, alter_sql in migrations:
            # Validate column name before using in SQL text
            if column_name not in valid_columns:
                raise ValueError("Invalid column name: %s" % column_name)

            try:
                # Check if column exists by trying to select it
                conn.execute(text("SELECT %s FROM service LIMIT 1" % column_name))
                logger.info("Column '%s' already exists, skipping.", column_name)
            except OperationalError:
                # Column doesn't exist, add it
                try:
                    conn.execute(text(alter_sql))
                    logger.info("Added column '%s' to service table.", column_name)
                except OperationalError as exc:
                    logger.error("Failed to add column '%s': %s", column_name, exc)
                    raise

        # Populate display_name for existing services (if null)
        result = conn.execute(text(
            "UPDATE service SET display_name = name "
            "WHERE display_name IS NULL OR display_name = ''"
        ))
        logger.info(
            "Updated %s existing services with display_name from name.",
            result.rowcount,
        )

    logger.info("Service table migration completed successfully.")


def run_cli(migrate_fn: object = None) -> None:
    """Run migration with CLI-style output."""
    print("Running service table migration...")
    try:
        (migrate_fn or migrate_service_table)()
        print("Migration completed successfully!")
    except Exception as exc:
        print("Migration failed: %s" % exc)
        raise


if __name__ == "__main__":
    run_cli()
