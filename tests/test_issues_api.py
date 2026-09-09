"""Tests for Orbit REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_get_projects():
    res = client.get("/api/projects")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["key"] == "PROJ"


def test_create_and_move_issue():
    # 1. Create issue
    create_res = client.post("/api/issues", json={
        "title": "Build Drag and Drop Kanban",
        "description": "Interactive HTML5 drag-and-drop",
        "status": "TODO",
        "priority": "HIGH",
        "assignee": "LeadDev"
    })
    assert create_res.status_code == 200
    issue = create_res.json()
    assert issue["key"].startswith("PROJ-")
    assert issue["status"] == "TODO"

    issue_id = issue["id"]

    # 2. Move issue to IN_PROGRESS
    move_res = client.patch(f"/api/issues/{issue_id}/move", json={
        "new_status": "IN_PROGRESS"
    })
    assert move_res.status_code == 200
    updated = move_res.json()
    assert updated["status"] == "IN_PROGRESS"

    # 3. Invalid move: IN_PROGRESS directly to BACKLOG is forbidden
    bad_res = client.patch(f"/api/issues/{issue_id}/move", json={
        "new_status": "BACKLOG"
    })
    assert bad_res.status_code == 400


def test_unassign_issue():
    """Verify that an issue assigned to an assignee can be unassigned."""
    # 1. Create issue assigned to 'alex'
    create_res = client.post("/api/issues", json={
        "title": "Task To Unassign",
        "status": "TODO",
        "assignee": "alex"
    })
    assert create_res.status_code == 200
    issue = create_res.json()
    issue_id = issue["id"]
    assert issue["assignee"] == "alex"

    # 2. Unassign via JSON null ({"assignee": None})
    unassign_res = client.patch(f"/api/issues/{issue_id}", json={
        "assignee": None
    })
    assert unassign_res.status_code == 200
    updated_issue = unassign_res.json()
    assert updated_issue["assignee"] is None, f"Expected assignee to be None, got: {updated_issue['assignee']}"

    # 3. Re-assign to 'sam'
    reassign_res = client.patch(f"/api/issues/{issue_id}", json={
        "assignee": "sam"
    })
    assert reassign_res.status_code == 200
    assert reassign_res.json()["assignee"] == "sam"

    # 4. Unassign via empty string ({"assignee": ""})
    unassign_empty_res = client.patch(f"/api/issues/{issue_id}", json={
        "assignee": ""
    })
    assert unassign_empty_res.status_code == 200
    assert unassign_empty_res.json()["assignee"] is None, f"Expected assignee to be None, got: {unassign_empty_res.json()['assignee']}"

    # 5. Verify board reflects unassigned state
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    board_res = client.get("/api/board?project_id=PROJ")
    assert board_res.status_code == 200
    board_issues = board_res.json()["issues"]
    board_issue = next(i for i in board_issues if i["id"] == issue_id)
    assert board_issue["assignee"] is None


