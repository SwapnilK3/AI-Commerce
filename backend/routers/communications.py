"""
Communication callback routers — handles Twilio status callbacks and voice responses.
Uses provider-based speech processing.
"""
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from models import Communication
from providers.factory import get_providers
from services.ai_engine import detect_intent, generate_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/communications", tags=["Communications"])


@router.post("/call-status")
async def call_status_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Twilio call status callback.
    Updates communication record based on call outcome.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "")
    call_status = form.get("CallStatus", "")

    logger.info("Call status update: SID=%s, Status=%s", call_sid, call_status)

    # Map Twilio status to our status
    status_map = {
        "completed": "completed",
        "busy": "failed",
        "no-answer": "failed",
        "failed": "failed",
        "canceled": "failed",
    }
    mapped_status = status_map.get(call_status, call_status)

    # Update the most recent voice communication
    comm = (
        db.query(Communication)
        .filter(Communication.comm_type == "voice", Communication.status == "initiated")
        .order_by(Communication.timestamp.desc())
        .first()
    )

    if comm:
        comm.status = mapped_status
        comm.response = f"Twilio status: {call_status}"
        db.commit()
        logger.info("Communication %s updated to '%s'", comm.id, mapped_status)

        # If call failed, trigger messaging fallback via provider
        if mapped_status == "failed":
            providers = get_providers()
            order = comm.order
            if order:
                from services.ai_engine import generate_whatsapp_message
                event_type = "order_created"
                if order.events:
                    event_type = order.events[-1].event_type

                wa_message = generate_whatsapp_message(order.customer_name, event_type)
                await providers.messaging.send_message(order.customer_phone, wa_message)

    return {"status": "received"}


@router.post("/voice-response")
async def voice_response_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Twilio Gather callback — processes customer speech response.
    Uses SpeechProvider for intent detection.
    """
    form = await request.form()
    speech_result = form.get("SpeechResult", "")
    call_sid = form.get("CallSid", "")

    logger.info("Voice response: SID=%s, Speech='%s'", call_sid, speech_result)

    # Use speech provider for intent detection
    providers = get_providers()
    speech_analysis = await providers.speech.detect_intent(speech_result)
    intent = speech_analysis.intent
    logger.info("Detected intent: %s (confidence: %.2f)", intent, speech_analysis.confidence)

    # Generate response
    response_text = generate_response(intent, "Customer")

    # Update communication record
    comm = (
        db.query(Communication)
        .filter(Communication.comm_type == "voice", Communication.status == "initiated")
        .order_by(Communication.timestamp.desc())
        .first()
    )

    if comm:
        comm.status = "completed"
        comm.response = f"Intent: {intent} | Speech: {speech_result}"
        db.commit()

        if comm.order:
            response_text = generate_response(intent, comm.order.customer_name)

    # Return TwiML response
    twiml = (
        f'<Response>'
        f'<Say voice="Polly.Aditi" language="en-IN">{response_text}</Say>'
        f'<Hangup/>'
        f'</Response>'
    )

    return Response(content=twiml, media_type="application/xml")
