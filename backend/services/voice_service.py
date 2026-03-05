"""
Voice Service — handles Twilio voice calls and ElevenLabs TTS.
"""
import logging
from config import settings

logger = logging.getLogger(__name__)


def _has_twilio_config() -> bool:
    """Check if Twilio credentials are configured."""
    return bool(
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_PHONE_NUMBER
        and settings.TWILIO_ACCOUNT_SID != "your_twilio_account_sid"
    )


async def make_call(phone: str, message: str) -> dict:
    """
    Initiate a voice call via Twilio with TTS message.
    Returns: {"success": bool, "call_sid": str|None, "error": str|None}
    """
    if not _has_twilio_config():
        logger.warning("Twilio not configured — skipping voice call to %s", phone)
        return {
            "success": False,
            "call_sid": None,
            "error": "Twilio credentials not configured",
        }

    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Build TwiML for the call
        twiml = (
            f'<Response>'
            f'<Say voice="Polly.Aditi" language="en-IN">{message}</Say>'
            f'<Gather input="speech" timeout="5" '
            f'action="{settings.APP_BASE_URL}/api/communications/voice-response" '
            f'method="POST">'
            f'<Say voice="Polly.Aditi" language="en-IN">I am waiting for your response.</Say>'
            f'</Gather>'
            f'<Say voice="Polly.Aditi" language="en-IN">We did not receive a response. Goodbye!</Say>'
            f'</Response>'
        )

        call = client.calls.create(
            to=phone,
            from_=settings.TWILIO_PHONE_NUMBER,
            twiml=twiml,
            status_callback=f"{settings.APP_BASE_URL}/api/communications/call-status",
            status_callback_method="POST",
            status_callback_event=["completed", "failed", "busy", "no-answer"],
        )

        logger.info("Call initiated: SID=%s, to=%s", call.sid, phone)
        return {"success": True, "call_sid": call.sid, "error": None}

    except Exception as e:
        logger.error("Failed to make call to %s: %s", phone, str(e))
        return {"success": False, "call_sid": None, "error": str(e)}


async def generate_speech_url(text: str) -> str | None:
    """
    Generate TTS audio via ElevenLabs and return audio URL.
    Returns None if ElevenLabs is not configured.
    """
    if not settings.ELEVENLABS_API_KEY or settings.ELEVENLABS_API_KEY == "your_elevenlabs_api_key":
        logger.warning("ElevenLabs not configured — using Twilio built-in TTS")
        return None

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}",
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                timeout=30.0,
            )
            if response.status_code == 200:
                # In production, save audio and return URL
                logger.info("ElevenLabs TTS generated successfully")
                return "elevenlabs_audio_generated"
            else:
                logger.error("ElevenLabs TTS failed: %s", response.text)
                return None
    except Exception as e:
        logger.error("ElevenLabs TTS error: %s", str(e))
        return None
