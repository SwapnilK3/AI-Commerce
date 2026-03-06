"""
Application configuration — loads all settings from .env file.
Supports auto-detection of available API keys for provider selection.
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class Settings(BaseSettings):
    # ── Database ───────────────────────────────────
    DATABASE_URL: str = "sqlite:///./commerce_platform.db"

    # ── Redis ──────────────────────────────────────
    REDIS_URL: str = ""

    # ── Twilio ─────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── ElevenLabs ─────────────────────────────────
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # ── WhatsApp (Meta Cloud API) ──────────────────
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""

    # ── WhatsApp Web Service (session-based) ──────
    WHATSAPP_WEB_SERVICE_URL: str = "http://localhost:3001"

    # ── Shopify ────────────────────────────────────
    SHOPIFY_WEBHOOK_SECRET: str = ""

    # ── WooCommerce ────────────────────────────────
    WOOCOMMERCE_WEBHOOK_SECRET: str = ""

    # ── App ────────────────────────────────────────
    APP_BASE_URL: str = "http://localhost:8000"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
