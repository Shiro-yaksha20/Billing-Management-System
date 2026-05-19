"""Integration tests for settings key migrations."""

from __future__ import annotations

from app.infrastructure import database as infra_db
from app.repositories.settings_repository import SettingsRepository
from app.services.settings_service import SettingsService


def test_get_setting_migrates_legacy_key(temp_db) -> None:
    repo = SettingsRepository(infra_db.db_session)
    repo.set_value("salon_name", "Legacy")
    service = SettingsService(repo)

    value = service.get_setting("business_name")

    assert value == "Legacy"
    assert repo.get_by_key("business_name") is not None


def test_get_setting_new_key_without_legacy(temp_db) -> None:
    repo = SettingsRepository(infra_db.db_session)
    repo.set_value("business_name", "Modern")
    service = SettingsService(repo)

    assert service.get_setting("business_name") == "Modern"


def test_get_setting_fallback_to_legacy(temp_db) -> None:
    repo = SettingsRepository(infra_db.db_session)
    repo.set_value("salon_phone", "999")
    service = SettingsService(repo)

    assert service.get_setting("business_phone") == "999"


def test_set_setting_overwrites_value(temp_db) -> None:
    repo = SettingsRepository(infra_db.db_session)
    service = SettingsService(repo)

    service.set_setting("business_name", "First")
    service.set_setting("business_name", "Second")

    assert repo.get_by_key("business_name").value == "Second"
