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
    metadata: Optional[dict] = None

class EventResponse(BaseModel):
    id: str
    order_id: str
    event_type: str
    metadata: Optional[dict] = None
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


# ── Inbox & Message Schemas ────────────────────────────────

class MessageBase(BaseModel):
    channel: str
    contact_id: str
    text: str

class MessageCreate(MessageBase):
    is_inbound: bool = True
    is_ai_reply: bool = False
    requires_human: bool = False

class MessageResponse(MessageBase):
    id: str
    merchant_id: str
    is_inbound: bool
    is_ai_reply: bool
    requires_human: bool
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True

class InboxContact(BaseModel):
    contact_id: str
    channel: str
    last_message: str
    last_timestamp: Optional[datetime] = None
    unread_count: int = 0
    requires_human: bool = False

# (Settings schema merged into MerchantConfig in routers/merchant_config.py)
