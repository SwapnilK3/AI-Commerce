"""
Webhook routers — receives events from Shopify and WooCommerce.
"""
import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.order_service import normalize_shopify_order, normalize_woocommerce_order, create_order
from services.event_service import create_event, process_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/shopify")
async def shopify_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive and process a Shopify webhook event."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Determine event type from headers or payload
    event_type = request.headers.get("X-Shopify-Topic", "order_created")
    event_type = _map_shopify_topic(event_type)

    # Normalize and store order
    order_data = normalize_shopify_order(payload)
    order = create_order(db, order_data)

    # Create event and process
    event = create_event(db, order.id, event_type)
    result = await process_event(db, order, event)

    return {
        "status": "received",
        "order_id": order.id,
        "event_type": event_type,
        "communication": result,
    }


@router.post("/woocommerce")
async def woocommerce_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive and process a WooCommerce webhook event."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Determine event type from headers or payload
    event_type = request.headers.get("X-WC-Webhook-Topic", "order_created")
    event_type = _map_woocommerce_topic(event_type)

    # Normalize and store order
    order_data = normalize_woocommerce_order(payload)
    order = create_order(db, order_data)

    # Create event and process
    event = create_event(db, order.id, event_type)
    result = await process_event(db, order, event)

    return {
        "status": "received",
        "order_id": order.id,
        "event_type": event_type,
        "communication": result,
    }


def _map_shopify_topic(topic: str) -> str:
    """Map Shopify webhook topic to internal event type."""
    mapping = {
        "orders/create": "order_created",
        "orders/fulfilled": "order_delivered",
        "orders/cancelled": "delivery_failed",
        "orders/paid": "order_created",
        "refunds/create": "order_returned",
    }
    return mapping.get(topic, "order_created")


def _map_woocommerce_topic(topic: str) -> str:
    """Map WooCommerce webhook topic to internal event type."""
    mapping = {
        "order.created": "order_created",
        "order.completed": "order_delivered",
        "order.cancelled": "delivery_failed",
        "order.refunded": "order_returned",
    }
    return mapping.get(topic, "order_created")
