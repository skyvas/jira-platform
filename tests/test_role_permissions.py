"""Tests for role-based permissions (Admin-only critical operations)."""
from fastapi.testclient import TestClient
import pytest

from backend.api.app import app

client = TestClient(app)


def setup_module(module):
    # Ensure standard users exist
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})


def test_unauthenticated_requests_blocked_with_401():
    # Logout to clear any session
    client.post("/api/auth/logout")

    # 1. Sprint operations
    res_sprint_create = client.post("/api/sprints", json={"project_id": "proj-1", "name": "Sprint Unauthorized"})
    assert res_sprint_create.status_code == 401

    res_sprint_start = client.post("/api/sprints/some-id/start")
    assert res_sprint_start.status_code == 401

    res_sprint_comp = client.post("/api/sprints/some-id/complete")
    assert res_sprint_comp.status_code == 401

    # 2. Column operations
    res_cols = client.put("/api/board/proj-1/columns", json={"columns": []})
    assert res_cols.status_code == 401

    # 3. Project creation
    res_proj = client.post("/api/projects", json={"key": "UNAUTH", "name": "Unauthorized Project"})
    assert res_proj.status_code == 401

    # 4. User management
    res_user = client.post("/api/users", json={"username": "hacker", "password": "123", "full_name": "Hacker", "email": "h@h.com", "role": "ADMIN"})
    assert res_user.status_code == 401


def test_member_and_viewer_blocked_with_403_from_critical_operations():
    # Fetch existing project and planned sprint created by admin
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_login.status_code == 200

    proj_res = client.get("/api/projects")
    proj_id = proj_res.json()[0]["id"]

    # Admin creates a planned sprint to test start/complete restrictions
    sprint_res = client.post("/api/sprints", json={
        "project_id": proj_id,
        "name": "Sprint Restricted Checks",
        "goal": "Test role enforcement"
    })
    assert sprint_res.status_code == 200
    sprint_id = sprint_res.json()["id"]

    # Test for both MEMBER ('alex') and VIEWER ('sam')
    for test_user in ["alex", "sam"]:
        pwd = f"{test_user}123"
        login_res = client.post("/api/auth/login", json={"username": test_user, "password": pwd})
        assert login_res.status_code == 200

        # 1. Creating sprint -> 403
        bad_sprint = client.post("/api/sprints", json={
            "project_id": proj_id,
            "name": f"Illegal Sprint by {test_user}"
        })
        assert bad_sprint.status_code == 403, f"{test_user} should receive 403 creating sprint"

        # 2. Starting sprint -> 403
        bad_start = client.post(f"/api/sprints/{sprint_id}/start")
        assert bad_start.status_code == 403, f"{test_user} should receive 403 starting sprint"

        # 3. Completing sprint -> 403
        bad_complete = client.post(f"/api/sprints/{sprint_id}/complete")
        assert bad_complete.status_code == 403, f"{test_user} should receive 403 completing sprint"

        # 4. Modifying board columns -> 403
        bad_cols = client.put(f"/api/board/{proj_id}/columns", json={
            "columns": [{"name": "To Do", "status": "TODO", "order_index": 0}]
        })
        assert bad_cols.status_code == 403, f"{test_user} should receive 403 updating columns"

        # 5. Creating project -> 403
        bad_proj = client.post("/api/projects", json={
            "key": f"NA_{test_user.upper()[:2]}",
            "name": f"Forbidden Project by {test_user}"
        })
        assert bad_proj.status_code == 403, f"{test_user} should receive 403 creating project"

        # 6. Creating user -> 403
        bad_create_user = client.post("/api/users", json={
            "username": f"user_by_{test_user}",
            "password": "Password123!",
            "full_name": "Test User",
            "email": "test@test.local",
            "role": "MEMBER"
        })
        assert bad_create_user.status_code == 403, f"{test_user} should receive 403 creating user"


def test_admin_permitted_all_critical_operations():
    # Login as admin
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_login.status_code == 200

    proj_res = client.get("/api/projects")
    proj_id = proj_res.json()[0]["id"]

    # 1. Admin creates sprint
    sprint_res = client.post("/api/sprints", json={
        "project_id": proj_id,
        "name": "Sprint Admin Allowed",
        "goal": "Admin is authorized"
    })
    assert sprint_res.status_code == 200
    sprint_id = sprint_res.json()["id"]

    # 2. Admin starts sprint
    start_res = client.post(f"/api/sprints/{sprint_id}/start")
    assert start_res.status_code == 200

    # 3. Admin completes sprint
    comp_res = client.post(f"/api/sprints/{sprint_id}/complete")
    assert comp_res.status_code == 200

    # 4. Admin updates board columns
    cols_res = client.put(f"/api/board/{proj_id}/columns", json={
        "columns": [
            {"name": "To Do", "status": "TODO", "order_index": 0},
            {"name": "Done", "status": "DONE", "order_index": 1}
        ]
    })
    assert cols_res.status_code == 200

