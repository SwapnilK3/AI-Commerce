"""
Merchant Configuration Router — save/load merchant settings (WhatsApp number, etc.)
Stored as a JSON file for simplicity (no extra DB table needed).
"""
import json
import logging
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["Configuration"])

# Simple JSON file store for merchant config
CONFIG_FILE = Path(__file__).resolve().parent.parent / "merchant_config.json"

DEFAULT_CONFIG = {
    "merchant_whatsapp": "",
    "merchant_name": "",
    "business_name": "",
    # Omnichannel / social presence
    "shopify_store_url": "",
    "woocommerce_store_url": "",
    "instagram_handle": "",
    "facebook_page": "",
    # Provider keys
    "twilio_account_sid": "",
    "twilio_auth_token": "",
    "twilio_phone_number": "",
    "elevenlabs_api_key": "",
    "elevenlabs_voice_id": "",
    "whatsapp_api_token": "",
    "whatsapp_phone_number_id": "",
}


def _load_config() -> dict:
    """Load merchant config from JSON file."""
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return {**DEFAULT_CONFIG}


def _save_config(config: dict):
    """Save merchant config to JSON file."""
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_merchant_whatsapp() -> str:
    """Get the merchant's WhatsApp number (used by deep link provider)."""
    config = _load_config()
    return config.get("merchant_whatsapp", "")


# ── Pydantic model ─────────────────────────────────────────

class MerchantConfig(BaseModel):
    merchant_whatsapp: str = ""
    merchant_name: str = ""
    business_name: str = ""
    shopify_store_url: str = ""
    woocommerce_store_url: str = ""
    instagram_handle: str = ""
    facebook_page: str = ""
    
    # Provider keys
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    whatsapp_api_token: str = ""
    whatsapp_phone_number_id: str = ""


# ── Endpoints ──────────────────────────────────────────────

from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_merchant
from models import Merchant
from providers.factory import clear_provider_cache

@router.get("/merchant")
def get_merchant_config(
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """Get current merchant configuration from DB."""
    raw = current_merchant.provider_config or "{}"
    if isinstance(raw, str):
        try:
            config_dict = json.loads(raw)
        except Exception:
            config_dict = {}
    else:
        config_dict = raw
    # Merge with defaults to ensure all fields are present
    merged = {**DEFAULT_CONFIG, **config_dict}
    return merged


@router.post("/merchant")
def save_merchant_config(
    config: MerchantConfig,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """Save merchant configuration (keys, business name, etc.) to DB."""
    data = config.model_dump()
    
    # Also save to local JSON file for backward compatibility/debugging if needed
    _save_config(data)
    
    # Save to the actual requested Database location (serialize to JSON string)
    current_merchant.provider_config = json.dumps(data)
    db.commit()
    db.refresh(current_merchant)
    
    # Clear provider cache so factory reloads with new keys immediately
    clear_provider_cache(current_merchant.id)
    
    logger.info("Merchant config saved in DB for merchant %s", current_merchant.id)
    return {"status": "saved", "config": data}


# ── WhatsApp Web Service Proxy ─────────────────────────────

@router.get("/whatsapp-web/status")
async def whatsapp_web_status(current_merchant: Merchant = Depends(get_current_merchant)):
    """Proxy to WhatsApp Web service — get connection status."""
    import httpx
    from config import settings
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.WHATSAPP_WEB_SERVICE_URL}/status?merchant_id={current_merchant.id}", timeout=3.0
            )
            return resp.json()
    except Exception as e:
        return {"connected": False, "error": str(e), "service_available": False}


@router.get("/whatsapp-web/qr")
async def whatsapp_web_qr(current_merchant: Merchant = Depends(get_current_merchant)):
    """Proxy to WhatsApp Web service — get QR code for linking."""
    import httpx
    from config import settings
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.WHATSAPP_WEB_SERVICE_URL}/qr?merchant_id={current_merchant.id}", timeout=5.0
            )
            return resp.json()
    except Exception as e:
        return {"connected": False, "qr": None, "error": str(e)}


@router.post("/whatsapp-web/disconnect")
async def whatsapp_web_disconnect(current_merchant: Merchant = Depends(get_current_merchant)):
    """Proxy to WhatsApp Web service — disconnect and clear session."""
    import httpx
    from config import settings
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.WHATSAPP_WEB_SERVICE_URL}/disconnect",
                json={"merchant_id": current_merchant.id}, 
                timeout=5.0
            )
            return resp.json()
    except Exception as e:
        return {"error": str(e)}
