"""Admin: availability exceptions (US-016)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models.availability import AvailabilityException
from app.models.user import User
from app.schemas.admin_calendar import AvailabilityExceptionOut, ExceptionCreate

router = APIRouter()


@router.post("", response_model=AvailabilityExceptionOut, status_code=status.HTTP_201_CREATED)
def create_exception(
    body: ExceptionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> AvailabilityException:
    if body.start >= body.end:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start must be before end",
        )
    row = AvailabilityException(start=body.start, end=body.end, comment=body.comment)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exception(
    exception_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> None:
    row = db.get(AvailabilityException, exception_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Exception not found")
    db.delete(row)
    db.commit()
