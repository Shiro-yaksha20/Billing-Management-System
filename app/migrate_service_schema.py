"""
Database migration script to add new columns to Service table.

This script safely adds:
- category (String)
- variant (String)
- display_name (String)
- notes (Text)

Run this once to upgrade existing databases.
"""

from sqlalchemy import text
from .database import engine
from .utils import logger


def migrate_service_table():
    """Add new columns to service table if they don't exist."""
    
    migrations = [
        ("category", "ALTER TABLE service ADD COLUMN category VARCHAR"),
        ("variant", "ALTER TABLE service ADD COLUMN variant VARCHAR"),
        ("display_name", "ALTER TABLE service ADD COLUMN display_name VARCHAR"),
        ("notes", "ALTER TABLE service ADD COLUMN notes TEXT"),
    ]

    # Whitelist allowed column names to avoid SQL injection
    ALLOWED_COLUMNS = {"category", "variant", "display_name", "notes"}
    
    # Use a single transaction for all migrations
    with engine.begin() as conn:
        for column_name, alter_sql in migrations:
            try:
                # Validate column name before using in SQL text
                if column_name not in ALLOWED_COLUMNS:
                    raise ValueError(f"Invalid column name: {column_name}")
                # Check if column exists by trying to select it
                conn.execute(text(f"SELECT {column_name} FROM service LIMIT 1"))
                logger.info(f"Column '{column_name}' already exists, skipping.")
            except Exception:
                # Column doesn't exist, add it
                try:
                    conn.execute(text(alter_sql))
                    logger.info(f"Added column '{column_name}' to service table.")
                except Exception as e:
                    logger.error(f"Failed to add column '{column_name}': {e}")
                    raise
        
        # Populate display_name for existing services (if null)
        result = conn.execute(text(
            "UPDATE service SET display_name = name WHERE display_name IS NULL OR display_name = ''"
        ))
        logger.info(f"Updated {result.rowcount} existing services with display_name from name.")
    
    logger.info("Service table migration completed successfully.")


if __name__ == "__main__":
    print("Running service table migration...")
    try:
        migrate_service_table()
        print("? Migration completed successfully!")
    except Exception as e:
        print(f"? Migration failed: {e}")
        raise
