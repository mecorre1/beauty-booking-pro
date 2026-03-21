"""ORM: default weekly hours and exceptions (SPEC + US-015)."""

from datetime import datetime, time

from sqlalchemy import DateTime, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WeeklySchedule(Base):
    """One open/close window per weekday (0=Monday … 6=Sunday)."""

    __tablename__ = "weekly_schedules"
    __table_args__ = (UniqueConstraint("day_of_week", name="uq_weekly_schedules_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)


class AvailabilityException(Base):
    __tablename__ = "availability_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
