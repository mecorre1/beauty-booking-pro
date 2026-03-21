"""ORM: WeeklyTemplate, TemplateSlot, Slot per SPEC."""

from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class WeeklyTemplate(Base):
    __tablename__ = "weekly_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    template_slots: Mapped[list["TemplateSlot"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
    )


class TemplateSlot(Base):
    """day_of_week: 0=Monday … 6=Sunday (ISO-style)."""

    __tablename__ = "template_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("weekly_templates.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    template: Mapped["WeeklyTemplate"] = relationship(back_populates="template_slots")


class Slot(Base):
    """Bookable time window; display price comes from PriceEntry (US-012)."""

    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("weekly_templates.id"),
        nullable=True,
    )

    booking: Mapped["Booking | None"] = relationship(  # noqa: F821
        back_populates="slot",
        uselist=False,
    )
