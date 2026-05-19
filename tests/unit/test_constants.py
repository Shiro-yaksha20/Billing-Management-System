"""Unit tests for application constants."""

from __future__ import annotations

from pathlib import Path

from app import constants


def test_paths_resolve_under_app_dir() -> None:
    app_dir = Path(constants.APP_DIR)

    assert Path(constants.DATABASE_FILE).is_absolute()
    assert Path(constants.RECEIPTS_DIR).is_absolute()
    assert Path(constants.LOGS_DIR).is_absolute()
    assert app_dir in Path(constants.DATABASE_FILE).parents


def test_database_url_prefix() -> None:
    assert constants.DATABASE_URL.startswith("sqlite:///")


def test_business_rule_constants() -> None:
    assert constants.MAX_IMPORT_ERRORS > 0
    assert constants.MAX_DISCOUNT_PERCENT == 100.0
    assert constants.MAX_SERVICE_NAME_LEN > 0
    assert constants.MAX_CATEGORY_LEN > 0
    assert constants.MAX_NOTES_LEN > 0
