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
    """Check if a config value is set to a real value (not empty/placeholder)."""
    if not val:
        return False
    placeholders = {"", "your_", "changeme", "xxx", "placeholder"}
    return not any(val.lower().startswith(p) for p in placeholders if p)


def _has_twilio(config: dict) -> bool:
    return all([
        _is_set(config.get("twilio_account_sid", settings.TWILIO_ACCOUNT_SID)),
        _is_set(config.get("twilio_auth_token", settings.TWILIO_AUTH_TOKEN)),
        _is_set(config.get("twilio_phone_number", settings.TWILIO_PHONE_NUMBER)),
    ])


def _has_whatsapp(config: dict) -> bool:
    return (
        _is_set(config.get("whatsapp_api_token", settings.WHATSAPP_API_TOKEN))
        or _is_set(config.get("whatsapp_access_token", settings.WHATSAPP_ACCESS_TOKEN))
    )


def _has_elevenlabs(config: dict) -> bool:
    return _is_set(config.get("elevenlabs_api_key", settings.ELEVENLABS_API_KEY))


# ── Factory Functions ──────────────────────────────────────

def create_voice_provider(config: dict) -> VoiceProvider:
    """Create voice provider based on available API keys (merchant DB > env)."""
    if _has_twilio(config):
        from providers.voice.twilio_voice import TwilioVoiceProvider
        logger.info("✓ Voice: Using Twilio (production config detected)")
        return TwilioVoiceProvider(config)
    else:
        from providers.voice.local_voice import LocalVoiceProvider
        logger.info("⟳ Voice: Using Local Simulation (fallback config detected)")
        return LocalVoiceProvider()


def create_messaging_provider(config: dict, merchant_id=None) -> MessagingProvider:
    """Create messaging provider based on available API keys (merchant DB > env)."""
    if _has_whatsapp(config):
        from providers.messaging.whatsapp_cloud import WhatsAppCloudProvider
        logger.info("\u2713 Messaging: Using WhatsApp Cloud API (production config detected)")
        return WhatsAppCloudProvider(config)
    else:
        from providers.messaging.local_messaging import LocalMessagingProvider
        logger.info("\u27f3 Messaging: Using Local Simulation (fallback config detected)")
        return LocalMessagingProvider(merchant_id=merchant_id)


def create_speech_provider(config: dict) -> SpeechProvider:
    """Create speech provider based on available API keys (merchant DB > env)."""
    if _has_twilio(config) or _has_elevenlabs(config):
        from providers.speech.twilio_speech import TwilioSpeechProvider
        logger.info("✓ Speech: Using Twilio + ElevenLabs (production config detected)")
        return TwilioSpeechProvider(config)
    else:
        from providers.speech.whisper_speech import WhisperSpeechProvider
        logger.info("⟳ Speech: Using Whisper + pyttsx3 (fallback config detected)")
        return WhisperSpeechProvider()


# ── Provider Container ─────────────────────────────────────

@dataclass
class Providers:
    """Container holding active provider instances for a given merchant context."""
    merchant_id: int
    voice: VoiceProvider
    messaging: MessagingProvider
    speech: SpeechProvider

    def summary(self) -> dict:
        return {
            "merchant_id": self.merchant_id,
            "voice": self.voice.get_provider_name(),
            "messaging": self.messaging.get_provider_name(),
            "speech": self.speech.get_provider_name(),
        }


# Cache of providers by merchant IDs
_merchant_providers: dict[int, Providers] = {}


def get_providers(merchant=None) -> Providers:
    """
    Get or create the provider instances for a specific merchant.
    If no merchant is provided (e.g., initial system boot or legacy tasks),
    it falls back to a dummy merchant ID (0) and uses global `.env` vars.
    """
    global _merchant_providers
    
    import json as _json
    merchant_id = merchant.id if merchant else 0
    raw_config = merchant.provider_config if (merchant and merchant.provider_config) else "{}"
    if isinstance(raw_config, str):
        try:
            config_dict = _json.loads(raw_config)
        except Exception:
            config_dict = {}
    else:
        config_dict = raw_config
    
    # We can cache providers per merchant. In a highly dynamic system, 
    # we might want to clear this cache if the merchant updates their keys.
    if merchant_id not in _merchant_providers:
        _merchant_providers[merchant_id] = init_providers(merchant_id, config_dict)
        
    return _merchant_providers[merchant_id]

def clear_provider_cache(merchant_id: int):
    """Force re-initialization of providers if merchant updates their config."""
    global _merchant_providers
    if merchant_id in _merchant_providers:
        del _merchant_providers[merchant_id]


def init_providers(merchant_id: int, config: dict) -> Providers:
    """Initialize all providers. Voice and Speech use global Env. Messaging uses Merchant config."""
    logger.info("═" * 50)
    logger.info(f"Initializing providers for Merchant {merchant_id}...")
    logger.info("═" * 50)

    # Voice and Speech use empty dict so they fall back to the env
    providers = Providers(
        merchant_id=merchant_id,
        voice=create_voice_provider({}), 
        messaging=create_messaging_provider(config, merchant_id=merchant_id),
        speech=create_speech_provider({}),
    )

    logger.info("═" * 50)
    logger.info("Active providers for Merchant %s: %s", merchant_id, providers.summary())
    logger.info("═" * 50)

    return providers
