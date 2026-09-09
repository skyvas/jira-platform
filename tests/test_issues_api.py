"""Tests for JiraPlatform REST API endpoints."""
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
