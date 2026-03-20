from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base; models inherit from this."""


# SQLite needs check_same_thread=False for use with FastAPI's threadpool.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if missing (idempotent). Imports models so metadata is populated."""
    import app.models  # noqa: F401

    from app.seed_admin import seed_bootstrap_admin
    from app.seed_price_entries import seed_price_entries
    from app.seed_salon import seed_salon
    from app.seed_services import seed_services

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_services(session)
        seed_salon(session)
        seed_price_entries(session)
        seed_bootstrap_admin(session)
