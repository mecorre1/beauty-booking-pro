from datetime import date, time, timedelta
from decimal import Decimal

from app.models.schedule import Slot


def _iso_week_label(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-{w:02d}"


def test_get_slots_returns_correct_week(client, db_session):
    """Only slots whose date falls in the requested ISO week are returned."""
    week_a_monday = date.fromisocalendar(2026, 11, 1)
    week_b_date = week_a_monday + timedelta(weeks=1)
    assert _iso_week_label(week_a_monday) == "2026-11"
    assert _iso_week_label(week_b_date) != "2026-11"

    in_week = Slot(
        date=week_a_monday,
        start_time=time(9, 0),
        end_time=time(9, 45),
        is_available=True,
        price=Decimal("45.00"),
    )
    other_week = Slot(
        date=week_b_date,
        start_time=time(10, 0),
        end_time=time(10, 30),
        is_available=False,
        price=Decimal("50.00"),
    )
    db_session.add_all([in_week, other_week])
    db_session.commit()

    response = client.get("/api/public/slots", params={"week": "2026-11"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    row = data[0]
    assert row["id"] == in_week.id
    assert row["date"] == week_a_monday.isoformat()
    assert row["start_time"] == "09:00:00"
    assert row["end_time"] == "09:45:00"
    assert row["duration_minutes"] == 45
    # US-012: list price is min resolved PriceEntry across services at slot start.
    assert row["price"] == 35.0
    assert row["is_available"] is True


def test_get_slots_empty_week_returns_200(client, db_session):
    db_session.commit()
    response = client.get("/api/public/slots", params={"week": "2030-01"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_slots_invalid_week_returns_422(client, db_session):
    db_session.commit()
    response = client.get("/api/public/slots", params={"week": "2030-99"})
    assert response.status_code == 422

    response2 = client.get("/api/public/slots", params={"week": "bad"})
    assert response2.status_code == 422


def test_get_slots_ordering(client, db_session):
    mon = date.fromisocalendar(2026, 20, 1)
    later = mon + timedelta(days=1)
    db_session.add(
        Slot(
            date=later,
            start_time=time(14, 0),
            end_time=time(15, 0),
            is_available=True,
            price=Decimal("40.00"),
        ),
    )
    db_session.add(
        Slot(
            date=mon,
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_available=True,
            price=Decimal("40.00"),
        ),
    )
    db_session.commit()

    response = client.get("/api/public/slots", params={"week": "2026-20"})
    assert response.status_code == 200
    dates = [row["date"] for row in response.json()]
    assert dates == [mon.isoformat(), later.isoformat()]
