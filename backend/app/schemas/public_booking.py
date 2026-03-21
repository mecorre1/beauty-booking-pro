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
    marketing_opt_in: bool = False
    client_note: str | None = None
    current_hairstyle_media_id: int | None = None
    inspiration_media_id: int | None = None


class BookingPublicOut(BaseModel):
    id: int
    slot_id: int
    service_id: int
    location: Location
    home_address: str | None
    client_name: str
    client_email: str
    client_phone: str
    marketing_opt_in: bool
    client_note: str | None
    current_hairstyle_media_id: int | None
    inspiration_media_id: int | None
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
    marketing_opt_in: bool = False
    client_note: str | None = None
    current_hairstyle_media_id: int | None = None
    inspiration_media_id: int | None = None


class SalonPublicOut(BaseModel):
    name: str
    address: str
    phone: str
    email: str


class PricingMetaOut(BaseModel):
    at_home_surcharge_eur: float
