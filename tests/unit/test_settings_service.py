"""Unit tests for SettingsService."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models import Setting
from app.services.settings_service import SettingsService


@dataclass
class _StubSettingsRepo:
    setting: Optional[Setting] = None

    def get_by_key(self, key: str) -> Optional[Setting]:
        return self.setting if self.setting and self.setting.key == key else None

    def set_value(self, key: str, value: str | None) -> Setting:
        self.setting = Setting(key=key, value=value)
        return self.setting


def test_get_setting_returns_default_when_missing() -> None:
    service = SettingsService(_StubSettingsRepo())
    assert service.get_setting("missing", "default") == "default"


def test_set_setting_updates_value() -> None:
    repo = _StubSettingsRepo()
    service = SettingsService(repo)
    service.set_setting("key", "value")
    assert repo.setting is not None
    assert repo.setting.value == "value"


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
