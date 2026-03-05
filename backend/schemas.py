"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Order Schemas ──────────────────────────────────────────

class OrderBase(BaseModel):
    customer_name: str
    customer_phone: str
    platform: str
    items: str = ""

class OrderCreate(OrderBase):
    order_id: Optional[str] = None
    status: str = "pending"

class OrderResponse(OrderBase):
    id: str
    order_id: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Event Schemas ──────────────────────────────────────────

class EventCreate(BaseModel):
    order_id: str
    event_type: str

class EventResponse(BaseModel):
    id: str
    order_id: str
    event_type: str
    timestamp: Optional[datetime] = None
    customer_name: Optional[str] = None
    platform: Optional[str] = None

    class Config:
        from_attributes = True


# ── Communication Schemas ──────────────────────────────────

class CommunicationResponse(BaseModel):
    id: str
    order_id: str
    comm_type: str
    status: str
    response: str
    message: str
    timestamp: Optional[datetime] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None

    class Config:
        from_attributes = True


# ── Simulate Schemas ───────────────────────────────────────

class SimulateOrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    platform: str = "shopify"
    event_type: str = "order_created"
    items: str = "Sample Item x1"


# ── Dashboard Schemas ─────────────────────────────────────

class DashboardStats(BaseModel):
    total_orders: int = 0
    total_events: int = 0
    total_calls: int = 0
    total_whatsapp: int = 0
    successful_calls: int = 0
    failed_calls: int = 0


# ── Settings Schemas ──────────────────────────────────────

class SettingsUpdate(BaseModel):
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
