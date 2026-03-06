"""
Communication Engine — orchestrates voice calls and messaging fallback
using the provider-based architecture. No direct API imports.

In fallback/simulation mode: BOTH voice AND WhatsApp are generated,
so the merchant always gets a clickable WhatsApp deep link.
"""
import logging
from sqlalchemy.orm import Session
from models import Order, Event, Communication
from services.ai_engine import generate_call_script, generate_whatsapp_message
from providers.factory import get_providers

logger = logging.getLogger(__name__)


def log_communication(
    db: Session,
    order_id: str,
    comm_type: str,
    status: str,
    message: str = "",
    response: str = "",
    provider: str = "",
    simulated: bool = False,
) -> Communication:
    """Record a communication attempt in the database."""
    comm = Communication(
        order_id=order_id,
        comm_type=comm_type,
        status="simulated" if simulated else status,
        message=message,
        response=response if not simulated else f"[{provider}] {response}".strip(),
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm


async def initiate_communication(db: Session, order: Order, event: Event) -> dict:
    """
    Primary communication flow using provider interfaces:
    1. Try voice call via VoiceProvider
    2. If call fails OR is simulated → ALSO send message via MessagingProvider
       (In fallback mode, both are generated so the merchant gets a WhatsApp link)
    """
    # Look up the merchant context for this order
    from models import Merchant
    merchant = db.query(Merchant).filter(Merchant.id == order.merchant_id).first()
    
    # Initialize providers specifically with this merchant's API keys
    providers = get_providers(merchant)
    
    call_script = generate_call_script(order.customer_name, event.event_type)
    whatsapp_message = generate_whatsapp_message(order.customer_name, event.event_type)

    result = {
        "method": "voice",
        "status": "initiated",
        "provider": providers.voice.get_provider_name(),
        "simulated": False,
    }

    # ── Step 1: Attempt voice call via provider ────────────
    logger.info(
        "Attempting voice call via [%s] to %s for order %s (Merchant %s)",
        providers.voice.get_provider_name(),
        order.customer_phone,
        order.id,
        merchant.id if merchant else "global",
    )
    call_result = await providers.voice.make_call(order.customer_phone, call_script)

    if call_result.success:
        log_communication(
            db,
            order_id=order.id,
            comm_type="voice",
            status="initiated",
            message=call_script,
            provider=call_result.provider,
            simulated=call_result.simulated,
        )
        result.update({
            "status": "simulated" if call_result.simulated else "initiated",
            "call_id": call_result.call_id,
            "simulated": call_result.simulated,
        })
    else:
        # Voice failed — log failure
        logger.warning(
            "Voice call failed via [%s] for order %s: %s",
            providers.voice.get_provider_name(),
            order.id,
            call_result.error,
        )
        log_communication(
            db,
            order_id=order.id,
            comm_type="voice",
            status="failed",
            message=call_script,
            response=call_result.error or "",
            provider=call_result.provider,
        )
        result.update({"method": "voice", "status": "failed"})

    # ── Step 2: Generate WhatsApp message ──────────────────
    # In fallback mode: ALWAYS generate WhatsApp link (voice is simulated too)
    # In production mode: only if voice failed
    should_send_whatsapp = (
        call_result.simulated  # Fallback mode → always also send WhatsApp
        or not call_result.success  # Production mode → only if voice failed
    )

    if should_send_whatsapp:
        logger.info(
            "Sending WhatsApp via [%s] to %s",
            providers.messaging.get_provider_name(),
            order.customer_phone,
        )
        msg_result = await providers.messaging.send_message(
            order.customer_phone, whatsapp_message
        )

        if msg_result.success:
            wa_link = (msg_result.details or {}).get("whatsapp_link", "")
            log_communication(
                db,
                order_id=order.id,
                comm_type="whatsapp",
                status="sent",
                message=whatsapp_message,
                response=wa_link if wa_link else "",
                provider=msg_result.provider,
                simulated=msg_result.simulated,
            )
            result["whatsapp_link"] = wa_link
            result["whatsapp_status"] = "link_generated" if wa_link else "sent"
            result["whatsapp_provider"] = msg_result.provider

            # If voice failed, WhatsApp is the primary method
            if not call_result.success:
                result["method"] = "whatsapp"
                result["status"] = "link_generated" if wa_link else "sent"
        else:
            log_communication(
                db,
                order_id=order.id,
                comm_type="whatsapp",
                status="failed",
                message=whatsapp_message,
                response=msg_result.error or "",
                provider=msg_result.provider,
            )

            if not call_result.success:
                result["method"] = "none"
                result["status"] = "all_failed"
                result["error"] = "Both voice call and messaging failed"

    return result
