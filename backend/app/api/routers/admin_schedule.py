"""Admin: weekly templates, apply to week, slot management."""

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin_user, get_db
from app.models.availability import AvailabilityException, WeeklySchedule
from app.models.booking import Booking, BookingStatus
from app.models.schedule import Slot, TemplateSlot, WeeklyTemplate
from app.models.user import User
from app.schemas.admin_calendar import (
    AdminScheduleBookingOut,
    AdminScheduleWeekOut,
    AvailabilityExceptionOut,
    DayScheduleOut,
    WeeklyScheduleDayOut,
    WeeklyScheduleUpdate,
)
from app.schemas.public_slots import bounds_for_iso_week_string
from app.services.booking_logic import occupied_interval_for_booking
router = APIRouter()


class TemplateSlotIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = Field(description="HH:MM or HH:MM:SS")
    duration_minutes: int = Field(gt=0, le=24 * 60)


class TemplateSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_of_week: int
    start_time: str
    duration_minutes: int

    @field_validator("start_time", mode="before")
    @classmethod
    def _time_to_str(cls, v: object) -> str:
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return str(v)


class WeeklyTemplateCreate(BaseModel):
    name: str
    slots: list[TemplateSlotIn]


class WeeklyTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    slots: list[TemplateSlotOut] = Field(validation_alias="template_slots")


class ApplyTemplateBody(BaseModel):
    template_id: int
    week: str = Field(description="ISO week YYYY-WW")


def _parse_time(s: str) -> time:
    parts = s.strip().split(":")
    if len(parts) < 2:
        raise ValueError("invalid time")
    h, m = int(parts[0]), int(parts[1])
    sec = int(parts[2]) if len(parts) > 2 else 0
    return time(h, m, sec)


def _end_time(start: time, duration_minutes: int) -> time:
    base = datetime.combine(date(2000, 1, 1), start) + timedelta(minutes=duration_minutes)
    return base.time()


