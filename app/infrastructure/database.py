"""Database session management."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..constants import DATABASE_URL
from ..models import Base

engine = create_engine(
    DATABASE_URL,
    # SQLite + StaticPool keeps one shared in-memory/file connection for app lifetime.
    # With check_same_thread=False this supports cross-thread access, but session scoping
    # remains mandatory to avoid thread contention.
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# expire_on_commit=False intentionally keeps ORM objects usable after commit in UI flows.
# Callers should reload entities when strict fresh state is required.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def db_session():
    """Provide a transactional scope around operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
