"""US-015: computed availability from weekly hours, exceptions, and bookings."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models.availability import AvailabilityException, WeeklySchedule
from app.models.booking import Booking, BookingStatus, Location
from app.models.client import Client
from app.models.schedule import Slot
from app.models.service import Gender, Service, ServiceType


def _seed_mon_fri_9_18(db_session) -> None:
    for dow in range(5):
        db_session.add(
            WeeklySchedule(
                day_of_week=dow,
                open_time=time(9, 0),
                close_time=time(18, 0),
            ),
        )
    db_session.commit()


def _male_haircut_id(db_session) -> int:
    svc = db_session.scalar(
        select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male),
    )
    assert svc is not None
    return svc.id


def _female_haircut_id(db_session) -> int:
    svc = db_session.scalar(
        select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.female),
    )
    assert svc is not None
    return svc.id


def test_availability_excludes_exceptions(client, db_session):
    _seed_mon_fri_9_18(db_session)
    mon = date.fromisocalendar(2026, 11, 1)
    tue = mon + timedelta(days=1)
    db_session.add(
        AvailabilityException(
            start=datetime.combine(tue, time(12, 0)),
            end=datetime.combine(tue, time(17, 0)),
            comment="Afternoon off",
        ),
    )
    db_session.commit()

    sid = _female_haircut_id(db_session)
    r = client.get("/api/public/availability", params={"service_id": sid, "week": "2026-11"})
    assert r.status_code == 200
    tue_rows = [w for w in r.json() if w["date"] == tue.isoformat()]
    assert sorted((w["start_time"], w["end_time"]) for w in tue_rows) == [
        ("09:00:00", "12:00:00"),
        ("17:00:00", "18:00:00"),
    ]


def test_availability_excludes_short_windows(client, db_session):
    db_session.add(
        WeeklySchedule(day_of_week=0, open_time=time(9, 0), close_time=time(9, 30)),
    )
    db_session.commit()

    sid = _female_haircut_id(db_session)
    mon = date.fromisocalendar(2026, 15, 1)
    assert mon.weekday() == 0

    r = client.get("/api/public/availability", params={"service_id": sid, "week": "2026-15"})
    assert r.status_code == 200
    assert r.json() == []


def test_availability_excludes_booked_slots(client, db_session):
    _seed_mon_fri_9_18(db_session)
    mon = date.fromisocalendar(2026, 22, 1)

    cli = Client(email="avail@test.com", name="A", phone="1")
    db_session.add(cli)
    db_session.commit()

    slot = Slot(
        date=mon,
        start_time=time(10, 0),
        end_time=time(11, 0),
        is_available=False,
    )
    db_session.add(slot)
    db_session.commit()

    sid = _male_haircut_id(db_session)
    db_session.add(
        Booking(
            slot_id=slot.id,
            service_id=sid,
            client_id=cli.id,
            price_at_booking=Decimal("35.00"),
            salon_address_at_booking="Test",
            location=Location.salon,
            status=BookingStatus.confirmed,
            edit_token="tok_avail_booked_1",
        ),
    )
    db_session.commit()

    r = client.get("/api/public/availability", params={"service_id": sid, "week": "2026-22"})
    assert r.status_code == 200
    mon_rows = [w for w in r.json() if w["date"] == mon.isoformat()]
    assert sorted((w["start_time"], w["end_time"]) for w in mon_rows) == [
        ("09:00:00", "10:00:00"),
        ("10:30:00", "18:00:00"),
    ]


def test_availability_unknown_service_404(client, db_session):
    db_session.commit()
    r = client.get("/api/public/availability", params={"service_id": 99999, "week": "2026-11"})
    assert r.status_code == 404
