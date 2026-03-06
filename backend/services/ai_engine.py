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
    Detect customer intent from speech transcript or WhatsApp text.
    Returns: yes, no, reschedule, cancel, refund, exchange, help, unknown

    NOTE: This is deliberately keyword-based so it works consistently
    across both voice (Twilio) and WhatsApp webhook flows.
    """
    if not transcript:
        return "unknown"

    text = transcript.lower().strip()

    # Normalise common punctuation / emojis that can appear in WhatsApp replies
    replacements = {
        "✅": "",
        "✔": "",
        "❌": "",
        "👍": " yes ",
        "👎": " no ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # Single-character quick replies
    if text in {"y", "yy"}:
        return "yes"
    if text in {"n", "nn"}:
        return "no"

    # Priority-ordered keyword matching
    intent_keywords = {
        # Hard cancellation should win over softer intents
        "cancel": [
            "cancel", "cancel order", "don't want", "do not want",
            "stop this order", "stop order",
        ],
        "reschedule": [
            "reschedule", "re schedule", "deliver tomorrow", "tomorrow delivery",
            "later", "next day", "another day", "change delivery date",
            "reschedule pickup", "change pickup",
        ],
        "refund": ["refund", "money back", "return money"],
        "exchange": ["exchange", "swap", "replace"],
        "help": ["help", "assistance", "support", "agent", "human"],
        "yes": [
            "yes", "yeah", "yep", "sure", "okay", "ok",
            "confirm", "confirmed", "done", "rate", "looks good",
        ],
        "no": ["no", "nope", "not now", "skip", "don't reschedule", "do not reschedule"],
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


def extract_intent_metadata(intent: str, text: str) -> dict:
    """
    Extract specific AI metadata from the customer's text based on their intent.
    This provides rich data for the order timeline.
    """
    metadata = {}
    text_lower = text.lower()
    
    if intent == "reschedule":
        # Look for simple date keywords for the MVP
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if "tomorrow" in text_lower:
            metadata["requested_date"] = "Tomorrow"
        elif "today" in text_lower:
            metadata["requested_date"] = "Today"
        elif "two days" in text_lower or "2 days" in text_lower:
            metadata["requested_date"] = "In 2 days"
        else:
            for day in days:
                if day in text_lower:
                    metadata["requested_date"] = day.capitalize()
                    break
        
        if "requested_date" not in metadata and len(text) > 10:
             # Capture the raw context if we couldn't parse a keyword
             metadata["context"] = text[:50] + "..." if len(text) > 50 else text

    elif intent in ("cancel", "refund", "exchange"):
        # For cancellations/refunds, the 'reason' can often be parsed if they say "because..."
        if "because" in text_lower:
            reason_part = text_lower.split("because")[-1].strip()
            metadata["reason"] = reason_part[:50] + "..." if len(reason_part) > 50 else reason_part
        elif len(text) > 15: # If they gave a longer explanation, just save the whole text as reason
             metadata["reason"] = text[:60] + "..." if len(text) > 60 else text
             
    return metadata


def generate_auto_reply(merchant_config: dict, message_text: str) -> dict:
    """
    Evaluates incoming Omnichannel messages.
    Returns {"is_ai": True, "reply": "..."} if it can handle it.
    Returns {"is_ai": False, "reply": None} if human intervention is needed.
    """
    text = message_text.lower().strip()
    
    # 1. Simple Q&A triggers
    simple_qa = {
        "where are you": "We are an online store, but our main office is in the city center. We deliver nationwide!",
        "location": "We deliver everywhere! You can check our exact shipping zones on our website.",
        "track": "You can track your order using the link sent to your email, or check the 'Orders' tab on our website.",
        "track order": "You can track your order using the link sent to your email, or check the 'Orders' tab on our website.",
        "how long": "Standard shipping usually takes 3-5 business days.",
        "shipping time": "Orders are processed within 24 hours, and shipping takes 3-5 business days.",
        "hello": "Hi there! How can we help you today?",
        "hi": "Hello! How can we assist you?",
    }
    
    for key, answer in simple_qa.items():
        if key in text:
            # Inject omnichannel context if available and relevant
            if "website" in answer and merchant_config.get("shopify_store_url"):
                answer = answer.replace("our website", f"our website ({merchant_config.get('shopify_store_url')})")
            return {"is_ai": True, "reply": answer}
            
    # 2. Complex or Angry triggers
    complex_triggers = ["broken", "refund", "scam", "wrong item", "damaged", "angry", "manager", "human"]
    if any(trigger in text for trigger in complex_triggers):
        return {"is_ai": False, "reply": None}
        
    # Default to requiring a human for anything unhandled
    return {"is_ai": False, "reply": None}
