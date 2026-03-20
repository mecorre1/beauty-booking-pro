"""US-004/005/006: public booking lifecycle."""

from datetime import date, time
from decimal import Decimal

from sqlalchemy import select

from app.models.booking import Booking, BookingStatus, Location
from app.models.schedule import Slot
from app.models.service import Gender, Service, ServiceType


def _make_slot(
    db_session,
    *,
    avail: bool = True,
    d: date | None = None,
    start: time | None = None,
    end: time | None = None,
) -> Slot:
    day = d or date(2030, 6, 3)
    st = start or time(9, 0)
    en = end or time(12, 0)
    s = Slot(
        date=day,
        start_time=st,
        end_time=en,
        is_available=avail,
        price=Decimal("40.00"),
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def test_create_booking_happy_path(client, db_session):
    slot = _make_slot(db_session)
    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
    assert svc is not None

    body = {
        "slot_id": slot.id,
        "service_id": svc.id,
        "location": "salon",
        "client_name": "Ada",
        "client_email": "ada@test.com",
        "client_phone": "555",
    }
    r = client.post("/api/public/bookings", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "confirmed"
    assert data["edit_token"]

    db_session.refresh(slot)
    assert slot.is_available is False
    b = db_session.scalar(select(Booking).where(Booking.slot_id == slot.id))
    assert b is not None
    assert b.price_at_booking is not None


def test_double_booking_same_slot_409(client, db_session):
    slot = _make_slot(db_session)
    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
    body = {
        "slot_id": slot.id,
        "service_id": svc.id,
        "location": "salon",
        "client_name": "Ada",
        "client_email": "ada@test.com",
        "client_phone": "555",
    }
    assert client.post("/api/public/bookings", json=body).status_code == 201
    r2 = client.post("/api/public/bookings", json=body)
    assert r2.status_code == 409


def test_home_booking_blocks_overlap(client, db_session):
    """Two slots back-to-back: home booking on first extends buffer into second."""
    s1 = Slot(
        date=date(2030, 7, 1),
        start_time=time(9, 0),
        end_time=time(9, 45),
        is_available=True,
        price=Decimal("40.00"),
    )
    s2 = Slot(
        date=date(2030, 7, 1),
        start_time=time(9, 45),
        end_time=time(10, 30),
        is_available=True,
        price=Decimal("40.00"),
    )
    db_session.add_all([s1, s2])
    db_session.commit()
    db_session.refresh(s1)
    db_session.refresh(s2)

    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
    r1 = client.post(
        "/api/public/bookings",
        json={
            "slot_id": s1.id,
            "service_id": svc.id,
            "location": "home",
            "home_address": "1 Main St",
            "client_name": "A",
            "client_email": "a@test.com",
            "client_phone": "555",
        },
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/public/bookings",
        json={
            "slot_id": s2.id,
            "service_id": svc.id,
            "location": "salon",
            "client_name": "B",
            "client_email": "b@test.com",
            "client_phone": "556",
        },
    )
    assert r2.status_code == 409


def test_confirmation_email_attempted(client, db_session):
    from app import email as email_mod

    prev = email_mod.default_email_sender
    email_mod.default_email_sender = email_mod.LoggingEmailSender(also_print=False)
    try:
        slot = _make_slot(db_session)
        svc = db_session.scalar(
            select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male),
        )
        client.post(
            "/api/public/bookings",
            json={
                "slot_id": slot.id,
                "service_id": svc.id,
                "location": "salon",
                "client_name": "Ada",
                "client_email": "ada@test.com",
                "client_phone": "555",
            },
        )
        sender = email_mod.default_email_sender
        assert isinstance(sender, email_mod.LoggingEmailSender)
        assert sender.last_subject and "booking" in sender.last_subject.lower()
        assert sender.last_body and "/book/edit/" in sender.last_body
    finally:
        email_mod.default_email_sender = prev


def test_edit_booking_swaps_slot(client, db_session):
    s1 = _make_slot(db_session, start=time(9, 0), end=time(10, 0))
    s2 = _make_slot(db_session, start=time(11, 0), end=time(12, 0))
    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
    created = client.post(
        "/api/public/bookings",
        json={
            "slot_id": s1.id,
            "service_id": svc.id,
            "location": "salon",
            "client_name": "Ada",
            "client_email": "ada@test.com",
            "client_phone": "555",
        },
    ).json()
    token = created["edit_token"]

    db_session.refresh(s1)
    db_session.refresh(s2)
    assert s1.is_available is False and s2.is_available is True

    r = client.put(
        f"/api/public/bookings/by-token/{token}",
        json={
            "slot_id": s2.id,
            "service_id": svc.id,
            "location": "salon",
            "client_name": "Ada",
            "client_email": "ada@test.com",
            "client_phone": "555",
        },
    )
    assert r.status_code == 200
    db_session.refresh(s1)
    db_session.refresh(s2)
    assert s1.is_available is True and s2.is_available is False


def test_cannot_edit_cancelled(client, db_session):
    slot = _make_slot(db_session)
    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
    tok = client.post(
        "/api/public/bookings",
        json={
            "slot_id": slot.id,
            "service_id": svc.id,
            "location": "salon",
            "client_name": "Ada",
            "client_email": "ada@test.com",
            "client_phone": "555",
        },
    ).json()["edit_token"]
    assert client.post(f"/api/public/bookings/by-token/{tok}/cancel").status_code == 200
    r = client.put(
        f"/api/public/bookings/by-token/{tok}",
        json={
            "slot_id": slot.id,
            "service_id": svc.id,
            "location": "salon",
            "client_name": "Ada",
            "client_email": "ada@test.com",
            "client_phone": "555",
        },
    )
    assert r.status_code == 409


def test_cancel_restores_slot_and_idempotent(client, db_session):
    slot = _make_slot(db_session)
    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
    tok = client.post(
        "/api/public/bookings",
        json={
            "slot_id": slot.id,
            "service_id": svc.id,
            "location": "salon",
            "client_name": "Ada",
            "client_email": "ada@test.com",
            "client_phone": "555",
        },
    ).json()["edit_token"]
    assert client.post(f"/api/public/bookings/by-token/{tok}/cancel").status_code == 200
    db_session.refresh(slot)
    assert slot.is_available is True
    r2 = client.post(f"/api/public/bookings/by-token/{tok}/cancel")
    assert r2.status_code == 409
