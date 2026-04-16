"""Shared UI helper functions for common interactions."""

from __future__ import annotations

import os
from decimal import Decimal
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox, QWidget

if TYPE_CHECKING:
    from ..dto.bill_dto import BillData
    from ..services.billing_service import BillingService
    from ..services.notification_service import NotificationService


def format_money(amount: Decimal, currency: str = "?") -> str:
    """Format a monetary value with a currency symbol."""
    return f"{currency}{amount:,.2f}"


def open_pdf(pdf_path: str | None, parent: QWidget, title: str = "Receipt") -> None:
    """Open a PDF path if present, otherwise show a warning message."""
    if not pdf_path or not os.path.exists(pdf_path):
        QMessageBox.warning(parent, "Not Found", "PDF receipt file not found.")
        return

    try:
        os.startfile(pdf_path)
    except OSError:
        QMessageBox.information(parent, title, f"Receipt saved at:\n{pdf_path}")


def confirm_action(parent: QWidget, title: str, message: str) -> bool:
    """Show a Yes/No confirmation dialog."""
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes


def send_whatsapp_receipt(
    bill: BillData,
    billing_service: BillingService,
    notification_service: NotificationService,
    parent: QWidget,
    customer_phone: str | None = None,
    customer_name: str | None = None,
) -> bool:
    """Send receipt to WhatsApp after optional PDF generation and confirmation."""
    target_phone = customer_phone or bill.customer_phone
    target_name = customer_name or bill.customer_name or "Customer"

    if not target_phone:
        QMessageBox.warning(parent, "Missing Phone", "Customer phone number is missing.")
        return False

    if not confirm_action(parent, "Send WhatsApp", f"Send receipt to {target_phone}?"):
        return False

    pdf_path = bill.pdf_path
    if not pdf_path or not os.path.exists(pdf_path):
        pdf_path = billing_service.generate_receipt(bill.id)

    result = notification_service.send_whatsapp_receipt(
        phone_number=target_phone,
        customer_name=target_name,
        total=f"{bill.total:.2f}",
        attachment_path=pdf_path,
    )

    if result.success:
        billing_service.update_whatsapp_status(bill.id, "Sent")
        QMessageBox.information(parent, "Sent", "Receipt sent successfully.")
        return True

    billing_service.update_whatsapp_status(bill.id, "Failed", result.error_message)
    QMessageBox.warning(parent, "Failed", result.error_message or "Send failed.")
    return False
