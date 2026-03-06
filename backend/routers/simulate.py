"""
Simulate router — creates test orders for demo purposes.
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import SimulateOrderRequest
from services.order_service import create_order
from services.event_service import create_event, process_event
from auth import get_current_merchant
from models import Merchant

router = APIRouter(prefix="/api/simulate", tags=["Simulate"])


@router.post("/order")
async def simulate_order(
    req: SimulateOrderRequest, 
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Create a simulated order and trigger event processing.
    Used for demo without real Shopify/WooCommerce webhooks.
    """
    order_data = {
        "order_id": f"SIM-{uuid.uuid4().hex[:8].upper()}",
        "merchant_id": current_merchant.id,
        "customer_name": req.customer_name,
        "customer_phone": req.customer_phone,
        "platform": req.platform,
        "status": "pending",
        "items": req.items,
    }

    # Create order
    order = create_order(db, order_data)

    # Create and process event
    event = create_event(db, order.id, req.event_type)
    result = await process_event(db, order, event)

    return {
        "status": "success",
        "order": order.to_dict(),
        "event": event.to_dict(),
        "communication": result,
    }
