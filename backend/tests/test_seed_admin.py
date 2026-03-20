"""Bootstrap admin seed (US-007)."""

from sqlalchemy import func, select

from app.config import settings
from app.models.user import User
from app.seed_admin import seed_bootstrap_admin


def test_seed_bootstrap_admin_creates_user_when_empty(db_session, monkeypatch):
    monkeypatch.setattr(settings, "bootstrap_admin_email", "bootstrap@test.com")
    monkeypatch.setattr(settings, "bootstrap_admin_password", "password12")
    seed_bootstrap_admin(db_session)
    n = db_session.scalar(select(func.count()).select_from(User)) or 0
    assert n == 1
    u = db_session.scalar(select(User).where(User.email == "bootstrap@test.com"))
    assert u is not None


def test_seed_bootstrap_admin_skips_when_users_exist(db_session, monkeypatch):
    monkeypatch.setattr(settings, "bootstrap_admin_email", "bootstrap@test.com")
    monkeypatch.setattr(settings, "bootstrap_admin_password", "password12")
    seed_bootstrap_admin(db_session)
    seed_bootstrap_admin(db_session)
    n = db_session.scalar(select(func.count()).select_from(User)) or 0
    assert n == 1


def test_seed_bootstrap_admin_skips_when_disabled(db_session, monkeypatch):
    monkeypatch.setattr(settings, "bootstrap_admin_email", "")
    monkeypatch.setattr(settings, "bootstrap_admin_password", "")
    seed_bootstrap_admin(db_session)
    n = db_session.scalar(select(func.count()).select_from(User)) or 0
    assert n == 0
