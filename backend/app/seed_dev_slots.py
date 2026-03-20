"""Dev-only: clear `slots` and insert deterministic demo rows for this and next ISO week (US-003)."""

from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db import SessionLocal, init_db
from app.models.schedule import Slot


def _this_and_next_iso_week(today: date) -> tuple[tuple[int, int], tuple[int, int]]:
    y, w, _ = today.isocalendar()
    monday = date.fromisocalendar(y, w, 1)
    next_monday = monday + timedelta(weeks=1)
    ny, nw, _ = next_monday.isocalendar()
    return (y, w), (ny, nw)


def _slots_for_iso_week(year: int, week: int) -> list[Slot]:
    """Fixed pattern per week: Mon (2), Tue (1), Thu (2) with mixed price and availability."""
    monday = date.fromisocalendar(year, week, 1)
    specs: list[tuple[int, int, int, int, int, str, bool]] = [
        (0, 9, 0, 9, 45, "48.00", True),  # Mon
        (0, 11, 30, 12, 15, "52.50", False),  # Mon
        (1, 10, 0, 11, 0, "45.00", True),  # Tue
        (3, 14, 0, 15, 30, "60.00", True),  # Thu
        (3, 16, 0, 16, 30, "35.00", False),  # Thu
    ]
    rows: list[Slot] = []
    for day_off, sh, sm, eh, em, price, avail in specs:
        d = monday + timedelta(days=day_off)
        rows.append(
            Slot(
                date=d,
                start_time=time(sh, sm),
                end_time=time(eh, em),
                is_available=avail,
                source_template_id=None,
                price=Decimal(price),
            ),
        )
    return rows


def seed_demo_slots(session: Session, *, today: date | None = None) -> int:
    """Delete all slots, insert demo data for current and next ISO week. Returns rows inserted."""
    if today is None:
        today = date.today()
    (y1, w1), (y2, w2) = _this_and_next_iso_week(today)
    session.execute(delete(Slot))
    batch = _slots_for_iso_week(y1, w1) + _slots_for_iso_week(y2, w2)
    session.add_all(batch)
    session.commit()
    return len(batch)


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        n = seed_demo_slots(db)
        print(f"Seeded {n} demo slot(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
