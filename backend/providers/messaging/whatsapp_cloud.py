"""
WhatsApp Cloud Provider — production messaging via Meta WhatsApp Cloud API.
"""
import logging
import httpx
from providers.base import MessagingProvider, MessageResult
from config import settings

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"


class WhatsAppCloudProvider(MessagingProvider):
    """Production messaging provider using Meta WhatsApp Cloud API with merchant config."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._token = self.config.get("whatsapp_api_token") or settings.WHATSAPP_API_TOKEN or settings.WHATSAPP_ACCESS_TOKEN
        self._phone_id = self.config.get("whatsapp_phone_number_id") or settings.WHATSAPP_PHONE_NUMBER_ID
        logger.info("WhatsAppCloudProvider initialized with keys from %s", "DB" if self.config else ".env")

    async def send_message(self, phone: str, message: str) -> MessageResult:
        try:
            url = f"{WHATSAPP_API_URL}/{self._phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            }

            # Clean phone number
            clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")

            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {"body": message},
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, json=payload, timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    msg_id = data.get("messages", [{}])[0].get("id", "")
                    logger.info("WhatsApp message sent: ID=%s, to=%s", msg_id, phone)
                    return MessageResult(
                        success=True,
                        message_id=msg_id,
                        provider=self.get_provider_name(),
                    )
                else:
                    error_msg = response.text
                    logger.error("WhatsApp send failed: %s", error_msg)
                    return MessageResult(
                        success=False,
                        error=error_msg,
                        provider=self.get_provider_name(),
                    )

        except Exception as e:
            logger.error("WhatsApp service error: %s", str(e))
            return MessageResult(
                success=False,
                error=str(e),
                provider=self.get_provider_name(),
            )

    def get_provider_name(self) -> str:
        return "WhatsApp Cloud API"
