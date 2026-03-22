"""Booking CRUD tools."""

import random
from datetime import datetime, timezone

from langchain_core.tools import tool
from sqlalchemy import func

from db.database import SessionLocal
from db.models import Booking
from config import BOOKING_REF_PREFIX


def _generate_booking_ref() -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand = random.randint(1000, 9999)
    return f"{BOOKING_REF_PREFIX}-{date_str}-{rand}"


@tool
def save_booking(booking_data: dict) -> dict:
    """Save a confirmed booking to the database.
    Args:
        booking_data: Dictionary containing all booking fields (shipper, consignee, shipment, service, payment details).
    """
    required = ["shipper_name", "shipper_phone", "pickup_address",
                 "consignee_name", "consignee_phone", "delivery_address",
                 "goods_type", "num_packages", "total_weight_kg",
                 "service_type", "transport_mode", "payment_mode"]

    missing = [f for f in required if not booking_data.get(f)]
    if missing:
        return {"success": False, "booking_ref": "", "error": f"Missing required fields: {', '.join(missing)}"}

    session = SessionLocal()
    try:
        booking_ref = _generate_booking_ref()
        booking = Booking(booking_ref=booking_ref, **{
            k: v for k, v in booking_data.items()
            if hasattr(Booking, k) and k not in ("id", "booking_ref", "created_at", "updated_at")
        })
        booking.booking_ref = booking_ref
        session.add(booking)
        session.commit()
        return {"success": True, "booking_ref": booking_ref, "error": ""}
    except Exception as e:
        session.rollback()
        return {"success": False, "booking_ref": "", "error": str(e)}
    finally:
        session.close()


@tool
def lookup_booking(booking_ref: str = "", shipper_phone: str = "") -> dict:
    """Look up an existing booking by reference number or shipper phone.
    Args:
        booking_ref: The booking reference number (e.g., LB-20260322-1234).
        shipper_phone: The shipper's phone number to search by.
    """
    if not booking_ref and not shipper_phone:
        return {"found": False, "booking": {}, "error": "Provide booking_ref or shipper_phone."}

    session = SessionLocal()
    try:
        query = session.query(Booking)
        if booking_ref:
            query = query.filter(Booking.booking_ref == booking_ref.strip())
        elif shipper_phone:
            query = query.filter(Booking.shipper_phone.contains(shipper_phone.strip()))

        booking = query.order_by(Booking.created_at.desc()).first()

        if not booking:
            return {"found": False, "booking": {}, "error": "No booking found."}

        return {
            "found": True,
            "booking": {
                "booking_ref": booking.booking_ref,
                "status": booking.status,
                "shipper_name": booking.shipper_name,
                "consignee_name": booking.consignee_name,
                "pickup_address": booking.pickup_address,
                "delivery_address": booking.delivery_address,
                "goods_type": booking.goods_type,
                "num_packages": booking.num_packages,
                "total_weight_kg": booking.total_weight_kg,
                "service_type": booking.service_type,
                "transport_mode": booking.transport_mode,
                "estimated_cost": booking.estimated_cost,
                "payment_mode": booking.payment_mode,
                "created_at": str(booking.created_at),
            },
            "error": "",
        }
    finally:
        session.close()


@tool
def cancel_booking(booking_ref: str) -> dict:
    """Cancel an existing booking.
    Args:
        booking_ref: The booking reference number to cancel.
    """
    session = SessionLocal()
    try:
        booking = session.query(Booking).filter(Booking.booking_ref == booking_ref.strip()).first()
        if not booking:
            return {"success": False, "error": "Booking not found."}
        if booking.status == "cancelled":
            return {"success": False, "error": "Booking is already cancelled."}

        booking.status = "cancelled"
        session.commit()
        return {"success": True, "error": ""}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()
