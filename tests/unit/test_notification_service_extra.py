"""Additional unit tests for NotificationService."""

from __future__ import annotations

from app.services.notification_service import NotificationService


def test_send_whatsapp_receipt_without_country_code(monkeypatch) -> None:
    captured = {}

    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "", "business_name": "Salon"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        captured["to_number"] = to_number
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    service.send_whatsapp_receipt("12345", "Alex", "50")

    assert captured["to_number"] == "12345"


def test_send_whatsapp_receipt_uses_default_template(monkeypatch) -> None:
    captured = {}

    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "91", "business_name": "Salon"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        captured["message"] = message
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    service.send_whatsapp_receipt("999", "Alex", "100")

    assert "Alex" in captured["message"]
    assert "Salon" in captured["message"]
