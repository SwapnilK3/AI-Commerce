"""
Local Messaging Provider — open-source fallback for WhatsApp messaging.
Simulates messages by logging to JSON files with the same interface.
"""
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from providers.base import MessagingProvider, MessageResult

logger = logging.getLogger(__name__)

# Directory for simulated messages
SIMULATED_DIR = Path(__file__).resolve().parent.parent.parent / "simulated_messages"


class LocalMessagingProvider(MessagingProvider):
    """
    Free fallback messaging provider.
    Simulates WhatsApp messages by logging them to JSON files.
    Same interface as production — zero code changes needed to switch.
    """

    def __init__(self):
        SIMULATED_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("LocalMessagingProvider initialized (messages saved to %s)", SIMULATED_DIR)

    async def send_message(self, phone: str, message: str) -> MessageResult:
        msg_id = f"LOCAL-MSG-{uuid.uuid4().hex[:10].upper()}"

        msg_log = {
            "message_id": msg_id,
            "phone": phone,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "simulated",
            "provider": self.get_provider_name(),
            "channel": "whatsapp_simulation",
        }

        # Save message log
        log_file = SIMULATED_DIR / f"{msg_id}.json"
        log_file.write_text(json.dumps(msg_log, indent=2), encoding="utf-8")

        logger.info(
            "Simulated WhatsApp message: ID=%s, to=%s, len=%d",
            msg_id, phone, len(message),
        )

        return MessageResult(
            success=True,
            message_id=msg_id,
            provider=self.get_provider_name(),
            simulated=True,
            details={
                "log_file": str(log_file),
                "message_preview": message[:80] + "..." if len(message) > 80 else message,
            },
        )

    def get_provider_name(self) -> str:
        return "Local Messaging (Simulated)"
