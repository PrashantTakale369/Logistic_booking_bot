"""Rate calculation and service availability tools."""

from langchain_core.tools import tool
from sqlalchemy import func

from db.database import SessionLocal
from db.models import RateCard


@tool
def calculate_shipping_rate(
    origin: str,
    destination: str,
    transport_mode: str,
    service_type: str,
    weight_kg: float,
    volume_cbm: float = 0.0,
    num_packages: int = 1,
    is_fragile: bool = False,
    is_perishable: bool = False,
    declared_value: float = 0.0,
    insurance: bool = False,
) -> dict:
    """Calculate shipping rate for a parcel based on route, mode, service, and weight.
    Args:
        origin: Origin city name.
        destination: Destination city name.
        transport_mode: Mode of transport (road/air/rail/sea).
        service_type: Type of service (standard/express/same-day/overnight/international).
        weight_kg: Total weight in kilograms.
        volume_cbm: Total volume in cubic meters (optional).
        num_packages: Number of packages.
        is_fragile: Whether shipment is fragile.
        is_perishable: Whether shipment is perishable.
        declared_value: Declared value of goods in INR.
        insurance: Whether insurance is required.
    """
    session = SessionLocal()
    try:
        rate = (
            session.query(RateCard)
            .filter(
                func.lower(RateCard.origin_city) == origin.strip().lower(),
                func.lower(RateCard.destination_city) == destination.strip().lower(),
                func.lower(RateCard.transport_mode) == transport_mode.strip().lower(),
                func.lower(RateCard.service_type) == service_type.strip().lower(),
                RateCard.weight_slab_min_kg <= weight_kg,
                RateCard.weight_slab_max_kg >= weight_kg,
                RateCard.is_active == True,
            )
            .first()
        )

        if not rate:
            return {
                "available": False,
                "total_cost": 0,
                "breakdown": {},
                "estimated_days": 0,
                "rate_card_id": None,
                "message": f"No rate found for {origin} -> {destination} via {transport_mode} ({service_type}) for {weight_kg}kg.",
            }

        # Calculate base cost
        weight_cost = weight_kg * rate.price_per_kg
        volume_cost = volume_cbm * rate.volume_rate_per_cbm if volume_cbm > 0 and rate.volume_rate_per_cbm else 0
        base_cost = max(weight_cost, volume_cost)

        # Package charges
        package_charges = num_packages * rate.per_package_charge

        # Surcharges
        fragile_charge = base_cost * (rate.fragile_surcharge_pct / 100) if is_fragile else 0
        perishable_charge = base_cost * (rate.perishable_surcharge_pct / 100) if is_perishable else 0

        # Insurance
        insurance_charge = declared_value * (rate.insurance_pct / 100) if insurance and declared_value > 0 else 0

        # Total
        subtotal = base_cost + package_charges + fragile_charge + perishable_charge + insurance_charge
        total = max(subtotal, rate.min_charge)

        return {
            "available": True,
            "total_cost": round(total, 2),
            "breakdown": {
                "base_cost (weight/volume)": round(base_cost, 2),
                "package_charges": round(package_charges, 2),
                "fragile_surcharge": round(fragile_charge, 2),
                "perishable_surcharge": round(perishable_charge, 2),
                "insurance": round(insurance_charge, 2),
            },
            "estimated_days": rate.estimated_days,
            "rate_card_id": rate.id,
            "message": f"Estimated cost: ₹{round(total, 2)} | Delivery in ~{rate.estimated_days} days",
        }
    finally:
        session.close()


@tool
def check_service_availability(
    origin: str,
    destination: str,
    transport_mode: str = "",
    service_type: str = "",
) -> dict:
    """Check available shipping services for a route.
    Args:
        origin: Origin city name.
        destination: Destination city name.
        transport_mode: Filter by transport mode (optional).
        service_type: Filter by service type (optional).
    """
    session = SessionLocal()
    try:
        query = session.query(RateCard).filter(
            func.lower(RateCard.origin_city) == origin.strip().lower(),
            func.lower(RateCard.destination_city) == destination.strip().lower(),
            RateCard.is_active == True,
        )

        if transport_mode:
            query = query.filter(func.lower(RateCard.transport_mode) == transport_mode.strip().lower())
        if service_type:
            query = query.filter(func.lower(RateCard.service_type) == service_type.strip().lower())

        rates = query.all()

        if not rates:
            return {
                "available": False,
                "options": [],
                "message": f"No services available for {origin} -> {destination}.",
            }

        # Group by mode+service, show price range
        seen = {}
        for r in rates:
            key = f"{r.transport_mode}|{r.service_type}"
            if key not in seen:
                seen[key] = {
                    "transport_mode": r.transport_mode,
                    "service_type": r.service_type,
                    "estimated_days": r.estimated_days,
                    "min_price_per_kg": r.price_per_kg,
                    "max_price_per_kg": r.price_per_kg,
                }
            else:
                seen[key]["min_price_per_kg"] = min(seen[key]["min_price_per_kg"], r.price_per_kg)
                seen[key]["max_price_per_kg"] = max(seen[key]["max_price_per_kg"], r.price_per_kg)

        options = list(seen.values())
        return {
            "available": True,
            "options": options,
            "message": f"Found {len(options)} service options for {origin} -> {destination}.",
        }
    finally:
        session.close()
