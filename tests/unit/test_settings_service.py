"""Unit tests for SettingsService."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models import Setting
from app.services.settings_service import SettingsService


@dataclass
class _StubSettingsRepo:
    setting: Optional[Setting] = None
    store: dict[str, Setting] | None = None

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = {}

    def get_by_key(self, key: str) -> Optional[Setting]:
        if self.store is None:
            return None
        return self.store.get(key)

    def set_value(self, key: str, value: str | None) -> Setting:
        setting = Setting(key=key, value=value)
        if self.store is not None:
            self.store[key] = setting
        self.setting = setting
        return setting


def test_get_setting_returns_default_when_missing() -> None:
    service = SettingsService(_StubSettingsRepo())
    assert service.get_setting("missing", "default") == "default"


def test_set_setting_updates_value() -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)
    service.set_setting("key", "value")
    assert repo.setting is not None
    assert repo.setting.value == "value"


def test_get_setting_migrates_legacy_key() -> None:
    repo = _StubSettingsRepo()
    repo.set_value("salon_name", "Legacy Salon")
    service = SettingsService(repo)

    value = service.get_setting("business_name")

    assert value == "Legacy Salon"
    assert repo.get_by_key("business_name") is not None


def test_get_setting_new_key_without_legacy() -> None:
    repo = _StubSettingsRepo()
    repo.set_value("custom_key", "Value")
    service = SettingsService(repo)

    assert service.get_setting("custom_key") == "Value"


def test_set_setting_with_none_value() -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)

    service.set_setting("business_tagline", None)

    assert repo.get_by_key("business_tagline") is not None
    assert repo.get_by_key("business_tagline").value is None


def test_set_setting_new_key_stores_directly() -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)

    service.set_setting("custom_key", "Custom")

    assert repo.get_by_key("custom_key").value == "Custom"


def test_get_setting_fallbacks_to_legacy_key() -> None:
    repo = _StubSettingsRepo()
    repo.set_value("salon_phone", "999")
    service = SettingsService(repo)

    assert service.get_setting("business_phone") == "999"


def test_set_setting_does_not_overwrite_migrated_key() -> None:
    repo = _StubSettingsRepo()
    repo.set_value("business_name", "New")
    service = SettingsService(repo)

    service.set_setting("salon_name", "Old")

    assert repo.get_by_key("business_name").value == "New"


def test_set_setting_overwrites_existing_value() -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)

    service.set_setting("business_name", "First")
    service.set_setting("business_name", "Second")

    assert repo.get_by_key("business_name").value == "Second"


def test_get_secret_returns_value(monkeypatch) -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)

    def _get_password(service_name, key):
        return "secret"

    monkeypatch.setattr("keyring.get_password", _get_password)

    assert service.get_secret("token") == "secret"


def test_get_secret_handles_exception(monkeypatch) -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)

    def _get_password(service_name, key):
        raise RuntimeError("fail")

    monkeypatch.setattr("keyring.get_password", _get_password)

    assert service.get_secret("token") is None


def test_set_secret_sets_password(monkeypatch) -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)
    calls = {}

    def _set_password(service_name, key, value):
        calls["value"] = value

    monkeypatch.setattr("keyring.set_password", _set_password)

    assert service.set_secret("token", "secret") is True
    assert calls["value"] == "secret"


def test_set_secret_deletes_password(monkeypatch) -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)
    calls = {"deleted": False}

    def _delete_password(service_name, key):
        calls["deleted"] = True

    monkeypatch.setattr("keyring.delete_password", _delete_password)

    assert service.set_secret("token", None) is True
    assert calls["deleted"] is True


def test_set_secret_handles_exception(monkeypatch) -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)

    def _set_password(service_name, key, value):
        raise RuntimeError("fail")

    monkeypatch.setattr("keyring.set_password", _set_password)

    assert service.set_secret("token", "secret") is False
