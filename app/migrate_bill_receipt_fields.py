"""Migration: Add transaction_id and payment_status columns to bill table.
Run with: python -m app.migrate_bill_receipt_fields
"""
from sqlalchemy import text
from .database import engine

def migrate():
    with engine.connect() as conn:
        # Add transaction_id
        try:
            conn.execute(text("ALTER TABLE bill ADD COLUMN transaction_id TEXT"))
        except Exception:
            pass
        # Add payment_status
        try:
            conn.execute(text("ALTER TABLE bill ADD COLUMN payment_status TEXT DEFAULT 'Paid'"))
        except Exception:
            pass
        conn.commit()

if __name__ == "__main__":
    migrate()
