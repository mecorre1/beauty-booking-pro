"""Resolve `PriceEntry` at a specific moment (US-012: slot datetime)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_entry import PriceEntry
from app.models.service import Service


def resolve_price_for_service(session: Session, service_id: int, at: datetime) -> Decimal:
    """Return price for `service_id` valid at naive local `at`."""
    row = session.scalar(
        select(PriceEntry)
        .where(PriceEntry.service_id == service_id)
        .where(PriceEntry.valid_from <= at)
        .where((PriceEntry.valid_to.is_(None)) | (PriceEntry.valid_to > at))
        .order_by(PriceEntry.valid_from.desc()),
    )
    if row is None:
        raise ValueError(f"No PriceEntry for service {service_id} at {at}")
    return row.price


def min_resolved_price_across_services(session: Session, at: datetime) -> Decimal:
    """Minimum price across all services at `at` — used for public slot display (US-001/012)."""
    services = session.scalars(select(Service)).all()
    if not services:
        return Decimal("0")
    prices = [resolve_price_for_service(session, s.id, at) for s in services]
    return min(prices)


def assert_no_overlapping_price_entry(
    session: Session,
    *,
    service_id: int,
    valid_from: datetime,
    valid_to: datetime | None,
    exclude_id: int | None = None,
) -> None:
    """Reject if new interval overlaps an existing row for the same service."""
    q = select(PriceEntry).where(PriceEntry.service_id == service_id)
    if exclude_id is not None:
        q = q.where(PriceEntry.id != exclude_id)
    existing = session.scalars(q).all()
    for e in existing:
        if _open_intervals_overlap(e.valid_from, e.valid_to, valid_from, valid_to):
            msg = "PriceEntry interval overlaps an existing row for this service"
            raise ValueError(msg)


def _open_intervals_overlap(
    a_start: datetime,
    a_end: datetime | None,
    b_start: datetime,
    b_end: datetime | None,
) -> bool:
    """Half-open style [start, end) with open end when `end` is None."""
    if a_end is not None and b_start >= a_end:
        return False
    if b_end is not None and a_start >= b_end:
        return False
    return True
