"""Public API schemas for slot listing (US-001)."""

import re
from datetime import date, datetime, timedelta

from pydantic import BaseModel, Field

ISO_WEEK_RE = re.compile(r"^(\d{4})-(\d{2})$")


def bounds_for_iso_week_string(week: str) -> tuple[date, date]:
    """Parse `YYYY-WW` (ISO week number, 01–53) and return Monday and Sunday dates inclusive."""
    m = ISO_WEEK_RE.match(week.strip())
    if not m:
        msg = "week must match YYYY-WW (e.g. 2026-11)"
        raise ValueError(msg)
    year, w = int(m.group(1)), int(m.group(2))
    if w < 1 or w > 53:
        msg = "week number must be between 01 and 53"
        raise ValueError(msg)
    try:
        monday = date.fromisocalendar(year, w, 1)
    except ValueError as exc:
        msg = "invalid ISO calendar week for that year"
        raise ValueError(msg) from exc
    sunday = monday + timedelta(days=6)
    return monday, sunday


class SlotPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    date: date
    start_time: str = Field(description="HH:MM:SS")
    end_time: str = Field(description="HH:MM:SS")
    duration_minutes: int
    price: float
    is_available: bool
