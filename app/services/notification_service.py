"""Notification service for outbound messaging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..infrastructure.whatsapp_client import send_whatsapp_message
from .settings_service import SettingsService


@dataclass(frozen=True)
class NotificationResult:
    """Result of a notification attempt."""

    success: bool
    response: dict
    error_message: Optional[str] = None


class NotificationService:
    """Service for sending notifications."""

    def __init__(self, settings_service: SettingsService) -> None:
        self._settings_service = settings_service

    def send_whatsapp_receipt(
        self,
        phone_number: str,
        customer_name: str,
        total: str,
        attachment_path: Optional[str] = None,
    ) -> NotificationResult:
        currency_symbol = (
            self._settings_service.get_setting("currency_symbol", "\u20B9") or "\u20B9"
        )
        template = self._settings_service.get_setting(
            "whatsapp_message_template",
            "Hi {customer_name}, thank you for visiting {business_name}. Your bill total is {currency_symbol}{total}.",
        )
        message = template.format(
            customer_name=customer_name,
            business_name=self._settings_service.get_setting("business_name", ""),
            currency_symbol=currency_symbol,
            total=total,
        )
        country_code = self._settings_service.get_setting("whatsapp_country_code", "91")
        normalized_country = (country_code or "").strip().lstrip("+")
        clean_phone = (phone_number or "").strip().lstrip("+")
        clean_phone = clean_phone.replace(" ", "").replace("-", "")

        if normalized_country and clean_phone.startswith(normalized_country):
            full_phone = clean_phone
        elif normalized_country:
            full_phone = f"{normalized_country}{clean_phone}"
        else:
            full_phone = clean_phone

        success, response = send_whatsapp_message(
            full_phone, message, self._settings_service, attachment_path
        )
        error_message = None
        if not success:
            error_message = str(response)[:500]
        return NotificationResult(success=success, response=response, error_message=error_message)
