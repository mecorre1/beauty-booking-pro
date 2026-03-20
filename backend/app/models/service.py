"""ORM: Service per SPEC."""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SAEnum, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ServiceType(str, Enum):
    haircut = "haircut"
    haircut_hairdressing = "haircut_hairdressing"
    color = "color"


class Gender(str, Enum):
    male = "male"
    female = "female"


class Service(Base):
    """One row per (type, gender); duration may differ by gender per SPEC."""

    __tablename__ = "services"
    __table_args__ = (UniqueConstraint("type", "gender", name="uq_service_type_gender"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[ServiceType] = mapped_column(
        SAEnum(ServiceType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    gender: Mapped[Gender] = mapped_column(
        SAEnum(Gender, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    base_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    # Internal-only in SPEC; not exposed on public JSON.
    at_home_buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    price_entries: Mapped[list["PriceEntry"]] = relationship(back_populates="service")  # noqa: F821
