"""US-016: admin weekly schedule, exceptions, bookings layers."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models.availability import AvailabilityException, WeeklySchedule
from app.models.booking import Booking, BookingStatus, Location
from app.models.client import Client
from app.models.schedule import Slot
from app.models.service import Gender, Service, ServiceType


def _auth_header(client, db_session) -> dict[str, str]:
    client.post("/api/admin/auth/register", json={"email": "owner@test.com", "password": "password12"})
    tok = client.post(
        "/api/admin/auth/login",
        json={"email": "owner@test.com", "password": "password12"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_admin_schedule_week_requires_auth(client, db_session):
    assert client.get("/api/admin/schedule?week=2026-11").status_code == 401


def test_admin_exceptions_require_auth(client, db_session):
    r = client.post(
        "/api/admin/exceptions",
        json={
            "start": "2026-06-01T10:00:00",
            "end": "2026-06-01T12:00:00",
        },
    )
    assert r.status_code == 401


def test_get_schedule_returns_all_layers(client, db_session):
    hdr = _auth_header(client, db_session)
    mon = date.fromisocalendar(2026, 20, 1)
    for dow in range(5):
        db_session.add(
            WeeklySchedule(
                day_of_week=dow,
                open_time=time(9, 0),
                close_time=time(18, 0),
            ),
        )
    tue = mon + timedelta(days=1)
    db_session.add(
        AvailabilityException(
            start=datetime.combine(tue, time(12, 0)),
            end=datetime.combine(tue, time(14, 0)),
            comment="Lunch",
        ),
    )
    cli = Client(email="cal@test.com", name="Cal Client", phone="1")
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

    svc = db_session.scalar(
        select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male),
    )
    assert svc is not None
    db_session.add(
        Booking(
            slot_id=slot.id,
            service_id=svc.id,
            client_id=cli.id,
            price_at_booking=Decimal("35.00"),
            salon_address_at_booking="Salon",
            location=Location.salon,
            status=BookingStatus.confirmed,
            edit_token="tok_cal_layer_1",
        ),
    )
    db_session.commit()

    r = client.get("/api/admin/schedule?week=2026-20", headers=hdr)
    assert r.status_code == 200
    data = r.json()
    assert len(data["days"]) == 7
    mon_row = next(d for d in data["days"] if d["date"] == mon.isoformat())
    assert mon_row["open_time"] == "09:00:00"
    assert mon_row["close_time"] == "18:00:00"
    assert len(data["exceptions"]) == 1
    assert data["exceptions"][0]["comment"] == "Lunch"
    assert len(data["bookings"]) == 1
    assert data["bookings"][0]["client_email"] == "cal@test.com"
    assert data["bookings"][0]["client_name"] == "Cal Client"


def test_create_exception_persists(client, db_session):
    hdr = _auth_header(client, db_session)
    r = client.post(
        "/api/admin/exceptions",
        headers={**hdr, "Content-Type": "application/json"},
        json={
            "start": "2031-05-04T15:00:00",
            "end": "2031-05-04T16:30:00",
            "comment": "Private",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["comment"] == "Private"
    eid = body["id"]

    row = db_session.get(AvailabilityException, eid)
    assert row is not None
    assert row.comment == "Private"

    del_r = client.delete(f"/api/admin/exceptions/{eid}", headers=hdr)
    assert del_r.status_code == 204
    assert db_session.get(AvailabilityException, eid) is None


def test_put_weekly_hours_upserts(client, db_session):
    hdr = _auth_header(client, db_session)
    r = client.put(
        "/api/admin/schedule",
        headers={**hdr, "Content-Type": "application/json"},
        json={"day_of_week": 2, "open_time": "08:30", "close_time": "19:00"},
    )
    assert r.status_code == 200
    assert r.json() == {
        "day_of_week": 2,
        "open_time": "08:30:00",
        "close_time": "19:00:00",
    }
    r2 = client.put(
        "/api/admin/schedule",
        headers={**hdr, "Content-Type": "application/json"},
        json={"day_of_week": 2, "open_time": "09:00", "close_time": "17:00"},
    )
    assert r2.status_code == 200
    rows = db_session.scalars(select(WeeklySchedule).where(WeeklySchedule.day_of_week == 2)).all()
    assert len(rows) == 1
    assert rows[0].open_time == time(9, 0)
