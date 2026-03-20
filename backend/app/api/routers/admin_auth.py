"""Admin email/password authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth import create_access_token, hash_password, verify_password
from app.models.user import User

router = APIRouter()


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterBody, db: Session = Depends(get_db)) -> TokenOut:
    n = db.scalar(select(func.count()).select_from(User)) or 0
    if n > 0:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Registration disabled")
    user = User(email=body.email.lower(), hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id))
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
def login(body: LoginBody, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=str(user.id))
    return TokenOut(access_token=token)
