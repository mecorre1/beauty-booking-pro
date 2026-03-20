"""Admin: salon entity CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models.salon import Salon
from app.models.user import User

router = APIRouter()


class SalonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    phone: str
    email: str


class SalonUpdate(BaseModel):
    name: str
    address: str
    phone: str
    email: str


def _single_salon(db: Session) -> Salon:
    row = db.scalar(select(Salon).order_by(Salon.id).limit(1))
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Salon not found")
    return row


@router.get("", response_model=SalonRead)
def get_salon_admin(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> Salon:
    return _single_salon(db)


@router.put("", response_model=SalonRead)
def put_salon(
    body: SalonUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> Salon:
    s = _single_salon(db)
    s.name = body.name
    s.address = body.address
    s.phone = body.phone
    s.email = body.email
    db.commit()
    db.refresh(s)
    return s
