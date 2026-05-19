"""Unit tests for shared UI helper utilities."""

from __future__ import annotations

from decimal import Decimal
import sys

from app.ui import helpers


class _StubParent:
    pass


def test_format_money_formats_decimal() -> None:
    result = helpers.format_money(Decimal("1234.5"), "?")

    assert result == "?1,234.50"


def test_format_money_zero_amount() -> None:
    result = helpers.format_money(Decimal("0"), "\u20B9")

    assert result == "\u20B90.00"


def test_format_money_large_amount() -> None:
    result = helpers.format_money(Decimal("1000000"), "$")

    assert result == "$1,000,000.00"


def test_format_money_negative_amount() -> None:
    result = helpers.format_money(Decimal("-5"), "$")

    assert result == "$-5.00"


def test_confirm_action_yes(monkeypatch) -> None:
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QMessageBox.question",
        lambda *args, **kwargs: helpers.QMessageBox.StandardButton.Yes,
    )

    assert helpers.confirm_action(_StubParent(), "T", "M") is True


def test_confirm_action_no(monkeypatch) -> None:
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QMessageBox.question",
        lambda *args, **kwargs: helpers.QMessageBox.StandardButton.No,
    )

    assert helpers.confirm_action(_StubParent(), "T", "M") is False


def test_open_pdf_missing_path_shows_warning(monkeypatch) -> None:
    calls = {"warned": False}

    def _warn(*args, **kwargs):
        calls["warned"] = True

    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.warning", _warn)

    helpers.open_pdf(None, _StubParent())

    assert calls["warned"] is True


def test_open_pdf_valid_path_calls_startfile(monkeypatch, tmp_path) -> None:
    pdf_path = tmp_path / "receipt.pdf"
    pdf_path.write_text("data", encoding="utf-8")
    calls = {"called": False}

    def _startfile(path):
        calls["called"] = True

    monkeypatch.setattr(helpers.os, "startfile", _startfile, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")

    helpers.open_pdf(str(pdf_path), _StubParent())

    assert calls["called"] is True


def test_send_whatsapp_receipt_success(monkeypatch) -> None:
    class _StubBill:
        id = 1
        customer_phone = "999"
        customer_name = "Alex"
        total = Decimal("10")
        pdf_path = "receipt.pdf"

    class _StubBilling:
        def generate_receipt(self, bill_id):
            return "receipt.pdf"

        def update_whatsapp_status(self, bill_id, status, error=None):
            pass

    class _StubNotification:
        def send_whatsapp_receipt(self, phone_number, customer_name, total, attachment_path=None):
            class _Result:
                success = True
                error_message = None

            return _Result()

    monkeypatch.setattr(helpers, "confirm_action", lambda *args, **kwargs: True)
    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)

    assert (
        helpers.send_whatsapp_receipt(
            bill=_StubBill(),
            billing_service=_StubBilling(),
            notification_service=_StubNotification(),
            parent=_StubParent(),
        )
        is True
    )


def test_send_whatsapp_receipt_missing_phone_shows_warning(monkeypatch) -> None:
    class _StubBill:
        id = 1
        customer_phone = None
        customer_name = "Alex"
        total = Decimal("10")
        pdf_path = None

    class _StubBilling:
        def generate_receipt(self, bill_id):
            return "receipt.pdf"

        def update_whatsapp_status(self, bill_id, status, error=None):
            pass

    class _StubNotification:
        def send_whatsapp_receipt(self, phone_number, customer_name, total, attachment_path=None):
            raise AssertionError("Should not send without phone")

    calls = {"warned": False}

    def _warn(*args, **kwargs):
        calls["warned"] = True

    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.warning", _warn)

    assert (
        helpers.send_whatsapp_receipt(
            bill=_StubBill(),
            billing_service=_StubBilling(),
            notification_service=_StubNotification(),
            parent=_StubParent(),
        )
        is False
    )
    assert calls["warned"] is True


def test_send_whatsapp_receipt_cancelled(monkeypatch) -> None:
    class _StubBill:
        id = 1
        customer_phone = "999"
        customer_name = "Alex"
        total = Decimal("10")
        pdf_path = None

    class _StubBilling:
        def generate_receipt(self, bill_id):
            return "receipt.pdf"

        def update_whatsapp_status(self, bill_id, status, error=None):
            pass

    class _StubNotification:
        def send_whatsapp_receipt(self, phone_number, customer_name, total, attachment_path=None):
            raise AssertionError("Should not send when cancelled")

    monkeypatch.setattr(helpers, "confirm_action", lambda *args, **kwargs: False)

    assert (
        helpers.send_whatsapp_receipt(
            bill=_StubBill(),
            billing_service=_StubBilling(),
            notification_service=_StubNotification(),
            parent=_StubParent(),
        )
        is False
    )
