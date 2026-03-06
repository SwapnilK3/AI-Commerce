"""
Webhook routers — receives events from Shopify and WooCommerce.
"""
import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.order_service import normalize_shopify_order, normalize_woocommerce_order, create_order
from services.event_service import create_event, process_event
from services.ai_engine import detect_intent

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


@router.post("/whatsapp-incoming")
async def whatsapp_incoming(request: Request, db: Session = Depends(get_db)):
    """
    Receive incoming WhatsApp messages from the Node.js WhatsApp Web sidecar.
    Matches the sender's phone number to an active order and logs the response.
    """
    import json
    from models import Order, Communication, Merchant, Message
    from datetime import datetime, timezone
    from providers.factory import get_providers

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    sender = payload.get("from", "")
    message_body = (payload.get("body") or "").strip()
    timestamp = payload.get("timestamp")
    # For MVP, assume Merchant ID 1 since whatsapp-web.js isn't multi-tenant yet
    merchant_id = request.query_params.get("merchant_id") or "1" 

    if not sender or not message_body:
        return {"status": "ignored", "reason": "Missing sender or body"}

    logger.info("📩 Received WhatsApp message from %s: %s", sender, message_body)

    # Clean the sender's phone 
    clean_sender = sender.replace("@c.us", "").replace("+", "").strip()
    
    # ── 1. UNIFIED INBOX LOGGING ──────────────────────────────
    # Try to find the merchant: first by explicit ID, then by order match, then first in DB
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        # Try to match via order's customer phone
        if len(clean_sender) > 10:
            search_phone_early = clean_sender[-10:]
        else:
            search_phone_early = clean_sender
        matched_order = (
            db.query(Order)
            .filter(Order.customer_phone.like(f"%{search_phone_early}%"))
            .order_by(Order.created_at.desc())
            .first()
        )
        if matched_order:
            merchant = db.query(Merchant).filter(Merchant.id == matched_order.merchant_id).first()
    if not merchant:
        # Final fallback for MVP: Route to the first registered merchant
        merchant = db.query(Merchant).first()
    
    if merchant:
        # A. Log the inbound message to the Inbox
        inbound_msg = Message(
            merchant_id=merchant.id,
            channel="whatsapp",
            contact_id=clean_sender,
            text=message_body,
            is_inbound=1,
            is_ai_reply=0,
            requires_human=0,
            timestamp=datetime.fromtimestamp(int(timestamp), tz=timezone.utc) if timestamp else datetime.now(timezone.utc)
        )
        db.add(inbound_msg)
        
        # B. Ask AI to evaluate for Auto-Response
        merchant_config = {}
        if merchant.provider_config:
            try:
                merchant_config = json.loads(merchant.provider_config)
            except:
                pass
                
        from services.ai_engine import generate_auto_reply
        auto_evaluation = generate_auto_reply(merchant_config, message_body)
        
        if auto_evaluation["is_ai"] and auto_evaluation["reply"]:
            # Send AI Reply via Providers
            providers = get_providers(merchant)
            try:
                await providers.messaging.send_message(clean_sender, auto_evaluation["reply"])
                
                # Log AI Outbound
                outbound_msg = Message(
                    merchant_id=merchant.id,
                    channel="whatsapp",
                    contact_id=clean_sender,
                    text=auto_evaluation["reply"],
                    is_inbound=0,
                    is_ai_reply=1,
                    requires_human=0
                )
                db.add(outbound_msg)
            except Exception as e:
                logger.error(f"Failed to send AI auto-reply: {e}")
        elif not auto_evaluation["is_ai"]:
            # Flag for human intervention
            inbound_msg.requires_human = 1
            
        db.commit()


    # ── 2. LEGACY ORDER INTENT DETECTION (If Applicable) ────────
    if len(clean_sender) > 10:
        search_phone = clean_sender[-10:]
    else:
        search_phone = clean_sender

    order = (
        db.query(Order)
        .filter(Order.customer_phone.like(f"%{search_phone}%"))
        .order_by(Order.created_at.desc())
        .first()
    )

    if not order:
        logger.warning("No matching order found for incoming message from %s", clean_sender)
        return {"status": "success", "reason": "Logged to Inbox, but no matching order found"}

    terminal_statuses = {"cancelled", "returned", "refund_requested"}
    if order.status in terminal_statuses:
        return {"status": "success", "reason": "Order in terminal state"}

    # Detect intent from the incoming WhatsApp message
    intent = detect_intent(message_body)
    
    last_event = order.events[-1] if order.events else None
    last_type = last_event.event_type if last_event else None

    event_type = None
    new_status = None

    if intent == "reschedule" or (intent == "yes" and last_type in {"delivery_failed", "payment_pending"}):
        event_type = "delivery_rescheduled"
        new_status = "delivery_rescheduled"
    elif intent == "yes" and last_type in {"order_created"}:
        event_type = "customer_confirmed"
        new_status = "confirmed"
    elif intent == "cancel":
        event_type = "order_cancellation_requested"
        new_status = "cancelled"
    elif intent == "no" and last_type in {"delivery_failed", "order_created"}:
        event_type = "customer_declined"
        new_status = "delivery_failed"
    elif intent == "refund":
        event_type = "refund_requested"
        new_status = "refund_requested"
    elif intent == "exchange":
        event_type = "exchange_requested"
        new_status = "exchange_requested"
    elif intent == "help":
        event_type = "support_requested"
        new_status = "support_requested"
    else:
        event_type = "customer_replied"
        new_status = "customer_replied"

    action_applied = event_type is not None

    created_event_id = None
    if event_type:
        # Only prevent exact back-to-back duplicates for the exact same event type
        is_duplicate = last_type == event_type
        if not is_duplicate:
            from services.ai_engine import extract_intent_metadata
            metadata = extract_intent_metadata(intent, message_body)
            event = create_event(db, order.id, event_type, metadata=metadata)
            created_event_id = event.id

    if new_status:
        order.status = new_status

    parsed_timestamp = None
    if timestamp:
        try:
            parsed_timestamp = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
        except (ValueError, TypeError):
            pass

    # Legacy communication log
    comm = Communication(
        order_id=order.id,
        comm_type="whatsapp",
        status="received",
        message=message_body,
        response="Incoming customer message",
        timestamp=parsed_timestamp,
    )
    db.add(comm)
    db.commit()

    return {
        "status": "success",
        "order": order.id,
        "message_logged": True,
        "intent": intent,
        "event_type": event_type,
        "event_id": created_event_id,
        "action_applied": action_applied,
    }
