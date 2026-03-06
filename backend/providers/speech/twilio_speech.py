"""
Twilio Speech Provider — production STT (Twilio) + TTS (ElevenLabs/Twilio).
"""
import logging
import httpx
from providers.base import SpeechProvider, SpeechResult
from config import settings
from services.ai_engine import detect_intent as keyword_detect

logger = logging.getLogger(__name__)


class TwilioSpeechProvider(SpeechProvider):
    """
    Production speech provider with merchant-specific config.
    TTS: ElevenLabs (high quality) with Twilio Polly fallback.
    STT: Twilio built-in speech recognition.
    Intent: Keyword matching (upgradeable to LLM).
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.elevenlabs_key = self.config.get("elevenlabs_api_key") or settings.ELEVENLABS_API_KEY
        self.elevenlabs_voice_id = self.config.get("elevenlabs_voice_id") or settings.ELEVENLABS_VOICE_ID

        self._has_elevenlabs = bool(
            self.elevenlabs_key
            and self.elevenlabs_key != "your_elevenlabs_api_key"
        )
        logger.info(
            "TwilioSpeechProvider initialized (ElevenLabs: %s)",
            "enabled" if self._has_elevenlabs else "disabled, using Twilio Polly",
        )

    async def text_to_speech(self, text: str) -> bytes | None:
        """Generate TTS audio via ElevenLabs if available."""
        if not self._has_elevenlabs:
            return None  # Twilio will use built-in Polly TTS

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}",
                    headers={
                        "xi-api-key": self.elevenlabs_key,
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
                    logger.info("ElevenLabs TTS generated: %d bytes", len(response.content))
                    return response.content
                else:
                    logger.error("ElevenLabs TTS failed: %s", response.text)
                    return None
        except Exception as e:
            logger.error("ElevenLabs TTS error: %s", str(e))
            return None

    async def speech_to_text(self, audio_data: bytes) -> str:
        """STT is handled by Twilio Gather in the call flow, not here."""
        # Twilio handles speech recognition inline via <Gather> TwiML
        logger.info("STT handled by Twilio Gather (inline)")
        return ""

    async def detect_intent(self, transcript: str) -> SpeechResult:
        """Detect intent from customer speech transcript."""
        intent = keyword_detect(transcript)
        return SpeechResult(
            text=transcript,
            intent=intent,
            confidence=0.9 if intent != "unknown" else 0.1,
            provider=self.get_provider_name(),
        )

    def get_provider_name(self) -> str:
        return "Twilio Speech + ElevenLabs TTS"
