"""Client-facing booking endpoints (availability, book, edit by token)."""

import secrets
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.email as email_pkg

from app.api.deps import get_db
from app.config import settings
from app.models.booking import Booking, BookingStatus, Location
from app.models.salon import Salon
from app.models.schedule import Slot
from app.models.service import Service
from app.schemas.public_booking import (
    BookingPublicOut,
    CreateBookingBody,
    PricingMetaOut,
    SalonPublicOut,
    UpdateBookingBody,
)
from app.schemas.public_services import ServicePublic
from app.schemas.public_slots import SlotPublic, bounds_for_iso_week_string
from app.services.booking_logic import (
    assert_slot_fits_service,
    has_time_conflict,
    occupied_interval_for_booking,
)
from app.services.pricing import min_resolved_price_across_services, resolve_price_for_service

router = APIRouter()


def _duration_minutes(slot_date: object, start_time: object, end_time: object) -> int:
    start_dt = datetime.combine(slot_date, start_time)  # type: ignore[arg-type]
    end_dt = datetime.combine(slot_date, end_time)  # type: ignore[arg-type]
    return int((end_dt - start_dt).total_seconds() // 60)


def _slot_to_public(db: Session, s: Slot) -> SlotPublic:
    at_dt = datetime.combine(s.date, s.start_time)
    display = float(min_resolved_price_across_services(db, at_dt))
    return SlotPublic(
        id=s.id,
        date=s.date,
        start_time=s.start_time.isoformat(),
        end_time=s.end_time.isoformat(),
        duration_minutes=_duration_minutes(s.date, s.start_time, s.end_time),
        price=display,
        is_available=s.is_available,
    )


@router.get("/slots", response_model=list[SlotPublic])
def list_public_slots(
    week: str = Query(..., description="ISO week YYYY-WW, e.g. 2026-11"),
    db: Session = Depends(get_db),
) -> list[SlotPublic]:
    try:
        monday, sunday = bounds_for_iso_week_string(week)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["query", "week"], "msg": str(e), "type": "value_error"}],
        ) from e

    rows = db.scalars(
        select(Slot)
        .where(Slot.date >= monday, Slot.date <= sunday)
        .order_by(Slot.date, Slot.start_time),
    ).all()
    return [_slot_to_public(db, s) for s in rows]


@router.get("/services", response_model=list[ServicePublic])
def list_public_services(db: Session = Depends(get_db)) -> list[ServicePublic]:
    rows = db.scalars(select(Service).order_by(Service.id)).all()
    return [ServicePublic.model_validate(r) for r in rows]


@router.get("/salon", response_model=SalonPublicOut)
def get_public_salon(db: Session = Depends(get_db)) -> Salon:
    s = db.scalar(select(Salon).order_by(Salon.id).limit(1))
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Salon not configured")
    return s


@router.get("/pricing-meta", response_model=PricingMetaOut)
def pricing_meta() -> PricingMetaOut:
    return PricingMetaOut(at_home_surcharge_eur=settings.at_home_display_surcharge_eur)


def _salon_snapshot(db: Session) -> str:
    s = db.scalar(select(Salon).order_by(Salon.id).limit(1))
    if s is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Salon not configured")
    return f"{s.name}, {s.address}"


def _total_price(db: Session, service_id: int, slot: Slot, location: Location) -> Decimal:
    at = datetime.combine(slot.date, slot.start_time)
    base = resolve_price_for_service(db, service_id, at)
    if location == Location.home:
        base = base + Decimal(str(settings.at_home_display_surcharge_eur))
    return base


def _send_confirmation_email(to: str, token: str) -> None:
    link = f"{settings.public_app_base_url.rstrip('/')}/book/edit/{token}"
    email_pkg.default_email_sender.send(
        to=to,
        subject="Your booking confirmation",
        body=f"Thanks for booking. Manage your appointment: {link}",
    )


