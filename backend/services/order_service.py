"""
Order Integration Service — normalizes webhook data and creates orders.
"""
import uuid
import logging
from sqlalchemy.orm import Session
from models import Order

logger = logging.getLogger(__name__)


def normalize_shopify_order(payload: dict) -> dict:
    """Extract standard order data from a Shopify webhook payload."""
    customer = payload.get("customer", {})
    line_items = payload.get("line_items", [])
    items_text = ", ".join(
        f"{item.get('title', 'Item')} x{item.get('quantity', 1)}"
        for item in line_items
    ) or payload.get("items", "N/A")

    phone = (
        payload.get("customer_phone")
        or payload.get("phone")
        or customer.get("phone")
        or payload.get("shipping_address", {}).get("phone", "")
    )

    return {
        "order_id": str(payload.get("id", payload.get("order_id", uuid.uuid4().hex[:8]))),
        "customer_name": (
            payload.get("customer_name")
            or f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            or "Unknown"
        ),
        "customer_phone": phone,
        "platform": "shopify",
        "status": payload.get("status", payload.get("financial_status", "pending")),
        "items": items_text,
    }


def normalize_woocommerce_order(payload: dict) -> dict:
    """Extract standard order data from a WooCommerce webhook payload."""
    billing = payload.get("billing", {})
    line_items = payload.get("line_items", [])
    items_text = ", ".join(
        f"{item.get('name', 'Item')} x{item.get('quantity', 1)}"
        for item in line_items
    ) or payload.get("items", "N/A")

    return {
        "order_id": str(payload.get("id", payload.get("order_id", uuid.uuid4().hex[:8]))),
        "customer_name": (
            payload.get("customer_name")
            or f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
            or "Unknown"
        ),
        "customer_phone": payload.get("customer_phone") or billing.get("phone", ""),
        "platform": "woocommerce",
        "status": payload.get("status", "pending"),
        "items": items_text,
    }


def create_order(db: Session, order_data: dict) -> Order:
    """Create and store a new order record."""
    order = Order(
        order_id=order_data.get("order_id", uuid.uuid4().hex[:8]),
        platform=order_data["platform"],
        customer_name=order_data["customer_name"],
        customer_phone=order_data["customer_phone"],
        status=order_data.get("status", "pending"),
        items=order_data.get("items", ""),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    logger.info("Order created: id=%s, platform=%s", order.id, order.platform)
    return order
