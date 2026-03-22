"""Pytest fixtures for testing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, RateCard


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed a few test rate cards
    test_rates = [
        RateCard(
            origin_city="Mumbai",
            destination_city="Delhi",
            transport_mode="road",
            service_type="standard",
            weight_slab_min_kg=0,
            weight_slab_max_kg=5,
            price_per_kg=15.0,
            volume_rate_per_cbm=3000.0,
            per_package_charge=50,
            fragile_surcharge_pct=15.0,
            perishable_surcharge_pct=20.0,
            insurance_pct=2.0,
            min_charge=200,
            estimated_days=5,
            is_active=True,
        ),
        RateCard(
            origin_city="Mumbai",
            destination_city="Delhi",
            transport_mode="air",
            service_type="express",
            weight_slab_min_kg=0,
            weight_slab_max_kg=20,
            price_per_kg=60.0,
            volume_rate_per_cbm=12000.0,
            per_package_charge=100,
            fragile_surcharge_pct=15.0,
            perishable_surcharge_pct=20.0,
            insurance_pct=2.0,
            min_charge=800,
            estimated_days=1,
            is_active=True,
        ),
    ]
    session.add_all(test_rates)
    session.commit()

    yield session
    session.close()
