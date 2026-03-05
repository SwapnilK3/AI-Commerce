"""
Communication Engine — orchestrates voice calls and messaging fallback
using the provider-based architecture. No direct API imports.
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
    2. If call fails → send message via MessagingProvider
    """
    providers = get_providers()
    call_script = generate_call_script(order.customer_name, event.event_type)

    # ── Step 1: Attempt voice call via provider ────────────
    logger.info(
        "Attempting voice call via [%s] to %s for order %s",
        providers.voice.get_provider_name(),
        order.customer_phone,
        order.id,
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
        return {
            "method": "voice",
            "status": "simulated" if call_result.simulated else "initiated",
            "call_id": call_result.call_id,
            "provider": call_result.provider,
            "simulated": call_result.simulated,
        }

    # ── Step 2: Voice failed → log failure ─────────────────
    logger.warning(
        "Voice call failed via [%s] for order %s: %s — triggering messaging fallback",
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

    # ── Step 3: Messaging fallback via provider ────────────
    whatsapp_message = generate_whatsapp_message(order.customer_name, event.event_type)

    logger.info(
        "Sending fallback message via [%s] to %s",
        providers.messaging.get_provider_name(),
        order.customer_phone,
    )
    msg_result = await providers.messaging.send_message(
        order.customer_phone, whatsapp_message
    )

    if msg_result.success:
        log_communication(
            db,
            order_id=order.id,
            comm_type="whatsapp",
            status="sent",
            message=whatsapp_message,
            provider=msg_result.provider,
            simulated=msg_result.simulated,
        )
        return {
            "method": "whatsapp",
            "status": "simulated" if msg_result.simulated else "sent",
            "message_id": msg_result.message_id,
            "provider": msg_result.provider,
            "simulated": msg_result.simulated,
        }

    # ── Both failed ────────────────────────────────────────
    log_communication(
        db,
        order_id=order.id,
        comm_type="whatsapp",
        status="failed",
        message=whatsapp_message,
        response=msg_result.error or "",
        provider=msg_result.provider,
    )

    return {
        "method": "none",
        "status": "all_failed",
        "error": "Both voice call and messaging failed",
        "voice_provider": providers.voice.get_provider_name(),
        "messaging_provider": providers.messaging.get_provider_name(),
    }
