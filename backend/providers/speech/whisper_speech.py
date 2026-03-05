"""
Whisper Speech Provider — open-source fallback for speech processing.
STT: OpenAI Whisper (local model) if installed, else text-only.
TTS: pyttsx3 (built-in, no install) or Piper TTS.
Intent: keyword matching.
"""
import io
import logging
from typing import Optional
from providers.base import SpeechProvider, SpeechResult
from services.ai_engine import detect_intent as keyword_detect

logger = logging.getLogger(__name__)


class WhisperSpeechProvider(SpeechProvider):
    """
    Free open-source speech provider.
    - TTS: pyttsx3 (works offline, zero API cost)
    - STT: Whisper (if installed) or keyword-based
    - Intent: keyword matching
    """

    def __init__(self):
        self._whisper_model = None
        self._tts_engine = None

        # Try loading Whisper
        try:
            import whisper
            self._whisper_model = whisper.load_model("base")
            logger.info("WhisperSpeechProvider: Whisper model loaded")
        except ImportError:
            logger.info("WhisperSpeechProvider: Whisper not installed, STT will use text input")
        except Exception as e:
            logger.warning("WhisperSpeechProvider: Whisper load failed: %s", str(e))

        # Try loading pyttsx3
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 150)
            logger.info("WhisperSpeechProvider: pyttsx3 TTS ready")
        except Exception:
            logger.info("WhisperSpeechProvider: pyttsx3 not available, TTS will be text-only")

        logger.info("WhisperSpeechProvider initialized")

    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Generate TTS audio using pyttsx3 or Piper."""
        if self._tts_engine:
            try:
                # pyttsx3 doesn't easily return bytes, so we save to buffer
                import tempfile
                import os
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_path = tmp.name
                tmp.close()

                self._tts_engine.save_to_file(text, tmp_path)
                self._tts_engine.runAndWait()

                with open(tmp_path, "rb") as f:
                    audio_data = f.read()

                os.unlink(tmp_path)
                logger.info("pyttsx3 TTS generated: %d bytes", len(audio_data))
                return audio_data

            except Exception as e:
                logger.warning("pyttsx3 TTS failed: %s", str(e))

        # Try Piper TTS as another fallback
        try:
            import subprocess
            result = subprocess.run(
                ["piper", "--model", "en_US-lessac-medium", "--output-raw"],
                input=text.encode(),
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                logger.info("Piper TTS generated: %d bytes", len(result.stdout))
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        logger.info("No TTS engine available, text-only mode")
        return None

    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert audio to text using Whisper."""
        if self._whisper_model:
            try:
                import tempfile
                import os
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp.write(audio_data)
                tmp_path = tmp.name
                tmp.close()

                result = self._whisper_model.transcribe(tmp_path)
                os.unlink(tmp_path)

                transcript = result.get("text", "").strip()
                logger.info("Whisper STT: '%s'", transcript)
                return transcript

            except Exception as e:
                logger.error("Whisper STT failed: %s", str(e))

        return ""

    async def detect_intent(self, transcript: str) -> SpeechResult:
        """Detect intent using keyword matching."""
        intent = keyword_detect(transcript)
        return SpeechResult(
            text=transcript,
            intent=intent,
            confidence=0.8 if intent != "unknown" else 0.1,
            provider=self.get_provider_name(),
        )

    def get_provider_name(self) -> str:
        return "Whisper STT + pyttsx3 TTS (Local)"
