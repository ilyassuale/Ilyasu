"""Auth API tests."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_register_and_login(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePass123", "full_name": "Test User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["email"] == "test@example.com"

    resp = await client.post(
        "/api/v1/auth/login/json",
        json={"email": "test@example.com", "password": "SecurePass123"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "test@example.com"


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_with_auth(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "password": "SecurePass123", "full_name": "Me"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_refresh_token(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "SecurePass123", "full_name": "Refresh"},
    )
    assert resp.status_code == 201
    refresh_token = resp.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_rbac_role_enforcement(client):
    # Candidate cannot access recruiter endpoints
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate@example.com",
            "password": "SecurePass123",
            "full_name": "Candidate",
            "role": "candidate",
        },
    )
    assert resp.status_code in (200, 201)
    token = resp.json()["access_token"]
    resp = await client.get("/api/v1/recruiter/candidates", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
