"""
Database models — Orders, Events, Communications.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    business_name = Column(String, nullable=False)
    merchant_name = Column(String, nullable=False)
    whatsapp_number = Column(String, default="")
    created_at = Column(DateTime, default=utcnow)
    
    # Store provider API keys as JSON string
    provider_config = Column(Text, default="{}")

    orders = relationship("Order", back_populates="merchant", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "business_name": self.business_name,
            "merchant_name": self.merchant_name,
            "whatsapp_number": self.whatsapp_number,
        }


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    order_id = Column(String, index=True)       # External order ID from platform
    platform = Column(String, nullable=False)     # shopify / woocommerce
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    status = Column(String, default="pending")
    items = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    merchant = relationship("Merchant", back_populates="orders")
    events = relationship("Event", back_populates="order", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "platform": self.platform,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "status": self.status,
            "items": self.items,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    event_type = Column(String, nullable=False)   # delivery_failed, order_created, etc.
    metadata_json = Column(Text, default="{}")    # JSON string for AI context values
    timestamp = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="events")

    def to_dict(self):
        import json
        meta = {}
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except:
                pass

        return {
            "id": self.id,
            "order_id": self.order_id,
            "event_type": self.event_type,
            "metadata": meta,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "customer_name": self.order.customer_name if self.order else None,
            "platform": self.order.platform if self.order else None,
        }


class Communication(Base):
    __tablename__ = "communications"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    comm_type = Column(String, nullable=False)    # voice / whatsapp
    status = Column(String, default="pending")    # pending, success, failed, skipped
    response = Column(Text, default="")           # Customer response text
    message = Column(Text, default="")            # Message sent
    timestamp = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="communications")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "comm_type": self.comm_type,
            "status": self.status,
            "response": self.response,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "customer_name": self.order.customer_name if self.order else None,
            "customer_phone": self.order.customer_phone if self.order else None,
        }


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)      # whatsapp, instagram, facebook
    contact_id = Column(String, nullable=False, index=True)   # customer phone or profile ID
    text = Column(Text, nullable=False)
    is_inbound = Column(Integer, default=1)       # 1 for incoming, 0 for outgoing
    is_ai_reply = Column(Integer, default=0)      # 1 if sent by AI, 0 if human
    requires_human = Column(Integer, default=0)   # 1 if AI failed and needs human
    timestamp = Column(DateTime, default=utcnow)

    # Relationships
    merchant = relationship("Merchant")

    def to_dict(self):
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "channel": self.channel,
            "contact_id": self.contact_id,
            "text": self.text,
            "is_inbound": bool(self.is_inbound),
            "is_ai_reply": bool(self.is_ai_reply),
            "requires_human": bool(self.requires_human),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
