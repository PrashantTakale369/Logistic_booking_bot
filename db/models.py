from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User {self.name} ({self.phone})>"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    booking_data_json = Column(Text, default="{}")
    current_section = Column(String(30), default="greeting")
    booking_ref = Column(String(20), nullable=True)
    is_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="sessions")

    def __repr__(self):
        return f"<ChatSession {self.session_id} ({self.current_section})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False, index=True)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ChatMessage {self.role} ({self.session_id})>"


class RateCard(Base):
    __tablename__ = "rate_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_city = Column(String(100), nullable=False)
    destination_city = Column(String(100), nullable=False)
    transport_mode = Column(String(20), nullable=False)  # road/air/rail/sea
    service_type = Column(String(30), nullable=False)  # standard/express/same-day/overnight/international
    weight_slab_min_kg = Column(Float, nullable=False)
    weight_slab_max_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    volume_rate_per_cbm = Column(Float, default=0)
    per_package_charge = Column(Float, default=0)
    fragile_surcharge_pct = Column(Float, default=0)
    perishable_surcharge_pct = Column(Float, default=0)
    insurance_pct = Column(Float, default=2.0)
    min_charge = Column(Float, default=0)
    estimated_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_rate_route", "origin_city", "destination_city", "transport_mode", "service_type"),
    )

    def __repr__(self):
        return f"<RateCard {self.origin_city}->{self.destination_city} {self.transport_mode}/{self.service_type}>"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_ref = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(String(20), default="confirmed")  # confirmed/cancelled/delivered

    # Shipper
    shipper_name = Column(String(200))
    shipper_contact = Column(String(200))
    shipper_phone = Column(String(20))
    shipper_email = Column(String(200))
    pickup_address = Column(Text)
    pickup_date = Column(String(20))
    pickup_time = Column(String(20))

    # Consignee
    consignee_name = Column(String(200))
    consignee_contact = Column(String(200))
    consignee_phone = Column(String(20))
    consignee_email = Column(String(200))
    delivery_address = Column(Text)
    preferred_delivery_date = Column(String(20))

    # Shipment
    goods_type = Column(String(200))
    num_packages = Column(Integer)
    total_weight_kg = Column(Float)
    dimensions = Column(Text)  # JSON string
    total_volume_cbm = Column(Float)
    declared_value = Column(Float)
    is_fragile = Column(Boolean, default=False)
    is_perishable = Column(Boolean, default=False)
    special_handling = Column(Text)

    # Service
    service_type = Column(String(30))
    transport_mode = Column(String(20))

    # Documentation
    invoice_number = Column(String(100))
    packing_list = Column(String(100))
    eway_bill = Column(String(100))

    # Payment
    payment_mode = Column(String(20))  # prepaid/COD/credit
    insurance_opted = Column(Boolean, default=False)
    insured_value = Column(Float)

    # Additional
    delivery_confirmation = Column(Boolean, default=False)
    return_option = Column(Boolean, default=False)
    remarks = Column(Text)

    # Calculated
    estimated_cost = Column(Float)
    rate_card_id = Column(Integer, ForeignKey("rate_cards.id"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    rate_card = relationship("RateCard", backref="bookings")

    def __repr__(self):
        return f"<Booking {self.booking_ref} ({self.status})>"
