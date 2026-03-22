"""Seed the rate_cards table with sample data for Indian logistics routes."""

from db.database import init_db, SessionLocal
from db.models import RateCard

ROUTES = [
    ("Mumbai", "Delhi"),
    ("Mumbai", "Bangalore"),
    ("Mumbai", "Chennai"),
    ("Delhi", "Kolkata"),
    ("Delhi", "Hyderabad"),
    ("Bangalore", "Chennai"),
    ("Bangalore", "Hyderabad"),
    ("Kolkata", "Chennai"),
    ("Pune", "Delhi"),
    ("Ahmedabad", "Mumbai"),
]

# (transport_mode, service_type, base_price_per_kg, per_pkg, est_days, min_charge)
MODE_SERVICE_CONFIGS = [
    ("road", "standard",   15,  50,  5, 200),
    ("road", "express",    25,  75,  3, 350),
    ("air",  "express",    60, 100,  1, 800),
    ("air",  "overnight",  80, 120,  1, 1000),
    ("rail", "standard",   12,  40,  4, 180),
    ("rail", "express",    20,  60,  2, 300),
    ("sea",  "standard",    8,  30, 10, 150),
]

WEIGHT_SLABS = [
    (0,    5,   1.0),   # 0-5 kg: base rate
    (5,   20,   0.85),  # 5-20 kg: 15% discount
    (20, 100,   0.70),  # 20-100 kg: 30% discount
    (100, 500,  0.55),  # 100-500 kg: 45% discount
    (500, 9999, 0.45),  # 500+ kg: 55% discount
]


def seed():
    init_db()
    session = SessionLocal()

    # Clear existing rate cards
    session.query(RateCard).delete()

    records = []
    for origin, dest in ROUTES:
        for mode, svc, base_price, per_pkg, days, min_chg in MODE_SERVICE_CONFIGS:
            # Not all routes have sea transport
            if mode == "sea" and origin not in ("Mumbai", "Chennai", "Kolkata"):
                continue

            for slab_min, slab_max, multiplier in WEIGHT_SLABS:
                records.append(RateCard(
                    origin_city=origin,
                    destination_city=dest,
                    transport_mode=mode,
                    service_type=svc,
                    weight_slab_min_kg=slab_min,
                    weight_slab_max_kg=slab_max,
                    price_per_kg=round(base_price * multiplier, 2),
                    volume_rate_per_cbm=round(base_price * multiplier * 200, 2),
                    per_package_charge=per_pkg,
                    fragile_surcharge_pct=15.0,
                    perishable_surcharge_pct=20.0,
                    insurance_pct=2.0,
                    min_charge=min_chg,
                    estimated_days=days,
                    is_active=True,
                ))

    session.add_all(records)
    session.commit()
    print(f"Seeded {len(records)} rate card entries.")
    session.close()


if __name__ == "__main__":
    seed()
