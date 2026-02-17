"""Unit tests for NotificationService."""

from __future__ import annotations

from app.services.notification_service import NotificationService


def test_send_whatsapp_receipt_success(monkeypatch) -> None:
    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "91", "salon_name": "Salon"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    result = service.send_whatsapp_receipt("999", "Alex", "100")

    assert result.success is True
    assert result.error_message is None


def test_send_whatsapp_receipt_failure(monkeypatch) -> None:
    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "91", "salon_name": "Salon"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        return False, {"error": "fail"}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    result = service.send_whatsapp_receipt("999", "Alex", "100")

    assert result.success is False
    assert result.error_message is not None
