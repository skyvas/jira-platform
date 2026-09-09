"""Tests for session revocation, logout, and board access guards."""
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_logout_invalidates_session_and_guards_board():
    # 1. Login successfully
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200
    assert "session_id" in login_res.cookies

    # 2. Access protected board endpoint while authenticated -> 200
    board_res = client.get("/api/board")
    assert board_res.status_code == 200
    assert "board" in board_res.json()

    # 3. Call logout endpoint
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # 4. Access protected board endpoint after logout -> strictly 401
    board_after = client.get("/api/board")
    assert board_after.status_code == 401
    assert "Authentication required" in board_after.json()["detail"]

    # 5. /api/auth/me after logout -> 401
    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 401


def test_unauthenticated_request_cannot_access_board():
    # Fresh unauthenticated client
    fresh_client = TestClient(app)
    res = fresh_client.get("/api/board")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]
