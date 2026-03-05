"""
AI Conversation Engine — generates call scripts, detects intents, creates responses.
"""
from typing import Optional


# ── Event-specific message templates ────────────────────────

CALL_TEMPLATES = {
    "delivery_failed": (
        "Hello {name}, this is an automated call regarding your order. "
        "Your order delivery failed today. "
        "Would you like to reschedule delivery? "
        "Please say YES to reschedule, or NO to cancel."
    ),
    "order_created": (
        "Hello {name}, thank you for your order! "
        "Your order has been successfully placed and is being processed. "
        "You will receive updates on your delivery. "
        "Say YES to confirm, or CANCEL to cancel the order."
    ),
    "payment_pending": (
        "Hello {name}, this is a reminder about your pending payment. "
        "Your order is on hold due to an incomplete payment. "
        "Please complete the payment to proceed. "
        "Say YES if you have completed it, or say HELP for assistance."
    ),
    "order_returned": (
        "Hello {name}, we have received your return request. "
        "Your order return is being processed. "
        "Would you like a refund or an exchange? "
        "Say REFUND for a refund, or EXCHANGE for an exchange."
    ),
    "order_delivered": (
        "Hello {name}, your order has been delivered successfully! "
        "We hope you enjoy your purchase. "
        "Would you like to rate your experience? "
        "Say YES to provide feedback, or NO to skip."
    ),
}

WHATSAPP_TEMPLATES = {
    "delivery_failed": (
        "Hi {name},\n\n"
        "Your order delivery failed today.\n\n"
        "Reply YES to reschedule delivery.\n"
        "Reply NO to cancel the order."
    ),
    "order_created": (
        "Hi {name},\n\n"
        "Your order has been successfully placed! 🎉\n\n"
        "We'll keep you updated on the delivery.\n"
        "Reply CONFIRM to confirm or CANCEL to cancel."
    ),
    "payment_pending": (
        "Hi {name},\n\n"
        "Your payment is still pending. ⏳\n\n"
        "Please complete your payment to proceed with the order.\n"
        "Reply DONE once completed."
    ),
    "order_returned": (
        "Hi {name},\n\n"
        "Your return request has been received. 📦\n\n"
        "Reply REFUND for a refund.\n"
        "Reply EXCHANGE for an exchange."
    ),
    "order_delivered": (
        "Hi {name},\n\n"
        "Your order has been delivered! ✅\n\n"
        "We hope you enjoy your purchase.\n"
        "Reply RATE to share your feedback."
    ),
}


def generate_call_script(customer_name: str, event_type: str) -> str:
    """Generate personalized TTS script based on event type."""
    template = CALL_TEMPLATES.get(event_type, CALL_TEMPLATES["order_created"])
    return template.format(name=customer_name)


def generate_whatsapp_message(customer_name: str, event_type: str) -> str:
    """Generate personalized WhatsApp message based on event type."""
    template = WHATSAPP_TEMPLATES.get(event_type, WHATSAPP_TEMPLATES["order_created"])
    return template.format(name=customer_name)


def detect_intent(transcript: str) -> str:
    """
    Detect customer intent from speech transcript.
    Returns: yes, no, reschedule, cancel, refund, exchange, help, unknown
    """
    if not transcript:
        return "unknown"

    text = transcript.lower().strip()

    # Priority-ordered keyword matching
    intent_keywords = {
        "cancel": ["cancel", "cancel order", "don't want", "stop"],
        "reschedule": ["reschedule", "deliver tomorrow", "later", "next day", "another day"],
        "refund": ["refund", "money back", "return money"],
        "exchange": ["exchange", "swap", "replace"],
        "help": ["help", "assistance", "support", "agent", "human"],
        "yes": ["yes", "yeah", "yep", "sure", "okay", "ok", "confirm", "done", "rate"],
        "no": ["no", "nope", "not now", "skip"],
    }

    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return intent

    return "unknown"


def generate_response(intent: str, customer_name: str) -> str:
    """Generate a follow-up response based on detected intent."""
    responses = {
        "yes": f"Thank you {customer_name}! Your confirmation has been recorded. Have a great day!",
        "no": f"Understood {customer_name}. No action will be taken. Have a great day!",
        "reschedule": f"Got it {customer_name}! Your delivery will be rescheduled. We'll notify you with the new date.",
        "cancel": f"Your order cancellation request has been noted, {customer_name}. Our team will process it shortly.",
        "refund": f"Your refund request has been submitted, {customer_name}. You'll receive it within 5-7 business days.",
        "exchange": f"Your exchange request has been noted, {customer_name}. We'll arrange the pickup and delivery.",
        "help": f"Connecting you to our support team, {customer_name}. Please hold on.",
        "unknown": f"Sorry {customer_name}, I didn't understand that. Our team will follow up with you shortly.",
    }
    return responses.get(intent, responses["unknown"])
