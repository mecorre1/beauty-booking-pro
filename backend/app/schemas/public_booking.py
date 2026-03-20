"""Public booking API schemas."""

from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.booking import BookingStatus, Location


class CreateBookingBody(BaseModel):
    slot_id: int
    service_id: int
    location: Location
    home_address: str | None = None
    client_name: str = Field(min_length=1, max_length=255)
    client_email: EmailStr
    client_phone: str = Field(min_length=3, max_length=64)


class BookingPublicOut(BaseModel):
    id: int
    slot_id: int
    service_id: int
    location: Location
    home_address: str | None
    client_name: str
    client_email: str
    client_phone: str
    status: BookingStatus
    price_at_booking: Decimal
    salon_address_at_booking: str
    edit_token: str


class UpdateBookingBody(BaseModel):
    slot_id: int
    service_id: int
    location: Location
    home_address: str | None = None
    client_name: str = Field(min_length=1, max_length=255)
    client_email: EmailStr
    client_phone: str = Field(min_length=3, max_length=64)


class SalonPublicOut(BaseModel):
    name: str
    address: str
    phone: str
    email: str


class PricingMetaOut(BaseModel):
    at_home_surcharge_eur: float
