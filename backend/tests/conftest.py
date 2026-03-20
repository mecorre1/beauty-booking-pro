import app.models  # noqa: F401 — register ORM metadata
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db import Base
from app.main import create_app


@pytest.fixture
def db_session() -> Session:
    # StaticPool: single connection so `:memory:` is shared across session + ORM (SQLite default is per-connection).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    from app.seed_price_entries import seed_price_entries
    from app.seed_salon import seed_salon
    from app.seed_services import seed_services

    seed_services(db)
    seed_salon(db)
    seed_price_entries(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    application = create_app(init_db_on_startup=False)
    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
