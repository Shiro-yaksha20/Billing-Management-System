"""Additional unit tests for SettingsService."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models import Setting
from app.services.settings_service import SettingsService


@dataclass
class _StubSettingsRepo:
    store: dict[str, Setting]

    def __init__(self) -> None:
        self.store = {}

    def get_by_key(self, key: str) -> Optional[Setting]:
        return self.store.get(key)

    def set_value(self, key: str, value: str | None) -> Setting:
        setting = Setting(key=key, value=value)
        self.store[key] = setting
        return setting


def test_get_setting_returns_default_when_mapped_missing() -> None:
    service = SettingsService(_StubSettingsRepo())

    assert service.get_setting("salon_name", "default") == "default"


def test_set_setting_maps_legacy_key_to_new() -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)

    service.set_setting("salon_name", "Legacy")

    assert repo.get_by_key("business_name") is not None
    assert repo.get_by_key("business_name").value == "Legacy"


def test_get_setting_uses_existing_new_key() -> None:
    repo = _StubSettingsRepo()
    repo.set_value("business_name", "New")
    repo.set_value("salon_name", "Old")
    service = SettingsService(repo)

    assert service.get_setting("business_name") == "New"
