"""Additional UI helper tests."""

from __future__ import annotations

import sys
from decimal import Decimal

from app.ui import helpers


class _StubParent:
    pass


def test_open_pdf_darwin_uses_open(monkeypatch, tmp_path) -> None:
    pdf_path = tmp_path / "receipt.pdf"
    pdf_path.write_text("data", encoding="utf-8")
    calls = {"called": False}

    def _run(cmd, check=True):
        calls["called"] = True

    monkeypatch.setattr(helpers.subprocess, "run", _run)
    monkeypatch.setattr(sys, "platform", "darwin")

    helpers.open_pdf(str(pdf_path), _StubParent())

    assert calls["called"] is True


def test_send_whatsapp_receipt_formats_total(monkeypatch) -> None:
    class _StubBill:
        id = 1
        customer_phone = "999"
        customer_name = "Alex"
        total = Decimal("12.5")
        pdf_path = "receipt.pdf"

    class _StubBilling:
        def generate_receipt(self, bill_id):
            return "receipt.pdf"

        def update_whatsapp_status(self, bill_id, status, error=None):
            pass

    class _StubNotification:
        def __init__(self):
            self.total = None

        def send_whatsapp_receipt(self, phone_number, customer_name, total, attachment_path=None):
            self.total = total

            class _Result:
                success = True
                error_message = None

            return _Result()

    notifier = _StubNotification()
    monkeypatch.setattr(helpers, "confirm_action", lambda *args, **kwargs: True)
    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)

    helpers.send_whatsapp_receipt(
        bill=_StubBill(),
        billing_service=_StubBilling(),
        notification_service=notifier,
        parent=_StubParent(),
    )

    assert notifier.total == "12.50"
