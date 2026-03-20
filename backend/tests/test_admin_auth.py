"""US-007: admin authentication."""

import pytest


def test_register_then_login(client, db_session):
    r = client.post("/api/admin/auth/register", json={"email": "admin@test.com", "password": "password12"})
    assert r.status_code == 201
    assert r.json()["access_token"]

    r2 = client.post("/api/admin/auth/login", json={"email": "admin@test.com", "password": "password12"})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_register_twice_forbidden(client, db_session):
    client.post("/api/admin/auth/register", json={"email": "a@a.com", "password": "password12"})
    r = client.post("/api/admin/auth/register", json={"email": "b@b.com", "password": "password12"})
    assert r.status_code == 403


def test_login_failure(client, db_session):
    r = client.post("/api/admin/auth/login", json={"email": "nope@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_protected_route_without_token(client, db_session):
    r = client.get("/api/admin/salon")
    assert r.status_code == 401


def test_protected_route_with_token(client, db_session):
    client.post("/api/admin/auth/register", json={"email": "admin@test.com", "password": "password12"})
    tok = client.post(
        "/api/admin/auth/login",
        json={"email": "admin@test.com", "password": "password12"},
    ).json()["access_token"]
    r = client.get("/api/admin/salon", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
