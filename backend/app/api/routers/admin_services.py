"""Admin: services and price entries."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models.price_entry import PriceEntry
from app.models.service import Service
from app.models.user import User
from app.services.pricing import assert_no_overlapping_price_entry

router = APIRouter()


class PriceEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    valid_from: datetime
    valid_to: datetime | None
    price: Decimal


class PriceEntryCreate(BaseModel):
    service_id: int
    valid_from: datetime
    valid_to: datetime | None = None
    price: Decimal = Field(gt=0)


@router.get("/price-entries", response_model=list[PriceEntryRead])
def list_price_entries(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> list[PriceEntry]:
    return list(db.scalars(select(PriceEntry).order_by(PriceEntry.service_id, PriceEntry.valid_from)).all())


@router.post("/price-entries", response_model=PriceEntryRead, status_code=status.HTTP_201_CREATED)
def create_price_entry(
    body: PriceEntryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> PriceEntry:
    svc = db.get(Service, body.service_id)
    if svc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Service not found")
    try:
        assert_no_overlapping_price_entry(
            db,
            service_id=body.service_id,
            valid_from=body.valid_from,
            valid_to=body.valid_to,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e
    row = PriceEntry(
        service_id=body.service_id,
        valid_from=body.valid_from,
        valid_to=body.valid_to,
        price=body.price,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
