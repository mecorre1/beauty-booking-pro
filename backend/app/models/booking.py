"""ORM: Booking per SPEC."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Location(str, Enum):
    salon = "salon"
    home = "home"


class BookingStatus(str, Enum):
    confirmed = "confirmed"
    edited = "edited"
    cancelled = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("edit_token", name="uq_bookings_edit_token"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), nullable=False, unique=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    price_at_booking: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    salon_address_at_booking: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Location] = mapped_column(
        SAEnum(Location, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    home_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BookingStatus.confirmed,
    )
    edit_token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    slot: Mapped["Slot"] = relationship(back_populates="booking", foreign_keys=[slot_id])
    service: Mapped["Service"] = relationship()
