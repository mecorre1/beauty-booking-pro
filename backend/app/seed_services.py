"""Idempotent seed for catalog `Service` rows (US-002)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.service import Gender, Service, ServiceType


def seed_services(session: Session) -> None:
    """Insert the six (type × gender) services if the table is empty."""
    n = session.scalar(select(func.count()).select_from(Service)) or 0
    if n > 0:
        return
    # Durations illustrate gender variance; buffer is internal for overlap logic later.
    rows = [
        Service(
            type=ServiceType.haircut,
            gender=Gender.male,
            base_duration_minutes=30,
            at_home_buffer_minutes=30,
        ),
        Service(
            type=ServiceType.haircut,
            gender=Gender.female,
            base_duration_minutes=45,
            at_home_buffer_minutes=30,
        ),
        Service(
            type=ServiceType.haircut_hairdressing,
            gender=Gender.male,
            base_duration_minutes=45,
            at_home_buffer_minutes=35,
        ),
        Service(
            type=ServiceType.haircut_hairdressing,
            gender=Gender.female,
            base_duration_minutes=60,
            at_home_buffer_minutes=35,
        ),
        Service(
            type=ServiceType.color,
            gender=Gender.male,
            base_duration_minutes=90,
            at_home_buffer_minutes=40,
        ),
        Service(
            type=ServiceType.color,
            gender=Gender.female,
            base_duration_minutes=120,
            at_home_buffer_minutes=40,
        ),
    ]
    session.add_all(rows)
    session.commit()
