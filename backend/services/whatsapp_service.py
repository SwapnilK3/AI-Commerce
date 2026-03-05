"""
WhatsApp Service — sends messages via Meta WhatsApp Cloud API.
"""
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"


def _has_whatsapp_config() -> bool:
    """Check if WhatsApp credentials are configured."""
    return bool(
        settings.WHATSAPP_ACCESS_TOKEN
        and settings.WHATSAPP_PHONE_NUMBER_ID
        and settings.WHATSAPP_ACCESS_TOKEN != "your_whatsapp_access_token"
    )


async def send_whatsapp_message(phone: str, message: str) -> dict:
    """
    Send a WhatsApp message via Meta Cloud API.
    Returns: {"success": bool, "message_id": str|None, "error": str|None}
    """
    if not _has_whatsapp_config():
        logger.warning("WhatsApp not configured — skipping message to %s", phone)
        return {
            "success": False,
            "message_id": None,
            "error": "WhatsApp credentials not configured",
        }

    try:
        url = f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        # Clean phone number (remove +, spaces)
        clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")

        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {"body": message},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)

            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id", "")
                logger.info("WhatsApp message sent: ID=%s, to=%s", message_id, phone)
                return {"success": True, "message_id": message_id, "error": None}
            else:
                error_msg = response.text
                logger.error("WhatsApp send failed: %s", error_msg)
                return {"success": False, "message_id": None, "error": error_msg}

    except Exception as e:
        logger.error("WhatsApp service error: %s", str(e))
        return {"success": False, "message_id": None, "error": str(e)}
