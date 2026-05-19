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


def test_send_whatsapp_receipt_formats_message_and_currency(monkeypatch) -> None:
    captured = {}

    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {
                "whatsapp_country_code": "91",
                "business_name": "Salon",
                "currency_symbol": "\u20B9",
            }.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        captured["to_number"] = to_number
        captured["message"] = message
        captured["attachment"] = attachment_path
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    result = service.send_whatsapp_receipt("999", "Alex", "100", attachment_path="receipt.pdf")

    assert result.success is True
    assert "Alex" in captured["message"]
    assert "Salon" in captured["message"]
    assert "\u20B9100" in captured["message"]
    assert captured["attachment"] == "receipt.pdf"


def test_send_whatsapp_receipt_custom_template(monkeypatch) -> None:
    captured = {}

    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {
                "whatsapp_country_code": "91",
                "business_name": "Salon",
                "currency_symbol": "$",
                "whatsapp_message_template": "Hello {customer_name} - {currency_symbol}{total}",
            }.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        captured["message"] = message
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    service.send_whatsapp_receipt("999", "Alex", "100")

    assert captured["message"] == "Hello Alex - $100"


def test_send_whatsapp_receipt_does_not_double_prepend_country_code(monkeypatch) -> None:
    captured = {}

    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "91"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        captured["to_number"] = to_number
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    service.send_whatsapp_receipt("911234", "Alex", "100")

    assert captured["to_number"] == "911234"


def test_send_whatsapp_receipt_handles_plus_prefix(monkeypatch) -> None:
    captured = {}

    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "91"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        captured["to_number"] = to_number
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    service.send_whatsapp_receipt("+91 1234", "Alex", "100")

    assert captured["to_number"] == "911234"


def test_send_whatsapp_receipt_truncates_error_message(monkeypatch) -> None:
    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "91"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        return False, {"error": "x" * 600}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    result = service.send_whatsapp_receipt("999", "Alex", "100")

    assert result.success is False
    assert result.error_message is not None
    assert len(result.error_message) <= 500


def test_send_whatsapp_receipt_allows_empty_phone(monkeypatch) -> None:
    captured = {}

    class _StubSettings:
        def get_setting(self, key: str, default: str | None = None) -> str | None:
            return {"whatsapp_country_code": "91"}.get(key, default)

        def get_secret(self, key: str) -> str | None:
            return "token"

    def _stub_send(to_number, message, settings_service, attachment_path=None):
        captured["to_number"] = to_number
        return True, {"ok": True}

    monkeypatch.setattr("app.services.notification_service.send_whatsapp_message", _stub_send)

    service = NotificationService(_StubSettings())
    result = service.send_whatsapp_receipt("", "Alex", "100")

    assert result.success is True
    assert captured["to_number"] == "91"
