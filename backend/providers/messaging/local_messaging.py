"""
Local Messaging Provider — WhatsApp Web session + deep link fallback.

Priority:
1. If WhatsApp Web service is connected (QR scanned) → send REAL message
2. If not connected → generate wa.me deep link for manual sending

Always generates a wa.me deep link in the result for the UI.
"""
import json
import uuid
import logging
import urllib.parse
import httpx
from pathlib import Path
from datetime import datetime, timezone
from providers.base import MessagingProvider, MessageResult
from config import settings

logger = logging.getLogger(__name__)

SIMULATED_DIR = Path(__file__).resolve().parent.parent.parent / "simulated_messages"


def _get_merchant_whatsapp() -> str:
    try:
        from routers.merchant_config import get_merchant_whatsapp
        return get_merchant_whatsapp()
    except Exception:
        return ""


class LocalMessagingProvider(MessagingProvider):
    """
    Free fallback messaging provider with two tiers:
    1. WhatsApp Web session (real messages via linked account)
    2. wa.me deep links (manual click-to-send)
    Always provides a wa.me link in the result for the UI.
    """

    def __init__(self, merchant_id=None):
        SIMULATED_DIR.mkdir(parents=True, exist_ok=True)
        self._wa_service_url = settings.WHATSAPP_WEB_SERVICE_URL.rstrip("/")
        self._merchant_id = str(merchant_id) if merchant_id else "1"
        logger.info(
            "LocalMessagingProvider initialized (WA Web: %s, Merchant: %s)", self._wa_service_url, self._merchant_id
        )

    def _generate_whatsapp_link(self, phone: str, message: str) -> str:
        """Generate a wa.me deep link with pre-filled message."""
        clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        encoded_message = urllib.parse.quote(message)
        return f"https://wa.me/{clean_phone}?text={encoded_message}"

    async def _check_wa_web_connected(self) -> bool:
        """Check if WhatsApp Web service is connected."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._wa_service_url}/status",
                    params={"merchant_id": self._merchant_id},
                    timeout=3.0
                )
                if resp.status_code == 200:
                    return resp.json().get("connected", False)
        except Exception:
            pass
        return False

    async def _try_send_via_wa_web(self, phone: str, message: str) -> bool:
        """Try to send via WhatsApp Web. Returns True if successful."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._wa_service_url}/send",
                    json={"phone": phone, "message": message, "merchant_id": self._merchant_id},
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        logger.info("WhatsApp Web message sent to %s", phone)
                        return True
        except Exception as e:
            logger.warning("WhatsApp Web send error: %s", str(e))
        return False

    async def send_message(self, phone: str, message: str) -> MessageResult:
        msg_id = f"WALINK-{uuid.uuid4().hex[:10].upper()}"
        merchant_wa = _get_merchant_whatsapp()

        # Always generate the deep link for the UI
        wa_link = self._generate_whatsapp_link(phone, message)

        # Try sending via WhatsApp Web session
        sent_via_web = False
        wa_connected = await self._check_wa_web_connected()
        if wa_connected:
            sent_via_web = await self._try_send_via_wa_web(phone, message)

        # Log to file
        msg_log = {
            "message_id": msg_id,
            "customer_phone": phone,
            "merchant_whatsapp": merchant_wa or "not_configured",
            "message": message,
            "whatsapp_link": wa_link,
            "sent_via_web": sent_via_web,
            "wa_web_connected": wa_connected,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "sent_via_web" if sent_via_web else "link_generated",
        }
        log_file = SIMULATED_DIR / f"{msg_id}.json"
        log_file.write_text(json.dumps(msg_log, indent=2), encoding="utf-8")

        provider_name = "WhatsApp Web (Session)" if sent_via_web else "WhatsApp Deep Link (wa.me)"
        status_msg = "sent" if sent_via_web else "link_generated"

        logger.info(
            "WhatsApp %s: ID=%s, to=%s, via=%s",
            status_msg, msg_id, phone, provider_name,
        )

        return MessageResult(
            success=True,
            message_id=msg_id,
            provider=provider_name,
            simulated=not sent_via_web,
            details={
                "whatsapp_link": wa_link,
                "sent_via_web": sent_via_web,
                "merchant_whatsapp": merchant_wa,
            },
        )

    def get_provider_name(self) -> str:
        return "WhatsApp Web + Deep Link"
