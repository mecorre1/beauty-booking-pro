"""Seed a single default salon row (US-011)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.salon import Salon


def seed_salon(session: Session) -> None:
    n = session.scalar(select(func.count()).select_from(Salon)) or 0
    if n > 0:
        return
    session.add(
        Salon(
            name="Studio Salon",
            address="123 Example Street, City",
            phone="+1 555 0100",
            email="hello@example.com",
        ),
    )
    session.commit()
