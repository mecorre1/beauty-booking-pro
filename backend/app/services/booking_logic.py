"""Occupied time intervals and overlap checks (SPEC + US-004)."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus, Location
from app.models.schedule import Slot
from app.models.service import Service


def slot_start_datetime(slot: Slot) -> datetime:
    return datetime.combine(slot.date, slot.start_time)


def slot_end_datetime(slot: Slot) -> datetime:
    return datetime.combine(slot.date, slot.end_time)


def occupied_interval_for_booking(
    slot: Slot,
    service: Service,
    location: Location,
) -> tuple[datetime, datetime]:
    """Wall-clock interval the stylist is blocked for this booking."""
    start = slot_start_datetime(slot)
    if location == Location.salon:
        end = start + timedelta(minutes=service.base_duration_minutes)
        return start, end
    # home: buffer after scheduled slot end (SPEC)
    end = slot_end_datetime(slot) + timedelta(minutes=service.at_home_buffer_minutes)
    return start, end


def intervals_overlap_dt(a: tuple[datetime, datetime], b: tuple[datetime, datetime]) -> bool:
    a0, a1 = a
    b0, b1 = b
    return a0 < b1 and b0 < a1


def has_time_conflict(
    session: Session,
    proposed: tuple[datetime, datetime],
    *,
    exclude_booking_id: int | None = None,
) -> bool:
    """True if proposed overlaps any non-cancelled booking's occupied interval."""
    bookings = session.scalars(
        select(Booking).where(Booking.status != BookingStatus.cancelled),
    ).all()
    for b in bookings:
        if exclude_booking_id is not None and b.id == exclude_booking_id:
            continue
        slot = session.get(Slot, b.slot_id)
        svc = session.get(Service, b.service_id)
        if slot is None or svc is None:
            continue
        occ = occupied_interval_for_booking(slot, svc, b.location)
        if intervals_overlap_dt(proposed, occ):
            return True
    return False


def assert_slot_fits_service(slot: Slot, service: Service) -> None:
    start = slot_start_datetime(slot)
    end = slot_end_datetime(slot)
    need = timedelta(minutes=service.base_duration_minutes)
    if start + need > end:
        msg = "Service duration does not fit in the selected slot window"
        raise ValueError(msg)
