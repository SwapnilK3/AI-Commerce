"""
Abstract Provider Interfaces — all providers must implement these contracts.
Switching between production and fallback requires NO code changes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ── Result Data Classes ─────────────────────────────────────

@dataclass
class CallResult:
    """Result from a voice call attempt."""
    success: bool
    call_id: Optional[str] = None
    error: Optional[str] = None
    provider: str = ""
    simulated: bool = False
    details: dict = field(default_factory=dict)


@dataclass
class MessageResult:
    """Result from a messaging attempt."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: str = ""
    simulated: bool = False
    details: dict = field(default_factory=dict)


@dataclass
class SpeechResult:
    """Result from speech processing."""
    text: str = ""
    intent: str = "unknown"
    confidence: float = 0.0
    provider: str = ""


# ── Abstract Interfaces ────────────────────────────────────

class VoiceProvider(ABC):
    """Interface for voice call providers."""

    @abstractmethod
    async def make_call(self, phone: str, message: str, callback_url: str = "") -> CallResult:
        """Initiate a voice call with TTS message."""
        ...

    @abstractmethod
    async def get_call_status(self, call_id: str) -> str:
        """Get the current status of a call."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name."""
        ...


class MessagingProvider(ABC):
    """Interface for messaging providers (WhatsApp, SMS, etc.)."""

    @abstractmethod
    async def send_message(self, phone: str, message: str) -> MessageResult:
        """Send a text message to a phone number."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name."""
        ...


class SpeechProvider(ABC):
    """Interface for speech processing providers (STT + TTS + Intent)."""

    @abstractmethod
    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech audio bytes. Returns None on failure."""
        ...

    @abstractmethod
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert audio bytes to text transcript."""
        ...

    @abstractmethod
    async def detect_intent(self, transcript: str) -> SpeechResult:
        """Detect intent from a text transcript."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name."""
        ...
