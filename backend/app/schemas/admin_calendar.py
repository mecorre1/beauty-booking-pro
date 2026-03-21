"""Admin weekly calendar API payloads (US-016)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus


class DayScheduleOut(BaseModel):
    """One column in the week: calendar date + default hours for that weekday."""

    date: date
    day_of_week: int = Field(description="0=Monday … 6=Sunday")
    open_time: str | None = Field(description="HH:MM:SS when open; null = no default hours")
    close_time: str | None = None


class AvailabilityExceptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start: datetime
    end: datetime
    created_at: datetime
    comment: str | None


class ExceptionCreate(BaseModel):
    start: datetime
    end: datetime
    comment: str | None = None


class AdminScheduleBookingOut(BaseModel):
    id: int
    start: datetime
    end: datetime
    client_name: str
    client_email: str
    client_phone: str
    service_type: str
    location: str
    status: BookingStatus
    slot_id: int


class AdminScheduleWeekOut(BaseModel):
    week: str
    days: list[DayScheduleOut]
    exceptions: list[AvailabilityExceptionOut]
    bookings: list[AdminScheduleBookingOut]


class WeeklyScheduleUpdate(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday … 6=Sunday")
    open_time: str = Field(description="HH:MM or HH:MM:SS")
    close_time: str = Field(description="HH:MM or HH:MM:SS")


class WeeklyScheduleDayOut(BaseModel):
    day_of_week: int
    open_time: str
    close_time: str
