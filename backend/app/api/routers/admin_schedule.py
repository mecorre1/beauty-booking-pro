"""Admin: weekly templates, apply to week, slot management."""

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin_user, get_db
from app.models.booking import Booking
from app.models.schedule import Slot, TemplateSlot, WeeklyTemplate
from app.models.user import User
from app.schemas.public_slots import bounds_for_iso_week_string
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
