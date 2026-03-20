from datetime import date

from sqlalchemy import func, select

from app.models.schedule import Slot
from app.schemas.public_slots import bounds_for_iso_week_string
from app.seed_dev_slots import seed_demo_slots


def test_seed_dev_slots_row_count_and_week_coverage(db_session):
    """In-memory DB: seed clears prior slots and fills current + next ISO week."""
    fixed_today = date(2026, 3, 18)
    y, w, _ = fixed_today.isocalendar()
    week_label = f"{y}-{w:02d}"

    n = seed_demo_slots(db_session, today=fixed_today)
    assert n == 10

    total = db_session.scalar(select(func.count()).select_from(Slot))
    assert total == 10

    monday, sunday = bounds_for_iso_week_string(week_label)
    in_week = db_session.scalars(
        select(Slot).where(Slot.date >= monday, Slot.date <= sunday),
    ).all()
    assert len(in_week) == 5
    assert any(s.is_available for s in in_week)
    assert any(not s.is_available for s in in_week)


def test_seed_dev_slots_api_returns_non_empty_current_week(client, db_session):
    fixed_today = date(2026, 3, 18)
    y, w, _ = fixed_today.isocalendar()
    week_label = f"{y}-{w:02d}"

    seed_demo_slots(db_session, today=fixed_today)

    response = client.get("/api/public/slots", params={"week": week_label})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    row = data[0]
    for key in ("date", "start_time", "end_time", "duration_minutes", "price", "is_available"):
        assert key in row


def test_seed_dev_slots_is_idempotent_replace(db_session):
    seed_demo_slots(db_session, today=date(2026, 3, 18))
    first = db_session.scalar(select(func.count()).select_from(Slot))
    seed_demo_slots(db_session, today=date(2026, 3, 18))
    second = db_session.scalar(select(func.count()).select_from(Slot))
    assert first == second == 10
