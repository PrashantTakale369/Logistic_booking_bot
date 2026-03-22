"""Tests for database models and operations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.models import RateCard, Booking


def test_rate_card_creation(db_session):
    rates = db_session.query(RateCard).all()
    assert len(rates) == 2


def test_rate_card_query_by_route(db_session):
    rate = (
        db_session.query(RateCard)
        .filter(
            RateCard.origin_city == "Mumbai",
            RateCard.destination_city == "Delhi",
            RateCard.transport_mode == "road",
        )
        .first()
    )
    assert rate is not None
    assert rate.price_per_kg == 15.0
    assert rate.estimated_days == 5


def test_booking_creation(db_session):
    booking = Booking(
        booking_ref="LB-20260322-0001",
        shipper_name="Test User",
        shipper_phone="+919876543210",
        pickup_address="123 Test Street, Mumbai 400001",
        consignee_name="Receiver",
        consignee_phone="+919876543211",
        delivery_address="456 Test Road, Delhi 110001",
        goods_type="Electronics",
        num_packages=2,
        total_weight_kg=10.5,
        service_type="express",
        transport_mode="air",
        payment_mode="prepaid",
        estimated_cost=1500.0,
    )
    db_session.add(booking)
    db_session.commit()

    fetched = db_session.query(Booking).filter(Booking.booking_ref == "LB-20260322-0001").first()
    assert fetched is not None
    assert fetched.shipper_name == "Test User"
    assert fetched.estimated_cost == 1500.0
    assert fetched.status == "confirmed"


def test_booking_no_duplicate_ref(db_session):
    b1 = Booking(booking_ref="LB-20260322-9999", shipper_name="A")
    db_session.add(b1)
    db_session.commit()

    b2 = Booking(booking_ref="LB-20260322-9999", shipper_name="B")
    db_session.add(b2)
    try:
        db_session.commit()
        assert False, "Should have raised IntegrityError"
    except Exception:
        db_session.rollback()
