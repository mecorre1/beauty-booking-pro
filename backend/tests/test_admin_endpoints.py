"""US-008/009/010/011/012: admin endpoints require auth; basic happy paths."""

from datetime import date, time
from decimal import Decimal

from sqlalchemy import select

from app.models.schedule import Slot
from app.models.service import Gender, Service, ServiceType


def _auth_header(client, db_session) -> dict[str, str]:
    client.post("/api/admin/auth/register", json={"email": "owner@test.com", "password": "password12"})
    tok = client.post(
        "/api/admin/auth/login",
        json={"email": "owner@test.com", "password": "password12"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_admin_bookings_requires_auth(client, db_session):
    assert client.get("/api/admin/bookings").status_code == 401


def test_admin_calendar_requires_auth(client, db_session):
    assert client.get("/api/admin/bookings/calendar?week=2030-01").status_code == 401


def test_admin_schedule_apply_requires_auth(client, db_session):
    r = client.post("/api/admin/schedule/apply", json={"template_id": 1, "week": "2030-01"})
    assert r.status_code == 401


def test_admin_salon_requires_auth(client, db_session):
    assert client.get("/api/admin/salon").status_code == 401


def test_admin_price_entries_requires_auth(client, db_session):
    assert client.get("/api/admin/services/price-entries").status_code == 401


def test_admin_bookings_lists_created_booking(client, db_session):
    hdr = _auth_header(client, db_session)
    slot = Slot(
        date=date(2040, 1, 1),
        start_time=time(9, 0),
        end_time=time(12, 0),
        is_available=True,
        price=Decimal("40.00"),
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
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
    r = client.get("/api/admin/bookings?upcoming=true", headers=hdr)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert data[0]["client_email"] == "ada@test.com"


def test_admin_calendar_week_authed(client, db_session):
    hdr = _auth_header(client, db_session)
    r = client.get("/api/admin/bookings/calendar?week=2040-01", headers=hdr)
    assert r.status_code == 200
    assert "slots" in r.json()


def test_apply_template_creates_slots(client, db_session):
    hdr = _auth_header(client, db_session)
    created = client.post(
        "/api/admin/schedule/templates",
        headers={**hdr, "Content-Type": "application/json"},
        json={
            "name": "T",
            "slots": [{"day_of_week": 0, "start_time": "09:00", "duration_minutes": 60}],
        },
    )
    assert created.status_code == 201
    tid = created.json()["id"]
    r = client.post(
        "/api/admin/schedule/apply",
        headers={**hdr, "Content-Type": "application/json"},
        json={"template_id": tid, "week": "2040-05"},
    )
    assert r.status_code == 201
    assert r.json()["slots_created"] >= 1


def test_salon_put_updates_row(client, db_session):
    hdr = _auth_header(client, db_session)
    r = client.put(
        "/api/admin/salon",
        headers={**hdr, "Content-Type": "application/json"},
        json={
            "name": "New Name",
            "address": "Addr",
            "phone": "123",
            "email": "e@e.com",
        },
    )
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"
    pub = client.get("/api/public/salon")
    assert pub.status_code == 200
    assert pub.json()["name"] == "New Name"


def test_list_price_entries(client, db_session):
    hdr = _auth_header(client, db_session)
    r = client.get("/api/admin/services/price-entries", headers=hdr)
    assert r.status_code == 200
    assert len(r.json()) >= 6


def test_create_price_entry_overlap_rejected(client, db_session):
    """Open-ended default rows overlap any new finite interval — expect 409."""
    hdr = _auth_header(client, db_session)
    svc = db_session.scalar(select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male))
    r = client.post(
        "/api/admin/services/price-entries",
        headers={**hdr, "Content-Type": "application/json"},
        json={
            "service_id": svc.id,
            "valid_from": "2045-01-01T00:00:00",
            "valid_to": "2045-06-01T00:00:00",
            "price": "99.00",
        },
    )
    assert r.status_code == 409
