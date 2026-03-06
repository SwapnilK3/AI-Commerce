"""
Twilio Voice Provider — production voice calls via Twilio Programmable Voice.
"""
import logging
from providers.base import VoiceProvider, CallResult
from config import settings

logger = logging.getLogger(__name__)


class TwilioVoiceProvider(VoiceProvider):
    """Production voice call provider using Twilio with merchant-specific config."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        # Use merchant config if provided, otherwise fallback to global .env for backward compatibility
        self.account_sid = self.config.get("twilio_account_sid") or settings.TWILIO_ACCOUNT_SID
        self.auth_token = self.config.get("twilio_auth_token") or settings.TWILIO_AUTH_TOKEN
        self.phone_number = self.config.get("twilio_phone_number") or settings.TWILIO_PHONE_NUMBER
        
        from twilio.rest import Client
        self._client = Client(self.account_sid, self.auth_token)
        logger.info("TwilioVoiceProvider initialized with keys from %s", "DB" if self.config else ".env")

    async def make_call(self, phone: str, message: str, callback_url: str = "") -> CallResult:
        try:
            base_url = settings.APP_BASE_URL

            twiml = (
                f'<Response>'
                f'<Say voice="Polly.Aditi" language="en-IN">{message}</Say>'
                f'<Gather input="speech" timeout="5" '
                f'action="{base_url}/api/communications/voice-response" '
                f'method="POST">'
                f'<Say voice="Polly.Aditi" language="en-IN">I am waiting for your response.</Say>'
                f'</Gather>'
                f'<Say voice="Polly.Aditi" language="en-IN">'
                f'We did not receive a response. Goodbye!</Say>'
                f'</Response>'
            )

            call = self._client.calls.create(
                to=phone,
                from_=self.phone_number,
                twiml=twiml,
                status_callback=f"{base_url}/api/communications/call-status",
                status_callback_method="POST",
                status_callback_event=["completed", "failed", "busy", "no-answer"],
            )

            logger.info("Twilio call initiated: SID=%s, to=%s", call.sid, phone)
            return CallResult(
                success=True,
                call_id=call.sid,
                provider=self.get_provider_name(),
                details={"call_sid": call.sid},
            )

        except Exception as e:
            logger.error("Twilio call failed to %s: %s", phone, str(e))
            return CallResult(
                success=False,
                error=str(e),
                provider=self.get_provider_name(),
            )

    async def get_call_status(self, call_id: str) -> str:
        try:
            call = self._client.calls(call_id).fetch()
            return call.status
        except Exception as e:
            logger.error("Failed to get call status for %s: %s", call_id, str(e))
            return "unknown"

    def get_provider_name(self) -> str:
        return "Twilio Voice"
