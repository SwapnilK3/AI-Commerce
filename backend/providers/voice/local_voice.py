"""
Local Voice Provider — open-source fallback for voice call simulation.
Uses pyttsx3 for TTS (zero-install) and simulates the call flow locally.
"""
import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from providers.base import VoiceProvider, CallResult

logger = logging.getLogger(__name__)

# Directory for simulated call logs
SIMULATED_DIR = Path(__file__).resolve().parent.parent.parent / "simulated_calls"


class LocalVoiceProvider(VoiceProvider):
    """
    Free fallback voice provider.
    Simulates voice calls locally:
    - Generates TTS audio via pyttsx3 (if available)
    - Logs full call details to JSON files
    - Returns simulated result
    """

    def __init__(self):
        SIMULATED_DIR.mkdir(parents=True, exist_ok=True)
        self._tts_engine = None

        # Try to initialize pyttsx3 for local TTS
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 150)
            logger.info("LocalVoiceProvider initialized with pyttsx3 TTS")
        except Exception:
            logger.info("LocalVoiceProvider initialized (pyttsx3 not available, text-only simulation)")

    async def make_call(self, phone: str, message: str, callback_url: str = "") -> CallResult:
        call_id = f"LOCAL-{uuid.uuid4().hex[:10].upper()}"

        # Log the simulated call
        call_log = {
            "call_id": call_id,
            "phone": phone,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "simulated",
            "provider": self.get_provider_name(),
        }

        # Save call log
        log_file = SIMULATED_DIR / f"{call_id}.json"
        log_file.write_text(json.dumps(call_log, indent=2), encoding="utf-8")

        # Optionally generate audio file
        audio_path = None
        if self._tts_engine:
            try:
                audio_file = SIMULATED_DIR / f"{call_id}.wav"
                self._tts_engine.save_to_file(message, str(audio_file))
                self._tts_engine.runAndWait()
                if audio_file.exists():
                    audio_path = str(audio_file)
                    call_log["audio_file"] = audio_path
            except Exception as e:
                logger.warning("TTS audio generation failed: %s", str(e))

        logger.info(
            "Simulated voice call: ID=%s, to=%s, message_len=%d",
            call_id, phone, len(message),
        )

        return CallResult(
            success=True,
            call_id=call_id,
            provider=self.get_provider_name(),
            simulated=True,
            details={
                "log_file": str(log_file),
                "audio_file": audio_path,
                "message_preview": message[:100] + "..." if len(message) > 100 else message,
            },
        )

    async def get_call_status(self, call_id: str) -> str:
        log_file = SIMULATED_DIR / f"{call_id}.json"
        if log_file.exists():
            data = json.loads(log_file.read_text(encoding="utf-8"))
            return data.get("status", "simulated")
        return "not_found"

    def get_provider_name(self) -> str:
        return "Local Voice (Simulated)"
