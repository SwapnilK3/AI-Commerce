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


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, index=True)       # External order ID from platform
    platform = Column(String, nullable=False)     # shopify / woocommerce
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    status = Column(String, default="pending")
    items = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    # Relationships
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
    timestamp = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="events")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "event_type": self.event_type,
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
