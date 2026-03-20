"""Admin: list and manage bookings."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin_user, get_db
from app.models.booking import Booking, BookingStatus
from app.models.schedule import Slot
from app.models.user import User
from app.schemas.public_slots import bounds_for_iso_week_string

router = APIRouter()


class BookingAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slot_id: int
    service_id: int
    location: str
    status: BookingStatus
    client_name: str
    client_email: str
    client_phone: str
    slot_date: date
    slot_start_time: str
    service_type: str


@router.get("", response_model=list[BookingAdminOut])
def list_bookings(
    upcoming: bool | None = Query(None, description="True = future only; False = past only; None = all"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> list[BookingAdminOut]:
    rows = db.scalars(
        select(Booking)
        .options(selectinload(Booking.slot), selectinload(Booking.service))
        .order_by(Booking.id),
    ).all()
    now = datetime.now()
    out: list[BookingAdminOut] = []
    for b in rows:
        if b.slot is None or b.service is None:
            continue
        dt = datetime.combine(b.slot.date, b.slot.start_time)
        if upcoming is True and dt < now:
            continue
        if upcoming is False and dt >= now:
            continue
        out.append(
            BookingAdminOut(
                id=b.id,
                slot_id=b.slot_id,
                service_id=b.service_id,
                location=b.location.value,
                status=b.status,
                client_name=b.client_name,
                client_email=b.client_email,
                client_phone=b.client_phone,
                slot_date=b.slot.date,
                slot_start_time=b.slot.start_time.isoformat(),
                service_type=b.service.type.value,
            ),
        )
    return out


class AdminCalendarSlotOut(BaseModel):
    id: int
    date: date
    start_time: str
    end_time: str
    is_available: bool
    booking_id: int | None = None


class AdminCalendarWeekOut(BaseModel):
    slots: list[AdminCalendarSlotOut]


@router.get("/calendar", response_model=AdminCalendarWeekOut)
def admin_calendar_week(
    week: str = Query(..., description="ISO week YYYY-WW"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> AdminCalendarWeekOut:
    try:
        monday, sunday = bounds_for_iso_week_string(week)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    slots = db.scalars(
        select(Slot)
        .where(Slot.date >= monday, Slot.date <= sunday)
        .order_by(Slot.date, Slot.start_time),
    ).all()
    bookings = db.scalars(select(Booking)).all()
    by_slot = {b.slot_id: b.id for b in bookings}
    out: list[AdminCalendarSlotOut] = []
    for s in slots:
        out.append(
            AdminCalendarSlotOut(
                id=s.id,
                date=s.date,
                start_time=s.start_time.isoformat(),
                end_time=s.end_time.isoformat(),
                is_available=s.is_available,
                booking_id=by_slot.get(s.id),
            ),
        )
    return AdminCalendarWeekOut(slots=out)
