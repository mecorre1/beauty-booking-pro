"""Default `PriceEntry` rows per service (US-012)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.price_entry import PriceEntry
from app.models.service import Gender, Service, ServiceType


def _default_price_for_service(s: Service) -> Decimal:
    """Deterministic demo prices aligned with catalog tiers."""
    base = {
        (ServiceType.haircut, Gender.male): Decimal("35.00"),
        (ServiceType.haircut, Gender.female): Decimal("42.00"),
        (ServiceType.haircut_hairdressing, Gender.male): Decimal("48.00"),
        (ServiceType.haircut_hairdressing, Gender.female): Decimal("55.00"),
        (ServiceType.color, Gender.male): Decimal("75.00"),
        (ServiceType.color, Gender.female): Decimal("95.00"),
    }
    return base[(s.type, s.gender)]


def seed_price_entries(session: Session) -> None:
    n = session.scalar(select(func.count()).select_from(PriceEntry)) or 0
    if n > 0:
        return
    services = session.scalars(select(Service)).all()
    start = datetime(2000, 1, 1, 0, 0, 0)
    for s in services:
        session.add(
            PriceEntry(
                service_id=s.id,
                valid_from=start,
                valid_to=None,
                price=_default_price_for_service(s),
            ),
        )
    session.commit()
