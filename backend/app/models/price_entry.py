"""ORM: PriceEntry — price per service over a datetime interval (SPEC)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PriceEntry(Base):
    __tablename__ = "price_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    service: Mapped["Service"] = relationship(back_populates="price_entries")
