"""Derive bookable time windows from weekly hours, exceptions, and bookings (US-015)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.availability import AvailabilityException, WeeklySchedule
from app.models.booking import Booking, BookingStatus
from app.models.schedule import Slot
from app.models.service import Service
from app.services.booking_logic import occupied_interval_for_booking


def _subtract_half_open(
    intervals: list[tuple[datetime, datetime]],
    block: tuple[datetime, datetime],
) -> list[tuple[datetime, datetime]]:
    """Split intervals around [b0, b1) (half-open block)."""
    b0, b1 = block
    if b0 >= b1:
        return intervals
    out: list[tuple[datetime, datetime]] = []
    for a0, a1 in intervals:
        if a1 <= b0 or a0 >= b1:
            out.append((a0, a1))
            continue
        if a0 < b0:
            seg_end = min(a1, b0)
            if a0 < seg_end:
                out.append((a0, seg_end))
        if b1 < a1:
            seg_start = max(a0, b1)
            if seg_start < a1:
                out.append((seg_start, a1))
    return out


def _base_windows_for_week(db: Session, monday: date, sunday: date) -> list[tuple[datetime, datetime]]:
    rows = db.scalars(select(WeeklySchedule)).all()
    by_dow: dict[int, WeeklySchedule] = {r.day_of_week: r for r in rows}
    windows: list[tuple[datetime, datetime]] = []
    d = monday
    while d <= sunday:
        dow = d.weekday()  # Monday=0 … Sunday=6
        row = by_dow.get(dow)
        if row is None:
            d += timedelta(days=1)
            continue
        if row.open_time >= row.close_time:
            d += timedelta(days=1)
            continue
        start = datetime.combine(d, row.open_time)
        end = datetime.combine(d, row.close_time)
        if start < end:
            windows.append((start, end))
        d += timedelta(days=1)
    return windows


def _exceptions_overlapping_week(db: Session, monday: date) -> list[AvailabilityException]:
    week_start = datetime.combine(monday, time.min)
    week_end_excl = datetime.combine(monday + timedelta(days=7), time.min)
    return list(
        db.scalars(
            select(AvailabilityException).where(
                AvailabilityException.start < week_end_excl,
                AvailabilityException.end > week_start,
            ),
        ).all(),
    )


def compute_bookable_windows(
    db: Session,
    *,
    service_id: int,
    monday: date,
    sunday: date,
) -> list[tuple[datetime, datetime]]:
    """Return contiguous free intervals (half-open [start, end)) inside the ISO week."""
    service = db.get(Service, service_id)
    if service is None:
        msg = "Service not found"
        raise ValueError(msg)

    intervals = _base_windows_for_week(db, monday, sunday)

    for ex in _exceptions_overlapping_week(db, monday):
        intervals = _subtract_half_open(intervals, (ex.start, ex.end))

    bookings = db.scalars(select(Booking).where(Booking.status != BookingStatus.cancelled)).all()
    for b in bookings:
        slot = db.get(Slot, b.slot_id)
        svc = db.get(Service, b.service_id)
        if slot is None or svc is None:
            continue
        occ = occupied_interval_for_booking(slot, svc, b.location)
        intervals = _subtract_half_open(intervals, occ)

    need = timedelta(minutes=service.base_duration_minutes)
    filtered: list[tuple[datetime, datetime]] = []
    for a0, a1 in intervals:
        if a1 - a0 >= need:
            filtered.append((a0, a1))

    filtered.sort(key=lambda t: (t[0], t[1]))
    return filtered
