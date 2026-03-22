from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from db.models import Base

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_session():
    """Get a new database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
