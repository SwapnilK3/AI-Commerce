"""
Omnichannel Inbox Router — Handles fetching conversations and manual merchant replies.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from database import get_db
from models import Merchant, Message
from schemas import MessageResponse, InboxContact, MessageCreate
from auth import get_current_merchant
from providers.factory import get_providers

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/inbox",
    tags=["Inbox"],
    responses={404: {"description": "Not found"}},
)

@router.get("/contacts", response_model=List[InboxContact])
def get_inbox_contacts(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Get a list of all unique contacts (grouped by contact_id and channel) 
    with their snippet of the most recent message.
    """
    # Find the latest message ID per contact and channel
    subquery = (
        db.query(
            Message.contact_id,
            Message.channel,
            func.max(Message.timestamp).label("max_timestamp")
        )
        .filter(Message.merchant_id == current_merchant.id)
        .group_by(Message.contact_id, Message.channel)
        .subquery()
    )

    # Join back to get the full message row
    latest_messages = (
        db.query(Message)
        .join(
            subquery,
            (Message.contact_id == subquery.c.contact_id) &
            (Message.channel == subquery.c.channel) &
            (Message.timestamp == subquery.c.max_timestamp)
        )
        .order_by(desc(Message.timestamp))
        .all()
    )

    contacts = []
    for msg in latest_messages:
        # TODO: Calculate actual unread_count based on a "read" flag if desired later
        requires_human = db.query(Message).filter(
            Message.merchant_id == current_merchant.id,
            Message.contact_id == msg.contact_id,
            Message.requires_human == 1
        ).count() > 0

        contacts.append(InboxContact(
            contact_id=msg.contact_id,
            channel=msg.channel,
            last_message=msg.text,
            last_timestamp=msg.timestamp,
            unread_count=0, 
            requires_human=requires_human
        ))

    return contacts


@router.get("/{contact_id}/messages", response_model=List[MessageResponse])
def get_chat_history(
    contact_id: str,
    channel: str = Query(..., description="The channel: whatsapp, instagram, facebook"),
    limit: int = 50,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Get the full chat history for a specific contact on a specific channel.
    """
    messages = (
        db.query(Message)
        .filter(
            Message.merchant_id == current_merchant.id,
            Message.contact_id == contact_id,
            Message.channel == channel
        )
        .order_by(Message.timestamp.asc())  # Order chronologically for a chat view
        .limit(limit)
        .all()
    )
    
    # If a merchant looks at the chat, we can clear the requires_human flag
    db.query(Message).filter(
        Message.merchant_id == current_merchant.id,
        Message.contact_id == contact_id,
        Message.requires_human == 1
    ).update({"requires_human": 0})
    db.commit()

    return messages


@router.post("/reply", response_model=MessageResponse)
async def send_manual_reply(
    payload: dict, # Expects {contact_id: "...", channel: "...", text: "..."}
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Send a manual reply from the merchant dashboard to the customer via the specific channel.
    """
    contact_id = payload.get("contact_id")
    channel = payload.get("channel")
    text = payload.get("text")

    if not all([contact_id, channel, text]):
        raise HTTPException(status_code=400, detail="Missing required fields: contact_id, channel, text")

    # 1. Dispatch the message using the proper provider configured by the merchant
    providers = get_providers(current_merchant)
    
    if channel == "whatsapp":
        try:
            await providers.messaging.send_message(contact_id, text)
        except Exception as e:
            logger.error(f"Failed to send manual WhatsApp reply: {e}")
            raise HTTPException(status_code=500, detail="Failed to route message through WhatsApp integration.")
    else:
        # TODO: Implement Instagram/Facebook outbound graph API calls
        logger.warning(f"Outbound provider for {channel} not yet implemented. Creating dummy record.")

    # 2. Save the outgoing message strictly as a human reply
    db_msg = Message(
        merchant_id=current_merchant.id,
        channel=channel,
        contact_id=contact_id,
        text=text,
        is_inbound=0,
        is_ai_reply=0,
        requires_human=0
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    return db_msg
