from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.db import SessionLocal
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_admin_user(
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(creds.credentials)
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = db.get(User, int(sub))
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — map JWT errors to 401
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
