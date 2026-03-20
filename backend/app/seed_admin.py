"""Optional bootstrap admin user from env (US-007)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.models.user import User


def seed_bootstrap_admin(session: Session) -> None:
    email = (settings.bootstrap_admin_email or "").strip().lower()
    pwd = settings.bootstrap_admin_password
    if not email or not pwd:
        return
    n = session.scalar(select(func.count()).select_from(User)) or 0
    if n > 0:
        return
    session.add(
        User(
            email=email,
            hashed_password=hash_password(pwd),
        ),
    )
    session.commit()
