"""WhatsApp API adapter."""

from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING

import requests

from .logging import logger

if TYPE_CHECKING:
    from ..services.settings_service import SettingsService


def send_whatsapp_message(
    to_number: str,
    message: str,
    settings_service: "SettingsService",
    attachment_path: Optional[str] = None,
):
    """Send a WhatsApp message with optional attachment.
    
    Args:
        to_number: The recipient phone number.
        message: The message body or caption.
        settings_service: SettingsService instance for retrieving API credentials.
        attachment_path: Optional path to a PDF attachment.
    """
    token = settings_service.get_secret("whatsapp_api_token")
    phone_id = settings_service.get_setting("whatsapp_phone_id")

    if not token or not phone_id:
        logger.error("WhatsApp API token or Phone ID is not configured.")
        return False, {"error": "WhatsApp API token or Phone ID is not configured."}

    api_version = settings_service.get_setting("whatsapp_api_version", "v15.0")
    url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        if attachment_path:
            upload_url = f"https://graph.facebook.com/{api_version}/{phone_id}/media"
            with open(attachment_path, "rb") as file:
                files = {
                    "file": (attachment_path.split("/")[-1], file, "application/pdf"),
                    "messaging_product": (None, "whatsapp"),
                }
                upload_headers = {"Authorization": f"Bearer {token}"}
                upload_response = requests.post(upload_url, headers=upload_headers, files=files)

            if upload_response.status_code != 200:
                logger.error("Failed to upload media to WhatsApp: %s", upload_response.text)
                return False, {"error": "Failed to upload media.", "details": upload_response.json()}

            media_id = upload_response.json().get("id")
            if not media_id:
                logger.error("Media ID not found in WhatsApp upload response.")
                return False, {"error": "Media ID not found in upload response."}

            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "document",
                "document": {
                    "id": media_id,
                    "filename": attachment_path.split("/")[-1],
                    "caption": message,
                },
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message},
            }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            logger.info("WhatsApp message sent to %s", to_number)
            return True, response.json()

        logger.error("Failed to send WhatsApp message to %s: %s", to_number, response.text)
        return False, response.json()

    except requests.exceptions.RequestException as exc:
        logger.error("HTTP error while sending WhatsApp message: %s", exc)
        return False, {"error": "HTTP error.", "details": str(exc)}
    except IOError as exc:
        logger.error("IO error while reading attachment: %s", exc)
        return False, {"error": "IO error.", "details": str(exc)}
    except Exception as exc:
        logger.error("Unexpected error in send_whatsapp_message: %s", exc)
        return False, {"error": "Unexpected error.", "details": str(exc)}
