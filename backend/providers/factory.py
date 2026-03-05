"""
Provider Factory — auto-detects available API keys and selects
the appropriate provider (production or open-source fallback).
"""
import logging
from dataclasses import dataclass
from config import settings
from providers.base import VoiceProvider, MessagingProvider, SpeechProvider

logger = logging.getLogger(__name__)


def _is_set(val: str, placeholder: str = "") -> bool:
    """Check if an env var is set to a real value (not empty/placeholder)."""
    if not val:
        return False
    placeholders = {"", "your_", "changeme", "xxx", "placeholder"}
    return not any(val.lower().startswith(p) for p in placeholders if p)


def _has_twilio() -> bool:
    return all([
        _is_set(settings.TWILIO_ACCOUNT_SID),
        _is_set(settings.TWILIO_AUTH_TOKEN),
        _is_set(settings.TWILIO_PHONE_NUMBER),
    ])


def _has_whatsapp() -> bool:
    return (
        _is_set(settings.WHATSAPP_API_TOKEN)
        or _is_set(settings.WHATSAPP_ACCESS_TOKEN)
    )


def _has_elevenlabs() -> bool:
    return _is_set(settings.ELEVENLABS_API_KEY)


# ── Factory Functions ──────────────────────────────────────

def create_voice_provider() -> VoiceProvider:
    """Create voice provider based on available API keys."""
    if _has_twilio():
        from providers.voice.twilio_voice import TwilioVoiceProvider
        logger.info("✓ Voice: Using Twilio (production)")
        return TwilioVoiceProvider()
    else:
        from providers.voice.local_voice import LocalVoiceProvider
        logger.info("⟳ Voice: Using Local Simulation (fallback)")
        return LocalVoiceProvider()


def create_messaging_provider() -> MessagingProvider:
    """Create messaging provider based on available API keys."""
    if _has_whatsapp():
        from providers.messaging.whatsapp_cloud import WhatsAppCloudProvider
        logger.info("✓ Messaging: Using WhatsApp Cloud API (production)")
        return WhatsAppCloudProvider()
    else:
        from providers.messaging.local_messaging import LocalMessagingProvider
        logger.info("⟳ Messaging: Using Local Simulation (fallback)")
        return LocalMessagingProvider()


def create_speech_provider() -> SpeechProvider:
    """Create speech provider based on available API keys."""
    if _has_twilio() or _has_elevenlabs():
        from providers.speech.twilio_speech import TwilioSpeechProvider
        logger.info("✓ Speech: Using Twilio + ElevenLabs (production)")
        return TwilioSpeechProvider()
    else:
        from providers.speech.whisper_speech import WhisperSpeechProvider
        logger.info("⟳ Speech: Using Whisper + pyttsx3 (fallback)")
        return WhisperSpeechProvider()


# ── Provider Container ─────────────────────────────────────

@dataclass
class Providers:
    """Container holding all active provider instances."""
    voice: VoiceProvider
    messaging: MessagingProvider
    speech: SpeechProvider

    def summary(self) -> dict:
        return {
            "voice": self.voice.get_provider_name(),
            "messaging": self.messaging.get_provider_name(),
            "speech": self.speech.get_provider_name(),
        }


# Singleton — initialized once at startup
_providers: Providers | None = None


def get_providers() -> Providers:
    """Get or create the global provider instances."""
    global _providers
    if _providers is None:
        _providers = init_providers()
    return _providers


def init_providers() -> Providers:
    """Initialize all providers with auto-detection."""
    global _providers

    logger.info("═" * 50)
    logger.info("Initializing providers (auto-detecting API keys)...")
    logger.info("═" * 50)

    providers = Providers(
        voice=create_voice_provider(),
        messaging=create_messaging_provider(),
        speech=create_speech_provider(),
    )

    logger.info("═" * 50)
    logger.info("Active providers: %s", providers.summary())
    logger.info("═" * 50)

    _providers = providers
    return providers