@router.get("/templates", response_model=list[WeeklyTemplateRead])
def list_templates(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> list[WeeklyTemplate]:
    return list(
        db.scalars(
            select(WeeklyTemplate)
            .options(selectinload(WeeklyTemplate.template_slots))
            .order_by(WeeklyTemplate.id),
        ).all(),
    )


@router.post("/templates", response_model=WeeklyTemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(
    body: WeeklyTemplateCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> WeeklyTemplate:
    t = WeeklyTemplate(name=body.name)
    db.add(t)
    db.flush()
    for s in body.slots:
        st = _parse_time(s.start_time)
        db.add(
            TemplateSlot(
                template_id=t.id,
                day_of_week=s.day_of_week,
                start_time=st,
                duration_minutes=s.duration_minutes,
            ),
        )
    db.commit()
    loaded = db.scalar(
        select(WeeklyTemplate)
        .options(selectinload(WeeklyTemplate.template_slots))
        .where(WeeklyTemplate.id == t.id),
    )
    assert loaded is not None
    return loaded


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> None:
    t = db.get(WeeklyTemplate, template_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
    db.delete(t)
    db.commit()


@router.post("/apply", status_code=status.HTTP_201_CREATED)
def apply_template(
    body: ApplyTemplateBody,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> dict[str, int]:
    """Apply template to ISO week: deletes all slots in that week (reject if any booking exists)."""
    try:
        monday, sunday = bounds_for_iso_week_string(body.week)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    template = db.get(WeeklyTemplate, body.template_id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")

    slots_in_week = db.scalars(
        select(Slot).where(Slot.date >= monday, Slot.date <= sunday),
    ).all()
    for s in slots_in_week:
        if db.scalar(select(Booking.id).where(Booking.slot_id == s.id)) is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Cannot apply template: week has existing bookings",
            )

    db.execute(delete(Slot).where(Slot.date >= monday, Slot.date <= sunday))
    db.flush()

    created = 0
    tslots = db.scalars(
        select(TemplateSlot).where(TemplateSlot.template_id == template.id),
    ).all()
    for ts in tslots:
        day = monday + timedelta(days=ts.day_of_week)
        start = ts.start_time
        end = _end_time(start, ts.duration_minutes)
        row = Slot(
            date=day,
            start_time=start,
            end_time=end,
            is_available=True,
            source_template_id=template.id,
        )
        db.add(row)
        created += 1
    db.commit()
    return {"slots_created": created}


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> None:
    s = db.get(Slot, slot_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if db.scalar(select(Booking.id).where(Booking.slot_id == s.id)) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Cannot delete slot with an existing booking",
        )
    db.delete(s)
    db.commit()


@router.get("", response_model=AdminScheduleWeekOut)
def get_admin_schedule_week(
    week: str = Query(..., description="ISO week YYYY-WW"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> AdminScheduleWeekOut:
    """Weekly view: default hours per day, exceptions, and bookings (occupied intervals)."""
    try:
        monday, sunday = bounds_for_iso_week_string(week)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    by_dow = {r.day_of_week: r for r in db.scalars(select(WeeklySchedule)).all()}
    days: list[DayScheduleOut] = []
    d = monday
    while d <= sunday:
        dow = d.weekday()
        row = by_dow.get(dow)
        if row is None:
            days.append(DayScheduleOut(date=d, day_of_week=dow, open_time=None, close_time=None))
        else:
            days.append(
                DayScheduleOut(
                    date=d,
                    day_of_week=dow,
                    open_time=row.open_time.isoformat(),
                    close_time=row.close_time.isoformat(),
                ),
            )
        d += timedelta(days=1)

    week_start = datetime.combine(monday, time.min)
    week_end_excl = datetime.combine(monday + timedelta(days=7), time.min)
    exceptions = list(
        db.scalars(
            select(AvailabilityException)
            .where(
                AvailabilityException.start < week_end_excl,
                AvailabilityException.end > week_start,
            )
            .order_by(AvailabilityException.start),
        ).all(),
    )

    bookings_raw = db.scalars(
        select(Booking)
        .where(Booking.status != BookingStatus.cancelled)
        .options(
            selectinload(Booking.slot),
            selectinload(Booking.service),
            selectinload(Booking.client),
        ),
    ).all()
    bookings_out: list[AdminScheduleBookingOut] = []
    for b in bookings_raw:
        if b.slot is None or b.service is None or b.client is None:
            continue
        occ = occupied_interval_for_booking(b.slot, b.service, b.location)
        if occ[1] <= week_start or occ[0] >= week_end_excl:
            continue
        bookings_out.append(
            AdminScheduleBookingOut(
                id=b.id,
                start=occ[0],
                end=occ[1],
                client_name=b.client.name,
                client_email=b.client.email,
                client_phone=b.client.phone,
                service_type=b.service.type.value,
                location=b.location.value,
                status=b.status,
                slot_id=b.slot_id,
            ),
        )
    bookings_out.sort(key=lambda x: (x.start, x.id))

    return AdminScheduleWeekOut(
        week=week.strip(),
        days=days,
        exceptions=[AvailabilityExceptionOut.model_validate(x) for x in exceptions],
        bookings=bookings_out,
    )


@router.put("", response_model=WeeklyScheduleDayOut)
def put_weekly_default_hours(
    body: WeeklyScheduleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> WeeklyScheduleDayOut:
    open_t = _parse_time(body.open_time)
    close_t = _parse_time(body.close_time)
    if open_t >= close_t:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="open_time must be before close_time",
        )
    row = db.scalar(select(WeeklySchedule).where(WeeklySchedule.day_of_week == body.day_of_week))
    if row is None:
        row = WeeklySchedule(day_of_week=body.day_of_week, open_time=open_t, close_time=close_t)
        db.add(row)
    else:
        row.open_time = open_t
        row.close_time = close_t
    db.commit()
    db.refresh(row)
    return WeeklyScheduleDayOut(
        day_of_week=row.day_of_week,
        open_time=row.open_time.isoformat(),
        close_time=row.close_time.isoformat(),
    )
