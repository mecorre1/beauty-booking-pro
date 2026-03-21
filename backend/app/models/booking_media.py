"""ORM: BookingMedia per SPEC (stored file id + type + original name)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MediaType(str, Enum):
    current_hairstyle = "current_hairstyle"
    inspiration = "inspiration"


class BookingMedia(Base):
    __tablename__ = "booking_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    media_type: Mapped[MediaType] = mapped_column(
        SAEnum(MediaType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
