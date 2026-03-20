from sqlalchemy import func, select

from app.models.service import Gender, Service, ServiceType


def test_get_services_returns_200_and_seeded_rows(client, db_session):
    response = client.get("/api/public/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    db_count = db_session.scalar(select(func.count()).select_from(Service))
    assert db_count == 6

    types = {row["type"] for row in data}
    genders = {row["gender"] for row in data}
    assert types == {"haircut", "haircut_hairdressing", "color"}
    assert genders == {"male", "female"}

    for row in data:
        assert "id" in row and isinstance(row["id"], int)
        assert "base_duration_minutes" in row and isinstance(row["base_duration_minutes"], int)
        assert row["type"] in ("haircut", "haircut_hairdressing", "color")
        assert row["gender"] in ("male", "female")
        assert "at_home_buffer_minutes" not in row
        assert "at_home_buffer" not in row

    first = data[0]
    assert set(first.keys()) == {"id", "type", "gender", "base_duration_minutes"}


def test_services_match_spec_enums_and_durations(db_session):
    """Stable seed: male haircut 30 min, female color 120 min, etc."""
    male_haircut = db_session.scalar(
        select(Service).where(Service.type == ServiceType.haircut, Service.gender == Gender.male),
    )
    assert male_haircut is not None
    assert male_haircut.base_duration_minutes == 30
    assert male_haircut.at_home_buffer_minutes == 30

    female_color = db_session.scalar(
        select(Service).where(Service.type == ServiceType.color, Service.gender == Gender.female),
    )
    assert female_color is not None
    assert female_color.base_duration_minutes == 120