@router.post("/bookings", response_model=BookingPublicOut, status_code=status.HTTP_201_CREATED)
def create_booking(body: CreateBookingBody, db: Session = Depends(get_db)) -> Booking:
    if body.location == Location.home and not (body.home_address and body.home_address.strip()):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="home_address required for home visits")

    slot = db.get(Slot, body.slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if not slot.is_available:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Slot not available")

    service = db.get(Service, body.service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Service not found")

    try:
        assert_slot_fits_service(slot, service)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    proposed = occupied_interval_for_booking(slot, service, body.location)
    if has_time_conflict(db, proposed):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Time conflict with another booking")

    token = secrets.token_urlsafe(24)
    address_snap = _salon_snapshot(db)
    price = _total_price(db, body.service_id, slot, body.location)

    b = Booking(
        slot_id=slot.id,
        service_id=body.service_id,
        price_at_booking=price,
        salon_address_at_booking=address_snap,
        location=body.location,
        home_address=body.home_address.strip() if body.home_address else None,
        client_name=body.client_name,
        client_email=str(body.client_email),
        client_phone=body.client_phone,
        status=BookingStatus.confirmed,
        edit_token=token,
    )
    slot.is_available = False
    db.add(b)
    db.commit()
    db.refresh(b)
    _send_confirmation_email(b.client_email, token)
    return b


def _booking_to_public(b: Booking) -> BookingPublicOut:
    return BookingPublicOut(
        id=b.id,
        slot_id=b.slot_id,
        service_id=b.service_id,
        location=b.location,
        home_address=b.home_address,
        client_name=b.client_name,
        client_email=b.client_email,
        client_phone=b.client_phone,
        status=b.status,
        price_at_booking=b.price_at_booking,
        salon_address_at_booking=b.salon_address_at_booking,
        edit_token=b.edit_token,
    )


@router.get("/bookings/by-token/{token}", response_model=BookingPublicOut)
def get_booking_by_token(token: str, db: Session = Depends(get_db)) -> BookingPublicOut:
    b = db.scalar(select(Booking).where(Booking.edit_token == token))
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return _booking_to_public(b)


@router.put("/bookings/by-token/{token}", response_model=BookingPublicOut)
def update_booking_by_token(token: str, body: UpdateBookingBody, db: Session = Depends(get_db)) -> BookingPublicOut:
    # US-005: edit_token stays stable so emailed links remain valid after edits.
    b = db.scalar(select(Booking).where(Booking.edit_token == token))
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if b.status == BookingStatus.cancelled:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Booking is cancelled")

    if body.location == Location.home and not (body.home_address and body.home_address.strip()):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="home_address required for home visits")

    new_slot = db.get(Slot, body.slot_id)
    if new_slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Slot not found")
    service = db.get(Service, body.service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Service not found")

    try:
        assert_slot_fits_service(new_slot, service)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    # Current slot treated as free for overlap (exclude this booking).
    proposed = occupied_interval_for_booking(new_slot, service, body.location)
    if has_time_conflict(db, proposed, exclude_booking_id=b.id):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Time conflict with another booking")

    old_slot = db.get(Slot, b.slot_id)
    if old_slot is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Slot missing")

    # If changing slot, ensure new slot is free or is the same slot.
    if new_slot.id != old_slot.id:
        if not new_slot.is_available:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Slot not available")
        old_slot.is_available = True
        new_slot.is_available = False

    b.slot_id = new_slot.id
    b.service_id = body.service_id
    b.location = body.location
    b.home_address = body.home_address.strip() if body.home_address else None
    b.client_name = body.client_name
    b.client_email = str(body.client_email)
    b.client_phone = body.client_phone
    b.status = BookingStatus.edited
    b.price_at_booking = _total_price(db, body.service_id, new_slot, body.location)
    b.salon_address_at_booking = _salon_snapshot(db)

    db.commit()
    db.refresh(b)
    return _booking_to_public(b)


@router.post("/bookings/by-token/{token}/cancel", status_code=status.HTTP_200_OK)
def cancel_booking(token: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Idempotent: second cancel returns 409 with clear message."""
    b = db.scalar(select(Booking).where(Booking.edit_token == token))
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if b.status == BookingStatus.cancelled:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Booking already cancelled")

    slot = db.get(Slot, b.slot_id)
    if slot:
        slot.is_available = True
    b.status = BookingStatus.cancelled
    db.commit()
    return {"status": "cancelled"}
