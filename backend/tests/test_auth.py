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
