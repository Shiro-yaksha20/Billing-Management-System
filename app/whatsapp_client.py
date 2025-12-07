import requests
import json
from . import settings_service
from .utils import logger


def send_whatsapp_message(to_number: str, message: str, attachment_path: str = None):
    """
    Sends a message via the WhatsApp Cloud API.

    Args:
        to_number: The recipient's phone number (with country code, e.g., "919876543210").
        message: The text message to send.
        attachment_path: The local path to a file to attach (e.g., a PDF receipt).

    Returns:
        A tuple of (success: bool, response_data: dict).
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
            # Upload the media first
            upload_url = f"https://graph.facebook.com/{api_version}/{phone_id}/media"
            
            with open(attachment_path, 'rb') as file:
                files = {
                    'file': (attachment_path.split('/')[-1], file, 'application/pdf'),
                    'messaging_product': (None, 'whatsapp')
                }
                upload_headers = {"Authorization": f"Bearer {token}"}
                upload_response = requests.post(upload_url, headers=upload_headers, files=files)

            if upload_response.status_code != 200:
                logger.error(f"Failed to upload media to WhatsApp: {upload_response.text}")
                return False, {"error": "Failed to upload media.", "details": upload_response.json()}

            media_id = upload_response.json().get("id")
            if not media_id:
                logger.error("Media ID not found in WhatsApp upload response.")
                return False, {"error": "Media ID not found in upload response."}

            # Send the document with a caption
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "document",
                "document": {
                    "id": media_id,
                    "filename": attachment_path.split("/")[-1],
                    "caption": message
                }
            }
        else:
            # Send a simple text message if no attachment
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message}
            }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            logger.info(f"WhatsApp message sent to {to_number}")
            return True, response.json()
        else:
            logger.error(f"Failed to send WhatsApp message to {to_number}: {response.text}")
            return False, response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"An HTTP error occurred while sending WhatsApp message: {e}")
        return False, {"error": "An HTTP error occurred.", "details": str(e)}
    except IOError as e:
        logger.error(f"An IO error occurred while reading attachment: {e}")
        return False, {"error": "An IO error occurred.", "details": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in send_whatsapp_message: {e}")
        return False, {"error": "Unexpected error.", "details": str(e)}
