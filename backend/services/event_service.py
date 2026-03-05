"""
Event Processing Engine — creates events and routes them to communication workflows.
Supports Redis queue for async processing with in-memory fallback.
"""
import logging
from sqlalchemy.orm import Session
from models import Event, Order
from services.communication_service import initiate_communication

logger = logging.getLogger(__name__)

VALID_EVENT_TYPES = {
    "delivery_failed",
    "order_created",
    "payment_pending",
    "order_returned",
    "order_delivered",
}

# Map event types to order status updates
EVENT_STATUS_MAP = {
    "delivery_failed": "delivery_failed",
    "order_created": "confirmed",
    "payment_pending": "payment_pending",
    "order_returned": "returned",
    "order_delivered": "delivered",
}


def create_event(db: Session, order_id: str, event_type: str) -> Event:
    """Log a new event for an order."""
    event = Event(order_id=order_id, event_type=event_type)
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info("Event created: id=%s, type=%s, order=%s", event.id, event_type, order_id)
    return event


async def process_event(db: Session, order: Order, event: Event) -> dict:
    """
    Process an event — update order status and trigger communication.
    Returns result dict with communication outcome.
    """
    # Update order status based on event type
    new_status = EVENT_STATUS_MAP.get(event.event_type)
    if new_status:
        order.status = new_status
        db.commit()
        logger.info("Order %s status updated to '%s'", order.id, new_status)

    # Trigger communication workflow via providers
    result = await initiate_communication(db, order, event)
    return result
