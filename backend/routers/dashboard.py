"""
Dashboard & data routers — provides stats, orders, events, communications listings.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from auth import get_current_merchant
from models import Order, Event, Communication, Merchant

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_merchant: Merchant = Depends(get_current_merchant)):
    """Return aggregate stats for the dashboard."""
    # Filter by merchant's orders
    merchant_orders_subquery = db.query(Order.id).filter(Order.merchant_id == current_merchant.id).subquery()

    total_orders = db.query(func.count(Order.id)).filter(Order.merchant_id == current_merchant.id).scalar() or 0
    total_events = db.query(func.count(Event.id)).filter(Event.order_id.in_(merchant_orders_subquery)).scalar() or 0
    
    # Comm stats
    base_comm_query = db.query(Communication).filter(Communication.order_id.in_(merchant_orders_subquery))
    
    total_calls = base_comm_query.filter(Communication.comm_type == "voice").count()
    total_whatsapp = base_comm_query.filter(Communication.comm_type == "whatsapp").count()
    successful_calls = base_comm_query.filter(
        Communication.comm_type == "voice",
        Communication.status.in_(["completed", "success", "simulated"]),
    ).count()
    failed_calls = base_comm_query.filter(
        Communication.comm_type == "voice",
        Communication.status == "failed",
    ).count()

    return {
        "total_orders": total_orders,
        "total_events": total_events,
        "total_calls": total_calls,
        "total_whatsapp": total_whatsapp,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
    }


@router.get("/orders")
def list_orders(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str = Query(None),
    platform: str = Query(None),
    search: str = Query(None),
):
    """List orders with optional filters."""
    query = db.query(Order).filter(Order.merchant_id == current_merchant.id)

    if status:
        query = query.filter(Order.status == status)
    if platform:
        query = query.filter(Order.platform == platform)
    if search:
        query = query.filter(
            Order.customer_name.ilike(f"%{search}%")
            | Order.order_id.ilike(f"%{search}%")
        )

    total = query.count()
    orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "orders": [o.to_dict() for o in orders],
    }


@router.get("/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db), current_merchant: Merchant = Depends(get_current_merchant)):
    """Get single order with its events and communications."""
    order = db.query(Order).filter(Order.id == order_id, Order.merchant_id == current_merchant.id).first()
    if not order:
        return {"error": "Order not found"}

    return {
        **order.to_dict(),
        "events": [e.to_dict() for e in order.events],
        "communications": [c.to_dict() for c in order.communications],
    }


@router.get("/events")
def list_events(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    event_type: str = Query(None),
):
    """List events with optional type filter."""
    query = db.query(Event).join(Order).filter(Order.merchant_id == current_merchant.id)

    if event_type:
        query = query.filter(Event.event_type == event_type)

    total = query.count()
    events = query.order_by(desc(Event.timestamp)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "events": [e.to_dict() for e in events],
    }


@router.get("/communications")
def list_communications(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    comm_type: str = Query(None),
    status: str = Query(None),
):
    """List communication logs with optional filters."""
    query = db.query(Communication).join(Order).filter(Order.merchant_id == current_merchant.id)

    if comm_type:
        query = query.filter(Communication.comm_type == comm_type)
    if status:
        query = query.filter(Communication.status == status)

    total = query.count()
    comms = query.order_by(desc(Communication.timestamp)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "communications": [c.to_dict() for c in comms],
    }
